"""ROUTER modulow — par. 6.5 design doca.

Deterministyczna tablica decyzyjna R1-R4. Dokument moze trafic do KILKU modulow
naraz (reklama finfluencera obiecujaca zyski jest jednoczesnie przypadkiem
Modulu 1 i Modulu 2), dlatego `modules` to lista, nie jedna liczba.

Pierwszenstwo przy `primary_module`: R3 > R2 > R1.
Swiadczenie uslug bez zezwolenia jest naruszeniem powazniejszym niz brak
ujawnienia wspolpracy, a ten powazniejszym niz uchybienie w ekspozycji
ostrzezenia we wlasnym materiale licencjonowanej firmy.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from analyzer.contracts import Relation, Routing, ScopeStatus

# --------------------------------------------------------------------------- #
# Sygnaly leksykalne
# --------------------------------------------------------------------------- #

PROFIT_CLAIM_SIGNALS = {
    "zysk", "zarobisz", "zarabiaj", "stopa zwrotu", "rentownosc", "do 1", "%",
    "podwoj", "pomnoz", "pewny zwrot", "gwarantowany zwrot", "zwrot rocznie",
}

# Rekomendacja dotyczaca instrumentow = doradztwo inwestycyjne, art. 76 ustawy
RECOMMENDATION_SIGNALS = {
    "polecamy akcje", "polecam akcje", "rekomendujemy", "rekomendacja",
    "nasz portfel", "sygnaly kupna", "sygnaly inwestycyjne", "sygnaly",
    "powiemy co kupic", "powiem co kupic", "co kupic teraz", "typy na gielde",
    "doradztwo inwestycyjne", "doradzamy w inwestycjach", "zarzadzamy portfelem",
    "wskazemy instrumenty", "wybierzemy spolki",
}

ADVISORY_BUSINESS_SIGNALS = {
    "wealth management", "investment consulting", "family office",
    "zarzadzanie majatkiem", "doradztwo finansowe", "butik inwestycyjny",
}


# Wzorce uzupelniajace slowniki literalne powyzej. Polski jest fleksyjny, a
# dopasowanie literalne przeoczalo odmiane: "rekomendacja" nie jest podciagiem
# "rekomendacji" ani "rekomendacje". Literaly zostaja (Modul 3 dopasowuje je
# literalnie), wzorce sa DODATKIEM, nie zamiennikiem.
RECOMMENDATION_PATTERNS: tuple[str, ...] = (
    r"\brekomend\w*",
    r"\bpolec\w*\s+(akcj|obligacj|fundusz|etf|cfd|spolk)\w*",
    r"\bnasz\w*\s+portfel\w*",
    r"\bsygnal\w*\s+(kupna|sprzedazy|inwestycyjn\w*)",
    r"\b(powiem|powiemy)\s+co\s+kupic",
    r"\bco\s+kupic\s+teraz",
    r"\btyp\w*\s+na\s+gield\w*",
    r"\bdoradztw\w*\s+inwestycyjn\w*",
    r"\bdoradza\w*\s+w\s+inwestycj\w*",
    r"\bzarzadza\w*\s+portfel\w*",
    r"\bwskaz\w*\s+instrument\w*",
    r"\bwybierz\w*\s+spolk\w*",
)

PROFIT_CLAIM_PATTERNS: tuple[str, ...] = (
    r"\bzysk\w*",
    r"\bzarabia\w*",
    r"\bzarob\w*",
    r"\bstop\w*\s+zwrotu",
    r"\brentown\w*",
    r"\bpodwoj\w*",
    r"\bpomnoz\w*",
    r"\b(pewny|gwarantowany)\w*\s+zwrot\w*",
    r"\bzwrot\w*\s+rocznie",
    # Dowolny procent. W reklamie inwestycyjnej liczba z procentem to praktycznie
    # zawsze obietnica stopy zwrotu. Zastapilo to goly literal "%", ktory lapal
    # kazdy znak procenta, i bezsensowny literal "do 1".
    r"\d+[.,]?\d*\s*%",
)

ADVISORY_BUSINESS_PATTERNS: tuple[str, ...] = (
    r"wealth\s+management",
    r"investment\s+consulting",
    r"family\s+office",
    r"zarzadzani\w*\s+majatk\w*",
    r"\bdoradztw\w*\s+finansow\w*",
    r"butik\w*\s+inwestycyjn\w*",
)


def normalize(text: str) -> str:
    """Male litery, bez ogonkow, zwiniete biale znaki.

    Publiczna — korzysta z niej takze Modul 3, zeby dopasowywac sygnaly
    dokladnie tak samo jak router.
    """
    lowered = text.lower()
    decomposed = unicodedata.normalize("NFKD", lowered)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    stripped = stripped.replace("ł", "l")
    return re.sub(r"\s+", " ", stripped)


# Alias zgodnosciowy — nie usuwac, importuja go inne moduly.
_normalize = normalize


def _has_any(haystack: str, needles: set[str]) -> bool:
    return any(n in haystack for n in needles)


def _matches_any(haystack: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(p, haystack) for p in patterns)


def has_profit_claims(text: str) -> bool:
    """Czy material twierdzi cokolwiek o zyskach.

    Decyduje o tym, czy DOLOZYC Modul 2 do dokumentu, ktory podstawowo
    nalezy do Modulu 1 albo 3 — bo obietnica zysku uruchamia wymog
    informacji o ryzyku (art. 44 ust. 2 lit. b rozp. 2017/565).
    """
    norm = normalize(text)
    return _has_any(norm, PROFIT_CLAIM_SIGNALS) or _matches_any(
        norm, PROFIT_CLAIM_PATTERNS
    )


def has_investment_recommendation(text: str) -> bool:
    """Czy tresc zawiera rekomendacje nabycia/zbycia/trzymania instrumentow.

    To warunek konieczny Modulu 3 — sama oferta 'family office' bez
    rekomendacji nie jest jeszcze doradztwem inwestycyjnym w rozumieniu
    art. 76 ustawy o obrocie.
    """
    norm = normalize(text)
    return _has_any(norm, RECOMMENDATION_SIGNALS) or _matches_any(
        norm, RECOMMENDATION_PATTERNS
    )


def looks_like_advisory_business(text: str) -> bool:
    norm = normalize(text)
    return _has_any(norm, ADVISORY_BUSINESS_SIGNALS) or _matches_any(
        norm, ADVISORY_BUSINESS_PATTERNS
    )


# --------------------------------------------------------------------------- #
# Wejscie routera
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class RoutingInput:
    """Wynik resolvera podmiotow (osoba A) + bramy zakresu (osoba B).

    Router nie robi zadnego matchowania sam — konsumuje gotowe ustalenia.
    """

    scope_status: ScopeStatus
    text: str
    publisher_relation: Relation
    publisher_is_authorized: bool
    mentions_authorized_firm: bool
    firm_name_in_ad: str | None = None
    publisher_name: str | None = None


@dataclass(frozen=True)
class RoutingDecision:
    modules: list[int]
    primary_module: int | None
    routing: Routing


def route(inp: RoutingInput) -> RoutingDecision:
    """Przypisz dokument do modulow wg tablicy R1-R4."""
    who = inp.publisher_name or "publikujacy"
    firm = inp.firm_name_in_ad or "firma inwestycyjna"
    profit = has_profit_claims(inp.text)

    # Poza zakresem nie oceniamy, ale TEZ NIE KASUJEMY — trafia do widoku
    # "poza zakresem" z zapisanym powodem.
    if inp.scope_status is ScopeStatus.OUT_OF_SCOPE:
        return RoutingDecision(
            modules=[],
            primary_module=None,
            routing=Routing(
                rule="R4",
                reason=(
                    "Material poza zakresem rezimu MiFID II — nie rozpoznano "
                    "opakowania bedacego instrumentem finansowym. Zachowany "
                    "do weryfikacji, nieoceniany regulami."
                ),
                scope_gate=inp.scope_status,
            ),
        )

    # --- R3: doradztwo bez zezwolenia (najpowazniejsze) -------------------- #
    if not inp.publisher_is_authorized and has_investment_recommendation(inp.text):
        modules = [3]
        if profit:
            modules.append(2)
        return RoutingDecision(
            modules=modules,
            primary_module=3,
            routing=Routing(
                rule="R3",
                reason=(
                    f"{who} nie wystepuje w rejestrze autoryzowanych firm "
                    f"inwestycyjnych, a tresc zawiera rekomendacje dotyczace "
                    f"instrumentow finansowych — mozliwe doradztwo inwestycyjne "
                    f"bez zezwolenia (art. 76 ustawy o obrocie)."
                    + (
                        " Material zawiera twierdzenia o zyskach, wiec dodatkowo "
                        "oceniany regulami Modulu 2."
                        if profit
                        else ""
                    )
                ),
                scope_gate=inp.scope_status,
            ),
        )

    # --- R2: podmiot trzeci reklamuje cos nieswojego ----------------------- #
    if inp.publisher_relation is not Relation.OFFICIAL and inp.mentions_authorized_firm:
        modules = [1]
        if profit:
            modules.append(2)
        return RoutingDecision(
            modules=modules,
            primary_module=1,
            routing=Routing(
                rule="R2",
                reason=(
                    f"{who} nie jest oficjalnym kanalem {firm}, a material "
                    f"reklamuje te firme lub jej produkty — reklama przez podmiot "
                    f"trzeci."
                    + (
                        " Material zawiera twierdzenia o zyskach, wiec dodatkowo "
                        "oceniany regulami Modulu 2."
                        if profit
                        else ""
                    )
                ),
                scope_gate=inp.scope_status,
            ),
        )

    # --- R1: wlasny material licencjonowanej firmy ------------------------- #
    if inp.publisher_relation is Relation.OFFICIAL and inp.publisher_is_authorized:
        return RoutingDecision(
            modules=[2],
            primary_module=2,
            routing=Routing(
                rule="R1",
                reason=(
                    f"Material opublikowany bezposrednio przez {firm} "
                    f"(oficjalny kanal, podmiot w rejestrze KNF) — pelna ocena "
                    f"informacji o ryzyku."
                ),
                scope_gate=inp.scope_status,
            ),
        )

    # --- R4: triage -------------------------------------------------------- #
    return RoutingDecision(
        modules=[],
        primary_module=None,
        routing=Routing(
            rule="R4",
            reason=(
                "Nie udalo sie przypisac modulu: brak dopasowania publikujacego "
                "do rejestru i brak wzmianki o autoryzowanej firmie. Do przegladu "
                "recznego; zasila liste brakow w rejestrze."
            ),
            scope_gate=inp.scope_status,
        ),
    )

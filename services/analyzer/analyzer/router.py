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
    "zysk", "zarobisz", "zarabiaj", "stopa zwrotu", "rentownosc",
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
    r"\b(?:doradz|powie)\w*,?\s+w\s+co\s+(?:zainwestowac|inwestowac|lokowac)",
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
    # Procent. Trafia tu tylko, gdy przezyl mask_non_claims(): procent bez slowa
    # o zysku/zwrocie w poblizu albo w kontekscie straty, znizki, sprawy sadowej
    # jest tam zamaskowany ("76% rachunkow traci pieniadze" to ostrzezenie, nie
    # obietnica). Wiec pozostaje "oprocentowanie 7%", "nawet 15% zysku".
    r"\d+[.,]?\d*\s*%",
)

# --------------------------------------------------------------------------- #
# Wykluczenia: to NIE jest obietnica zysku
# --------------------------------------------------------------------------- #

_PROFIT_WORD = (
    r"(?:zysk\w*|zarob\w*|zarabia\w*|rentown\w*|stop\w*\s+zwrotu|dochod\w*|wynik\w*)"
)
# Zaprzeczenie/zastrzezenie: "nie oznacza gwarancji zysku", "nie gwarantujemy
# zyskow", "brak gwarancji zysku", "bez gwarancji zarobku". Celowo wymagamy
# slowa o gwarancji/obietnicy: "bez ryzyka zarobisz" to nadal obietnica.
_NEGATED_PROFIT = re.compile(
    r"\b(?:nie|ani|bez|brak)\s+(?:\w+\s+){0,2}?"
    r"(?:gwarancj\w*|gwarantuj\w*|obiecuj\w*|zapewnia\w*|zapewnic\w*)"
    r"\s+(?:\w+\s+){0,2}?" + _PROFIT_WORD
)
# "podatek od zyskow kapitalowych" to nazwa podatku, nie obietnica
_TAX_NAME = re.compile(r"\bzysk\w*\s+kapitalow\w*")
_FEE_WORD = re.compile(r"\b(?:podatek|podatk\w*|opodatkowan\w*|prowizj\w*|oplat\w*|koszt\w*|marz[aey]\b)")
_PERCENT = re.compile(r"\d+[.,]?\d*\s*%")
# Slowa zwrotu/zysku: procent obok nich to stopa zwrotu.
_RETURN_WORD = re.compile(
    r"\b(?:zysk\w*|zwrot\w*|stop\w*\s+zwrotu|rentown\w*|oprocentowan\w*|odsetk\w*"
    r"|zarob\w*|zarabia\w*|dochod\w*|wzrost\w*|przyrost\w*|podwoj\w*|pomnoz\w*"
    r"|rocznie|miesiecznie|kwartalnie|w\s+skali\s+(?:roku|miesiaca)|p\.a\.)"
)
# Kontekst straty, znizki, sprawy sadowej, kodu promocyjnego: procent obok nich
# to NIE stopa zwrotu.
_NON_RETURN_WORD = re.compile(
    r"\b(?:trac\w*|strat\w*|stracic|znizk\w*|rabat\w*|taniej|promocj\w*|kod\w*\s+promocyjn\w*"
    r"|kupon\w*|spraw\w*|wyrok\w*|wygra\w*|przegra\w*|sadow\w*|pozw\w*)"
)
# Program partnerski / polecen: bonus za polecenie to nie zwrot z inwestycji.
_REFERRAL = re.compile(
    r"\bprogram\w*\s+(?:partnersk|polecaj|afiliac)\w*|\b(?:kod|link)\w*\s+polecaj\w*"
    r"|\bpolec\w*\s+znajomym|\bbonus\w*\s+za\s+polecen\w*"
)
_WINDOW = 50
# Granica zdania; kropka po skrocie ("min. 3 zl") i przed cyfra nie konczy zdania.
_SENTENCE_BREAK = re.compile(
    r"(?<!\bmin)(?<!\bmln)(?<!\bmld)(?<!\btys)(?<!\bnp)(?<!\btj)(?<!\bok)"
    r"[.!?]+\s+(?=[a-z])"
)


def _blank(chars: list[str], start: int, end: int) -> None:
    for i in range(start, end):
        chars[i] = " "


def mask_non_claims(norm: str) -> str:
    """Zamaskuj (spacjami, ta sama dlugosc) fragmenty, ktore nie sa obietnica zysku.

    Wejscie: tekst po normalize(). Maskowane: zaprzeczone zastrzezenia o zysku,
    nazwa podatku "zysk kapitalowy" oraz procenty w zdaniach o podatkach,
    prowizjach i oplatach (stawka 19%, prowizja 0,29% to nie stopa zwrotu).
    """
    chars = list(norm)
    for rx in (_NEGATED_PROFIT, _TAX_NAME):
        for m in rx.finditer(norm):
            _blank(chars, m.start(), m.end())
    start = 0
    bounds = [m.end() for m in _SENTENCE_BREAK.finditer(norm)] + [len(norm)]
    for end in bounds:
        sentence = norm[start:end]
        if _REFERRAL.search(sentence):
            _blank(chars, start, end)  # cale zdanie o programie partnerskim
            start = end
            continue
        fee = bool(_FEE_WORD.search(sentence))
        for pm in _PERCENT.finditer(sentence):
            if fee or not _percent_is_return(sentence, pm):
                _blank(chars, start + pm.start(), start + pm.end())
        start = end
    return "".join(chars)


def _percent_is_return(sentence: str, pm: re.Match[str]) -> bool:
    """Czy procent w zdaniu jest stopa zwrotu: slowo zysku w poblizu, i blizej
    niz slowo straty/znizki/sprawy."""
    lo, hi = max(0, pm.start() - _WINDOW), pm.end() + _WINDOW
    window = sentence[lo:hi]
    centre = pm.start() - lo

    def nearest(rx: re.Pattern[str]) -> int | None:
        ds = [min(abs(m.start() - centre), abs(m.end() - centre)) for m in rx.finditer(window)]
        return min(ds) if ds else None

    ret, non = nearest(_RETURN_WORD), nearest(_NON_RETURN_WORD)
    if ret is None:
        return False
    return non is None or ret <= non


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
    norm = mask_non_claims(normalize(text))
    return _has_any(norm, PROFIT_CLAIM_SIGNALS) or _matches_any(
        norm, PROFIT_CLAIM_PATTERNS
    )


def has_investment_recommendation(text: str) -> bool:
    """Czy tresc zawiera rekomendacje nabycia/zbycia/trzymania instrumentow.

    To warunek konieczny Modulu 3 — sama oferta 'family office' bez
    rekomendacji nie jest jeszcze doradztwem inwestycyjnym w rozumieniu
    art. 76 ustawy o obrocie.
    """
    return bool(find_recommendations(normalize(text)))


# Negacja tuz przed slowem kluczowym zamienia rekomendacje w zastrzezenie:
# "nie stanowi porady ani rekomendacji", "wpisy nie sa rekomendacjami".
_NEGATION_TOKENS = frozenset(
    {"nie", "ani", "zadna", "zadne", "zadnej", "zadnych", "zadnym", "bez", "brak"}
)
_NEGATION_WINDOW = 6
_CLAUSE_BREAK = re.compile(r"[.!?;:,]")
_RECOMMENDATION_ALL: tuple[str, ...] = tuple(
    re.escape(sig) for sig in sorted(RECOMMENDATION_SIGNALS)
) + RECOMMENDATION_PATTERNS


def _is_negated(norm: str, start: int) -> bool:
    """Czy w ~6 tokenach przed `start` (w tej samej frazie) stoi zaprzeczenie."""
    before = norm[max(0, start - 80) : start]
    breaks = list(_CLAUSE_BREAK.finditer(before))
    if breaks:
        before = before[breaks[-1].end() :]
    tokens = re.findall(r"[a-z0-9]+", before)[-_NEGATION_WINDOW:]
    return any(t in _NEGATION_TOKENS for t in tokens)


def find_recommendations(norm: str) -> list[str]:
    """Dopasowania sygnalow rekomendacji w tekscie PO normalize(), bez zaprzeczonych.

    Publiczne: korzysta z tego rowniez Modul 3, zeby zastrzezenia "nie stanowi
    rekomendacji" nie liczyly sie jako rekomendacja.
    """
    hits: list[str] = []
    for p in _RECOMMENDATION_ALL:
        for m in re.finditer(p, norm):
            if not _is_negated(norm, m.start()):
                hits.append(m.group(0))
    return hits


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

    # --- R4: podmiot nieustalony, ale material OCENIAMY -------------------- #
    #
    # Wazna poprawka wzgledem pierwotnego designu. Wczesniej R4 dawalo
    # `modules=[]`, czyli ZERO ocenionych regul. Na realnym dokumencie ze
    # scrapera (reklama z Meta Ad Library, bez jeszcze dopasowanego rejestru
    # KNF) oznaczalo to, ze material nie byl oceniany w ogole — a razem z nim
    # przepadaly wyniki regul DET, ktore scraper juz policzyl.
    #
    # Wymogi informacji o ryzyku z art. 44 rozporzadzenia del. 2017/565 dotycza
    # MATERIALU, nie statusu publikujacego. To, czy podmiot ma zezwolenie,
    # rozstrzyga o PRZYPISANIU do Modulu 1 albo 3 — nie o tym, czy ostrzezenie
    # o ryzyku musi byc czytelne. Dlatego Modul 2 jest ocena bazowa kazdego
    # materialu w zakresie, a `status: triage` nadal sygnalizuje, ze podmiot
    # wymaga ustalenia przez czlowieka.
    return RoutingDecision(
        modules=[2],
        primary_module=2,
        routing=Routing(
            rule="R4",
            reason=(
                "Nie ustalono podmiotu: brak dopasowania publikujacego do "
                "rejestru KNF i brak wzmianki o autoryzowanej firmie. Material "
                "jest jednak w zakresie, wiec oceniono informacje o ryzyku "
                "(Modul 2). Przypisanie podmiotu wymaga przegladu recznego "
                "i zasila liste brakow w rejestrze."
            ),
            scope_gate=inp.scope_status,
        ),
    )

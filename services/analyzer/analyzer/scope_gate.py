"""Brama zakresu — par. 6.6 design doca.

KRYTERIUM JEST INSTRUMENTOWE, NIE AKTYWOWE.

Material jest w zakresie, gdy rozpoznano OPAKOWANIE bedace instrumentem
finansowym wg art. 2 ustawy o obrocie instrumentami finansowymi — bez wzgledu
na to, co jest aktywem bazowym.

CFD na bitcoina JEST instrumentem finansowym (art. 2 ust. 1 pkt 2 lit. h)
i zostaje w zakresie z PODWYZSZONYM priorytetem. Slownikowe wykluczanie slow
"krypto" / "bitcoin" wycielo by najagresywniej reklamowane produkty detaliczne,
czyli dalo false negative dokladnie tam, gdzie UKNF zalezy najbardziej.

Poza zakresem jest wylacznie zakup spot bez opakowania — podlega rezimowi MiCA,
a nie MiFID II, na ktorym stoi nasze 18 regul.

Ta warstwa to PRE-FILTR leksykalny. Rozstrzygniecie niepewnych przypadkow
nalezy do LLM-a z lista instrumentow z Zalacznika 3 w promptcie — "kontrakt
na roznice kursu", "CFD" i "roznice kursowe z dzwignia" to to samo opakowanie
opisane trzema sposobami i regex tego nie obejmie.
"""

from __future__ import annotations

import re
import unicodedata

from analyzer.contracts import Scope, ScopeStatus

# --------------------------------------------------------------------------- #
# Opakowania = instrumenty finansowe wg art. 2 i art. 3 ustawy o obrocie
# --------------------------------------------------------------------------- #

INSTRUMENT_WRAPPERS: dict[str, tuple[str, str]] = {
    # klucz -> (nazwa opakowania, podstawa prawna)
    "cfd": ("cfd", "art. 2 ust. 1 pkt 2 lit. h ustawy o obrocie"),
    "kontrakt na roznice": ("cfd", "art. 2 ust. 1 pkt 2 lit. h ustawy o obrocie"),
    "kontrakty na roznice": ("cfd", "art. 2 ust. 1 pkt 2 lit. h ustawy o obrocie"),
    "roznice kursowe": ("cfd", "art. 2 ust. 1 pkt 2 lit. h ustawy o obrocie"),
    "kontrakt terminowy": ("futures", "art. 2 ust. 1 pkt 2 lit. c ustawy o obrocie"),
    "kontrakty terminowe": ("futures", "art. 2 ust. 1 pkt 2 lit. c ustawy o obrocie"),
    "futures": ("futures", "art. 2 ust. 1 pkt 2 lit. c ustawy o obrocie"),
    "opcja": ("opcje", "art. 2 ust. 1 pkt 2 lit. c ustawy o obrocie"),
    "opcje": ("opcje", "art. 2 ust. 1 pkt 2 lit. c ustawy o obrocie"),
    "swap": ("swap", "art. 2 ust. 1 pkt 2 lit. c ustawy o obrocie"),
    "forward": ("forward", "art. 2 ust. 1 pkt 2 lit. c ustawy o obrocie"),
    "etf": ("etf", "art. 2 ust. 1 pkt 2 lit. a ustawy o obrocie"),
    "etn": ("etn", "art. 3 pkt 1 lit. a ustawy o obrocie"),
    "certyfikat inwestycyjny": ("certyfikat", "art. 3 pkt 1 lit. a ustawy o obrocie"),
    "certyfikaty inwestycyjne": ("certyfikat", "art. 3 pkt 1 lit. a ustawy o obrocie"),
    "tytul uczestnictwa": ("fundusz", "art. 2 ust. 1 pkt 2 lit. a ustawy o obrocie"),
    "fundusz inwestycyjny": ("fundusz", "art. 2 ust. 1 pkt 2 lit. a ustawy o obrocie"),
    "jednostki uczestnictwa": ("fundusz", "art. 2 ust. 1 pkt 2 lit. a ustawy o obrocie"),
    "akcje": ("akcje", "art. 3 pkt 1 lit. a ustawy o obrocie"),
    "akcji": ("akcje", "art. 3 pkt 1 lit. a ustawy o obrocie"),
    "obligacje": ("obligacje", "art. 3 pkt 1 lit. a ustawy o obrocie"),
    "obligacji": ("obligacje", "art. 3 pkt 1 lit. a ustawy o obrocie"),
    "list zastawny": ("list_zastawny", "art. 3 pkt 1 lit. a ustawy o obrocie"),
    "warrant": ("warrant", "art. 3 pkt 1 lit. a ustawy o obrocie"),
    "kwit depozytowy": ("kwit_depozytowy", "art. 3 pkt 1 lit. a ustawy o obrocie"),
    "prawa pochodne": ("prawa_pochodne", "art. 3 pkt 1 lit. b ustawy o obrocie"),
    "instrument pochodny": ("pochodny", "art. 2 ust. 1 pkt 2 ustawy o obrocie"),
    "uprawnienia do emisji": ("emisje", "art. 2 ust. 1 pkt 2 lit. j ustawy o obrocie"),
}

# --------------------------------------------------------------------------- #
# Aktywa bazowe — NIE decyduja o zakresie, tylko go opisuja i tagują
# --------------------------------------------------------------------------- #

CRYPTO_UNDERLYING = {
    "krypto", "kryptowalut", "kryptoaktyw", "bitcoin", "btc", "ethereum", "eth",
    "altcoin", "token", "stablecoin", "defi", "nft", "blockchain", "staking",
}

# Sygnaly zakupu spot, czyli BRAKU opakowania. Dopiero to wyklucza z zakresu.
SPOT_CRYPTO_SIGNALS = {
    "kup bitcoina", "kup krypto", "kantor krypto", "gielda krypto", "portfel krypto",
    "wlasny portfel", "cold wallet", "hot wallet", "wymien krypto", "wyplac krypto",
    "stakuj", "staking", "kopanie krypto", "mining krypto", "airdrop",
}

NON_FINANCIAL_ASSETS = {
    "nieruchomosc", "apartament", "mieszkanie na wynajem", "dzialka", "grunt",
    "dzielo sztuki", "obraz inwestycyjny", "whisky inwestycyjna", "wino inwestycyjne",
    "zloto fizyczne", "sztabka", "moneta kolekcjonerska", "diament",
}

LEVERAGE_SIGNALS = {"dzwignia", "leverage", "1:30", "1:100", "1:500", "margin"}


def _normalize(text: str) -> str:
    """Male litery, bez ogonkow, znormalizowane biale znaki.

    Bez tego 'Kontrakt na Różnicę' nie trafi w klucz 'kontrakt na roznice'.
    """
    lowered = text.lower()
    decomposed = unicodedata.normalize("NFKD", lowered)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    # polskie l z kreska nie rozklada sie przez NFKD
    stripped = stripped.replace("ł", "l")
    return re.sub(r"\s+", " ", stripped)


def _find_any(haystack: str, needles: set[str]) -> str | None:
    for n in needles:
        if n in haystack:
            return n
    return None


def classify_scope(text: str) -> Scope:
    """Zdecyduj, czy material podlega regulom MiFID II.

    Kolejnosc sprawdzen jest istotna:
    1. Najpierw szukamy OPAKOWANIA. Jesli jest — material jest w zakresie,
       niezaleznie od aktywa bazowego. To chroni CFD na krypto.
    2. Dopiero gdy opakowania NIE ma, sprawdzamy, czy to zakup spot krypto
       albo aktywo niefinansowe — i wtedy wykluczamy z podaniem powodu.
    3. Nic nie rozpoznane -> `uncertain`, czyli do triage, NIE do kosza.
    """
    norm = _normalize(text)

    underlying: str | None = None
    tags: list[str] = []

    if _find_any(norm, CRYPTO_UNDERLYING):
        underlying = "crypto"
    elif _find_any(norm, NON_FINANCIAL_ASSETS):
        underlying = "non_financial"

    # --- 1. opakowanie decyduje -------------------------------------------- #
    for needle, (wrapper, basis) in INSTRUMENT_WRAPPERS.items():
        if needle in norm:
            if underlying == "crypto":
                # NIE wykluczamy. Oznaczamy i podnosimy priorytet.
                tags.append("crypto_derivative")
            if _find_any(norm, LEVERAGE_SIGNALS):
                tags.append("leveraged")
            return Scope(
                status=ScopeStatus.IN_SCOPE,
                instrument_wrapper=wrapper,
                underlying=underlying,
                legal_basis=basis,
                tags=tags,
            )

    # --- 2. brak opakowania: dopiero teraz mozna wykluczyc ------------------ #
    if underlying == "crypto" and _find_any(norm, SPOT_CRYPTO_SIGNALS):
        return Scope(
            status=ScopeStatus.OUT_OF_SCOPE,
            underlying="crypto",
            reason="spot_crypto_mica",
            legal_basis="brak opakowania bedacego instrumentem finansowym; rezim MiCA",
        )

    if underlying == "non_financial":
        return Scope(
            status=ScopeStatus.OUT_OF_SCOPE,
            underlying="non_financial",
            reason="not_financial_instrument",
            legal_basis="nie jest instrumentem finansowym wg art. 2 ustawy o obrocie",
        )

    # --- 3. nie wiemy -> triage, nie kosz ---------------------------------- #
    return Scope(
        status=ScopeStatus.UNCERTAIN,
        underlying=underlying,
        reason="nie rozpoznano opakowania instrumentu — wymaga oceny LLM lub recznej",
    )

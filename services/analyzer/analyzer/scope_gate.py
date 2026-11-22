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

# WZORCE, nie dopasowanie literalne — polski jest jezykiem fleksyjnym i reklama
# napisze "handluj kontraktami na roznice", a nie "kontrakt na roznice".
# Dopasowanie literalne przeoczyloby wiekszosc realnych materialow.
# Wzorce stosujemy do tekstu PO normalizacji (male litery, bez ogonkow).
#
# (wzorzec, nazwa opakowania, podstawa prawna)
ART2_DERIV = "art. 2 ust. 1 pkt 2 lit. c ustawy o obrocie"
ART2_CFD = "art. 2 ust. 1 pkt 2 lit. h ustawy o obrocie"
ART2_FUND = "art. 2 ust. 1 pkt 2 lit. a ustawy o obrocie"
ART3_SEC = "art. 3 pkt 1 lit. a ustawy o obrocie"

INSTRUMENT_WRAPPERS: list[tuple[str, str, str]] = [
    (r"\bcfd\w*", "cfd", ART2_CFD),
    (r"kontrakt\w*\s+na\s+roznic\w*", "cfd", ART2_CFD),
    (r"roznic\w*\s+kursow\w*", "cfd", ART2_CFD),
    (r"kontrakt\w*\s+terminow\w*", "futures", ART2_DERIV),
    (r"\bfutures\b", "futures", ART2_DERIV),
    # Zawezone formy, bo `opcj\w*` lapie "opcjonalnie".
    (r"\bopcj(a|e|i|ami|ach|om)\b", "opcje", ART2_DERIV),
    (r"\bswap\w*", "swap", ART2_DERIV),
    (r"\bforward\w*", "forward", ART2_DERIV),
    (r"\betf\w*", "etf", ART2_FUND),
    (r"\betn\w*", "etn", ART3_SEC),
    # ETP / ETC — produkty notowane na gieldzie, zbywalne papiery wartosciowe.
    # Stoja PRZED "akcje", bo reklama ETP czesto porownuje go do akcji
    # ("inwestowanie w Solane w podobny sposob jak zakup akcji") i bez tego
    # wykrylibysmy opakowanie "akcje" na podstawie porownania, nie instrumentu.
    (r"\betp\w*", "etp", ART3_SEC),
    (r"\betc\b", "etc", ART3_SEC),
    (r"\bexchange\s+traded\s+(product|note|commodit)\w*", "etp", ART3_SEC),
    # Notowanie na rynku regulowanym samo w sobie wskazuje papier wartosciowy.
    (r"notowan\w*\s+na\s+(gield|rynku\s+regulowan)\w*", "papier_notowany", ART3_SEC),
    (r"giel\w*\s+papierow\s+wartosciowych", "papier_notowany", ART3_SEC),
    (r"certyfikat\w*\s+inwestycyjn\w*", "certyfikat", ART3_SEC),
    (r"tytul\w*\s+uczestnictwa", "fundusz", ART2_FUND),
    (r"fundusz\w*\s+inwestycyjn\w*", "fundusz", ART2_FUND),
    (r"jednostk\w*\s+uczestnictwa", "fundusz", ART2_FUND),
    # "akcja promocyjna" / "akcja marketingowa" to NIE instrument finansowy,
    # a w reklamach wystepuje czesto — stad negatywny lookahead.
    (
        r"\bakcj(a|e|i|ami|ach|om)\b"
        r"(?!\s*(promocyjn|marketingow|reklamow|charytatywn|spoleczn|informacyjn))",
        "akcje",
        ART3_SEC,
    ),
    (r"\bobligacj\w*", "obligacje", ART3_SEC),
    (r"list\w*\s+zastawn\w*", "list_zastawny", ART3_SEC),
    (r"\bwarrant\w*", "warrant", ART3_SEC),
    (r"kwit\w*\s+depozytow\w*", "kwit_depozytowy", ART3_SEC),
    (r"praw\w*\s+pochodn\w*", "prawa_pochodne", "art. 3 pkt 1 lit. b ustawy o obrocie"),
    (r"instrument\w*\s+pochodn\w*", "pochodny", "art. 2 ust. 1 pkt 2 ustawy o obrocie"),
    (r"uprawnien\w*\s+do\s+emisji", "emisje", "art. 2 ust. 1 pkt 2 lit. j ustawy o obrocie"),
]

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


# --------------------------------------------------------------------------- #
# Deterministyczne sygnaly POZA zakresem (zywe dane 21.11: kancelarie
# frankowe, kupony, karty bankowe, ostrzezenia o oszustwach). Obowiazuja
# WYLACZNIE, gdy nie ma zadnego sygnalu instrumentu finansowego.
# --------------------------------------------------------------------------- #

# (wzorzec, powod). Wzorce na tekscie po normalizacji.
OUT_OF_SCOPE_SIGNALS: list[tuple[str, str]] = [
    (r"\bfrankowicz\w*|\bkredyt\w*\s+(?:we?\s+)?frank\w*|\bfrank\w*\s+szwajcarsk\w*"
     r"|uniewazni\w*\s+umow\w*|\bsankcj\w*\s+kredyt\w*\s+darmow\w*",
     "kredyt_frankowy_usluga_prawna"),
    (r"\bkod\w*\s+(?:promocyjn|rabatow)\w*|\bkupon\w*|\bkody\s+promocyjn\w*"
     r"|\bznizk\w*|\brabat\w*|\bvoucher\w*",
     "kupony_i_znizki"),
    (r"\bkart\w*\s+(?:walutow|kredytow|debetow|platnicz|przedplacon)\w*",
     "produkt_bankowy_karta"),
    (r"\bpodaj\w*\s+sie\s+za\b|\bpodszywa\w*|\boszust\w*|\boszukan\w*"
     r"|\bphishing\w*|\bwyludz\w*",
     "ostrzezenie_o_oszustwie"),
]

# Jakikolwiek sygnal instrumentu / uslugi inwestycyjnej wylacza wykluczenie.
INSTRUMENT_HINT = re.compile(
    r"\bakcj(?:a|e|i|ami|ach|om)\b|\betf\w*|\bcfd\w*|\bobligacj\w*|\bfundusz\w*"
    r"|\bkontrakt\w*|\bforex\b|\bfx\b|\bdzwigni\w*|\bleverage\b"
    r"|(?:rachun\w*|kont\w*|dom\w*)\s+maklersk\w*|\bmaklersk\w*"
    r"|portfel\w*\s+inwestycyjn\w*|\bgield\w*|\bpapier\w*\s+wartosciow\w*"
    r"|\binwestowa\w*|\bopcj(?:a|e|i|ami|ach|om)\b|\bfutures\b|\bswap\w*|\bwarrant\w*"
)


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
    for pattern, wrapper, basis in INSTRUMENT_WRAPPERS:
        if re.search(pattern, norm):
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

    # --- 2b. sygnaly poza zakresem, o ile brak sygnalu instrumentu -------- #
    if not INSTRUMENT_HINT.search(norm):
        for pattern, reason in OUT_OF_SCOPE_SIGNALS:
            if re.search(pattern, norm):
                return Scope(
                    status=ScopeStatus.OUT_OF_SCOPE,
                    underlying=underlying,
                    reason=reason,
                    legal_basis="brak opakowania bedacego instrumentem finansowym",
                )

    # --- 3. nie wiemy -> triage, nie kosz ---------------------------------- #
    return Scope(
        status=ScopeStatus.UNCERTAIN,
        underlying=underlying,
        reason="nie rozpoznano opakowania instrumentu — wymaga oceny LLM lub recznej",
    )

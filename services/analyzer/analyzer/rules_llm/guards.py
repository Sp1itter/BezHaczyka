"""Straznicy werdyktow modelu — obiektywne elementy rozstrzygane W KODZIE.

DLACZEGO TO ISTNIEJE

Bielik 4.5B ignoruje czesc polecen z promptow (zob. preconditions.py,
lang_consistency.py). Tam, gdzie kryterium da sie sprawdzic wzorcem w tekscie,
nie polegamy na modelu: po sparsowaniu odpowiedzi wsadu `apply_guards`
koryguje werdykt, a `evidence` niesie doslowny cytat albo jasne
"rozstrzygniete w kodzie: ...".

ZASADY

  - Straznik NIGDY nie rusza `not_applicable`: awaria modelu, pominieta regula
    albo nieznany werdykt niczego nie twierdza i tak ma zostac.
  - Straznik reguly 2 moze zamienic fail na pass (jednoznaczne oznaczenie
    reklamy w tekscie jest faktem, nie opinia). Pozostali straznicy tylko
    PRZESTAWIAJA pass na fail, gdy model "zobaczyl" cos, czego w tekscie nie ma
    (halucynacja), albo gdy tekst jawnie narusza regule — nigdy odwrotnie.
  - Wzorce dzialaja po normalize() (male litery, bez ogonkow).
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable, Mapping

from analyzer.contracts import Engine, Evidence, EvidenceKind, RuleResult, Verdict
from analyzer.router import normalize

RuleMeta = Mapping[str, tuple[str, int, str]]

# --------------------------------------------------------------------------- #
# Pomocnik: dopasowanie na tekscie znormalizowanym, cytat z ORYGINALU
# --------------------------------------------------------------------------- #


def _norm_with_map(text: str) -> tuple[str, list[int]]:
    """Jak normalize(), ale zwraca tez mape indeks_znormalizowany -> oryginalu.

    Dzieki temu cytat jest doslownym fragmentem materialu (z ogonkami i wielkoscia
    liter), a wzorce dalej dzialaja na tekscie bez ogonkow.
    """
    out: list[str] = []
    idx: list[int] = []
    prev_space = False
    for i, ch in enumerate(text):
        piece = unicodedata.normalize("NFKD", ch.lower())
        piece = "".join(c for c in piece if not unicodedata.combining(c))
        piece = piece.replace("ł", "l")
        for c in piece:
            if c.isspace():
                if prev_space:
                    continue
                c = " "
                prev_space = True
            else:
                prev_space = False
            out.append(c)
            idx.append(i)
    return "".join(out), idx


def _literal(m: tuple[str, list[int]], original: str, start: int, end: int) -> str:
    idx = m[1]
    return original[idx[start] : idx[end - 1] + 1]


def _replace(
    current: RuleResult,
    verdict: Verdict,
    summary: str,
    quote: str | None,
    confidence: float,
) -> RuleResult:
    return RuleResult(
        rule_id=current.rule_id,
        rule_name=current.rule_name,
        engine=Engine.HYBRID,
        verdict=verdict,
        confidence=confidence,
        severity=current.severity,
        legal_basis=current.legal_basis,
        evidence=Evidence(
            kind=EvidenceKind.QUOTE if quote else EvidenceKind.ABSENCE,
            summary=summary,
            quote=quote,
        ),
    )


# --------------------------------------------------------------------------- #
# Regula 2 — oznaczenie reklamy
# --------------------------------------------------------------------------- #

AD_MARKER_PATTERNS: tuple[str, ...] = (
    r"\breklama\b",
    r"\bmaterial\w* (reklamow|promocyjn|marketingow)\w*",
    r"#ad\b",
    r"#reklama",
    r"\bwspolprac\w* (platn|reklamow)\w*",
    r"\bsponsorowan\w*",
)


def _guard_rule_2(current: RuleResult, text: str) -> RuleResult:
    m = _norm_with_map(text)
    for p in AD_MARKER_PATTERNS:
        hit = re.search(p, m[0])
        if hit:
            quote = _literal(m, text, hit.start(), hit.end())
            return _replace(
                current,
                Verdict.PASS,
                "rozstrzygniete w kodzie: w materiale wystepuje jednoznaczne "
                f"oznaczenie reklamy ('{quote}').",
                quote,
                1.0,
            )
    return current  # brak oznaczenia — zostaje werdykt modelu


# --------------------------------------------------------------------------- #
# Regula 12a — okres wynikow historycznych >= 5 lat
# --------------------------------------------------------------------------- #

_YEAR = r"(?:19|20)\d{2}"
_PHRASE_5Y = re.compile(
    r"\b(ostatni\w*|minion\w*)\s+(5|pieciu|piec|6|7|8|9|10|szesciu|siedmiu|osmiu"
    r"|dziewieciu|dziesieciu|\d{2})\s+lat"
)
_SINCE_YEAR = re.compile(rf"\bod\s+(?:roku\s+)?({_YEAR})\b")
_CURRENT_YEAR = 2026
_RANGE = re.compile(rf"\b({_YEAR})\s*[–\-−—]\s*({_YEAR})\b")


def historical_years_covered(norm: str) -> tuple[bool, int]:
    """(czy okres >= 5 lat, ile roznych lat wykryto) dla tekstu znormalizowanego."""
    years = {int(y) for y in re.findall(rf"\b({_YEAR})\b", norm)}
    if _PHRASE_5Y.search(norm):
        return True, len(years)
    for a, b in _RANGE.findall(norm):
        if abs(int(b) - int(a)) >= 4:
            return True, len(years)
    for y in _SINCE_YEAR.findall(norm):
        if _CURRENT_YEAR - int(y) >= 5:
            return True, len(years)
    return len(years) >= 5, len(years)


def _guard_rule_12a(current: RuleResult, text: str) -> RuleResult:
    if current.verdict is not Verdict.PASS:
        return current
    ok, n = historical_years_covered(normalize(text))
    if ok:
        return current
    return _replace(
        current,
        Verdict.FAIL,
        "rozstrzygniete w kodzie: wyniki historyczne nie obejmuja okresu "
        f"co najmniej 5 lat (wykryto lat: {n}, brak zakresu >= 5 lat) "
        "— prezentacja wyrywkowa.",
        None,
        0.85,
    )


# --------------------------------------------------------------------------- #
# Regula 12b — ostrzezenie o kursach walut i wplywie oplat
# --------------------------------------------------------------------------- #

# DECYZJA (produkt w PLN): kryterium UKNF pyta, "czy zawarto ostrzezenie
# o wplywie zmian kursow walutowych" oraz o wplyw prowizji i oplat. Brzmienie
# nie robi wyjatku dla produktu w zlotych, a fikstura m2-13 (fundusz bez zadnej
# waluty) jest oczekiwanym `fail`. Dlatego PASS wymaga OBU wzmianek; model nie
# moze ich "wymyslic".
_CURRENCY = re.compile(r"\bwalut\w*|\bkurs\w*\s+walut\w*|\bkurs\w*\s+wymian\w*")
_FEES = re.compile(r"\boplat\w*|\bprowizj\w*|\bkoszt\w*")


def _guard_rule_12b(current: RuleResult, text: str) -> RuleResult:
    if current.verdict is not Verdict.PASS:
        return current
    norm = normalize(text)
    has_cur = bool(_CURRENCY.search(norm))
    has_fee = bool(_FEES.search(norm))
    if has_cur and has_fee:
        return current
    missing = []
    if not has_cur:
        missing.append("ostrzezenia o wplywie kursow walut")
    if not has_fee:
        missing.append("wzmianki o wplywie oplat i prowizji")
    return _replace(
        current,
        Verdict.FAIL,
        "rozstrzygniete w kodzie: w materiale brak " + " oraz ".join(missing) + ".",
        None,
        0.85,
    )


# --------------------------------------------------------------------------- #
# Regula 14 — zastrzezenie przy wynikach historycznych
# --------------------------------------------------------------------------- #

# Wymog jest obiektywny: zastrzezenie albo jest w tekscie, albo go nie ma.
# Bielik potrafil "zobaczyc" je w materiale, ktory go nie zawieral.
_PAST_CAVEAT = re.compile(
    r"\bnie\s+(stanowi\w*|sa|jest)\s+(\w+\s+){0,2}"
    r"(wiarygodn\w*|gwarancj\w*|wskaznik\w*|zapowiedz\w*|obietnic\w*)"
    r"|\bnie\s+gwarantuj\w*"
)


def _guard_rule_14(current: RuleResult, text: str) -> RuleResult:
    if current.verdict is not Verdict.PASS:
        return current
    if _PAST_CAVEAT.search(normalize(text)):
        return current
    return _replace(
        current,
        Verdict.FAIL,
        "rozstrzygniete w kodzie: material prezentuje wyniki historyczne, ale "
        "nie zawiera zastrzezenia, ze nie sa one wiarygodnym wskaznikiem "
        "przyszlych wynikow.",
        None,
        0.85,
    )


# --------------------------------------------------------------------------- #
# Regula 16 — informacja podatkowa
# --------------------------------------------------------------------------- #

_TAX_CAVEAT = re.compile(
    r"\bindywidualn\w*|\bmoze\s+ulec\s+zmian\w*|\bzmian\w*\s+przepis\w*"
    r"|\bsytuacj\w*\s+podatkow\w*|\bprzepis\w*\s+podatkow\w*\s+moga"
)


def _guard_rule_16(current: RuleResult, text: str) -> RuleResult:
    if current.verdict is not Verdict.PASS:
        return current
    if _TAX_CAVEAT.search(normalize(text)):
        return current
    return _replace(
        current,
        Verdict.FAIL,
        "rozstrzygniete w kodzie: material mowi o traktowaniu podatkowym, ale "
        "nie zawiera zastrzezenia o indywidualnej sytuacji klienta ani o "
        "mozliwej zmianie przepisow.",
        None,
        0.85,
    )


# --------------------------------------------------------------------------- #
# Regula 17 — sugerowanie aprobaty organu nadzoru
# --------------------------------------------------------------------------- #

_APPROVAL = re.compile(
    r"\b(zatwierdz|zaakceptowa|sprawdzon|pozytywnie\s+ocen|rekomendowan|polecan"
    r"|autoryzowan\w*\s+produkt)\w*"
)
_REGULATOR = re.compile(r"\bknf\b|\bkomisj\w*\s+nadzoru")
# Zatwierdzenie PROSPEKTU to prawdziwa czynnosc organu, nie aprobata produktu.
_DOCUMENT_CONTEXT = re.compile(r"prospekt|memorandum|statut|regulamin|sprawozdan")
_MAX_DISTANCE = 60


def _guard_rule_17(current: RuleResult, text: str) -> RuleResult:
    if current.verdict is not Verdict.PASS:
        return current
    m = _norm_with_map(text)
    norm = m[0]
    for a in _APPROVAL.finditer(norm):
        for r in _REGULATOR.finditer(norm):
            if r.start() >= a.end():
                gap = r.start() - a.end()
            elif a.start() >= r.end():
                gap = a.start() - r.end()
            else:
                gap = 0
            if gap > _MAX_DISTANCE:
                continue
            between = (
                norm[a.end() : r.start()] if r.start() >= a.end() else norm[r.end() : a.start()]
            )
            if re.search(r"[.!?]", between):
                continue  # inne zdanie — to nie jest ta sama sugestia
            lo, hi = min(a.start(), r.start()), max(a.end(), r.end())
            if _DOCUMENT_CONTEXT.search(norm[max(0, lo - 30) : hi + 30]):
                continue
            quote = _literal(m, text, lo, hi)
            return _replace(
                current,
                Verdict.FAIL,
                "rozstrzygniete w kodzie: material wiaze organ nadzoru "
                f"z aprobata produktu ('{quote}').",
                quote,
                0.9,
            )
    return current


# --------------------------------------------------------------------------- #

_GUARDS: dict[str, Callable[[RuleResult, str], RuleResult]] = {
    "2": _guard_rule_2,
    "12a": _guard_rule_12a,
    "12b": _guard_rule_12b,
    "16": _guard_rule_16,
    "17": _guard_rule_17,
    "14": _guard_rule_14,
}


def apply_guards(
    results: list[RuleResult], text: str, rule_meta: RuleMeta | None = None
) -> list[RuleResult]:
    """Zastosuj straznikow do wynikow wsadu. `not_applicable` zostaje bez zmian."""
    out: list[RuleResult] = []
    for r in results:
        guard = _GUARDS.get(r.rule_id)
        if guard is None or r.verdict is Verdict.NOT_APPLICABLE:
            out.append(r)
        else:
            out.append(guard(r, text))
    return out

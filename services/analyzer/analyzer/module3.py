"""Modul 3 — nieautoryzowane doradztwo inwestycyjne (shadow advisory).

Podstawa: art. 76 ustawy o obrocie instrumentami finansowymi — doradztwo
inwestycyjne to przygotowywanie i przekazywanie klientowi REKOMENDACJI
nabycia, zbycia albo powstrzymania sie od czynnosci dotyczacej instrumentow
finansowych.

Warunek PODWOJNY, oba musza zajsc jednoczesnie:
  (a) tresc zawiera rekomendacje dotyczaca instrumentow finansowych, ORAZ
  (b) podmiot NIE wystepuje w rejestrze autoryzowanych firm KNF.
Sama oferta "family office" czy "wealth management" bez rekomendacji nie jest
doradztwem w rozumieniu art. 76 — to zabezpieczenie przed falą falszywych
pozytywow. Brak danych i awarie modelu to ZAWSZE not_applicable, nigdy fail.
"""

from __future__ import annotations

import re

from analyzer.contracts import (
    AdDocument,
    Engine,
    Evidence,
    EvidenceKind,
    RuleResult,
    Verdict,
)
from analyzer.llm import LlmError, OllamaClient, load_prompt
from analyzer.router import _is_negated, find_recommendations, normalize as _normalize
from analyzer.rules_llm.batching import VERDICT_MAP, quote_is_verifiable
from analyzer.scope_gate import INSTRUMENT_WRAPPERS

RULE_ID = "M3"
RULE_NAME = "Nieautoryzowane doradztwo inwestycyjne"
SEVERITY = 5
LEGAL_BASIS = "art. 76 ustawy o obrocie instrumentami finansowymi"
PROMPT_FILE = "module3.txt"

# Dodatkowe wzorce na tekscie znormalizowanym (bez diakrytykow). Rdzenie
# z koncowka \w*, bo polska fleksja: rekomendujemy / rekomendacja / rekomendacji.
# "polecamy nasz newsletter" celowo NIE pasuje — polecenie wymaga instrumentu.
_INSTRUMENT_OBJECT = (
    r"(akcj\w*|obligacj\w*|etf\w*|spolk\w*|cfd\w*|kontrakt\w*|fundusz\w*|"
    r"instrument\w*|papier\w*|opcj\w*|certyfikat\w*|walor\w*|futures)"
)
_EXTRA_PATTERNS: list[tuple[str, str]] = [
    (r"rekomend\w*", "rekomendacja"),
    (r"sygnal\w*\s+(kupna|sprzedazy|inwestycyjn\w*)", "sygnaly kupna/sprzedazy"),
    (r"polec\w*\s+" + _INSTRUMENT_OBJECT, "polecenie instrumentu"),
    (
        r"(radz\w*|zalec\w*|sugeruj\w*)\s+(\w+\s+)?(kupi\w*|sprzeda\w*|trzyma\w*)",
        "porada kup/sprzedaj/trzymaj",
    ),
    (r"\bkup(uj|cie)\s+" + _INSTRUMENT_OBJECT, "wezwanie do kupna"),
    (r"\bsprzedaj(cie)?\s+" + _INSTRUMENT_OBJECT, "wezwanie do sprzedazy"),
    (r"co\s+kupowac|co\s+kupic", "co kupic"),
    (r"typ\w*\s+na\s+gield\w*", "typy na gielde"),
    (r"\bkupuj\w*|\bkupcie\b|\bsprzedawaj\w*|\bsprzedajcie\b", "imperatyw kup/sprzedaj"),
    (r"wskaz\w*\s+(\w+\s+){0,3}(obligacj|akcj|etf|fundusz)\w*", "wskazanie instrumentu"),
    (r"alokacj\w*", "alokacja"),
    (
        r"w\s+(jakie|ktore)\s+(fundusz|etf|akcj|obligacj)\w*\s+(\w+\s+)?(wejsc|zainwestowac|inwestowac)",
        "w co zainwestowac",
    ),
    (r"(ulozymy|uloze|zbudujemy|zbuduje)\s+(ci\s+|dla\s+ciebie\s+|ci\s+indywidualny\s+)?portfel", "budowa portfela"),
]

# Rzeczownik instrumentu / portfela (wezsze niz scope_gate.INSTRUMENT_HINT, ktore
# lapie kazde "inwest*" i otwieralo by bramke przy zastrzezeniach).
_INSTRUMENT_MENTION_WORDS = re.compile(
    r"\bakcj(?:a|e|i|ami|ach|om)\b|\betf\w*|\bcfd\w*|\bobligacj\w*|\bfundusz\w*"
    r"|\bkontrakt\w*|\bportfel\w*|\bwalor\w*|\bcertyfikat\w*|\bfutures\b"
    r"|\bopcj(?:a|e|i|ami|ach|om)\b|\bpapier\w*\s+wartosciow\w*|\bspolk\w*"
)


def advisory_signals(text: str) -> list[str]:
    """Sygnaly doradcze wykryte w tekscie (bez duplikatow, w stalej kolejnosci)."""
    norm = _normalize(text or "")
    found: list[str] = []
    # Maskowanie negacji z routera: "nie stanowi porady ani rekomendacji" != sygnal.
    for hit in find_recommendations(norm):
        if hit not in found:
            found.append(hit)
    for pattern, label in _EXTRA_PATTERNS:
        if label in found:
            continue
        if any(not _is_negated(norm, m.start()) for m in re.finditer(pattern, norm)):
            found.append(label)
    return found


def mentions_financial_instrument(text: str) -> bool:
    """Czy tresc wskazuje konkretny instrument finansowy (opakowanie ze scope_gate)."""
    norm = _normalize(text or "")
    return any(re.search(p, norm) for p, _w, _b in INSTRUMENT_WRAPPERS)


def has_instrument_mention(text: str) -> bool:
    """Szersze niz mentions_financial_instrument: slowa-klucze instrumentow/portfela."""
    norm = _normalize(text or "")
    return mentions_financial_instrument(text) or bool(
        _INSTRUMENT_MENTION_WORDS.search(norm)
    )


def _result(
    verdict: Verdict,
    summary: str,
    *,
    confidence: float = 1.0,
    quote: str | None = None,
) -> RuleResult:
    kind = EvidenceKind.QUOTE if quote else EvidenceKind.ABSENCE
    return RuleResult(
        rule_id=RULE_ID,
        rule_name=RULE_NAME,
        engine=Engine.LLM,
        verdict=verdict,
        confidence=round(confidence, 3),
        severity=SEVERITY,
        legal_basis=LEGAL_BASIS,
        evidence=Evidence(kind=kind, summary=summary, quote=quote),
    )


def _na(reason: str) -> RuleResult:
    return _result(Verdict.NOT_APPLICABLE, reason)


def assess_shadow_advisory(
    doc: AdDocument,
    *,
    publisher_is_authorized: bool,
    client: OllamaClient | None = None,
) -> RuleResult:
    """Ocen, czy material to doradztwo inwestycyjne bez zezwolenia. Zwraca jeden wynik."""
    if publisher_is_authorized:
        return _na(
            "Podmiot posiada zezwolenie (wpis w rejestrze KNF) — doradztwo "
            "inwestycyjne jest dla niego dozwolone, regula nie ma zastosowania."
        )

    material = doc.analyzable_text
    if not material.strip():
        return _na("Material nie zawiera tekstu do oceny.")

    # Regex to tylko skrot kosztowy dla materialow BEZ wzmianki o instrumentach.
    # Gdy instrument pada w tekscie, ocenia model (regex mial zbyt duzo FN).
    if not advisory_signals(material) and not has_instrument_mention(material):
        return _na(
            "W tresci nie wykryto sygnalow rekomendacji ani wzmianki o instrumentach "
            "— sama oferta uslug doradczych bez rekomendacji nie jest doradztwem z art. 76."
        )

    client = client or OllamaClient()
    try:
        prompt = load_prompt(PROMPT_FILE).replace("{material}", material)
        data = client.generate_json(prompt)
    except LlmError as exc:
        return _na(f"Model niedostepny lub bledna odpowiedz: {exc}")

    if not isinstance(data, dict):
        return _na("Odpowiedz modelu miala nieoczekiwany ksztalt — wymaga oceny recznej.")

    verdict = VERDICT_MAP.get(str(data.get("verdict", "")).strip().lower())
    if verdict is None:
        return _na(
            f"Model zwrocil nieznany werdykt {data.get('verdict')!r} — "
            "wymaga oceny recznej."
        )

    try:
        confidence = float(data.get("confidence", 0.5))
    except (TypeError, ValueError):
        confidence = 0.5
    confidence = min(max(confidence, 0.0), 1.0)

    summary = str(data.get("summary") or "").strip() or "Brak uzasadnienia od modelu."
    quote = str(data.get("quote")).strip() if data.get("quote") else None
    verified = quote_is_verifiable(quote, material)

    if verdict is Verdict.FAIL:
        if not verified:
            confidence *= 0.4
            summary += (
                " [UWAGA: cytatu nie udalo sie odnalezc w materiale — "
                "ustalenie wymaga weryfikacji recznej]"
            )
            quote = None
        elif not mentions_financial_instrument(material):
            # Rekomendacja bez rozpoznanego instrumentu: mniej pewne.
            confidence = min(confidence, 0.6)
            summary += " [Nie rozpoznano wprost nazwy instrumentu — do weryfikacji.]"

    if quote and not verified:
        quote = None  # nie przekazujemy dalej niesprawdzonego cytatu

    return _result(verdict, summary, confidence=confidence, quote=quote)

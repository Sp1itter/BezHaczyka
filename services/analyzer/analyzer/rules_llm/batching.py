"""Wspolna logika wsadow regul semantycznych (LLM).

Jedno wywolanie modelu zwraca kilka RuleResult. Odpornosc jest wazniejsza niz
elegancja: model moze nie odpowiedziec, pominac regule, zwrocic nieznany
werdykt albo zmyslony cytat. Zadna z tych sytuacji nie moze wywrocic potoku
ani wyprodukowac falszywego naruszenia. Brak danych / awaria modelu to ZAWSZE
not_applicable z powodem, nigdy fail.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Collection, Mapping

from analyzer.contracts import (
    AdDocument,
    Engine,
    Evidence,
    EvidenceKind,
    RuleResult,
    Verdict,
)
from analyzer.llm import LlmError, OllamaClient, load_prompt

# rule_id -> (nazwa, severity, podstawa prawna)
RuleMeta = Mapping[str, tuple[str, int, str]]

VERDICT_MAP = {
    "pass": Verdict.PASS,
    "fail": Verdict.FAIL,
    "not_applicable": Verdict.NOT_APPLICABLE,
    "n/a": Verdict.NOT_APPLICABLE,
}


def _normalize_for_match(text: str) -> str:
    """Do porownywania cytatu z materialem: male litery, zwiniete biale znaki.

    Model czesto zmienia wielkosc liter albo lamanie wiersza, i to jest
    akceptowalne — ale nie wolno mu wymyslic tresci.
    """
    return re.sub(r"\s+", " ", text.lower()).strip()


def quote_is_verifiable(quote: str | None, material: str) -> bool:
    """Czy cytat faktycznie wystepuje w materiale.

    To nasza ochrona przed halucynacja. `evidence` ma byc weryfikowalne przez
    nadzorce — cytat, ktorego nie ma w materiale, jest bezwartosciowy i gorszy
    niz brak cytatu, bo wyglada na dowod.
    """
    if not quote:
        return False
    needle = _normalize_for_match(quote)
    if len(needle) < 8:  # za krotkie, zeby cokolwiek dowodzic
        return False
    return needle in _normalize_for_match(material)


def _not_applicable(rule_id: str, rule_meta: RuleMeta, reason: str) -> RuleResult:
    name, severity, basis = rule_meta[rule_id]
    return RuleResult(
        rule_id=rule_id,
        rule_name=name,
        engine=Engine.LLM,
        verdict=Verdict.NOT_APPLICABLE,
        confidence=1.0,
        severity=severity,
        legal_basis=basis,
        evidence=Evidence(kind=EvidenceKind.ABSENCE, summary=reason),
    )


def _all_not_applicable(rule_meta: RuleMeta, reason: str) -> list[RuleResult]:
    return [_not_applicable(rid, rule_meta, reason) for rid in rule_meta]


def _build_result(
    rule_id: str,
    entry: dict,
    material: str,
    rule_meta: RuleMeta,
    fail_means_absence: Collection[str],
) -> RuleResult:
    name, severity, basis = rule_meta[rule_id]

    verdict = VERDICT_MAP.get(str(entry.get("verdict", "")).strip().lower())
    if verdict is None:
        return _not_applicable(
            rule_id,
            rule_meta,
            "Model zwrocil nieznany werdykt "
            f"{entry.get('verdict')!r} — wymaga oceny recznej.",
        )

    try:
        confidence = float(entry.get("confidence", 0.5))
    except (TypeError, ValueError):
        confidence = 0.5
    confidence = min(max(confidence, 0.0), 1.0)

    summary = str(entry.get("summary") or "").strip() or "Brak uzasadnienia od modelu."
    quote = entry.get("quote")
    quote = str(quote).strip() if quote else None

    # --- weryfikacja cytatu ------------------------------------------- #
    verified = quote_is_verifiable(quote, material)

    if verdict is Verdict.FAIL and not verified and rule_id not in fail_means_absence:
        # Model twierdzi, ze w materiale cos JEST, ale nie potrafi tego
        # wskazac. Nie kasujemy ustalenia, ale mocno je odwazamy — `confidence`
        # wchodzi do risk_score, wiec halucynacja sama sie wytlumia.
        confidence *= 0.4
        summary += (
            " [UWAGA: cytatu nie udalo sie odnalezc w materiale — "
            "ustalenie wymaga weryfikacji recznej]"
        )
        quote = None

    if quote and not verified:
        quote = None  # nie przekazujemy dalej niesprawdzonego cytatu

    kind = EvidenceKind.QUOTE if quote else EvidenceKind.ABSENCE

    return RuleResult(
        rule_id=rule_id,
        rule_name=name,
        engine=Engine.LLM,
        verdict=verdict,
        confidence=round(confidence, 3),
        severity=severity,
        legal_basis=basis,
        evidence=Evidence(kind=kind, summary=summary, quote=quote),
    )


def evaluate_batch(
    doc: AdDocument,
    client: OllamaClient | None,
    *,
    prompt_file: str,
    rule_meta: RuleMeta,
    fail_means_absence: Collection[str],
    precondition: Callable[[str], bool] | None = None,
    precondition_reason: str = "",
) -> list[RuleResult]:
    """Ocen wszystkie reguly wsadu jednym wywolaniem modelu.

    Zwraca ZAWSZE tyle wynikow, ile regul w `rule_meta`, w jej kolejnosci.
    Brak odpowiedzi modelu albo brakujaca regula daje `not_applicable`
    z powodem, nigdy `fail`.
    """
    client = client or OllamaClient()
    material = doc.analyzable_text

    if not material.strip():
        return _all_not_applicable(rule_meta, "Material nie zawiera tekstu do oceny.")

    # BRAMKA WARUNKU WSTEPNEGO — deterministyczna, PRZED wywolaniem modelu.
    #
    # Czesc regul jest warunkowa: regula 16 dotyczy tylko materialow mowiacych
    # o podatkach, a reguly 12a/12b/14 tylko tych, ktore prezentuja wyniki
    # historyczne. Bielik 4.5B ignorowal taki warunek zapisany w promptcie
    # i dawal `fail` na materiale z sama prognoza, bez zadnych wynikow
    # historycznych — czyli falszywy alarm, najgorszy kierunek bledu
    # w narzedziu nadzorczym.
    #
    # Warunek wstepny rozstrzygamy wiec w kodzie, nie w promptcie. Zysk podwojny:
    # znika cala klasa falszywych alarmow ORAZ oszczedzamy wywolanie modelu.
    if precondition is not None and not precondition(material):
        return _all_not_applicable(
            rule_meta,
            precondition_reason
            or "Material nie spelnia warunku wstepnego tych regul.",
        )

    prompt = load_prompt(prompt_file).replace("{material}", material)

    try:
        data = client.generate_json(prompt)
    except LlmError as exc:
        return _all_not_applicable(
            rule_meta, f"Model niedostepny lub bledna odpowiedz: {exc}"
        )

    entries = data.get("results") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        return _all_not_applicable(
            rule_meta,
            "Odpowiedz modelu nie zawierala listy 'results' — wymaga oceny recznej.",
        )

    by_id: dict[str, dict] = {}
    for e in entries:
        if isinstance(e, dict) and "rule_id" in e:
            by_id[str(e["rule_id"]).strip()] = e

    results: list[RuleResult] = []
    for rule_id in rule_meta:
        entry = by_id.get(rule_id)
        if entry is None:
            results.append(
                _not_applicable(
                    rule_id, rule_meta, "Model pominal te regule w odpowiedzi."
                )
            )
        else:
            results.append(
                _build_result(rule_id, entry, material, rule_meta, fail_means_absence)
            )
    return results

"""Prompt wsadowy nr 1 — reguly 1, 2, 17, 18.

JEDNO wywolanie Bielika zwraca cztery RuleResult. Osiemnascie osobnych
requestow na dokument zabilo by przepustowosc przy 8 GB VRAM.

Odpornosc jest tu wazniejsza niz elegancja: model moze nie odpowiedziec,
zwrocic brakujaca regule, nieznany werdykt albo zmyslony cytat. Zadna z tych
sytuacji nie moze wywrocic potoku ani wyprodukowac falszywego naruszenia
na oczach jury.
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

PROMPT_FILE = "batch_1.txt"

# rule_id -> (nazwa, severity, podstawa prawna)
RULE_META: dict[str, tuple[str, int, str]] = {
    "1": (
        "Identyfikacja firmy",
        3,
        "art. 44 ust. 2 lit. a rozporządzenia del. 2017/565",
    ),
    "2": (
        "Oznaczenie reklamy",
        3,
        "art. 24 ust. 3 MiFID II",
    ),
    "17": (
        "Zakaz sugerowania aprobaty organu nadzoru",
        5,
        "art. 44 ust. 8 rozporządzenia del. 2017/565",
    ),
    "18": (
        "Nadzór jako argument bezpieczeństwa",
        5,
        "art. 44 ust. 8 rozporządzenia del. 2017/565",
    ),
}

# Reguly, dla ktorych `fail` oznacza BRAK czegos wymaganego — wtedy nie ma
# czego cytowac i brak cytatu jest poprawny.
# Dla regul 17 i 18 `fail` twierdzi, ze w materiale COS JEST, wiec cytat
# musi istniec i dac sie odnalezc.
FAIL_MEANS_ABSENCE = {"1", "2"}

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


def _all_not_applicable(reason: str) -> list[RuleResult]:
    out: list[RuleResult] = []
    for rule_id, (name, severity, basis) in RULE_META.items():
        out.append(
            RuleResult(
                rule_id=rule_id,
                rule_name=name,
                engine=Engine.LLM,
                verdict=Verdict.NOT_APPLICABLE,
                confidence=1.0,
                severity=severity,
                legal_basis=basis,
                evidence=Evidence(kind=EvidenceKind.ABSENCE, summary=reason),
            )
        )
    return out


def _build_result(rule_id: str, entry: dict, material: str) -> RuleResult:
    name, severity, basis = RULE_META[rule_id]

    verdict = VERDICT_MAP.get(str(entry.get("verdict", "")).strip().lower())
    if verdict is None:
        return RuleResult(
            rule_id=rule_id,
            rule_name=name,
            engine=Engine.LLM,
            verdict=Verdict.NOT_APPLICABLE,
            confidence=1.0,
            severity=severity,
            legal_basis=basis,
            evidence=Evidence(
                kind=EvidenceKind.ABSENCE,
                summary=(
                    "Model zwrocil nieznany werdykt "
                    f"{entry.get('verdict')!r} — wymaga oceny recznej."
                ),
            ),
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

    if verdict is Verdict.FAIL and not verified and rule_id not in FAIL_MEANS_ABSENCE:
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


def evaluate_batch_1(
    doc: AdDocument,
    client: OllamaClient | None = None,
) -> list[RuleResult]:
    """Ocen reguly 1, 2, 17, 18 jednym wywolaniem modelu.

    Zwraca ZAWSZE cztery wyniki, w stalej kolejnosci. Brak odpowiedzi modelu
    albo brakujaca regula daje `not_applicable` z powodem, nigdy `fail`.
    """
    client = client or OllamaClient()
    material = doc.analyzable_text

    if not material.strip():
        return _all_not_applicable("Material nie zawiera tekstu do oceny.")

    prompt = load_prompt(PROMPT_FILE).replace("{material}", material)

    try:
        data = client.generate_json(prompt)
    except LlmError as exc:
        return _all_not_applicable(f"Model niedostepny lub bledna odpowiedz: {exc}")

    entries = data.get("results")
    if not isinstance(entries, list):
        return _all_not_applicable(
            "Odpowiedz modelu nie zawierala listy 'results' — wymaga oceny recznej."
        )

    by_id: dict[str, dict] = {}
    for e in entries:
        if isinstance(e, dict) and "rule_id" in e:
            by_id[str(e["rule_id"]).strip()] = e

    results: list[RuleResult] = []
    for rule_id in RULE_META:
        entry = by_id.get(rule_id)
        if entry is None:
            name, severity, basis = RULE_META[rule_id]
            results.append(
                RuleResult(
                    rule_id=rule_id,
                    rule_name=name,
                    engine=Engine.LLM,
                    verdict=Verdict.NOT_APPLICABLE,
                    confidence=1.0,
                    severity=severity,
                    legal_basis=basis,
                    evidence=Evidence(
                        kind=EvidenceKind.ABSENCE,
                        summary="Model pominal te regule w odpowiedzi.",
                    ),
                )
            )
        else:
            results.append(_build_result(rule_id, entry, material))

    return results

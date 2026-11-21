"""Wypelniacze dla regul DET 4-8 (Modul 2), gdy scraper nie dostarczyl wyniku.

To WYPELNIACZ, a nie ocena: werdykt zawsze `not_applicable`. Cel: nadzorca
i `scoring.coverage` maja widziec, ze regul wizualnych nie oceniono, zamiast
po cichu je pomijac. Zasada projektu: brak danych -> not_applicable z powodem,
nigdy fail.

Metadane (nazwy, severity, podstawa) sa zgodne z services/scraper/sources/
facebook_rules.py oraz fixtures/contract-examples/rule_result_facebook.json.
"""

from __future__ import annotations

from analyzer.contracts import (
    AdDocument,
    Engine,
    Evidence,
    EvidenceKind,
    RuleResult,
    Verdict,
)

_BASIS = "rozporządzenia del. 2017/565"

# rule_id: (nazwa, severity, podstawa prawna)
DET_RULES: dict[str, tuple[str, int, str]] = {
    "4": ("Rozmiar czcionki ryzyka", 4, f"art. 44 ust. 2 lit. c {_BASIS}"),
    "5": ("Ekspozycja i kontrast", 3, f"art. 44 ust. 2 lit. c, e {_BASIS}"),
    "6": ("Zakrywanie / ukrywanie", 4, f"art. 44 ust. 2 lit. e {_BASIS}"),
    "7": ("Dostępność za 1 kliknięciem", 4, f"art. 44 ust. 2 lit. b, e {_BASIS}"),
    "8": ("Responsywność", 2, f"art. 44 ust. 2 lit. g {_BASIS}"),
}

REASON_NO_PROBE = "Brak pomiaru renderu (RenderProbe) — regula wizualna nie zostala oceniona"
REASON_NO_RESULT = "Scraper nie dostarczyl wyniku reguly deterministycznej"


def missing_det_placeholders(
    doc: AdDocument, det_results: list[RuleResult] | None
) -> list[RuleResult]:
    """not_applicable dla kazdej z regul 4-8, ktorej nie ma w `det_results`."""
    present = {r.rule_id for r in (det_results or [])}
    reason = REASON_NO_PROBE if doc.render_probe is None else REASON_NO_RESULT
    out: list[RuleResult] = []
    for rule_id, (name, severity, basis) in DET_RULES.items():
        if rule_id in present:
            continue
        out.append(
            RuleResult(
                rule_id=rule_id,
                rule_name=name,
                engine=Engine.DET,
                verdict=Verdict.NOT_APPLICABLE,
                confidence=1.0,
                severity=severity,
                legal_basis=basis,
                evidence=Evidence(kind=EvidenceKind.ABSENCE, summary=reason),
            )
        )
    return out

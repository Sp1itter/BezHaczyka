"""Reguly DET 4-8 (osoba A). Punkt wejscia: `evaluate_det(doc)`.

Dla `source == "facebook"` deleguje do `sources.facebook_rules.facebook_det_results`:
w Meta Ad Library tekst w DOM sklada platforma, wiec R4/R5/R8 sa `not_applicable`,
a R7 korzysta z heurystyki feedu. Pozostale zrodla ocenia `rules_det.rules`.
"""

from __future__ import annotations

from contracts import AdDocument, RuleResult
from rules_det.rules import DET_RULES
from sources.facebook_rules import facebook_det_results


def evaluate_det(doc: AdDocument) -> list[RuleResult]:
    """RuleResult regul 4, 5, 6, 7, 8 w tej kolejnosci."""
    if doc.source == "facebook":
        return facebook_det_results(doc)
    return [rule.evaluate(doc) for rule in DET_RULES]


__all__ = ["DET_RULES", "evaluate_det"]

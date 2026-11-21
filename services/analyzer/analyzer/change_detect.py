"""Detektor zmian — z porownania dwoch przebiegow robi zdarzenie nadzorcze.

Nadzorce nie interesuje, ze reklama istnieje, tylko ze reklamodawca usunal
ostrzezenie o ryzyku, podmienil tresc albo wycofal material. Pojedynczy przebieg
scrapera tego nie widzi. Modul to czyste funkcje: bez bazy, bez modelu, bez sieci.
"""

from __future__ import annotations

from analyzer.contracts import RuleDiff, RuleResult

# Reguly mowiace o ostrzezeniu o ryzyku (3, 6, 14). Tylko ich zmiana pass<->fail
# jest "usunieciem/dodaniem ostrzezenia".
RISK_WARNING_RULES: frozenset[str] = frozenset({"3", "6", "14"})


def diff_rule_results(
    previous: list[RuleResult], current: list[RuleResult]
) -> list[RuleDiff]:
    """Reguly, ktorych werdykt sie zmienil, posortowane po rule_id.

    Regula obecna tylko w jednym przebiegu nie jest roznica werdyktu - pomijana.
    Przejscie not_applicable -> fail NIE jest usunieciem ostrzezenia: znaczy tylko,
    ze tym razem dalo sie regule ocenic. Rozroznia to wywolujacy po from_verdict.
    """
    prev = {r.rule_id: r.verdict for r in previous}
    out: list[RuleDiff] = []
    for r in current:
        if r.rule_id in prev and prev[r.rule_id] != r.verdict:
            out.append(
                RuleDiff(
                    rule_id=r.rule_id,
                    from_verdict=prev[r.rule_id],
                    to_verdict=r.verdict,
                )
            )
    return sorted(out, key=lambda d: d.rule_id)

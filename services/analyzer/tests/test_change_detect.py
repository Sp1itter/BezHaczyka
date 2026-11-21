"""Testy detektora zmian: diff regul i klasyfikacja zdarzen."""

from __future__ import annotations

from datetime import datetime, timezone

from analyzer.change_detect import (
    RISK_WARNING_RULES,


    diff_rule_results,
)
from analyzer.contracts import (
    AdDocument,
    ChangeKind,
    Embedding,
    Evidence,
    EvidenceKind,
    Engine,
    Finding,
    RiskLevel,
    Routing,
    RuleDiff,
    RuleResult,
    ScopeStatus,
    Verdict,
)
from analyzer.embeddings import simhash_hex

_BASIS = {"3": "art. 44 ust. 2 lit. a", "6": "art. 44 ust. 2 lit. e", "14": "art. 44 ust. 2 lit. h"}


def _r(rule_id: str, verdict: Verdict) -> RuleResult:
    return RuleResult(
        rule_id=rule_id,
        rule_name=f"Regula {rule_id}",
        engine=Engine.LLM,
        verdict=verdict,
        legal_basis=_BASIS.get(rule_id, "art. 1"),
        evidence=Evidence(kind=EvidenceKind.ABSENCE, summary="x"),
    )


def _finding(
    fid: str,
    results: list[RuleResult],
    risk: RiskLevel = RiskLevel.LOW,
) -> Finding:
    return Finding(
        id=fid,
        document_id="doc-1",
        routing=Routing(rule="R1", reason="powod", scope_gate=ScopeStatus.IN_SCOPE),
        risk_level=risk,
        rule_results=results,
        created_at=datetime(2026, 11, 22, tzinfo=timezone.utc),
    )


def _doc(text: str, vector: list[float] | None = None, with_hash: bool = True) -> AdDocument:
    return AdDocument(
        id="doc-1",
        source="test",
        url="http://localhost/x",
        fetched_at=datetime(2026, 11, 22, tzinfo=timezone.utc),
        text=text,
        simhash=simhash_hex(text) if with_hash else None,
        embedding=Embedding(dim=len(vector), vector=vector) if vector else None,
    )


# --------------------------------------------------------------------------- #
# Zadanie 5: diff regul
# --------------------------------------------------------------------------- #


def test_identyczne_wyniki_daja_pusty_diff():
    rs = [_r("1", Verdict.PASS), _r("6", Verdict.FAIL)]
    assert diff_rule_results(rs, list(rs)) == []


def test_zmiana_werdyktu_jest_wykrywana():
    d = diff_rule_results([_r("6", Verdict.PASS)], [_r("6", Verdict.FAIL)])
    assert d == [RuleDiff(rule_id="6", from_verdict=Verdict.PASS, to_verdict=Verdict.FAIL)]


def test_przejscie_z_not_applicable_nie_jest_usunieciem_ostrzezenia():
    # Review Focus 5: not_applicable -> fail znaczy "dalo sie ocenic",
    # NIE "reklamodawca usunal ostrzezenie". Pomylenie da falszywy alarm.
    d = diff_rule_results([_r("6", Verdict.NOT_APPLICABLE)], [_r("6", Verdict.FAIL)])
    assert d[0].from_verdict is Verdict.NOT_APPLICABLE


def test_regula_tylko_w_jednym_przebiegu_jest_pomijana():
    d = diff_rule_results(
        [_r("1", Verdict.PASS)], [_r("2", Verdict.FAIL), _r("1", Verdict.PASS)]
    )
    assert d == []


def test_diff_jest_posortowany_po_rule_id():
    prev = [_r("9", Verdict.PASS), _r("10", Verdict.PASS), _r("2", Verdict.PASS)]
    cur = [_r("9", Verdict.FAIL), _r("10", Verdict.FAIL), _r("2", Verdict.FAIL)]
    assert [d.rule_id for d in diff_rule_results(prev, cur)] == sorted(["9", "10", "2"])



"""Wypelniacze DET 4-8: not_applicable bez wplywu na ryzyko, z wplywem na coverage."""

from __future__ import annotations

from datetime import datetime, timezone

from analyzer.contracts import (
    AdDocument, Engine, Evidence, EvidenceKind, RenderProbe, RuleResult, Verdict,
)
from analyzer.det_placeholders import (
    DET_RULES, REASON_NO_PROBE, REASON_NO_RESULT, missing_det_placeholders,
)
from analyzer.scoring import coverage, risk_level, risk_score


def _doc(probe=None) -> AdDocument:
    d = AdDocument(
        id="d1", source="web", url="https://example.invalid/x",
        fetched_at=datetime(2026, 11, 21, tzinfo=timezone.utc), text="x",
    )
    if probe is not None:
        d.render_probe = probe
    return d


def _res(rid: str, verdict: Verdict) -> RuleResult:
    return RuleResult(
        rule_id=rid, rule_name="r", engine=Engine.DET, verdict=verdict, severity=4,
        evidence=Evidence(kind=EvidenceKind.ABSENCE, summary="s"),
    )


def test_wszystkie_pieciu_gdy_brak_wynikow_i_probe():
    out = missing_det_placeholders(_doc(), None)
    assert [r.rule_id for r in out] == ["4", "5", "6", "7", "8"]
    assert all(r.verdict is Verdict.NOT_APPLICABLE and r.engine is Engine.DET for r in out)
    assert all(r.evidence.kind is EvidenceKind.ABSENCE for r in out)
    assert all(r.evidence.summary == REASON_NO_PROBE for r in out)
    assert [r.severity for r in out] == [4, 3, 4, 4, 2]


def test_powod_gdy_probe_jest_ale_brak_wyniku():
    probe = RenderProbe.model_construct()
    out = missing_det_placeholders(_doc(probe), [])
    assert all(r.evidence.summary == REASON_NO_RESULT for r in out)


def test_nie_dubluje_regul_ze_scrapera():
    out = missing_det_placeholders(_doc(), [_res("4", Verdict.FAIL), _res("8", Verdict.PASS)])
    assert [r.rule_id for r in out] == ["5", "6", "7"]
    assert set(DET_RULES) == {"4", "5", "6", "7", "8"}


def test_placeholdery_nie_zmieniaja_ryzyka_a_obnizaja_coverage():
    base = [_res("1", Verdict.FAIL), _res("2", Verdict.PASS)]
    withp = base + missing_det_placeholders(_doc(), None)
    assert risk_score(withp) == risk_score(base)
    assert risk_level(risk_score(withp), withp) == risk_level(risk_score(base), base)
    assert coverage(base) == 1.0
    assert coverage(withp) == round(2 / 7, 3)

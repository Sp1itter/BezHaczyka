"""Straz niekompletnego materialu: FAIL typu "brak" przy czesciowej transkrypcji -> NA."""

from __future__ import annotations

import pytest

from datetime import datetime, timezone

from analyzer.contracts import (
    AdDocument, Engine, Evidence, EvidenceKind, RuleResult, Transcript, TranscriptSegment, Verdict,
)
from analyzer.pipeline import ABSENCE_FAIL_RULES, AnalyzerConfig, analyze


def _doc(engine: str) -> AdDocument:
    return AdDocument(
        id="d", source="youtube", url="https://example.invalid/v",
        fetched_at=datetime(2026, 11, 21, tzinfo=timezone.utc),
        text="Fundusz akcji ETF, inwestuj.",
        transcript=Transcript(engine=engine, text="ETF", segments=[TranscriptSegment(start=0, end=5, text="ETF")]),
    )


def _rule(rid: str, verdict: Verdict = Verdict.FAIL, sev: int = 3) -> RuleResult:
    return RuleResult(rule_id=rid, rule_name=f"r{rid}", engine=Engine.LLM, verdict=verdict,
                      severity=sev, confidence=0.8,
                      evidence=Evidence(kind=EvidenceKind.QUOTE, summary="x" * 500))


def _run(doc, rules):
    f = analyze(doc, config=AnalyzerConfig(module2_runners=[lambda d: rules]))
    return f, {r.rule_id: r for r in f.rule_results}


def test_partial_fail_braku_staje_sie_na():
    _, res = _run(_doc("youtube-captions-clips:partial"), [_rule("1")])
    r = res["1"]
    assert r.verdict is Verdict.NOT_APPLICABLE and r.confidence == 1.0
    assert r.evidence.kind is EvidenceKind.ABSENCE
    assert r.evidence.summary.startswith("Material znany tylko we fragmentach")
    assert "Pierwotne ustalenie modelu:" in r.evidence.summary
    assert len(r.evidence.summary) < 400


def test_partial_fail_obecnosci_zostaje():
    _, res = _run(_doc("youtube-captions-clips:partial"), [_rule("18")])
    assert res["18"].verdict is Verdict.FAIL


def test_partial_regula_10_i_pass_bez_zmian():
    _, res = _run(_doc("x:partial"), [_rule("10"), _rule("2", Verdict.PASS)])
    assert res["10"].verdict is Verdict.FAIL and res["2"].verdict is Verdict.PASS


def test_pelna_transkrypcja_bez_zmian():
    _, res = _run(_doc("faster-whisper"), [_rule("1")])
    assert res["1"].verdict is Verdict.FAIL


def test_risk_score_spada_przy_partial():
    rules = [_rule("1", sev=5), _rule("18", Verdict.PASS, sev=5)]
    full, _ = _run(_doc("faster-whisper"), rules)
    part, _ = _run(_doc("y:partial"), rules)
    assert full.risk_score == 40.0 and part.risk_score == 0.0


def test_lista_regul_braku():
    assert set(ABSENCE_FAIL_RULES) == {"1", "2", "3", "11", "12a", "12b", "14", "15", "16"}


@pytest.mark.parametrize("rule_id", ["11", "12a", "15", "16"])
def test_reguly_brakujacego_zastrzezenia_sa_degradowane(rule_id):
    from analyzer.pipeline import ABSENCE_FAIL_RULES
    assert rule_id in ABSENCE_FAIL_RULES

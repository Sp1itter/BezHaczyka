"""Fallback regul DET 4-8 liczony w analyzerze z RenderProbe."""

from __future__ import annotations

from datetime import datetime, timezone

from analyzer.contracts import (
    AdDocument, BBox, Engine, EvidenceKind, RenderProbe, RuleResult, TextNode,
    Verdict, ViewportProbe,
)
from analyzer.pipeline import analyze
from analyzer.rules_det_fallback import REASON_NO_RISK, det_fallback_results

RISK = "Inwestowanie wiaze sie z ryzykiem utraty kapitalu."


def _node(text=RISK, font=16.0, y=100.0, **kw) -> TextNode:
    base = dict(text=text, font_px=font, color="#000", bbox=BBox(x=0, y=y, w=300, h=20),
                background_confidence="resolved", contrast_ratio=7.0)
    base.update(kw)
    return TextNode(**base)


def _doc(nodes, vp="desktop", dominant=16.0, page_h=2000.0) -> AdDocument:
    vps = {vp: ViewportProbe(dominant_font_px=dominant, page_height_px=page_h, nodes=nodes)}
    return AdDocument(id="d", source="web", url="https://example.invalid/a",
                      fetched_at=datetime(2026, 11, 21, tzinfo=timezone.utc),
                      text="x", render_probe=RenderProbe(viewports=vps))


def _by(res):
    return {r.rule_id: r for r in res}


def _run(doc, det=None):
    return _by(det_fallback_results(doc, det))


def test_brak_probe_nic_nie_liczy():
    d = AdDocument(id="d", source="web", url="https://example.invalid/a",
                   fetched_at=datetime(2026, 11, 21, tzinfo=timezone.utc), text="x")
    assert det_fallback_results(d, None) == []


def test_brak_wezla_ryzyka_to_na_ze_wskazaniem_reguly_3():
    res = _run(_doc([_node(text="Kup teraz")]))
    assert set(res) == {"4", "5", "6", "7", "8"}
    for r in res.values():
        assert r.verdict is Verdict.NOT_APPLICABLE and r.engine is Engine.DET
        assert REASON_NO_RISK in r.evidence.summary


def test_regula_4_fail_i_pass():
    f = _run(_doc([_node(font=10.0)]))["4"]
    assert f.verdict is Verdict.FAIL
    assert f.evidence.kind is EvidenceKind.MEASUREMENT
    assert f.evidence.measured["ratio"] == 0.625 and f.evidence.quote == RISK
    assert f.evidence.viewport == "desktop"
    assert _run(_doc([_node(font=15.0)]))["4"].verdict is Verdict.PASS


def test_regula_5_unknown_i_none_to_na_nigdy_fail():
    assert _run(_doc([_node(contrast_ratio=2.0)]))["5"].verdict is Verdict.FAIL
    unk = _run(_doc([_node(contrast_ratio=2.0, background_confidence="unknown")]))["5"]
    assert unk.verdict is Verdict.NOT_APPLICABLE
    assert _run(_doc([_node(contrast_ratio=None)]))["5"].verdict is Verdict.NOT_APPLICABLE
    assert _run(_doc([_node(contrast_ratio=5.0)]))["5"].verdict is Verdict.PASS


def test_regula_6_stopka_dol_strony_i_gora():
    assert _run(_doc([_node(in_footer=True, y=10)]))["6"].verdict is Verdict.FAIL
    assert _run(_doc([_node(dom_path="div>div.Legal>p", y=10)]))["6"].verdict is Verdict.FAIL
    assert _run(_doc([_node(y=1800)]))["6"].verdict is Verdict.FAIL
    assert _run(_doc([_node(y=300)]))["6"].verdict is Verdict.PASS


def test_regula_7_za_interakcja_fail_nawet_gdy_wezel_niewidoczny():
    n = _node(behind_interaction="accordion", collapsed_evidence="aria-expanded=false", visible=False)
    r = _run(_doc([n]))["7"]
    assert r.verdict is Verdict.FAIL and "aria-expanded=false" in r.evidence.summary
    assert _run(_doc([_node()]))["7"].verdict is Verdict.PASS


def test_regula_8_clipped_mala_czcionka_mobile_i_brak_mobile():
    assert _run(_doc([_node(clipped=True)]))["8"].verdict is Verdict.FAIL
    assert _run(_doc([_node(font=8.0)], vp="mobile"))["8"].verdict is Verdict.FAIL
    assert _run(_doc([_node(font=12.0)], vp="mobile"))["8"].verdict is Verdict.PASS
    assert _run(_doc([_node(font=12.0)]))["8"].verdict is Verdict.NOT_APPLICABLE


def test_wynik_scrapera_ma_pierwszenstwo():
    scr = RuleResult(rule_id="4", rule_name="r", engine=Engine.DET, verdict=Verdict.PASS,
                     evidence={"kind": "absence", "summary": "s"})
    out = det_fallback_results(_doc([_node(font=5.0)]), [scr])
    assert [r.rule_id for r in out] == ["5", "6", "7", "8"]


def test_pipeline_bez_dubli_priorytet_scrapera():
    scr = RuleResult(rule_id="4", rule_name="r", engine=Engine.DET, verdict=Verdict.PASS,
                     evidence={"kind": "absence", "summary": "s"})
    doc = _doc([_node(font=5.0)])
    doc.text = "Fundusz akcji, inwestuj w ETF. " + RISK
    f = analyze(doc, det_results=[scr])
    ids = sorted(r.rule_id for r in f.rule_results if r.rule_id in {"4", "5", "6", "7", "8"})
    assert ids == ["4", "5", "6", "7", "8"]
    assert [r for r in f.rule_results if r.rule_id == "4"][0].verdict is Verdict.PASS


def test_facebook_nie_dostaje_fallbacku_typografia_meta():
    d = _doc([_node(font=5.0)])
    d.source = "facebook"
    assert det_fallback_results(d, None) == []

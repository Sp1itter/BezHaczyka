"""Reguly DET 4-8 na syntetycznych RenderProbe: kazda regula ma fail i pass."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from contracts import AdDocument, BBox, Engine, RenderProbe, TextNode, Verdict, ViewportProbe
from rules_det import DET_RULES, evaluate_det
from rules_det.base import Rule
from tests.conftest import REPO_ROOT

RISK = "Inwestowanie wiąże się z ryzykiem utraty kapitału."
BODY = "Zarabiaj na giełdzie z naszym kursem dla początkujących. " * 3


def node(text: str = RISK, **kw) -> TextNode:
    base = {"text": text, "font_px": 16.0, "color": "#111111", "background_effective": "#ffffff",
                "background_confidence": "resolved", "contrast_ratio": 18.9,
                "bbox": BBox(x=0, y=200, w=300, h=20), "dom_path": "main>p"}
    base.update(kw)
    return TextNode(**base)


def doc_with(risk: TextNode | None = None, *, mobile: TextNode | None = None, source: str = "web",
             viewports: tuple[str, ...] = ("desktop", "tablet", "mobile")) -> AdDocument:
    vps = {}
    for name in viewports:
        nodes = [node(BODY, dom_path="main>h1")]
        chosen = mobile if (name == "mobile" and mobile is not None) else risk
        if chosen is not None:
            nodes.append(chosen)
        vps[name] = ViewportProbe(dominant_font_px=16.0, page_height_px=2000.0, nodes=nodes)
    return AdDocument(id="d1", source=source, url="https://example.invalid/a", fetched_at=datetime.now(UTC),
                      screenshots={"desktop": "s3://shots/d1-1920.png", "mobile": "s3://shots/d1-390.png"},
                      render_probe=RenderProbe(viewports=vps))


def by_id(doc: AdDocument) -> dict[str, Verdict]:
    return {r.rule_id: r.verdict for r in evaluate_det(doc)}


def test_rules_satisfy_protocol_and_metadata():
    assert [r.rule_id for r in DET_RULES] == ["4", "5", "6", "7", "8"]
    for r in DET_RULES:
        assert isinstance(r, Rule)
        assert r.engine is Engine.DET and r.rule_name and r.legal_basis.startswith("art. 44")


def test_clean_warning_passes_all():
    assert set(by_id(doc_with(node())).values()) == {Verdict.PASS}


def test_no_probe_and_no_warning_are_not_applicable():
    no_probe = AdDocument(id="x", source="web", url="u", fetched_at=datetime.now(UTC))
    assert set(by_id(no_probe).values()) == {Verdict.NOT_APPLICABLE}
    assert set(by_id(doc_with(None)).values()) == {Verdict.NOT_APPLICABLE}


def test_r4_small_font_fails_with_measurement():
    r4 = evaluate_det(doc_with(node(font_px=12.0)))[0]
    assert r4.verdict is Verdict.FAIL
    assert r4.evidence.measured == {"risk_font_px": 12.0, "dominant_font_px": 16.0, "ratio": 0.75}
    assert r4.evidence.quote == RISK


def test_r4_threshold_is_inclusive_pass():
    assert by_id(doc_with(node(font_px=14.4)))["4"] is Verdict.PASS  # 14.4/16 = 0.9


def test_r5_low_contrast_fails():
    assert by_id(doc_with(node(color="#c9c9c9", contrast_ratio=1.9)))["5"] is Verdict.FAIL


def test_r5_unknown_background_never_fails():
    risk = node(background_confidence="unknown", background_effective=None, contrast_ratio=None)
    assert by_id(doc_with(risk))["5"] is Verdict.NOT_APPLICABLE


@pytest.mark.parametrize("kw", [
    {"in_footer": True},
    {"dom_path": "body>div.legal>p"},
    {"bbox": BBox(x=0, y=1900, w=300, h=20)},  # 95% wysokosci
])
def test_r6_footer_legal_or_bottom_fails(kw):
    assert by_id(doc_with(node(**kw)))["6"] is Verdict.FAIL


def test_r7_behind_interaction_fails():
    risk = node(behind_interaction="details", collapsed_evidence="details[not(@open)]", visible=False)
    r7 = evaluate_det(doc_with(risk))[3]
    assert r7.verdict is Verdict.FAIL and "details" in r7.evidence.summary


def test_r8_clipped_on_mobile_fails():
    assert by_id(doc_with(node(), mobile=node(clipped=True)))["8"] is Verdict.FAIL


def test_r8_tiny_mobile_font_fails():
    assert by_id(doc_with(node(), mobile=node(font_px=8.0)))["8"] is Verdict.FAIL


def test_r8_without_mobile_viewport_not_applicable():
    assert by_id(doc_with(node(), viewports=("desktop",)))["8"] is Verdict.NOT_APPLICABLE


def test_rhetorical_risky_question_is_not_a_warning():
    doc = doc_with(node("Czy inwestują w ryzykowne aktywa, np. kryptowaluty?", font_px=7.0))
    assert set(by_id(doc).values()) == {Verdict.NOT_APPLICABLE}


def test_facebook_source_delegates_to_platform_rules():
    results = {r.rule_id: r.verdict for r in evaluate_det(doc_with(node(font_px=7.0), source="facebook"))}
    for rid in ("4", "5", "8"):
        assert results[rid] is Verdict.NOT_APPLICABLE  # typografia platformy, nie 7 px reklamodawcy


def test_base_copy_matches_analyzer():
    ours = (REPO_ROOT / "services" / "scraper" / "rules_det" / "base.py").read_text(encoding="utf-8")
    theirs_path = REPO_ROOT / "services" / "analyzer" / "analyzer" / "rules_llm" / "base.py"
    if not theirs_path.exists():
        pytest.skip("brak kopii analyzera")
    body = lambda s: s.split("from typing import Protocol, runtime_checkable", 1)[1]
    assert body(ours).replace("from contracts import", "from analyzer.contracts import") == body(
        Path(theirs_path).read_text(encoding="utf-8"))

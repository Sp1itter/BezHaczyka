"""RuleResult 4–8 dla zrodla facebook (par. 6.3) — na dokumencie z fixture (replay) i na atrapach."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from contracts import (
    AdDocument,
    BBox,
    Engine,
    RenderProbe,
    RuleResult,
    TextNode,
    Verdict,
    ViewportProbe,
)
from sources.facebook import (
    PLATFORM_TYPOGRAPHY_REASON,
    FacebookAdsSource,
    FacebookConfig,
)
from sources.facebook_rules import FEED_FOLD_CONFIDENCE, facebook_det_results
from sources.meta_json import canonical_ad_url
from storage import LocalBlobStore

from tests.conftest import FIXTURES

AD_ID = "1234567890123456"


def score(results: list[RuleResult]) -> float:
    """Wzor z par. 9 (kopia lokalna — scraper nie importuje analyzera)."""
    den = sum(r.severity for r in results if r.verdict is not Verdict.NOT_APPLICABLE)
    num = sum(r.severity * r.confidence for r in results if r.verdict is Verdict.FAIL)
    return 100 * num / den if den else 0.0


@pytest.fixture(scope="module")
def doc(tmp_path_factory, chromium_available) -> AdDocument:
    src = FacebookAdsSource(
        config=FacebookConfig(mode="replay", fixtures_dir=FIXTURES / "facebook", min_interval_s=0),
        store=LocalBlobStore(tmp_path_factory.mktemp("blobs")),
    )
    return src.fetch(canonical_ad_url(AD_ID))


def _doc(text: str, nodes: list[TextNode] | None = None) -> AdDocument:
    probe = RenderProbe(viewports={"desktop": ViewportProbe(dominant_font_px=15, page_height_px=1000,
                                                             nodes=nodes or [])})
    return AdDocument(id="x", source="facebook", url=canonical_ad_url(AD_ID),
                      fetched_at=datetime.now(UTC), text=text, render_probe=probe)


def _node(text: str, y: float, **kw) -> TextNode:
    return TextNode(text=text, font_px=15, color="#000000", bbox=BBox(x=0, y=y, w=300, h=20), **kw)


def test_rules_4_to_8_in_order_and_schema_valid(doc):
    results = facebook_det_results(doc)
    assert [r.rule_id for r in results] == ["4", "5", "6", "7", "8"]
    for r in results:
        RuleResult.model_validate(r.model_dump(mode="json"))


def test_platform_typography_rules_not_applicable(doc):
    by_id = {r.rule_id: r for r in facebook_det_results(doc)}
    for rid in ("4", "5", "8"):
        assert by_id[rid].verdict is Verdict.NOT_APPLICABLE
        assert by_id[rid].evidence.summary.startswith(PLATFORM_TYPOGRAPHY_REASON)
        assert by_id[rid].engine is Engine.DET


def test_rule7_hybrid_beyond_feed_fold(doc):
    r7 = next(r for r in facebook_det_results(doc) if r.rule_id == "7")
    assert r7.engine is Engine.HYBRID and r7.verdict is Verdict.FAIL
    assert r7.confidence == FEED_FOLD_CONFIDENCE
    assert r7.evidence.measured["risk_offset_chars"] > 125
    assert "ryzykiem utraty kapitału" in r7.evidence.quote


def test_rule7_pass_when_warning_above_fold():
    r7 = facebook_det_results(_doc("Ryzyko utraty kapitału. Zarabiaj z nami."))[3]
    assert r7.verdict is Verdict.PASS and r7.engine is Engine.HYBRID


def test_rule7_fail_det_when_risk_node_behind_interaction():
    nodes = [_node("Inwestowanie wiąże się z ryzykiem", 10, behind_interaction="accordion",
                   collapsed_evidence="aria-expanded=false")]
    r7 = facebook_det_results(_doc("Ryzyko na początku.", nodes))[3]
    assert r7.verdict is Verdict.FAIL and r7.engine is Engine.DET and r7.confidence == 1.0


def test_rules_6_and_7_not_applicable_without_any_warning():
    results = facebook_det_results(_doc("Zarabiaj 18% rocznie!", [_node("Zarabiaj 18% rocznie!", 0)]))
    assert results[2].verdict is Verdict.NOT_APPLICABLE  # R6
    assert results[3].verdict is Verdict.NOT_APPLICABLE  # R7


def test_rule6_bottom_of_creative_fails_top_passes():
    low = [_node("Oferta", 0), _node("Tekst", 500), _node("Ryzyko utraty kapitału", 950)]
    assert facebook_det_results(_doc("x", low))[2].verdict is Verdict.FAIL
    high = [_node("Ryzyko utraty kapitału", 0), _node("Tekst", 500), _node("Oferta", 950)]
    assert facebook_det_results(_doc("x", high))[2].verdict is Verdict.PASS


def test_not_applicable_rules_stay_out_of_score_denominator(doc):
    """Par. 9: przy samych not_applicable dla 4/5/8 wynik zalezy tylko od 6 i 7."""
    results = facebook_det_results(doc)
    assessed = [r for r in results if r.verdict is not Verdict.NOT_APPLICABLE]
    assert {r.rule_id for r in assessed} <= {"6", "7"}
    assert 0 <= score(results) <= 100


def test_rejects_other_sources(doc):
    with pytest.raises(ValueError):
        facebook_det_results(doc.model_copy(update={"source": "web"}))

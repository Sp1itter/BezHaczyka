"""Test kontraktowy FacebookAdsSource na lokalnej fixture HTML (tryb replay, offline).

fetch() idzie DOKLADNIE ta sama sciezka co na zywo (Playwright, 3 viewporty,
neutralizacja nakladek, blokada nawigacji, RenderProbe, zrzuty, zapis do S3) —
rozni sie tylko tym, ze odpowiedzi serwuje fixture zamiast Meta.
"""

from __future__ import annotations

import json

import pytest

from contracts import AdDocument
from sources import Source, SourceError
from sources.facebook import (
    FacebookAdsSource,
    FacebookConfig,
    feed_fold_evidence,
)
from sources.meta_json import canonical_ad_url
from state import CircuitBreaker
from storage import LocalBlobStore
from tests.conftest import FIXTURES, REPO_ROOT

AD_ID = "1234567890123456"


@pytest.fixture
def source(tmp_path, chromium_available):  # pomija test, gdy brak Chromium
    config = FacebookConfig(mode="replay", fixtures_dir=FIXTURES / "facebook", min_interval_s=0)
    return FacebookAdsSource(config=config, store=LocalBlobStore(tmp_path))


@pytest.fixture
def doc(source) -> AdDocument:
    return source.fetch(canonical_ad_url(AD_ID))


def test_implements_source_protocol(source):
    assert isinstance(source, Source)
    assert source.name == "facebook"


def test_discover_replay_yields_canonical_urls(source):
    assert source.discover("inwestycje") == [canonical_ad_url(AD_ID)]


def test_document_matches_frozen_contract(doc):
    payload = doc.model_dump(mode="json")
    AdDocument.model_validate(payload)
    example = json.loads(
        (REPO_ROOT / "fixtures" / "contract-examples" / "ad_document.json").read_text(encoding="utf-8")
    )
    assert set(payload) == set(example)
    assert set(payload["publisher"]) == set(example["publisher"])


def test_identity_and_url(doc):
    assert doc.source == "facebook"
    assert doc.url == canonical_ad_url(AD_ID)
    assert doc.lang == "pl"
    assert doc.publisher.handle == "@inwestorpl"
    assert doc.publisher.display_name == "Inwestor PL"
    assert doc.publisher.is_official_firm_channel is False


def test_screenshots_only_desktop_and_mobile(doc, source):
    assert doc.screenshots == {
        "desktop": f"s3://shots/{doc.id}-1920.png",
        "mobile": f"s3://shots/{doc.id}-390.png",
    }
    assert doc.html_path == f"s3://raw/{doc.id}.html"
    for uri in [*doc.screenshots.values(), doc.html_path]:
        path = source.store.path_of(uri)
        assert path.is_file() and path.stat().st_size > 0
    assert source.store.path_of(doc.screenshots["desktop"]).read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_tablet_measured_but_not_serialized_as_screenshot(doc):
    assert set(doc.render_probe.viewports) == {"desktop", "tablet", "mobile"}
    assert "tablet" not in doc.screenshots


def test_text_from_json_without_dco_placeholders(doc):
    assert doc.title == "Zyski do 18% rocznie!"
    assert doc.text.startswith("Chcesz zarabiać więcej niż na lokacie?")
    assert "{{" not in doc.text and "\u200b" not in doc.text
    assert "utm_campaign=sygnaly24&aff=jan77" in doc.text  # link rozwiniety z l.php


def test_probe_scoped_to_creative_in_dialog(doc):
    for name, vp in doc.render_probe.viewports.items():
        texts = {n.text for n in vp.nodes}
        assert not any("Identyfikator biblioteki" in t for t in texts), name  # metadane Meta poza zakresem
        assert not any("POD dialogiem" in t for t in texts), name  # karta z listy pod dialogiem
        assert not any("Zaloguj" in t or "cookie" in t for t in texts), name
        assert all(n.behind_interaction != "modal" for n in vp.nodes), name


def test_text_on_image_unknown_background_on_every_viewport(doc):
    for name, vp in doc.render_probe.viewports.items():
        overlay = next(n for n in vp.nodes if n.text == "Zyski do 18% rocznie!")
        assert overlay.background_confidence == "unknown", name
        assert overlay.background_source == "media:img", name
        body = next(n for n in vp.nodes if n.text.startswith("Chcesz zarabiać"))
        assert body.background_confidence == "resolved", name


def test_cta_block_is_not_link_behind_interaction(doc):
    desc = next(n for n in doc.render_probe.viewports["desktop"].nodes if n.text == "Ryzyko utraty kapitału")
    assert desc.behind_interaction is None


def test_feed_fold_hybrid_evidence_from_document_text(doc):
    ev = feed_fold_evidence(doc.text)
    assert ev is not None and ev.beyond_fold
    assert "ryzykiem utraty kapitału" in ev.quote


def test_deterministic_document_id(source, doc):
    again = source.fetch(canonical_ad_url(AD_ID))
    assert again.id == doc.id


def test_auto_mode_falls_back_to_fixture_when_breaker_open(tmp_path, chromium_available):
    breaker = CircuitBreaker(threshold=1)
    breaker.record_failure()
    config = FacebookConfig(mode="auto", fixtures_dir=FIXTURES / "facebook", min_interval_s=0)
    src = FacebookAdsSource(config=config, store=LocalBlobStore(tmp_path), breaker=breaker)
    assert src.fetch(canonical_ad_url(AD_ID)).source == "facebook"
    assert src.discover("cokolwiek") == [canonical_ad_url(AD_ID)]


def test_replay_without_fixture_is_a_source_error(source):
    with pytest.raises(SourceError):
        source.fetch(canonical_ad_url("9999999999999999"))


def test_login_redirect_blocked_and_overlays_removed_without_clicks(source, caplog):
    caplog.set_level("INFO", logger="scraper.facebook")
    source.fetch(canonical_ad_url(AD_ID))
    lines = [r.getMessage() for r in caplog.records if "nakladki=" in r.getMessage()]
    assert len(lines) == 3  # kazdy viewport
    for line in lines:
        assert "'login'" in line and "'cookie'" in line
        assert "zablokowane nawigacje=1" in line  # skrypt /login/ nie opuscil strony

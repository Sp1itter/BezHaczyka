from __future__ import annotations

import pytest
import yaml
from sources.base import SourceError, SourceGone
from sources.tiktok import TikTokSource, video_id, video_url

from tests.conftest import REPO_ROOT

FIX = REPO_ROOT / "fixtures" / "demo-ads" / "tiktok"


def test_discover_filters_by_description():
    src = TikTokSource(FIX)
    assert src.discover("kodem polecającym") == [video_url("inwestor.przyklad", "7300000000000000001")]
    assert len(src.discover("")) == 2


def test_fetch_document_with_subtitles_and_links():
    doc = TikTokSource(FIX).fetch(video_url("inwestor.przyklad", "7300000000000000001"))
    assert doc.source == "tiktok" and doc.publisher.handle == "@inwestor.przyklad"
    assert "Gwarantowany zysk" in doc.text and "broker.example.invalid" in doc.text
    assert doc.transcript.engine == "tiktok-subtitles" and len(doc.transcript.segments) == 2
    assert "bez ryzyka" in doc.analyzable_text


def test_fetch_without_subtitles_has_no_transcript():
    doc = TikTokSource(FIX).fetch(video_url("edukacja.finansowa", "7300000000000000002"))
    assert doc.transcript is None and doc.text


def test_errors():
    src = TikTokSource(FIX)
    with pytest.raises(SourceError):
        src.fetch("https://blog.example.invalid/x")
    with pytest.raises(SourceGone):
        src.fetch(video_url("ktos", "1"))
    with pytest.raises(SourceError):
        TikTokSource(FIX, mode="live")
    assert video_id("https://www.tiktok.com/@a.b/video/123?lang=pl") == "123"


def test_disabled_by_default_in_schedule():
    jobs = yaml.safe_load((REPO_ROOT / "services" / "scraper" / "schedule.yaml").read_text(encoding="utf-8"))["jobs"]
    tiktok = [j for j in jobs if j.get("source") == "tiktok"]
    assert tiktok and not any(j["enabled"] for j in tiktok)

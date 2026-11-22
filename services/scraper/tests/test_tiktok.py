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


def test_schedule_live_enabled_replay_disabled():
    jobs = yaml.safe_load((REPO_ROOT / "services" / "scraper" / "schedule.yaml").read_text(encoding="utf-8"))["jobs"]
    by_name = {j["name"]: j for j in jobs if j.get("source") == "tiktok"}
    assert by_name["tiktok-live"]["enabled"] and not by_name["tiktok-demo"]["enabled"]


# --- A3: tryb live (wyszukiwarka + yt-dlp) ------------------------------------

from sources.tiktok import LiveTikTokSource  # noqa: E402

INFO = {"id": "7685824606007086369", "uploader": "tomaszfinanse", "channel": "Tomasz Finanse",
        "description": "Kod polecający XTB w bio! #inwestowanie #xtb", "duration": 46, "timestamp": 1763700000,
        "subtitles": {"pol-PL": [{"ext": "vtt", "url": "sub"}]}}
VTT = "WEBVTT\n\n00:00:01.000 --> 00:00:03.500\nZałóż konto w XTB\n\n00:00:04.000 --> 00:00:06.000\nlink w bio\n"


class MemStore:
    def __init__(self):
        self.items = {}

    def put(self, bucket, key, data, content_type):
        self.items[(bucket, key)] = data
        return f"s3://{bucket}/{key}"


def _live(**kw):
    kw.setdefault("search", lambda q, n: ["https://www.tiktok.com/@tomaszfinanse/video/7685824606007086369?lang=pl",
                                          "https://www.tiktok.com/@tomaszfinanse", "https://example.pl/x"])
    kw.setdefault("extract", lambda url: INFO)
    kw.setdefault("download_text", lambda url: VTT)
    kw.setdefault("download_video", lambda url: b"mp4")
    kw.setdefault("suffixes", ("",))
    return LiveTikTokSource(store=MemStore(), **kw)


def test_live_discover_keeps_only_video_urls():
    assert _live().discover("inwestowanie") == [video_url("tomaszfinanse", "7685824606007086369")]


def test_live_fetch_with_subtitles():
    src = _live()
    doc = src.fetch(video_url("tomaszfinanse", "7685824606007086369"))
    assert doc.source == "tiktok" and doc.publisher.handle == "@tomaszfinanse"
    assert "Kod polecający XTB" in doc.text
    assert [s.text for s in doc.transcript.segments] == ["Załóż konto w XTB", "link w bio"]
    assert doc.transcript.segments[0].start == 1.0 and doc.media[0].kind == "video"


def test_live_fetch_without_subtitles_keeps_video_for_whisper():
    info = {k: v for k, v in INFO.items() if k != "subtitles"}
    doc = _live(extract=lambda url: info).fetch(video_url("tomaszfinanse", "7685824606007086369"))
    assert doc.transcript is None and [m.kind for m in doc.media] == ["video"]


def test_from_env_live(monkeypatch):
    monkeypatch.setenv("TIKTOK_MODE", "live")
    monkeypatch.delenv("S3_ENDPOINT", raising=False)
    assert isinstance(TikTokSource.from_env(), LiveTikTokSource)


def test_live_off_topic_video_is_not_qualified_and_not_downloaded():
    info = {**{k: v for k, v in INFO.items() if k != "subtitles"}, "description": "Letnia stylizacja #moda"}
    src = _live(extract=lambda url: info, download_video=lambda url: pytest.fail("pobrano wideo spoza tematu"))
    doc = src.fetch(video_url("tomaszfinanse", "7685824606007086369"))
    assert doc.media == [] and src.last_meta["qualified"] is False


def test_live_discover_uses_query_variants():
    asked = []
    src = _live(search=lambda q, n: asked.append(q) or [], suffixes=("", "porady"))
    src.discover("ETF")
    assert asked == ["site:tiktok.com ETF", "site:tiktok.com ETF porady"]

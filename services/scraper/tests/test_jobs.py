"""Testy zadan RQ (jobs.py) na atrapach: baza, kolejka i zrodlo."""

from __future__ import annotations

import jobs
import pytest
from contracts import AdDocument, Publisher
from resolver import Registry
from sources.base import SourceGone

ROWS = [{"knf_id": "DM-XTB", "name": "XTB S.A.", "aliases": [], "domains": ["xtb.com"], "handles": []}]


class FakeConn:
    commits = 0

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def commit(self):
        FakeConn.commits += 1


class FakeSource:
    def __init__(self, doc=None, gone=False):
        self.doc, self.gone = doc, gone

    def fetch(self, url):
        if self.gone:
            raise SourceGone("404")
        return self.doc


@pytest.fixture
def env(monkeypatch):
    calls = {"record": [], "gone": [], "analysis": []}
    FakeConn.commits = 0
    Registry.clear_cache()
    monkeypatch.setattr(jobs, "_redis", lambda: object())
    monkeypatch.setattr(jobs.db, "connect", lambda: FakeConn())
    monkeypatch.setattr(Registry, "from_db", classmethod(lambda cls, conn: Registry.from_rows(ROWS)))
    monkeypatch.setattr(jobs.store, "record_document", lambda conn, doc, **kw: calls["record"].append((doc, kw)) or ("cid", "new"))
    monkeypatch.setattr(jobs.store, "mark_gone", lambda conn, cid: calls["gone"].append(cid))
    monkeypatch.setattr(jobs, "_enqueue_analysis", lambda *a: calls["analysis"].append(a))
    return calls


def doc():
    return AdDocument(id="1", source="www", url="https://blog.example/a", fetched_at="2026-11-21T10:00:00Z",
                      publisher=Publisher(handle="blog.example", display_name="Blog"), text="Konto w XTB")


def test_fetch_job_records_resolves_and_enqueues(monkeypatch, env):
    monkeypatch.setattr(jobs, "build_source", lambda *a, **k: FakeSource(doc()))
    assert jobs.fetch_job("www", "https://blog.example/a") == {"case_id": "cid", "outcome": "new"}
    (stored, kw), = env["record"]
    assert kw["entity_resolution"]["publisher_relation"] == "third_party" and kw["qualified"] is True
    assert stored["publisher"]["is_official_firm_channel"] is False
    assert FakeConn.commits == 1 and len(env["analysis"]) == 1


def test_fetch_job_gone(monkeypatch, env):
    monkeypatch.setattr(jobs, "build_source", lambda *a, **k: FakeSource(gone=True))
    out = jobs.fetch_job("www", "https://blog.example/a", recheck=True)
    assert out["outcome"] == "gone" and env["gone"] and not env["record"]


def test_fetch_job_unqualified_is_not_analyzed(monkeypatch, env):
    monkeypatch.setattr(jobs, "build_source", lambda *a, **k: FakeSource(doc()))
    monkeypatch.setattr(jobs, "_fetch", lambda *a: (doc(), False, []))
    jobs.fetch_job("youtube", "https://blog.example/a")
    assert env["record"][0][1]["qualified"] is False and not env["analysis"]


def test_youtube_content_mapping():
    meta = {"evidence": [{"quote": "kod XTB", "field": "title", "target": "XTB", "extra_ignored": 1}],
            "clips": [{"text": "polecam", "start": 1.0, "end": 9.5, "url": "u", "targets": ["XTB"], "signals": ["kod"]}]}
    ev, clip = jobs._youtube_content(meta)
    assert (ev.kind, ev.body, ev.extra) == ("evidence", "kod XTB", {"field": "title", "target": "XTB"})
    assert (clip.kind, clip.start_s, clip.end_s, clip.extra["targets"]) == ("clip", 1.0, 9.5, ["XTB"])


def test_build_source_www_and_unknown(monkeypatch):
    monkeypatch.delenv("S3_ENDPOINT", raising=False)
    assert jobs.build_source("www").name == "www"
    with pytest.raises(ValueError):
        jobs.build_source("tiktok")


def test_build_source_youtube_uses_registry_rows():
    src = jobs.build_source("youtube", registry=Registry.from_rows(ROWS))
    assert any(e["type"] == "domain" for e in src.dictionary)
    assert src.limiter.key == "yt:ratelimit"

"""A1 (sprint finalowy): kolejki per zrodlo, seen dopiero po sukcesie, timeouty, pula procesow workera."""

from __future__ import annotations

import jobs
import pytest
import worker
from contracts import AdDocument, Publisher
from resolver import Registry
from sources.base import SourceError, SourceGone

ROWS = [{"knf_id": "DM-XTB", "name": "XTB S.A.", "aliases": [], "domains": ["xtb.com"], "handles": []}]


class MiniRedis:
    """Tyle Valkey, ile potrzebuja jobs: SET z NX/EX, DELETE, SADD/SISMEMBER."""

    def __init__(self):
        self.kv: dict[str, str] = {}
        self.sets: dict[str, set[str]] = {}

    def set(self, key, value, nx=False, ex=None, px=None):
        if nx and key in self.kv:
            return None
        self.kv[key] = value
        return True

    def delete(self, *keys):
        return sum(1 for k in keys if self.kv.pop(k, None) is not None)

    def sadd(self, key, *items):
        s = self.sets.setdefault(key, set())
        before = len(s)
        s.update(items)
        return len(s) - before

    def sismember(self, key, item):
        return item in self.sets.get(key, set())


class FakeQueue:
    enqueued: list[tuple[str, tuple, dict]] = []

    def __init__(self, name, connection=None):
        self.name = name

    def enqueue(self, func, *args, **kwargs):
        FakeQueue.enqueued.append((self.name, args, kwargs))


class ListSource:
    def __init__(self, urls=(), doc=None, error=None):
        self.urls, self.doc, self.error = list(urls), doc, error

    def discover(self, query):
        return self.urls

    def fetch(self, url):
        if self.error:
            raise self.error
        return self.doc


class FakeConn:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def commit(self):
        pass


@pytest.fixture
def redis(monkeypatch):
    import rq

    r = MiniRedis()
    FakeQueue.enqueued = []
    monkeypatch.setattr(jobs, "_redis", lambda: r)
    monkeypatch.setattr(rq, "Queue", FakeQueue)
    Registry.clear_cache()
    monkeypatch.setattr(jobs.db, "connect", lambda: FakeConn())
    monkeypatch.setattr(Registry, "from_db", classmethod(lambda cls, conn, **kw: Registry.from_rows(ROWS)))
    monkeypatch.setattr(jobs.store, "record_document", lambda conn, doc, **kw: ("cid", "new"))
    monkeypatch.setattr(jobs.store, "mark_gone", lambda conn, cid: None)
    monkeypatch.setattr(jobs, "_enqueue_analysis", lambda *a: None)
    return r


def _doc(url="https://blog.example/a"):
    return AdDocument(id="1", source="www", url=url, fetched_at="2026-11-21T10:00:00Z",
                      publisher=Publisher(handle="blog.example"), text="Konto w XTB")


@pytest.mark.parametrize(("source", "queue"), [
    ("facebook", "q:render:fb"), ("youtube", "q:render:yt"), ("www", "q:fetch:www"), ("tiktok", "q:render:tt"),
])
def test_each_source_has_its_own_render_queue(source, queue):
    assert jobs.render_queue_for(source) == queue


def test_discover_enqueues_to_source_queue_without_marking_seen(monkeypatch, redis):
    monkeypatch.setattr(jobs, "build_source", lambda *a, **k: ListSource(["https://a.pl/1", "https://a.pl/2"]))
    assert jobs.discover_job("www", "x") == 2
    assert [q for q, _, _ in FakeQueue.enqueued] == ["q:fetch:www", "q:fetch:www"]
    assert not redis.sets.get("www:seen")  # seen dopiero po udanym pobraniu


def test_discover_skips_seen_and_in_flight(monkeypatch, redis):
    redis.sadd("www:seen", "https://a.pl/1")
    monkeypatch.setattr(jobs, "build_source", lambda *a, **k: ListSource(["https://a.pl/1", "https://a.pl/2"]))
    assert jobs.discover_job("www", "x") == 1
    assert jobs.discover_job("www", "x") == 0  # https://a.pl/2 jest juz w kolejce (pending)


def test_fetch_success_marks_seen_and_clears_pending(monkeypatch, redis):
    monkeypatch.setattr(jobs, "build_source", lambda *a, **k: ListSource(["https://a.pl/1"], doc=_doc()))
    jobs.discover_job("www", "x")
    jobs.fetch_job("www", "https://a.pl/1")
    assert redis.sismember("www:seen", "https://a.pl/1")
    assert not any(k.startswith("www:pending") for k in redis.kv)


def test_fetch_failure_does_not_mark_seen(monkeypatch, redis):
    monkeypatch.setattr(jobs, "build_source",
                        lambda *a, **k: ListSource(["https://a.pl/1"], error=SourceError("brak kreacji")))
    jobs.discover_job("www", "x")
    with pytest.raises(SourceError):
        jobs.fetch_job("www", "https://a.pl/1")
    assert not redis.sismember("www:seen", "https://a.pl/1")
    assert jobs.discover_job("www", "x") == 1  # nastepny discover sprobuje ponownie


def test_fetch_gone_marks_seen(monkeypatch, redis):
    monkeypatch.setattr(jobs, "build_source", lambda *a, **k: ListSource(error=SourceGone("404")))
    assert jobs.fetch_job("www", "https://a.pl/9")["outcome"] == "gone"
    assert redis.sismember("www:seen", "https://a.pl/9")


def test_facebook_seen_key_is_ad_id(monkeypatch, redis):
    url = "https://www.facebook.com/ads/library/?id=123456789012"
    monkeypatch.setattr(jobs, "build_source", lambda *a, **k: ListSource(error=SourceGone("404")))
    jobs.fetch_job("facebook", url)
    assert redis.sismember("facebook:seen", "123456789012")


def test_analysis_job_has_timeout_and_retry(monkeypatch):
    import rq

    FakeQueue.enqueued = []
    monkeypatch.setattr(rq, "Queue", FakeQueue)
    jobs._enqueue_analysis(object(), _doc(), "cid", {})
    (name, args, kwargs), = FakeQueue.enqueued
    assert name == "q:gpu" and args[0]["document_id"] == "cid"
    assert kwargs["job_timeout"] == jobs.ANALYSIS_TIMEOUT_S == 900
    assert kwargs["retry"].max == 2


# ------------------------------------------------------------- pula workera --

def test_render_pool_expands_to_per_source_processes():
    plan = worker.process_plan("q:render", {})
    flat = [tuple(p) for p in plan]
    assert ("q:render:fb", "q:render") in flat and ("q:render:yt", "q:render") in flat
    assert flat.count(("q:fetch:www", "q:render")) == 2  # WWW: lekkie httpx, dwa procesy


def test_pool_size_from_env():
    plan = worker.process_plan("q:ingest,q:render", {"SCRAPER_INGEST_PROCS": "3", "SCRAPER_POOL_FB": "2",
                                                     "SCRAPER_POOL_WWW": "0"})
    flat = [tuple(p) for p in plan]
    assert flat.count(("q:ingest:fb", "q:ingest")) == 1 and flat.count(("q:ingest", "q:ingest:fb")) == 2
    assert flat.count(("q:render:fb", "q:render")) == 2
    assert not any(p[0] == "q:fetch:www" for p in flat)


def test_explicit_queue_runs_single_process():
    assert worker.process_plan("q:render:fb", {}) == [["q:render:fb"]]


def test_seen_cleanup_finds_members_without_case():
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
    import seen_cleanup
    from casedb.store import case_id_for
    from sources.meta_json import canonical_ad_url

    known = {case_id_for(canonical_ad_url("111111111111"))}
    assert seen_cleanup.stale_members("facebook", ["111111111111", "222222222222"], known) == ["222222222222"]
    assert seen_cleanup.stale_members("www", ["https://a.pl/1"], {case_id_for("https://a.pl/1")}) == []


def test_discover_queues_keep_slow_sources_apart():
    assert jobs.discover_queue_for("facebook") == "q:ingest:fb"
    assert jobs.discover_queue_for("youtube") == "q:render"
    assert jobs.discover_queue_for("www_live") == jobs.discover_queue_for("tiktok") == "q:ingest"


def test_recheck_goes_to_low_priority_shared_queue(monkeypatch, redis):
    monkeypatch.setattr(jobs.store, "cases_for_recheck", lambda conn, limit, older_than_minutes: [
        {"source": "youtube", "url": "https://www.youtube.com/watch?v=aaaaaaaaaaa"}])
    assert jobs.recheck_job(5, 0) == 1
    assert [q for q, _, _ in FakeQueue.enqueued] == ["q:render"]

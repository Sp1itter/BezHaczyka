"""Launchery workera i harmonogramu — bez Redisa (atrapa schedulera)."""
from __future__ import annotations

import re

import pytest

import scheduler_main
import worker_main
from jobs import _job_slug, schedule_facebook


class _Job:
    def __init__(self, id):
        self.id = id


class FakeScheduler:
    def __init__(self, ids):
        self.jobs = [_Job(i) for i in ids]
        self.cancelled = []
        self.scheduled = []

    def get_jobs(self):
        return iter(self.jobs)

    def cancel(self, job):
        self.cancelled.append(job.id)

    def schedule(self, **kw):
        self.scheduled.append(kw)


def test_register_cancels_only_fb_discover_and_schedules_per_query(monkeypatch):
    monkeypatch.setenv("FB_QUERIES", "mieszkania; domy ;")
    sch = FakeScheduler(["fb-discover-stare", "inny-job", "fb-discover-x"])
    n = scheduler_main.register(sch)
    assert n == 2
    assert sch.cancelled == ["fb-discover-stare", "fb-discover-x"]
    assert [s["id"] for s in sch.scheduled] == ["fb-discover-mieszkania", "fb-discover-domy"]


def test_register_empty_queries(monkeypatch):
    monkeypatch.setenv("FB_QUERIES", "")
    assert scheduler_main.register(FakeScheduler([])) == 0


def test_worker_requires_queue():
    with pytest.raises(SystemExit):
        worker_main.main([])


def test_job_slug_strips_polish_and_punctuation():
    assert _job_slug("zarabiaj na giełdzie") == "zarabiaj-na-gieldzie"
    assert _job_slug("ETF / akcje!") == "etf-akcje"


def test_job_slug_fallback_hash_for_empty():
    slug = _job_slug("!!!")
    assert len(slug) == 12
    assert all(c in "0123456789abcdef" for c in slug)


def test_schedule_facebook_ids_match_rq_rule():
    sch = FakeScheduler([])
    schedule_facebook(sch, queries=["inwestycje", "zarabiaj na giełdzie"], interval_min=30)
    ids = [s["id"] for s in sch.scheduled]
    assert ids == ["fb-discover-inwestycje", "fb-discover-zarabiaj-na-gieldzie"]
    assert all(re.fullmatch(r"[A-Za-z0-9_-]+", i) for i in ids)

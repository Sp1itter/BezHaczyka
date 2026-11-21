"""Launchery workera i harmonogramu — bez Redisa (atrapa schedulera)."""
from __future__ import annotations

import pytest

import scheduler_main
import worker_main


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

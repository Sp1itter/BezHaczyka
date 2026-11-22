"""Testy harmonogramu: loader yaml, rejestracja na atrapie schedulera, --once na atrapie kolejki."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
import scheduler
from rq.job import validate_job_id
from scheduler import ID_PREFIX, expand, load_schedule, register, run_once


class FakeScheduler:
    def __init__(self):
        self.jobs: dict[str, dict] = {}

    def get_jobs(self):
        return [SimpleNamespace(id=i) for i in self.jobs]

    def cancel(self, job):
        self.jobs.pop(job.id, None)

    def schedule(self, **kw):
        self.jobs[kw["id"]] = kw


class FakeQueue:
    def __init__(self, name, sink):
        self.name, self.sink = name, sink

    def enqueue(self, func, **kw):
        self.sink.append((self.name, func.__name__, kw))


def test_default_schedule_loads():
    specs = {s.name: s for s in load_schedule(env={})}
    assert set(specs) == {"fb-inwestycje", "yt-finfluencerzy", "www-demo", "www-live", "recheck", "tiktok-demo",
                          "tiktok-live"}
    assert not specs["tiktok-demo"].enabled  # szkielet, domyslnie wylaczony
    assert not specs["www-demo"].enabled and specs["www-live"].enabled  # fikcyjny korpus tylko offline
    assert specs["fb-inwestycje"].queries[0] == "XTB" and specs["fb-inwestycje"].interval_minutes == 60
    assert specs["yt-finfluencerzy"].registry_limit == 24
    assert specs["www-demo"].seeds == ["http://nginx/www/index.html"]


def test_env_overrides():
    specs = {s.name: s for s in load_schedule(env={"SCHEDULE_DISABLE": "fb-inwestycje, recheck",
                                                    "SCHEDULE_INTERVAL_WWW_LIVE": "5"})}
    assert not specs["fb-inwestycje"].enabled and not specs["recheck"].enabled
    assert specs["www-live"].enabled and specs["www-live"].interval_minutes == 5


@pytest.mark.parametrize("body", [
    "jobs: [{name: a, kind: nieznany, interval_minutes: 1}]",
    "jobs: [{name: a, kind: recheck, interval_minutes: 0}]",
    "jobs: [{name: a, kind: discover, source: www, interval_minutes: 1}]",
    "jobs: [{name: a, kind: discover, source: x, queries: [q], interval_minutes: 1}]",
    "jobs: [{name: a, kind: recheck, interval_minutes: 1}, {name: a, kind: recheck, interval_minutes: 1}]",
])
def test_invalid_config(tmp_path, body):
    f = tmp_path / "s.yaml"
    f.write_text(body, encoding="utf-8")
    with pytest.raises(ValueError):
        load_schedule(f, env={})


def _tasks(monkeypatch, once=False):
    monkeypatch.setattr(scheduler, "_registry_queries", lambda spec: ["XTB kod polecajacy", "XTB link partnerski"])
    return expand(load_schedule(env={}), once=once)


def test_expand(monkeypatch):
    tasks = _tasks(monkeypatch)
    ids = [t.id for t in tasks]
    assert ids.count("sched-recheck") == 1 and len(ids) == len(set(ids))
    for i in ids:
        validate_job_id(i)  # RQ dopuszcza tylko litery, cyfry, '_' i '-'
    assert sum(t.job == "fb-inwestycje" for t in tasks) == 32
    assert sum(t.job == "yt-finfluencerzy" for t in tasks) == 2
    assert [t.args for t in tasks if t.id == "sched-recheck"] == [[20, 60]]
    assert [t.args for t in _tasks(monkeypatch, once=True) if t.id == "sched-recheck"] == [[20, 0]]


def test_register_is_idempotent_and_drops_stale(monkeypatch):
    fake = FakeScheduler()
    fake.jobs[ID_PREFIX + "stare-1"] = {}
    fake.jobs["obce-zadanie"] = {}
    tasks = _tasks(monkeypatch)
    register(fake, tasks)
    first = dict(fake.jobs)
    register(fake, tasks)
    assert fake.jobs.keys() == first.keys() == {t.id for t in tasks} | {"obce-zadanie"}
    job = fake.jobs["sched-www-live-1"]
    assert job["interval"] == 3600 and job["queue_name"] == "q:ingest" and job["args"] == ["www_live", "doradztwo inwestycyjne"]


def test_run_once(monkeypatch):
    sink: list = []
    tasks = _tasks(monkeypatch, once=True)
    assert run_once(lambda name: FakeQueue(name, sink), tasks) == len(tasks)
    # discover YouTube idzie do kolejki YT: dzieli limiter z pobraniami YT i nie blokuje q:ingest
    assert {q for q, _, _ in sink} == {"q:ingest", "q:ingest:fb", "q:render:yt"}
    assert {t.queue for t in tasks if t.job == "yt-finfluencerzy"} == {"q:render:yt"}
    assert {f for _, f, _ in sink} == {"discover_job", "recheck_job"}
    assert len({kw["job_id"] for _, _, kw in sink}) == len(sink)


def test_registry_failure_does_not_block_others(monkeypatch):
    def boom(spec):
        raise RuntimeError("brak bazy")

    monkeypatch.setattr(scheduler, "_registry_queries", boom)
    tasks = expand(load_schedule(env={}))
    assert not any(t.job == "yt-finfluencerzy" for t in tasks) and any(t.job == "www-live" for t in tasks)


def test_registry_queries_respect_knf_ids(monkeypatch):
    import contextlib
    import types

    import scheduler
    from resolver import Registry

    rows = [{"knf_id": "DM-BOS", "name": "Dom Maklerski BOS", "aliases": ["Bossa"]},
            {"knf_id": "DM-XTB", "name": "XTB S.A.", "aliases": ["XTB"]},
            {"knf_id": "BM-ING", "name": "ING Bank", "aliases": []}]
    fake_db = types.SimpleNamespace(connect=lambda: contextlib.nullcontext(None))
    monkeypatch.setitem(__import__("sys").modules, "casedb.db", fake_db)
    monkeypatch.setattr("casedb.db", fake_db, raising=False)
    monkeypatch.setattr(Registry, "from_db", classmethod(lambda cls, conn: Registry.from_rows(rows)))
    spec = scheduler.JobSpec(name="yt", kind="discover", interval_minutes=60, source="youtube",
                             registry_phrases=["kod"], registry_ids=["DM-XTB", "DM-BOS"])
    assert scheduler._registry_queries(spec) == ["XTB kod", "Bossa kod"]

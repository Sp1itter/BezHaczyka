"""Harmonogram Modulu 1: wczytuje schedule.yaml i rejestruje zadania w rq-scheduler.

    python -m scheduler           rejestracja (idempotentna) + petla rq_scheduler.Scheduler
    python -m scheduler --once    jednorazowe zlecenie wszystkich zadan do kolejki i wyjscie
                                  (demo/testy; recheck bez progu wieku, wiec odswieza wszystko)

Konfiguracja deklaratywna w `schedule.yaml`; nadpisania z env: SCHEDULE_FILE,
SCHEDULE_DISABLE (lista nazw po przecinku), SCHEDULE_INTERVAL_<NAZWA> (minuty).
"""

from __future__ import annotations

import argparse
import logging
import os
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import jobs
import yaml

log = logging.getLogger("scraper.scheduler")

DEFAULT_FILE = Path(__file__).with_name("schedule.yaml")
ID_PREFIX = "sched-"
KINDS = ("discover", "recheck")


@dataclass
class Task:
    """Jedno zarejestrowane zadanie (po rozwinieciu fraz/seedow)."""

    id: str
    func: Callable[..., Any]
    args: list[Any]
    interval_s: int
    job: str = ""
    queue: str = jobs.INGEST_QUEUE


@dataclass
class JobSpec:
    name: str
    kind: str
    interval_minutes: int
    enabled: bool = True
    source: str = ""
    queries: list[str] = field(default_factory=list)
    seeds: list[str] = field(default_factory=list)
    registry_phrases: list[str] = field(default_factory=list)
    registry_limit: int = 0
    registry_ids: list[str] = field(default_factory=list)
    limit: int = 20
    older_than_minutes: int = 60


def load_schedule(path: str | Path | None = None, env: Mapping[str, str] = os.environ) -> list[JobSpec]:
    """Wczytuje yaml i nakłada nadpisania z env. Bledna konfiguracja = ValueError z nazwa zadania."""
    path = Path(path or env.get("SCHEDULE_FILE") or DEFAULT_FILE)
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    disabled = {n.strip() for n in env.get("SCHEDULE_DISABLE", "").split(",") if n.strip()}
    specs: list[JobSpec] = []
    for raw in data.get("jobs") or []:
        name = str(raw.get("name") or "").strip()
        kind = raw.get("kind")
        if not name or kind not in KINDS:
            raise ValueError(f"zadanie {name!r}: wymagane name i kind in {KINDS}")
        if any(s.name == name for s in specs):
            raise ValueError(f"zdublowana nazwa zadania: {name}")
        env_key = "SCHEDULE_INTERVAL_" + re.sub(r"[^A-Za-z0-9]", "_", name).upper()
        interval = int(env.get(env_key) or raw.get("interval_minutes") or 0)
        if interval <= 0:
            raise ValueError(f"zadanie {name}: interval_minutes musi byc dodatnie")
        reg = raw.get("queries_from_registry") or {}
        spec = JobSpec(
            name=name, kind=kind, interval_minutes=interval,
            enabled=bool(raw.get("enabled", True)) and name not in disabled,
            source=raw.get("source") or "", queries=[str(q) for q in raw.get("queries") or []],
            seeds=[str(s) for s in raw.get("seeds") or []],
            registry_phrases=[str(p) for p in reg.get("phrases") or []],
            registry_limit=int(reg.get("limit") or 0),
            registry_ids=[str(i) for i in reg.get("knf_ids") or []],
            limit=int(raw.get("limit", 20)), older_than_minutes=int(raw.get("older_than_minutes", 60)),
        )
        if kind == "discover":
            if spec.source not in jobs.SOURCES:
                raise ValueError(f"zadanie {name}: source musi byc jednym z {jobs.SOURCES}")
            if not (spec.queries or spec.seeds or spec.registry_phrases):
                raise ValueError(f"zadanie {name}: brak queries/seeds/queries_from_registry")
        specs.append(spec)
    return specs


def _registry_queries(spec: JobSpec) -> list[str]:
    from casedb import db
    from resolver import Registry
    from sources.youtube import queries_for

    with db.connect() as conn:
        rows = Registry.from_db(conn).rows
    if spec.registry_ids:
        order = {k: i for i, k in enumerate(spec.registry_ids)}
        rows = sorted((r for r in rows if r["knf_id"] in order), key=lambda r: order[r["knf_id"]])
    queries = queries_for(rows, spec.registry_phrases)
    return queries[: spec.registry_limit] if spec.registry_limit else queries


def expand(specs: list[JobSpec], *, once: bool = False) -> list[Task]:
    """Aktywne specyfikacje -> konkretne zadania (jedno na fraze/seed). `once`: recheck bez progu wieku."""
    tasks: list[Task] = []
    for spec in (s for s in specs if s.enabled):
        interval = spec.interval_minutes * 60
        if spec.kind == "recheck":
            older = 0 if once else spec.older_than_minutes
            tasks.append(Task(f"{ID_PREFIX}{spec.name}", jobs.recheck_job, [spec.limit, older], interval, spec.name))
            continue
        queries = [*spec.queries, *spec.seeds]
        if spec.registry_phrases:
            try:
                queries += _registry_queries(spec)
            except Exception:
                log.exception("zadanie %s: nie udalo sie zbudowac fraz z rejestru - pomijam", spec.name)
        tasks.extend(
            Task(f"{ID_PREFIX}{spec.name}-{i}", jobs.discover_job, [spec.source, q], interval, spec.name)
            for i, q in enumerate(dict.fromkeys(queries), 1)
        )
    return tasks


def register(scheduler: Any, tasks: list[Task]) -> int:
    """Idempotentna rejestracja: kasuje wczesniej zarejestrowane zadania `sched-*`, potem dodaje aktualne."""
    wanted = {t.id for t in tasks}
    for existing in list(scheduler.get_jobs()):
        if str(existing.id).startswith(ID_PREFIX) or existing.id in wanted:
            scheduler.cancel(existing)
    for t in tasks:
        scheduler.schedule(
            scheduled_time=datetime.now(UTC), func=t.func, args=t.args, interval=t.interval_s,
            repeat=None, queue_name=t.queue, id=t.id, description=f"{t.job}: {t.args}",
        )
        log.info("zarejestrowano %s co %d min: %s%s", t.id, t.interval_s // 60, t.func.__name__, tuple(t.args))
    return len(tasks)


def run_once(queue_factory: Callable[[str], Any], tasks: list[Task]) -> int:
    """Zleca wszystkie zadania natychmiast (bez rq-scheduler)."""
    for t in tasks:
        queue_factory(t.queue).enqueue(t.func, args=t.args, job_id=f"once-{t.id.removeprefix(ID_PREFIX)}-{os.urandom(3).hex()}",
                                       job_timeout=jobs.FETCH_TIMEOUT_S)
        log.info("zlecono %s: %s%s", t.id, t.func.__name__, tuple(t.args))
    return len(tasks)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="scheduler", description=__doc__.split("\n")[0])
    parser.add_argument("--once", action="store_true", help="zlec wszystkie zadania raz i zakoncz")
    parser.add_argument("--file", help="plik harmonogramu (domyslnie SCHEDULE_FILE lub schedule.yaml)")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    from redis import Redis
    from rq import Queue

    tasks = expand(load_schedule(args.file), once=args.once)
    redis = Redis.from_url(os.getenv("VALKEY_URL", "redis://valkey:6379/0"))
    if args.once:
        n = run_once(lambda name: Queue(name, connection=redis), tasks)
        log.info("--once: zlecono %d zadan", n)
        return 0

    from rq_scheduler import Scheduler

    scheduler = Scheduler(queue_name=jobs.INGEST_QUEUE, connection=redis,
                          interval=int(os.getenv("SCHEDULE_POLL_S", "10")))
    log.info("harmonogram: %d zadan", register(scheduler, tasks))
    scheduler.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

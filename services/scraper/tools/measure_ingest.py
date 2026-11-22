"""Pomiar przepustowosci Modulu 1: `scheduler --once`, potem nowe materialy/min per zrodlo.

    python tools/measure_ingest.py [--minutes 10] [--no-trigger]

Zlicza przypadki z `first_seen_at >= T0` (nowe materialy w bazie) co 30 s, az kolejki scrapera
opustoszeja albo minie limit czasu. Wynik: tabela per zrodlo + JSON (do opisu PR / README).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SCRAPER_QUEUES = ("q:ingest", "q:render", "q:render:fb", "q:render:yt", "q:fetch:www", "q:render:tt")


def rate_table(counts: dict[str, int], minutes: float) -> dict[str, float]:
    """Materialy/min per zrodlo i lacznie."""
    out = {s: round(n / minutes, 2) for s, n in sorted(counts.items())} if minutes > 0 else {}
    out["total"] = round(sum(counts.values()) / minutes, 2) if minutes > 0 else 0.0
    return out


def _counts(conn, t0: datetime) -> dict[str, int]:
    rows = conn.execute(
        "SELECT source, count(*) AS n FROM cases WHERE first_seen_at >= %s GROUP BY source", (t0,)
    ).fetchall()
    return {(r["source"] if isinstance(r, dict) else r[0]): int(r["n"] if isinstance(r, dict) else r[1]) for r in rows}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--minutes", type=float, default=10)
    parser.add_argument("--no-trigger", action="store_true", help="nie zlecaj --once, tylko mierz")
    args = parser.parse_args(argv)

    from casedb import db
    from redis import Redis
    from rq import Queue

    import scheduler

    redis = Redis.from_url(os.getenv("VALKEY_URL", "redis://valkey:6379/0"))
    t0 = datetime.now(UTC)
    start = time.monotonic()
    if not args.no_trigger:
        tasks = scheduler.expand(scheduler.load_schedule(), once=True)
        scheduler.run_once(lambda name: Queue(name, connection=redis), tasks)
    counts: dict[str, int] = {}
    idle_polls = 0
    while time.monotonic() - start < args.minutes * 60:
        time.sleep(30)
        with db.connect() as conn:
            counts = _counts(conn, t0)
        backlog = {q: Queue(q, connection=redis).count for q in SCRAPER_QUEUES}
        busy = sum(Queue(q, connection=redis).started_job_registry.count for q in SCRAPER_QUEUES)
        elapsed = (time.monotonic() - start) / 60
        print(f"[{elapsed:5.1f} min] nowe={counts} kolejki={backlog} w_toku={busy}", flush=True)
        idle_polls = idle_polls + 1 if not any(backlog.values()) and not busy else 0
        if idle_polls >= 2:
            break
    minutes = (time.monotonic() - start) / 60
    result = {"t0": t0.isoformat(), "minutes": round(minutes, 2), "new": counts,
              "per_min": rate_table(counts, minutes)}
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

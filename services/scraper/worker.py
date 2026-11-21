"""Worker RQ scrapera: kolejki q:ingest i q:render (jeden proces = jedno zadanie naraz).

Skalowanie: kilka replik kontenera (`SCRAPER_WORKERS` w infra/.env); limiter i breaker sa
we wspolnym Valkey, wiec repliki dziela jeden budzet zapytan do platform.
Healthcheck: `python worker.py --ping` (laczy sie z Valkey i konczy kodem 0/1).
"""

from __future__ import annotations

import logging
import os
import sys

QUEUES = ("q:ingest", "q:render")


def main(argv: list[str] | None = None) -> int:
    from redis import Redis
    from rq import Queue, Worker

    conn = Redis.from_url(os.getenv("VALKEY_URL", "redis://valkey:6379/0"))
    if "--ping" in (argv if argv is not None else sys.argv[1:]):
        return 0 if conn.ping() else 1
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    # Importujemy jobs z gory: blad importu ma sie ujawnic przy starcie, a nie przy pierwszym zadaniu.
    import jobs  # noqa: F401

    logging.getLogger("scraper.worker").info("worker na kolejkach %s", ", ".join(QUEUES))
    Worker([Queue(q, connection=conn) for q in QUEUES], connection=conn).work()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

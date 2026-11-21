"""Worker RQ scrapera: kolejki q:ingest i q:render (jeden proces = jedno zadanie naraz).

Kolejki z `SCRAPER_QUEUES` (po przecinku, domyslnie obie). W compose sa osobne repliki:
`scraper-worker` (q:ingest, discover) i `scraper-worker-render` (q:render, `SCRAPER_WORKERS`
replik), zeby dlugi discover nie blokowal renderu, a render nie czekal za discoverami
(RQ obsluguje kolejki w kolejnosci listy, wiec wspolny worker zawsze bral najpierw q:ingest).
Limiter i breaker sa we wspolnym Valkey, wiec repliki dziela jeden budzet zapytan do platform.
Healthcheck: `python worker.py --ping` (laczy sie z Valkey i konczy kodem 0/1).
"""

from __future__ import annotations

import logging
import os
import sys

QUEUES = ("q:ingest", "q:render")


def queues_from_env(value: str | None) -> tuple[str, ...]:
    """`SCRAPER_QUEUES="q:render"` -> ("q:render",); puste -> obie kolejki."""
    names = tuple(q.strip() for q in (value or "").split(",") if q.strip())
    unknown = [q for q in names if q not in QUEUES]
    if unknown:
        raise ValueError(f"nieznane kolejki w SCRAPER_QUEUES: {unknown} (dozwolone: {', '.join(QUEUES)})")
    return names or QUEUES


def main(argv: list[str] | None = None) -> int:
    from redis import Redis
    from rq import Queue, Worker

    conn = Redis.from_url(os.getenv("VALKEY_URL", "redis://valkey:6379/0"))
    if "--ping" in (argv if argv is not None else sys.argv[1:]):
        return 0 if conn.ping() else 1
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    # Importujemy jobs z gory: blad importu ma sie ujawnic przy starcie, a nie przy pierwszym zadaniu.
    import jobs  # noqa: F401

    queues = queues_from_env(os.getenv("SCRAPER_QUEUES"))
    logging.getLogger("scraper.worker").info("worker na kolejkach %s", ", ".join(queues))
    Worker([Queue(q, connection=conn) for q in queues], connection=conn).work()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

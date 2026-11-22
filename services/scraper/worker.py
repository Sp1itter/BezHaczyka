"""Worker RQ scrapera: pula procesow na kolejkach q:ingest i kolejkach pobierania per zrodlo.

`SCRAPER_QUEUES` (po przecinku) mowi, CO kontener obsluguje; `process_plan` zamienia to na pule
procesow wewnatrz kontenera (bez zmian w compose):

  q:ingest  -> SCRAPER_INGEST_PROCS procesow (domyslnie 3) — discover rownolegle dla wielu fraz
  q:render  -> osobne procesy per zrodlo, kazdy z kolejka zrodla na czele i wspolna q:render na koncu:
               q:render:fb  SCRAPER_POOL_FB  (1)   Chromium, limiter Meta
               q:render:yt  SCRAPER_POOL_YT  (1)   yt-dlp, limiter YouTube (spi tylko ten proces)
               q:fetch:www  SCRAPER_POOL_WWW (2)   httpx/curl_cffi
               q:render:tt  SCRAPER_POOL_TT  (1)   TikTok
  inna nazwa (np. q:render:fb) -> jeden proces na te kolejke.

Kazdy proces to `SimpleWorker` (bez forka na zadanie), wiec przegladarka Chromium, rejestr KNF
i klienci HTTP zyja przez caly proces zamiast byc tworzeni dla kazdej reklamy od nowa.
Limiter i breaker sa we wspolnym Valkey, wiec procesy i repliki dziela jeden budzet zapytan.
Healthcheck: `python worker.py --ping` (laczy sie z Valkey i konczy kodem 0/1).
"""

from __future__ import annotations

import logging
import multiprocessing
import os
import sys
import time
from collections.abc import Mapping

QUEUES = ("q:ingest", "q:render")
SOURCE_POOLS = (  # (kolejka, zmienna env, domyslna liczba procesow)
    ("q:render:fb", "SCRAPER_POOL_FB", 1),
    ("q:render:yt", "SCRAPER_POOL_YT", 1),
    ("q:fetch:www", "SCRAPER_POOL_WWW", 2),
    ("q:render:tt", "SCRAPER_POOL_TT", 1),
)
ALL_QUEUES = (*QUEUES, *(q for q, _, _ in SOURCE_POOLS))


def queues_from_env(value: str | None) -> tuple[str, ...]:
    """`SCRAPER_QUEUES="q:render"` -> ("q:render",); puste -> q:ingest i q:render."""
    names = tuple(q.strip() for q in (value or "").split(",") if q.strip())
    unknown = [q for q in names if q not in ALL_QUEUES]
    if unknown:
        raise ValueError(f"nieznane kolejki w SCRAPER_QUEUES: {unknown} (dozwolone: {', '.join(ALL_QUEUES)})")
    return names or QUEUES


def process_plan(value: str | None, env: Mapping[str, str]) -> list[list[str]]:
    """Lista procesow; kazdy to lista kolejek w kolejnosci priorytetu."""
    plan: list[list[str]] = []
    for name in queues_from_env(value):
        if name == "q:ingest":
            plan += [["q:ingest"] for _ in range(int(env.get("SCRAPER_INGEST_PROCS", 3)))]
        elif name == "q:render":
            for queue, var, default in SOURCE_POOLS:
                plan += [[queue, "q:render"] for _ in range(int(env.get(var, default)))]
        else:
            plan.append([name])
    return plan


def _run(queues: list[str]) -> None:
    from redis import Redis
    from rq import Queue, SimpleWorker

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    os.environ.setdefault("SCRAPER_SHARED_BROWSER", "1")  # SimpleWorker: przegladarka zyje przez proces
    import jobs  # noqa: F401 — blad importu ma sie ujawnic przy starcie, a nie przy pierwszym zadaniu

    conn = Redis.from_url(os.getenv("VALKEY_URL", "redis://valkey:6379/0"))
    logging.getLogger("scraper.worker").info("proces %d na kolejkach %s", os.getpid(), ", ".join(queues))
    SimpleWorker([Queue(q, connection=conn) for q in queues], connection=conn).work()


def main(argv: list[str] | None = None) -> int:
    from redis import Redis

    conn = Redis.from_url(os.getenv("VALKEY_URL", "redis://valkey:6379/0"))
    if "--ping" in (argv if argv is not None else sys.argv[1:]):
        return 0 if conn.ping() else 1
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    log = logging.getLogger("scraper.worker")
    plan = process_plan(os.getenv("SCRAPER_QUEUES"), os.environ)
    if len(plan) == 1:
        _run(plan[0])
        return 0

    ctx = multiprocessing.get_context("spawn")  # czysty proces: Playwright nie lubi forka
    procs: dict[int, tuple[list[str], multiprocessing.process.BaseProcess]] = {}
    for i, queues in enumerate(plan):
        p = ctx.Process(target=_run, args=(queues,), daemon=False)
        p.start()
        procs[i] = (queues, p)
    log.info("pula: %d procesow (%s)", len(plan), "; ".join(",".join(q) for q in plan))
    while True:  # nadzorca: proces, ktory padl (OOM Chromium itp.), wstaje ponownie
        time.sleep(5)
        for i, (queues, p) in list(procs.items()):
            if not p.is_alive():
                log.warning("proces %s (%s) zakonczyl sie kodem %s — restart", p.pid, ",".join(queues), p.exitcode)
                p = ctx.Process(target=_run, args=(queues,), daemon=False)
                p.start()
                procs[i] = (queues, p)


if __name__ == "__main__":
    raise SystemExit(main())

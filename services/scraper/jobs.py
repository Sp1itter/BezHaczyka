"""Zadania RQ zrodla facebook i rejestracja w rq-scheduler (design doc par. 10).

Podzial na kolejki:
  q:ingest (n=4)  discover_job — lekkie: jedna strona wyszukiwania + scroll,
                  dedup po ad_archive_id (Valkey SET fb:seen), enqueue fetch.
  q:render (n=2)  fetch_job — Playwright x3 viewporty, RenderProbe, zrzuty, wideo.

Globalny RateLimiter w Valkey obejmuje OBA rodzaje zadan — 4 + 2 workery
dziela jeden budzet zapytan do Meta.

Przekazanie do analyzera: przez NAZWE funkcji (string), bez importu z innego
serwisu (par. 5 — zero importow miedzy serwisami):
    SCRAPER_OUTPUT_QUEUE=q:gpu
    SCRAPER_OUTPUT_FUNC=analyzer.jobs.analyze_document
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any

from sources.facebook import FacebookAdsSource, FacebookConfig
from sources.meta_json import ad_id_from_url
from state import CircuitBreaker, NodeCache, RateLimiter, SeenSet
from storage import blob_store_from_env

INGEST_QUEUE = "q:ingest"
RENDER_QUEUE = "q:render"


def _redis() -> Any:
    from redis import Redis

    return Redis.from_url(os.getenv("VALKEY_URL", "redis://valkey:6379/0"))


def build_facebook_source(redis: Any = None) -> FacebookAdsSource:
    config = FacebookConfig.from_env()
    return FacebookAdsSource(
        config=config,
        store=blob_store_from_env(),
        limiter=RateLimiter(config.min_interval_s, redis=redis),
        breaker=CircuitBreaker(
            threshold=config.breaker_threshold, cooldown_s=config.breaker_cooldown_s, redis=redis
        ),
        node_cache=NodeCache(redis=redis),
    )


def discover_job(query: str) -> int:
    """q:ingest — znajdz reklamy dla frazy i wrzuc nowe do q:render. Zwraca liczbe nowych."""
    from rq import Queue

    redis = _redis()
    source = build_facebook_source(redis)
    seen = SeenSet(redis=redis)
    render = Queue(RENDER_QUEUE, connection=redis)
    new = 0
    for url in source.discover(query):
        ad_id = ad_id_from_url(url)
        if seen.add(ad_id):
            render.enqueue(fetch_job, url, job_id=f"fb-fetch-{ad_id}", job_timeout=300)
            new += 1
    return new


def fetch_job(url: str) -> dict:
    """q:render — pelny AdDocument. Wynik zadania = JSON zgodny z kontraktem par. 6.1."""
    redis = _redis()
    doc = build_facebook_source(redis).fetch(url)
    payload = doc.model_dump(mode="json")
    out_queue, out_func = os.getenv("SCRAPER_OUTPUT_QUEUE"), os.getenv("SCRAPER_OUTPUT_FUNC")
    if out_queue and out_func:
        from rq import Queue

        Queue(out_queue, connection=redis).enqueue(out_func, payload)
    return payload


def schedule_facebook(scheduler: Any, queries: list[str] | None = None, interval_min: int | None = None) -> int:
    """CronJob Modulu 1: cykliczne discover dla fraz z `.env` (FB_QUERIES, FB_REFRESH_MIN).

    `scheduler` to instancja `rq_scheduler.Scheduler` tworzona przez infrastrukture
    serwisu — ten modul nie importuje rq-scheduler.
    """
    if queries is None:
        queries = [q.strip() for q in os.getenv("FB_QUERIES", "").split(";") if q.strip()]
    interval = 60 * (interval_min or int(os.getenv("FB_REFRESH_MIN", "30")))
    for query in queries:
        scheduler.schedule(
            scheduled_time=datetime.now(UTC),
            func=discover_job,
            args=[query],
            interval=interval,
            repeat=None,
            queue_name=INGEST_QUEUE,
            id=f"fb-discover-{query}",
        )
    return len(queries)

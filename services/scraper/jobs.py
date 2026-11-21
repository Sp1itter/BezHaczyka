"""Zadania RQ zrodla facebook i rejestracja w rq-scheduler (design doc par. 10).

Podzial na kolejki:
  q:ingest (n=4)  discover_job — lekkie: jedna strona wyszukiwania + scroll,
                  dedup po ad_archive_id (Valkey SET fb:seen), enqueue fetch.
  q:render (n=2)  fetch_job — Playwright x3 viewporty, RenderProbe, zrzuty, wideo.

Globalny RateLimiter w Valkey obejmuje OBA rodzaje zadan — 4 + 2 workery
dziela jeden budzet zapytan do Meta.

Przekazanie do analyzera wg docs/INTEGRACJA.md:
  1. `POST {API_BASE_URL}/documents` z pelnym AdDocument (API zapisuje dokument),
  2. zadanie `analyzer.worker.analyze_document` w kolejce q:gpu z MINIMALNYM
     payloadem `{document_id, enqueued_at, det_results}`. Analyzer czyta tresc
     z API (`GET /documents/{id}`), a gotowe wyniki regul DET 4-8 dostaje w zadaniu.
Funkcja analyzera jest podana jako string — zero importow miedzy serwisami (par. 5).
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from contracts import AdDocument
from rules_det import evaluate_det
from sources.facebook import FacebookAdsSource, FacebookConfig
from sources.meta_json import ad_id_from_url
from state import CircuitBreaker, NodeCache, RateLimiter, SeenSet
from storage import blob_store_from_env

INGEST_QUEUE = "q:ingest"
RENDER_QUEUE = "q:render"
ANALYSIS_QUEUE = "q:gpu"
ANALYZE_FUNC = "analyzer.worker.analyze_document"
DEFAULT_API_URL = "http://api:8000"


class ApiError(RuntimeError):
    """API odrzucilo dokument albo jest nieosiagalne. Zadanie RQ ma wtedy PASC
    (i zostac ponowione), a nie po cichu nie wyslac nic do analyzera."""


def api_base_url() -> str:
    return os.getenv("API_BASE_URL", DEFAULT_API_URL).rstrip("/")


def post_document(
    doc: AdDocument,
    base_url: str | None = None,
    timeout_s: float = 30,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> str:
    """`POST /documents`. Zwraca id dokumentu potwierdzone przez API."""
    url = f"{(base_url or api_base_url())}/documents"
    body = json.dumps(doc.model_dump(mode="json"), ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, method="POST", headers={"Content-Type": "application/json; charset=utf-8"}
    )
    try:
        with opener(req, timeout=timeout_s) as resp:
            status = resp.status
            raw = resp.read()
    except (urllib.error.URLError, OSError) as exc:
        raise ApiError(f"POST {url} nieudany: {exc}") from exc
    if status not in (200, 201):
        raise ApiError(f"POST {url} zwrocil {status}")
    try:
        returned = json.loads(raw or b"{}").get("id")
    except (ValueError, AttributeError):
        returned = None
    return str(returned or doc.id)


def det_results_for(doc: AdDocument) -> list[dict]:
    """Wyniki regul DET 4-8 dla zadania q:gpu (JSON gotowy do walidacji RuleResult)."""
    return [r.model_dump(mode="json") for r in evaluate_det(doc)]


def build_analysis_payload(document_id: str, det_results: list[dict], now: datetime | None = None) -> dict:
    """Kontrakt zadania z docs/INTEGRACJA.md („Co A wrzuca do kolejki”)."""
    stamp = (now or datetime.now(UTC)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {"document_id": document_id, "enqueued_at": stamp, "det_results": det_results}


def hand_off(doc: AdDocument, queue: Any, poster: Callable[[AdDocument], str] = post_document) -> dict:
    """Zapis w API + zadanie dla analyzera. Zwraca wyslany payload."""
    document_id = poster(doc)
    payload = build_analysis_payload(document_id, det_results_for(doc))
    queue.enqueue(ANALYZE_FUNC, payload, job_timeout=600)
    return payload


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
    """q:render — pelny AdDocument, zapis w API i zadanie dla analyzera.

    Wynik zadania RQ = AdDocument jako JSON (kontrakt par. 6.1).
    """
    from rq import Queue

    redis = _redis()
    doc = build_facebook_source(redis).fetch(url)
    hand_off(doc, Queue(ANALYSIS_QUEUE, connection=redis))
    return doc.model_dump(mode="json")


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

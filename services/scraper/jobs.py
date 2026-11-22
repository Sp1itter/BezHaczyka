"""Zadania RQ Modulu 1 dla wszystkich zrodel (facebook, youtube, www, tiktok).

Podzial na kolejki:
  q:ingest  discover_job(source, query)   lekkie: wyszukanie URL-i + dedup (Valkey SET `<source>:seen`)
  q:render  fetch_job(source, url)        pobranie, resolver podmiotow, zapis do bazy, zlecenie analizy
            recheck_job(limit, older)     ponowne pobranie najdawniej widzianych (okresowa aktualizacja)

Warstwa danych: pakiet `casedb` (wspolny dla scrapera i analyzera, instalowany pip-em, polaczenie
z `DATABASE_URL` przez `casedb.db.connect()`). Rejestr KNF pochodzi z `authorized_entities`.

Przekazanie do analyzera: przez NAZWE funkcji (string), bez importu z innego serwisu
(zero importow miedzy serwisami):
    SCRAPER_OUTPUT_QUEUE=q:gpu                              (domyslnie)
    SCRAPER_OUTPUT_FUNC=analyzer.worker.analyze_document    (domyslnie)
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
import unicodedata
import uuid
from datetime import UTC, datetime
from typing import Any

from casedb import db, store

from resolver import Registry, resolve, with_official_flag
from sources.base import SourceGone
from sources.meta_json import ad_id_from_url
from state import CircuitBreaker, NodeCache, RateLimiter, SeenSet
from storage import blob_store_from_env

log = logging.getLogger("scraper.jobs")

INGEST_QUEUE = "q:ingest"
RENDER_QUEUE = "q:render"  # stara wspolna kolejka; workery render nadal ja obsluguja (na koncu listy)
# Osobna kolejka pobierania na zrodlo: wolny limiter YouTube nie blokuje Facebooka i odwrotnie,
# a lekkie WWW (httpx) nie czeka za Chromium. Pule procesow: worker.process_plan.
SOURCE_QUEUES = {
    "facebook": "q:render:fb",
    "youtube": "q:render:yt",
    "www": "q:fetch:www",
    "www_live": "q:fetch:www",
    "tiktok": "q:render:tt",
    "tiktok_ads": "q:render:tt",
}
DEFAULT_OUTPUT_QUEUE = "q:gpu"
DEFAULT_OUTPUT_FUNC = "analyzer.worker.analyze_document"
SOURCES = ("facebook", "youtube", "www", "tiktok", "www_live")
FETCH_TIMEOUT_S = 600
ANALYSIS_TIMEOUT_S = int(os.getenv("ANALYSIS_JOB_TIMEOUT_S", "900"))  # do 5 wywolan LLM na dokument
ANALYSIS_RETRIES = 2
# Znacznik "URL juz czeka w kolejce" (zamiast seen.add w discover): wygasa sam, gdyby worker padl.
PENDING_TTL_S = 2 * FETCH_TIMEOUT_S
_EVIDENCE_KEYS = ("field", "type", "target", "signals", "comment_id")


def _redis() -> Any:
    from redis import Redis

    return Redis.from_url(os.getenv("VALKEY_URL", "redis://valkey:6379/0"))


def _rows(registry: Registry | list[dict] | None) -> list[dict]:
    if registry is None:
        with db.connect() as conn:
            return Registry.from_db(conn).rows
    return registry.rows if isinstance(registry, Registry) else registry


def build_facebook_source(redis: Any = None) -> Any:
    from sources.facebook import FacebookAdsSource, FacebookConfig

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


def build_source(name: str, redis: Any = None, registry: Registry | list[dict] | None = None) -> Any:
    """Fabryka zrodel. `registry`: obiekt Registry albo wiersze rejestru (domyslnie z bazy)."""
    if name == "facebook":
        return build_facebook_source(redis)
    if name == "youtube":
        from sources.youtube import YouTubeSource, dictionary_from_registry

        limiter = RateLimiter(float(os.getenv("YT_MIN_INTERVAL_S", "8")), redis=redis, key="yt:ratelimit")
        curated = [r for r in _rows(registry) if r.get("source", "curated") == "curated"]
        return YouTubeSource(dictionary_from_registry(curated), limiter=limiter, store=blob_store_from_env(),
                             results_per_query=int(os.getenv("YT_RESULTS_PER_QUERY", "20")),
                             audio_max_s=int(os.getenv("YT_AUDIO_MAX_S", "1200")))
    if name == "www":
        from sources.www import WebPageSource

        return WebPageSource(store=blob_store_from_env())
    if name == "www_live":
        from resolver import host_of
        from sources.www_live import LiveWebSource

        domains = {d for r in _rows(registry) for d in (host_of(x) for x in r.get("domains") or []) if d}
        return LiveWebSource(store=blob_store_from_env(), registry_domains=domains, redis=redis)
    if name == "tiktok":
        from sources.tiktok import TikTokSource

        return TikTokSource.from_env()
    raise ValueError(f"nieznane zrodlo: {name!r} (dozwolone: {', '.join(SOURCES)})")


def _seen_key(source: str, url: str) -> str:
    return ad_id_from_url(url) if source == "facebook" else url


def render_queue_for(source: str) -> str:
    """Kolejka pobierania dla zrodla (nieznane -> wspolna q:render)."""
    return SOURCE_QUEUES.get(source, RENDER_QUEUE)


INGEST_FB_QUEUE = "q:ingest:fb"


def discover_queue_for(source: str) -> str:
    """Discover zrodel z wolnym limiterem nie blokuje szybkich (WWW, TikTok) w q:ingest.

    YouTube: kolejka YT (wspolny limiter z pobraniami). Facebook: q:ingest:fb — pierwszy proces
    q:ingest bierze ja przed q:ingest, pozostale dopiero gdy q:ingest jest pusta.
    """
    if source == "youtube":
        return SOURCE_QUEUES["youtube"]
    return INGEST_FB_QUEUE if source == "facebook" else INGEST_QUEUE


def _pending_key(source: str, key: str) -> str:
    return f"{source}:pending:{key}"


def _mark_done(redis: Any, source: str, url: str) -> None:
    """Sukces albo trwale zniknięcie: URL do `seen`, zdjecie znacznika pending."""
    key = _seen_key(source, url)
    try:
        SeenSet(redis=redis, key=f"{source}:seen").add(key)
        redis.delete(_pending_key(source, key))
    except AttributeError:  # atrapa bez Valkey (testy jednostkowe)
        pass


def _clear_pending(redis: Any, source: str, url: str) -> None:
    try:
        redis.delete(_pending_key(source, _seen_key(source, url)))
    except AttributeError:
        pass


def _job_id(source: str, kind: str, url: str) -> str:
    return f"{source}-{kind}-{uuid.uuid5(uuid.NAMESPACE_URL, url)}"


def discover_job(source: str, query: str) -> int:
    """q:ingest — znajdz URL-e dla frazy/seeda i wrzuc nowe do q:render. Zwraca liczbe nowych."""
    from rq import Queue

    redis = _redis()
    seen = SeenSet(redis=redis, key=f"{source}:seen")
    render = Queue(render_queue_for(source), connection=redis)
    new = 0
    for url in build_source(source, redis).discover(query):
        key = _seen_key(source, url)
        # `seen` zapisuje dopiero udany fetch_job (wczesniej nieudane pobrania wypadaly na zawsze).
        if seen.contains(key) or not redis.set(_pending_key(source, key), "1", nx=True, ex=PENDING_TTL_S):
            continue
        render.enqueue(fetch_job, source, url, job_id=_job_id(source, "fetch", url),
                       job_timeout=FETCH_TIMEOUT_S)
        new += 1
    log.info("discover %s %r: %d nowych", source, query, new)
    return new


def _youtube_content(meta: dict) -> list[store.Content]:
    """Dowody i fragmenty filmu jako tresc przypadku (tak jak casedb.ingest.from_youtube)."""
    out = [store.Content("evidence", e.get("quote") or "", extra={k: e[k] for k in _EVIDENCE_KEYS if k in e})
           for e in meta.get("evidence") or []]
    out += [store.Content("clip", c.get("text") or "", start_s=c.get("start"), end_s=c.get("end"),
                          url=c.get("url"), extra={"targets": c.get("targets", []), "signals": c.get("signals", [])})
            for c in meta.get("clips") or []]
    return out


def _fetch(source: Any, name: str, url: str) -> tuple[Any, bool, list[store.Content]]:
    if name == "youtube":
        doc, meta = source.fetch_with_evidence(url)
        return doc, bool(meta.get("qualified")), _youtube_content(meta)
    doc = source.fetch(url)
    # Zrodla z wlasnym filtrem tematycznym (TikTok) zglaszaja `qualified` w last_meta.
    return doc, bool((getattr(source, "last_meta", None) or {}).get("qualified", True)), []


def fetch_job(source: str, url: str, recheck: bool = False) -> dict:
    """q:render — pobierz, rozpoznaj podmioty, zapisz w bazie, zleć analizę (new/changed + zakwalifikowane)."""
    redis = _redis()
    with db.connect() as conn:
        registry = Registry.from_db(conn)
        try:
            src = build_source(source, redis, registry)
            doc, qualified, extra = _fetch(src, source, url)
        except SourceGone:
            case_id = store.case_id_for(url)
            store.mark_gone(conn, case_id)
            conn.commit()
            _mark_done(redis, source, url)
            log.info("%s zniknal: %s", source, url)
            return {"case_id": case_id, "outcome": "gone"}
        except Exception:
            _clear_pending(redis, source, url)  # nastepny discover sprobuje ponownie
            raise
        resolution = resolve(doc, registry)
        doc = with_official_flag(doc, resolution)
        case_id, outcome = store.record_document(
            conn, doc.model_dump(mode="json"), entity_resolution=resolution,
            extra_content=extra, qualified=qualified,
            meta=getattr(src, "last_meta", None) or None,
        )
        conn.commit()
    _mark_done(redis, source, url)
    log.info("%s %s -> %s%s", source, url, outcome, " (recheck)" if recheck else "")
    if outcome in ("new", "changed") and qualified:
        _enqueue_analysis(redis, doc, case_id, resolution)
    return {"case_id": case_id, "outcome": outcome}


def _enqueue_analysis(redis: Any, doc: Any, case_id: str, resolution: dict) -> None:
    from rq import Queue

    from rules_det import evaluate_det  # FB: typografia platformy; pozostale zrodla: R4-R8 z RenderProbe

    det = [r.model_dump(mode="json") for r in evaluate_det(doc)] if doc.render_probe else []
    payload = {
        "document_id": case_id,
        "enqueued_at": datetime.now(UTC).isoformat(),
        "entity_resolution": resolution,
        "det_results": det,
    }
    queue = os.getenv("SCRAPER_OUTPUT_QUEUE") or DEFAULT_OUTPUT_QUEUE
    func = os.getenv("SCRAPER_OUTPUT_FUNC") or DEFAULT_OUTPUT_FUNC
    from rq import Retry

    Queue(queue, connection=redis).enqueue(func, payload, job_timeout=ANALYSIS_TIMEOUT_S,
                                           retry=Retry(max=ANALYSIS_RETRIES, interval=[10, 60]))


def recheck_job(limit: int = 20, older_than_minutes: int = 60) -> int:
    """q:ingest — ponownie pobierz najdawniej widziane przypadki (okresowa aktualizacja)."""
    from rq import Queue

    redis = _redis()
    with db.connect() as conn:
        cases = store.cases_for_recheck(conn, limit, older_than_minutes=older_than_minutes)
    # Recheck do wspolnej q:render: kazdy proces bierze ja dopiero, gdy jego kolejka zrodla jest pusta,
    # wiec odswiezanie starych przypadkow nie blokuje pobierania nowych materialow.
    render = Queue(RENDER_QUEUE, connection=redis)
    for c in cases:
        render.enqueue(fetch_job, c["source"], c["url"], True,
                       job_id=_job_id(c["source"], "recheck", c["url"]), job_timeout=FETCH_TIMEOUT_S)
    log.info("recheck: %d przypadkow", len(cases))
    return len(cases)


def _job_slug(query: str) -> str:
    """Slug frazy do ID zadania rq (dozwolone tylko a-z0-9, _ i -)."""
    text = unicodedata.normalize("NFKD", query.lower().replace("ł", "l"))
    text = "".join(c for c in text if not unicodedata.combining(c))
    slug = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return slug or hashlib.sha1(query.encode("utf-8")).hexdigest()[:12]


def schedule_facebook(scheduler: Any, queries: list[str] | None = None, interval_min: int | None = None) -> int:
    """Uproszczony CronJob tylko dla Facebooka (FB_QUERIES, FB_REFRESH_MIN) - launcher scheduler_main.py.

    Pelny harmonogram Modulu 1 (FB/YT/WWW + recheck) to scheduler.py ze schedule.yaml;
    tego uzywa docker-compose. `scheduler` to instancja `rq_scheduler.Scheduler`.
    """
    if queries is None:
        queries = [q.strip() for q in os.getenv("FB_QUERIES", "").split(";") if q.strip()]
    interval = 60 * (interval_min or int(os.getenv("FB_REFRESH_MIN", "30")))
    for query in queries:
        scheduler.schedule(
            scheduled_time=datetime.now(UTC),
            func=discover_job,
            args=["facebook", query],
            interval=interval,
            repeat=None,
            queue_name=INGEST_QUEUE,
            id=f"fb-discover-{_job_slug(query)}",
        )
    return len(queries)

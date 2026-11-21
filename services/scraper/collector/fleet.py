"""Poziom 2 — flota: bierze URL-e z url_store (najwyzszy priorytet), fetch + DET + przekazanie.

Jeden URL = jeden aktywny lease (`locked_until`), wiec kilka procesow floty
moze dzialac rownolegle bez dublowania pracy. Collector niczego tu nie robi
i odwrotnie: flota nie wyszukuje, tylko przetwarza kolejke.

Drogi tor (analyzer: Bielik) dostaja tylko kandydaci z priorytetem
>= analyzer_min_priority (lub pas instrumentow, jesli wlaczony) — reszta konczy
jako `fetched` z zapisanym AdDocument.
"""

from __future__ import annotations

import json
import logging
import socket
import time
from collections.abc import Callable
from typing import Any

from collector.config import CollectorConfig
from collector.lexicons import CollectorConfigFiles
from collector.scoring import wants_analysis
from collector.store import UrlStore
from contracts import AdDocument
from sources.base import SourceBlocked

log = logging.getLogger("collector.fleet")

Fetcher = Callable[[dict[str, Any]], AdDocument]
Handoff = Callable[[AdDocument], None]


def default_worker_id() -> str:
    return f"{socket.gethostname()}:{id(object()) % 100000}"


def make_fetcher(cfg: CollectorConfig) -> Fetcher:
    """Fetch wg source_type. FB bierze wezel z url_store (bez ponownego wyszukiwania)."""

    def fetch(row: dict[str, Any]) -> AdDocument:
        st = row["source_type"]
        if st == "facebook":
            from sources.facebook import FacebookAdsSource, FacebookConfig
            from storage import blob_store_from_env

            fb_cfg = FacebookConfig.from_env()
            fb_cfg.mode = "live"  # flota pracuje na zywych URL-ach; korpus offline to osobny tryb demo
            src = FacebookAdsSource(config=fb_cfg, store=blob_store_from_env())
            node = (row.get("payload") or {}).get("node")
            if isinstance(node, dict):
                src.node_cache[row["external_id"]] = node
            return src.fetch(row["url"])
        if st in ("synthetic", "web"):
            from sources.local_corpus import LocalCorpusSource
            from storage import blob_store_from_env

            return LocalCorpusSource(store=blob_store_from_env()).fetch(row["url"])
        raise NotImplementedError(f"brak fetchera dla source_type={st!r}")

    return fetch


def make_handoff(cfg: CollectorConfig) -> Handoff:
    """Przekazanie do analyzera wg docs/INTEGRACJA.md (POST /documents + q:gpu)."""

    def handoff(doc: AdDocument) -> None:
        from rq import Queue

        from jobs import ANALYSIS_QUEUE, _redis, hand_off

        hand_off(doc, Queue(ANALYSIS_QUEUE, connection=_redis()))

    return handoff


def _save_document(cfg: CollectorConfig, doc: AdDocument) -> None:
    out = cfg.state_dir / "documents"
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{doc.id}.json").write_text(json.dumps(doc.model_dump(mode="json"), ensure_ascii=False), encoding="utf-8")


def process_one(store: UrlStore, files: CollectorConfigFiles, cfg: CollectorConfig, worker: str,
                fetcher: Fetcher, handoff: Handoff | None) -> str | None:
    """Jeden kandydat z kolejki. Zwraca stan koncowy albo None, gdy kolejka pusta."""
    row = store.claim(worker, lease_s=cfg.lease_s)
    if row is None:
        return None
    try:
        doc = fetcher(row)
    except SourceBlocked as exc:
        log.warning("flota: blokada zrodla przy %s — wraca do kolejki za %.0f s", row["url"], cfg.blocked_pause_s)
        return store.fail(row["id"], f"blocked: {exc}", cfg.max_attempts + 1, retry_after_s=cfg.blocked_pause_s)
    except Exception as exc:  # noqa: BLE001 — blad jednego URL-a nie zatrzymuje floty
        log.warning("flota: blad %s: %s", row["url"], exc)
        return store.fail(row["id"], f"{type(exc).__name__}: {exc}", cfg.max_attempts, cfg.retry_after_s)

    _save_document(cfg, doc)
    if handoff is not None and wants_analysis(row["priority"], row.get("signals") or {}, files.lexicons()):
        try:
            handoff(doc)
        except Exception as exc:  # noqa: BLE001 — API/kolejka niedostepne: dokument zostaje zapisany
            log.warning("flota: przekazanie %s do analyzera nieudane: %s", doc.id, exc)
            return store.fail(row["id"], f"handoff: {exc}", cfg.max_attempts, cfg.retry_after_s)
        store.finish(row["id"], "done", document_id=doc.id)
        return "done"
    store.finish(row["id"], "fetched", document_id=doc.id)
    return "fetched"


def run_fleet(store: UrlStore, files: CollectorConfigFiles, cfg: CollectorConfig, *,
              worker: str | None = None, fetcher: Fetcher | None = None, handoff: Handoff | None = None,
              max_items: int | None = None, stop_when_empty: bool = False,
              sleep: Callable[[float], None] = time.sleep) -> dict[str, int]:
    worker = worker or default_worker_id()
    fetcher = fetcher or make_fetcher(cfg)
    if handoff is None and cfg.analyze:
        handoff = make_handoff(cfg)
    done: dict[str, int] = {}
    processed = 0
    while max_items is None or processed < max_items:
        state = process_one(store, files, cfg, worker, fetcher, handoff)
        if state is None:
            if stop_when_empty:
                break
            sleep(cfg.idle_sleep_s)
            continue
        processed += 1
        done[state] = done.get(state, 0) + 1
    return done

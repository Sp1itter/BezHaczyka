"""Poziom 1 — collector: wylacznie URL-e i metadane kandydatow, non-stop.

Bez RenderProbe, bez Bielika, bez Findingow. Na FB tresc reklamy jest w JSON
strony wyszukiwania, wiec priorytet i kwarantanne liczymy tutaj, a drogi
render (3 viewporty) dostaje tylko to, co przejdzie do kolejki.

Zachowanie wobec platformy: maly ruch (przerwa + jitter, limit zapytan na
godzine), breaker przy SourceBlocked pauzuje ZRODLO (nie probujemy innego
proxy), zero logowania i cookies.
"""

from __future__ import annotations

import json
import logging
import random
import time
from collections import Counter
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

from collector.candidates import from_facebook_node
from collector.config import CollectorConfig
from collector.lexicons import CollectorConfigFiles
from collector.scoring import creative_key, landing_key, score
from collector.store import UrlStore
from sources.base import SourceBlocked, SourceError

log = logging.getLogger("collector")


@dataclass
class CollectReport:
    source: str
    query: str
    tag: str
    found: int = 0
    created: int = 0
    seen_again: int = 0
    states: dict[str, int] = field(default_factory=dict)
    error: str | None = None


def collect_facebook_query(store: UrlStore, files: CollectorConfigFiles, source: Any, spec: dict) -> CollectReport:
    """Jedno zapytanie Ad Library -> kandydaci w url_store."""
    report = CollectReport(source="facebook", query=spec["q"], tag=spec.get("tag", ""))
    try:
        nodes = source.discover_nodes(spec["q"], spec.get("type", "keyword_unordered"))
    except SourceBlocked as exc:
        report.error = f"blocked: {exc}"
        raise
    except SourceError as exc:
        report.error = str(exc)
        return report
    lex = files.lexicons()
    states: Counter[str] = Counter()
    for ad_id, node in nodes.items():
        cand = from_facebook_node(ad_id, node, spec.get("tag") or spec["q"])
        scored = score(cand, lex)
        outcome = store.upsert(cand, scored, creative_key(cand.publisher_key, cand.primary_text),
                               landing_key(cand.links[0] if cand.links else None))
        if outcome.created:
            states[outcome.state] += 1
        else:
            report.seen_again += 1
    report.found = len(nodes)
    report.created = sum(states.values())
    report.states = dict(states)
    return report


def write_stats(store: UrlStore, cfg: CollectorConfig, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    stats = store.stats()
    stats["paused"] = cfg.pause_flag.exists()
    stats["updated_at"] = datetime.now(UTC).isoformat()
    if extra:
        stats.update(extra)
    cfg.state_dir.mkdir(parents=True, exist_ok=True)
    (cfg.state_dir / "stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    return stats


def run_collector(store: UrlStore, files: CollectorConfigFiles, cfg: CollectorConfig,
                  source_factory: Callable[[], Any], *, max_iterations: int | None = None,
                  sleep: Callable[[float], None] = time.sleep,
                  clock: Callable[[], float] = time.monotonic) -> list[CollectReport]:
    """Petla collectora: zapytania z queries.yaml po kolei (round-robin), z przerwa i jitterem.

    Pauza (plik PAUSED) wstrzymuje tylko collector — flota dalej przerabia kolejke.
    """
    source = source_factory()
    reports: list[CollectReport] = []
    window: list[float] = []
    idx, iterations = 0, 0
    while max_iterations is None or iterations < max_iterations:
        iterations += 1
        if cfg.pause_flag.exists():
            log.info("collector: pauza (%s)", cfg.pause_flag)
            sleep(cfg.interval_s)
            continue
        specs = files.queries().get("facebook", [])
        if not specs:
            log.warning("collector: brak zapytan facebook w queries.yaml")
            sleep(cfg.interval_s)
            continue
        now = clock()
        window = [t for t in window if now - t < 3600]
        if len(window) >= cfg.max_queries_per_hour:
            sleep(max(1.0, 3600 - (now - window[0])))
            continue
        spec = specs[idx % len(specs)]
        idx += 1
        window.append(now)
        try:
            report = collect_facebook_query(store, files, source, spec)
        except SourceBlocked as exc:
            report = CollectReport(source="facebook", query=spec["q"], tag=spec.get("tag", ""), error=str(exc))
            log.warning("collector: blokada zrodla — pauza %.0f s", cfg.blocked_pause_s)
            reports.append(report)
            write_stats(store, cfg, {"last_report": asdict(report)})
            sleep(cfg.blocked_pause_s)
            continue
        reports.append(report)
        log.info("collector: %r -> znaleziono %d, nowe %d %s, ponownie %d",
                 spec["q"], report.found, report.created, report.states, report.seen_again)
        write_stats(store, cfg, {"last_report": asdict(report)})
        sleep(cfg.interval_s + random.uniform(0, cfg.jitter_s))
    return reports


def reprioritize(store: UrlStore, files: CollectorConfigFiles) -> dict[str, int]:
    """Po zmianie slownikow: przelicz priorytet i stan kandydatow, ktorych jeszcze nie pobrano."""
    from collector.synthetic import candidate_from_row

    lex = files.lexicons()
    changed: Counter[str] = Counter()
    for row in store.rows(("queued", "quarantined", "rejected", "new")):
        cand = candidate_from_row(row)
        if cand is None:
            continue
        scored = score(cand, lex, seen_count=row["seen_count"])
        if scored.priority != row["priority"] or scored.state != row["state"]:
            store.set_priority(row["id"], scored.priority, scored.state, scored.signals)
            changed[f"{row['state']}->{scored.state}"] += 1
    return dict(changed)

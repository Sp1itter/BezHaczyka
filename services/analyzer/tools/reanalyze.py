"""Ponowne wstawienie analizy dla przypadkow z bazy (po zmianie routera/regul).

Kolejkuje zadania DOKLADNIE tak jak scraper (services/scraper/jobs.py,
_enqueue_analysis): kolejka `q:gpu`, funkcja `analyzer.worker.analyze_document`,
payload {document_id, enqueued_at, entity_resolution, det_results}.
`entity_resolution` bierzemy z `cases.entity_resolution` (to, co zapisal resolver).

UWAGA: `det_results` (reguly 4-8 z RenderProbe) nie sa przechowywane w tabeli
cases, wiec ponowna analiza wysyla je puste; analyzer policzy 4-8 z fallbacku
render_probe albo zostawi wypelniacze not_applicable.

`--apply` NIE jest idempotentne: kazde wywolanie kolejkuje zadania od nowa
(przypadki w statusie processing/queued sa pomijane). job_timeout=900 s.
Kolejka/funkcja z SCRAPER_OUTPUT_QUEUE / SCRAPER_OUTPUT_FUNC (jak scraper).

Domyslnie DRY-RUN (tylko wypisuje, ile i co by zakolejkowal). `--apply` kolejkuje.

Uzycie (z services/analyzer, DATABASE_URL i VALKEY_URL w srodowisku):

    python tools/reanalyze.py                       # dry-run, wszystkie przypadki
    python tools/reanalyze.py --source facebook     # tylko Facebook
    python tools/reanalyze.py --since 2026-11-20    # od daty (fetched_at)
    python tools/reanalyze.py --source facebook --limit 50 --apply
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone

DEFAULT_QUEUE = "q:gpu"
DEFAULT_FUNC = "analyzer.worker.analyze_document"
QUEUE_NAME = os.getenv("SCRAPER_OUTPUT_QUEUE") or DEFAULT_QUEUE
FUNC_NAME = os.getenv("SCRAPER_OUTPUT_FUNC") or DEFAULT_FUNC
SOURCES = ("facebook", "youtube", "www")
JOB_TIMEOUT_S = 900
SKIP_STATUSES = ("processing", "queued")


def build_payload(row: dict) -> dict:
    """Payload zadania z wiersza `cases` (case_id, entity_resolution)."""
    resolution = row.get("entity_resolution") or {}
    return {
        "document_id": str(row["case_id"]),
        "enqueued_at": datetime.now(timezone.utc).isoformat(),
        "entity_resolution": resolution if isinstance(resolution, dict) else {},
        "det_results": [],
    }


def select_cases(conn, source: str | None, since: str | None, limit: int | None) -> list[dict]:
    where, params = [], []
    if source:
        where.append("source = %s")
        params.append(source)
    if since:
        where.append("fetched_at >= %s")
        params.append(since)
    where.append("status <> ALL(%s)")  # nie dubluj przypadkow w toku
    params.append(list(SKIP_STATUSES))
    sql = "SELECT case_id, source, status, entity_resolution FROM cases"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY fetched_at DESC"
    if limit:
        sql += " LIMIT %s"
        params.append(limit)
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return list(cur.fetchall())


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--since", help="ISO data, np. 2026-11-20 (fetched_at >=)")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--apply", action="store_true", help="faktycznie zakolejkuj (domyslnie dry-run)")
    args = ap.parse_args(argv)

    from analyzer.casedb_bridge import connect

    with connect() as conn:
        rows = select_cases(conn, args.source, args.since, args.limit)

    print(f"Przypadkow do ponownej analizy: {len(rows)}")
    if not args.apply:
        for r in rows[:10]:
            print(f"  {r['case_id']} ({r['source']})")
        print("DRY-RUN: nic nie zakolejkowano. Dodaj --apply.")
        return 0

    from redis import Redis
    from rq import Queue

    queue = Queue(QUEUE_NAME, connection=Redis.from_url(
        os.getenv("VALKEY_URL", "redis://valkey:6379/0")))
    for r in rows:
        queue.enqueue(FUNC_NAME, build_payload(r), job_timeout=JOB_TIMEOUT_S)
    print(f"Zakolejkowano: {len(rows)} -> {QUEUE_NAME}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

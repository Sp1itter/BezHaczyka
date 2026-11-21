"""Most analyzera do wspolnej bazy przypadkow (casedb), tryb jobow.

NIE importujemy pakietu casedb (osobny serwis) - SQL jest powielony minimalnie
z services/casedb/casedb/{store,export}.py i migrations/001_cases.sql.
Polaczenie musi miec row_factory=dict_row (jak casedb.db.connect). psycopg
importujemy LENIWIE, tylko w connect() i _jsonb().
"""

from __future__ import annotations

import logging
import os
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Callable
from uuid import UUID

log = logging.getLogger("analyzer.casedb_bridge")

WORKER = "analyzer"
_CONTENT_FIELDS = ("seq", "body", "start_s", "end_s", "url")
_INTERNAL = {"raw", "extra"}


def connect(url: str | None = None):
    """Polaczenie do bazy (DATABASE_URL z env). psycopg tylko tutaj."""
    import psycopg
    from psycopg.rows import dict_row

    url = url or os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("Brak DATABASE_URL")
    return psycopg.connect(url, row_factory=dict_row)


def _jsonb(value: Any):
    from psycopg.types.json import Jsonb

    return Jsonb(value)


def _plain(v: Any) -> Any:
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, UUID):
        return str(v)
    if isinstance(v, Decimal):
        return float(v)
    return v


def claim(conn, limit: int, *, source: str | None = None, worker: str = WORKER,
          statuses: tuple[str, ...] = ("new",)) -> list[str]:
    """Jak casedb.store.claim: atomowa rezerwacja (FOR UPDATE SKIP LOCKED)."""
    rows = conn.execute(
        """
        UPDATE cases SET status = 'queued', assigned_to = %s, attempts = attempts + 1,
                         updated_at = now()
        WHERE case_id IN (
            SELECT case_id FROM cases
            WHERE status = ANY(%s) AND (%s::text IS NULL OR source = %s)
            ORDER BY created_at
            LIMIT %s
            FOR UPDATE SKIP LOCKED
        )
        RETURNING case_id
        """,
        (worker, list(statuses), source, source, limit),
    ).fetchall()
    return [str(r["case_id"]) for r in rows]


def set_status(conn, case_id: str, status: str, error: str | None = None) -> None:
    """Jak casedb.store.set_status."""
    conn.execute(
        "UPDATE cases SET status = %s, last_error = %s, updated_at = now() WHERE case_id = %s",
        (status, error, case_id),
    )


def fetch_case(conn, case_id: str) -> dict | None:
    """Rownowazne casedb.export.export_cases(..., include_raw=True) dla jednego przypadku."""
    c = conn.execute("SELECT * FROM cases WHERE case_id = %s::uuid", (case_id,)).fetchone()
    if c is None:
        return None
    content: dict[str, list] = defaultdict(list)
    for r in conn.execute(
        "SELECT * FROM case_content WHERE case_id = %s::uuid ORDER BY kind, seq", (case_id,)
    ):
        item = {k: _plain(r[k]) for k in _CONTENT_FIELDS if r[k] is not None}
        item.update(r["extra"] or {})
        content[r["kind"]].append(item)
    assets = [
        {k: _plain(v) for k, v in r.items() if k not in ("id", "case_id")}
        for r in conn.execute(
            "SELECT * FROM case_assets WHERE case_id = %s::uuid ORDER BY id", (case_id,))
    ]
    drop = ("case_id", "source", "url", "status", *_INTERNAL)
    return {
        "case_id": str(c["case_id"]),
        "source": c["source"],
        "url": c["url"],
        "status": c["status"],
        "metadata": {**{k: _plain(v) for k, v in c.items() if k not in drop},
                     **(c["extra"] or {})},
        "content": dict(content),
        "assets": assets,
        "ai_results": {},
        "raw": c["raw"],
    }


def save_ai_result(conn, case_id: str, ai: dict) -> None:
    """Upsert jak casedb.store.save_ai_result (ten sam case/task/model/version nadpisuje)."""
    conn.execute(
        """
        INSERT INTO ai_results (case_id, task, model, version, endpoint, label, score, result)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (case_id, task, model, version) DO UPDATE SET
            endpoint = EXCLUDED.endpoint, label = EXCLUDED.label, score = EXCLUDED.score,
            result = EXCLUDED.result, created_at = now()
        """,
        (case_id, ai["task"], ai["model"], ai.get("version", ""), None, ai.get("label"),
         ai.get("score"), _jsonb(ai["result"])),
    )


def process_cases(conn, analyze_case: Callable[[dict], dict], *, limit: int,
                  source: str | None = None,
                  statuses: tuple[str, ...] = ("new",)) -> dict[str, str]:
    """claim -> processing -> analiza -> ai_result -> done | error. Zwraca {case_id: status}.

    Blad jednego przypadku nie przerywa reszty: rollback, status error + last_error.
    """
    ids = claim(conn, limit, source=source, statuses=statuses)
    conn.commit()
    out: dict[str, str] = {}
    for cid in ids:
        try:
            set_status(conn, cid, "processing")
            conn.commit()
            case = fetch_case(conn, cid)
            if case is None:
                raise LookupError(f"brak przypadku {cid}")
            ai = analyze_case(case)
            save_ai_result(conn, cid, ai)
            set_status(conn, cid, "done")
            conn.commit()
            out[cid] = "done"
        except Exception as exc:  # noqa: BLE001 - jeden przypadek nie wywraca reszty
            log.exception("Przypadek %s nieudany", cid)
            conn.rollback()
            set_status(conn, cid, "error", f"{type(exc).__name__}: {exc}"[:2000])
            conn.commit()
            out[cid] = "error"
    return out

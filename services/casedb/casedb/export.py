"""Eksport przypadkow do JSON dla modulu przydzialu zadan do endpointow modeli."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

import psycopg

_CONTENT_FIELDS = ("seq", "body", "start_s", "end_s", "url")
_INTERNAL = {"raw", "extra"}


def _plain(v: Any) -> Any:
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, UUID):
        return str(v)
    if isinstance(v, Decimal):
        return float(v)
    return v


def _row(r: dict[str, Any], drop: tuple[str, ...] = ()) -> dict[str, Any]:
    return {k: _plain(v) for k, v in r.items() if k not in drop}


def export_cases(
    conn: psycopg.Connection, case_ids: list[str], *, include_raw: bool = False
) -> list[dict[str, Any]]:
    if not case_ids:
        return []
    cases = conn.execute(
        "SELECT * FROM cases WHERE case_id = ANY(%s::uuid[]) ORDER BY created_at", (case_ids,)
    ).fetchall()
    content: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    for r in conn.execute(
        "SELECT * FROM case_content WHERE case_id = ANY(%s::uuid[]) ORDER BY kind, seq", (case_ids,)
    ):
        item = {k: _plain(r[k]) for k in _CONTENT_FIELDS if r[k] is not None}
        item.update(r["extra"] or {})
        content[str(r["case_id"])][r["kind"]].append(item)
    assets: dict[str, list] = defaultdict(list)
    for r in conn.execute(
        "SELECT * FROM case_assets WHERE case_id = ANY(%s::uuid[]) ORDER BY id", (case_ids,)
    ):
        assets[str(r["case_id"])].append(_row(r, ("id", "case_id")))
    ai: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    for r in conn.execute(
        "SELECT * FROM ai_results WHERE case_id = ANY(%s::uuid[]) ORDER BY created_at", (case_ids,)
    ):
        ai[str(r["case_id"])][r["task"]].append(_row(r, ("id", "case_id", "task")))

    out = []
    for c in cases:
        cid = str(c["case_id"])
        doc = {
            "case_id": cid,
            "source": c["source"],
            "url": c["url"],
            "status": c["status"],
            # Wszystkie pozostale kolumny cases, takze te dodane pozniej przez add_column.
            "metadata": {**_row(c, ("case_id", "source", "url", "status", *_INTERNAL)),
                         **(c["extra"] or {})},
            "content": {k: v for k, v in content[cid].items()},
            "assets": assets[cid],
            "ai_results": {k: v for k, v in ai[cid].items()},
        }
        if include_raw:
            doc["raw"] = c["raw"]
        out.append(doc)
    return out


def find_case_ids(
    conn: psycopg.Connection, *, status: str | None = None, source: str | None = None,
    limit: int | None = None,
) -> list[str]:
    rows = conn.execute(
        "SELECT case_id FROM cases WHERE (%s::text IS NULL OR status = %s)"
        " AND (%s::text IS NULL OR source = %s) ORDER BY created_at LIMIT %s",
        (status, status, source, source, limit),
    ).fetchall()
    return [str(r["case_id"]) for r in rows]

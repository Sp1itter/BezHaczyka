"""Zapis i odczyt przypadkow. Jedyne miejsce z SQL-em poza migracjami."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb

CASE_COLUMNS = (
    "title", "author_name", "author_id", "author_url", "lang", "published_at", "fetched_at",
)
TABLES = ("cases", "case_content", "case_assets", "ai_results")
COLUMN_TYPES = (
    "text", "integer", "bigint", "double precision", "real", "numeric", "boolean",
    "jsonb", "timestamptz", "date", "text[]",
)
STATUSES = ("new", "queued", "processing", "done", "error", "skipped")
_IDENT = re.compile(r"^[a-z_][a-z0-9_]{0,62}$")


def case_id_for(url: str) -> str:
    """Ten sam schemat co AdDocument.id w scraperze FB."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, url))


@dataclass
class Content:
    kind: str
    body: str = ""
    start_s: float | None = None
    end_s: float | None = None
    url: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class Asset:
    kind: str
    uri: str
    label: str | None = None
    mime: str | None = None
    sha256: str | None = None
    bytes: int | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class Case:
    source: str
    source_item_id: str
    url: str
    case_id: str | None = None
    title: str | None = None
    author_name: str | None = None
    author_id: str | None = None
    author_url: str | None = None
    lang: str | None = None
    published_at: datetime | str | None = None
    fetched_at: datetime | str | None = None
    extra: dict[str, Any] = field(default_factory=dict)
    raw: Any = field(default_factory=dict)
    content: list[Content] = field(default_factory=list)
    assets: list[Asset] = field(default_factory=list)


def save_case(conn: psycopg.Connection, case: Case) -> str:
    """Upsert przypadku. Tresc jest podmieniana w calosci, assety dopisywane.

    Status i przydzial NIE sa resetowane przy ponownym scrapowaniu.
    """
    case_id = case.case_id or case_id_for(case.url)
    with conn.transaction():
        conn.execute(
            """
            INSERT INTO cases (case_id, source, source_item_id, url, title, author_name, author_id,
                               author_url, lang, published_at, fetched_at, extra, raw)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, COALESCE(%s, now()), %s, %s)
            ON CONFLICT (case_id) DO UPDATE SET
                url = EXCLUDED.url, title = EXCLUDED.title, author_name = EXCLUDED.author_name,
                author_id = EXCLUDED.author_id, author_url = EXCLUDED.author_url,
                lang = EXCLUDED.lang, published_at = COALESCE(EXCLUDED.published_at, cases.published_at),
                fetched_at = EXCLUDED.fetched_at, extra = cases.extra || EXCLUDED.extra,
                raw = EXCLUDED.raw, updated_at = now()
            """,
            (case_id, case.source, case.source_item_id, case.url, case.title, case.author_name,
             case.author_id, case.author_url, case.lang, case.published_at, case.fetched_at,
             Jsonb(case.extra), Jsonb(case.raw)),
        )
        conn.execute("DELETE FROM case_content WHERE case_id = %s", (case_id,))
        seqs: dict[str, int] = {}
        for c in case.content:
            seq = seqs.get(c.kind, 0)
            seqs[c.kind] = seq + 1
            conn.execute(
                "INSERT INTO case_content (case_id, kind, seq, body, start_s, end_s, url, extra)"
                " VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (case_id, c.kind, seq, c.body or "", c.start_s, c.end_s, c.url, Jsonb(c.extra)),
            )
        for a in case.assets:
            add_asset(conn, case_id, a)
    return case_id


def add_asset(conn: psycopg.Connection, case_id: str, a: Asset) -> None:
    conn.execute(
        """
        INSERT INTO case_assets (case_id, kind, label, uri, mime, sha256, bytes, extra)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (case_id, uri) DO UPDATE SET kind = EXCLUDED.kind, label = EXCLUDED.label,
            mime = COALESCE(EXCLUDED.mime, case_assets.mime),
            sha256 = COALESCE(EXCLUDED.sha256, case_assets.sha256),
            bytes = COALESCE(EXCLUDED.bytes, case_assets.bytes),
            extra = case_assets.extra || EXCLUDED.extra
        """,
        (case_id, a.kind, a.label, a.uri, a.mime, a.sha256, a.bytes, Jsonb(a.extra)),
    )


def save_ai_result(
    conn: psycopg.Connection, case_id: str, task: str, model: str, result: Any, *,
    version: str = "", endpoint: str | None = None, label: str | None = None,
    score: float | None = None,
) -> None:
    """Wynik modelu. Ten sam (case, task, model, version) nadpisuje poprzedni."""
    conn.execute(
        """
        INSERT INTO ai_results (case_id, task, model, version, endpoint, label, score, result)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (case_id, task, model, version) DO UPDATE SET
            endpoint = EXCLUDED.endpoint, label = EXCLUDED.label, score = EXCLUDED.score,
            result = EXCLUDED.result, created_at = now()
        """,
        (case_id, task, model, version, endpoint, label, score, Jsonb(result)),
    )


def add_column(conn: psycopg.Connection, table: str, name: str, col_type: str) -> None:
    """Dodaje kolumne (idempotentnie). Nowa kolumna w `cases` od razu trafia do eksportu."""
    if table not in TABLES:
        raise ValueError(f"Nieznana tabela: {table}")
    if not _IDENT.match(name):
        raise ValueError(f"Niedozwolona nazwa kolumny: {name}")
    col_type = col_type.strip().lower()
    if col_type not in COLUMN_TYPES:
        raise ValueError(f"Niedozwolony typ: {col_type}. Dozwolone: {', '.join(COLUMN_TYPES)}")
    conn.execute(
        sql.SQL("ALTER TABLE {} ADD COLUMN IF NOT EXISTS {} " + col_type).format(
            sql.Identifier(table), sql.Identifier(name)
        )
    )


def set_columns(conn: psycopg.Connection, case_id: str, values: dict[str, Any]) -> None:
    """Ustawia wartosci kolumn (np. dodanych przez add_column) dla jednego przypadku."""
    if not values:
        return
    for k in values:
        if not _IDENT.match(k) or k in ("case_id", "source", "source_item_id"):
            raise ValueError(f"Niedozwolona kolumna: {k}")
    assignments = sql.SQL(", ").join(
        sql.SQL("{} = %s").format(sql.Identifier(k)) for k in values
    )
    params = [Jsonb(v) if isinstance(v, (dict, list)) else v for v in values.values()]
    conn.execute(
        sql.SQL("UPDATE cases SET {}, updated_at = now() WHERE case_id = %s").format(assignments),
        [*params, case_id],
    )


def set_status(
    conn: psycopg.Connection, case_id: str, status: str, error: str | None = None
) -> None:
    if status not in STATUSES:
        raise ValueError(f"Nieznany status: {status}")
    conn.execute(
        "UPDATE cases SET status = %s, last_error = %s, updated_at = now() WHERE case_id = %s",
        (status, error, case_id),
    )


def claim(
    conn: psycopg.Connection, worker: str, limit: int, *, source: str | None = None,
    statuses: tuple[str, ...] = ("new",),
) -> list[str]:
    """Atomowo rezerwuje przypadki dla modulu przydzialu (bezpieczne przy wielu workerach)."""
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

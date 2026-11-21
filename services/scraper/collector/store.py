"""url_store — magazyn kandydatow poziomu 1 i kolejka pracy poziomu 2.

Dwa backendy z tym samym API:
  * SQLite (domyslnie, plik COLLECTOR_DB_PATH) — dziala bez Dockera,
  * Postgres (COLLECTOR_DATABASE_URL) — docelowo baza casedb.

Gwarancje:
  * jeden kandydat = jeden wiersz: UNIQUE(source_type, external_id); ponowne
    zobaczenie podbija last_seen i seen_count, nie dubluje pracy,
  * ta sama kreacja (creative_key) u tego samego publishera -> wiersz `merged`
    wskazujacy kanoniczny (bez fetch i bez LLM),
  * `claim` jest atomowy: dwa workery nigdy nie dostana tego samego URL-a;
    wygasly lease (padniety worker) wraca do puli.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from collector.scoring import Candidate, Scored

STATES = ("new", "queued", "in_progress", "fetched", "rejected", "quarantined", "merged", "error", "done")
_SQL_DIR = Path(__file__).resolve().parent / "sql"

_SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS url_store (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type   TEXT NOT NULL CHECK (source_type IN ('facebook', 'youtube', 'web', 'synthetic')),
    external_id   TEXT NOT NULL,
    url           TEXT NOT NULL,
    query_tag     TEXT,
    publisher_key TEXT,
    creative_key  TEXT,
    landing_key   TEXT,
    priority      REAL NOT NULL DEFAULT 0,
    signals       TEXT NOT NULL DEFAULT '{}',
    payload       TEXT NOT NULL DEFAULT '{}',
    state         TEXT NOT NULL DEFAULT 'new' CHECK (state IN
                  ('new', 'queued', 'in_progress', 'fetched', 'rejected', 'quarantined', 'merged', 'error', 'done')),
    merged_into   INTEGER REFERENCES url_store (id),
    document_id   TEXT,
    attempts      INTEGER NOT NULL DEFAULT 0,
    last_error    TEXT,
    locked_until  TEXT,
    locked_by     TEXT,
    first_seen    TEXT NOT NULL,
    last_seen     TEXT NOT NULL,
    seen_count    INTEGER NOT NULL DEFAULT 1,
    updated_at    TEXT NOT NULL,
    UNIQUE (source_type, external_id)
);
CREATE INDEX IF NOT EXISTS ix_url_ready    ON url_store (priority DESC, first_seen) WHERE state = 'queued';
CREATE INDEX IF NOT EXISTS ix_url_state    ON url_store (state);
CREATE INDEX IF NOT EXISTS ix_url_creative ON url_store (creative_key);
CREATE INDEX IF NOT EXISTS ix_url_landing  ON url_store (landing_key);
CREATE INDEX IF NOT EXISTS ix_url_lease    ON url_store (locked_until) WHERE state = 'in_progress';
"""


def _now() -> datetime:
    return datetime.now(UTC)


@dataclass
class UpsertOutcome:
    id: int
    created: bool
    state: str
    merged_into: int | None = None


class UrlStore:
    """Wspolna logika; roznice dialektow w `ph`, `_ts`, `_json_param`, `_execute`."""

    ph = "?"

    # ----------------------------------------------------------- dialekt --

    def _execute(self, sql: str, params: tuple | list = ()) -> list[dict[str, Any]]:
        raise NotImplementedError

    def _ts(self, dt: datetime) -> Any:
        return dt

    def _json_param(self) -> str:
        return self.ph

    def _row(self, row: dict[str, Any]) -> dict[str, Any]:
        out = dict(row)
        for key in ("signals", "payload"):
            if isinstance(out.get(key), str):
                out[key] = json.loads(out[key])
        return out

    def ensure_schema(self) -> None:
        raise NotImplementedError

    # ------------------------------------------------------------ zapis --

    def upsert(self, cand: Candidate, scored: Scored, creative_key: str | None,
               landing_key: str | None, now: datetime | None = None) -> UpsertOutcome:
        now = now or _now()
        p = self.ph
        existing = self._execute(
            f"SELECT id, state, merged_into FROM url_store WHERE source_type = {p} AND external_id = {p}",
            (cand.source_type, cand.external_id),
        )
        if existing:
            row = existing[0]
            self._execute(
                f"UPDATE url_store SET last_seen = {p}, seen_count = seen_count + 1, updated_at = {p} WHERE id = {p}",
                (self._ts(now), self._ts(now), row["id"]),
            )
            return UpsertOutcome(id=row["id"], created=False, state=row["state"], merged_into=row["merged_into"])

        state, merged_into = scored.state, None
        if creative_key and state != "rejected":
            canon = self._execute(
                f"SELECT id FROM url_store WHERE creative_key = {p} AND state <> 'merged' ORDER BY id LIMIT 1",
                (creative_key,),
            )
            if canon:
                state, merged_into = "merged", canon[0]["id"]
                self._execute(
                    f"UPDATE url_store SET seen_count = seen_count + 1, last_seen = {p}, updated_at = {p} WHERE id = {p}",
                    (self._ts(now), self._ts(now), merged_into),
                )
        j = self._json_param()
        rows = self._execute(
            f"INSERT INTO url_store (source_type, external_id, url, query_tag, publisher_key, creative_key,"
            f" landing_key, priority, signals, payload, state, merged_into, first_seen, last_seen, updated_at)"
            f" VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {j}, {j}, {p}, {p}, {p}, {p}, {p}) RETURNING id",
            (cand.source_type, cand.external_id, cand.url, cand.query_tag, cand.publisher_key, creative_key,
             landing_key, scored.priority, json.dumps(scored.signals, ensure_ascii=False),
             json.dumps(cand.payload, ensure_ascii=False), state, merged_into,
             self._ts(now), self._ts(now), self._ts(now)),
        )
        return UpsertOutcome(id=rows[0]["id"], created=True, state=state, merged_into=merged_into)

    # ------------------------------------------------------- kolejka pracy --

    def claim(self, worker: str, lease_s: float = 300, now: datetime | None = None) -> dict[str, Any] | None:
        raise NotImplementedError

    def finish(self, row_id: int, state: str, *, document_id: str | None = None,
               error: str | None = None, now: datetime | None = None) -> None:
        if state not in STATES:
            raise ValueError(f"nieznany stan {state!r}")
        now = now or _now()
        p = self.ph
        self._execute(
            f"UPDATE url_store SET state = {p}, document_id = COALESCE({p}, document_id), last_error = {p},"
            f" locked_until = NULL, locked_by = NULL, updated_at = {p} WHERE id = {p}",
            (state, document_id, error, self._ts(now), row_id),
        )

    def fail(self, row_id: int, error: str, max_attempts: int, retry_after_s: float = 60,
             now: datetime | None = None) -> str:
        """Blad przetwarzania: ponowienie z opoznieniem albo `error` po max_attempts."""
        now = now or _now()
        p = self.ph
        attempts = self._execute(f"SELECT attempts FROM url_store WHERE id = {p}", (row_id,))[0]["attempts"]
        if attempts >= max_attempts:
            self.finish(row_id, "error", error=error, now=now)
            return "error"
        # wraca do kolejki, ale lease blokuje go do retry_after (backoff)
        self._execute(
            f"UPDATE url_store SET state = 'in_progress', last_error = {p}, locked_until = {p},"
            f" locked_by = 'retry', updated_at = {p} WHERE id = {p}",
            (error, self._ts(now + timedelta(seconds=retry_after_s)), self._ts(now), row_id),
        )
        return "retry"

    # ----------------------------------------------------------- odczyt --

    def get(self, row_id: int) -> dict[str, Any] | None:
        rows = self._execute(f"SELECT * FROM url_store WHERE id = {self.ph}", (row_id,))
        return self._row(rows[0]) if rows else None

    def rows(self, states: tuple[str, ...]) -> list[dict[str, Any]]:
        marks = ", ".join([self.ph] * len(states))
        return [self._row(r) for r in self._execute(
            f"SELECT * FROM url_store WHERE state IN ({marks}) ORDER BY id", tuple(states))]

    def set_priority(self, row_id: int, priority: float, state: str, signals: dict[str, Any],
                     now: datetime | None = None) -> None:
        now = now or _now()
        p, j = self.ph, self._json_param()
        self._execute(
            f"UPDATE url_store SET priority = {p}, state = {p}, signals = {j}, updated_at = {p} WHERE id = {p}",
            (priority, state, json.dumps(signals, ensure_ascii=False), self._ts(now), row_id),
        )

    def stats(self) -> dict[str, Any]:
        by_state = {r["state"]: r["n"] for r in self._execute(
            "SELECT state, COUNT(*) AS n FROM url_store GROUP BY state")}
        by_source = {r["source_type"]: r["n"] for r in self._execute(
            "SELECT source_type, COUNT(*) AS n FROM url_store GROUP BY source_type")}
        total = sum(by_state.values())
        top = [self._row(r) for r in self._execute(
            "SELECT id, url, priority, state, query_tag, signals FROM url_store"
            " WHERE state IN ('queued', 'in_progress', 'fetched', 'done') ORDER BY priority DESC LIMIT 10")]
        return {
            "total": total,
            "by_state": {s: by_state.get(s, 0) for s in STATES},
            "by_source": by_source,
            "noise_ratio": round((by_state.get("quarantined", 0) + by_state.get("rejected", 0)
                                  + by_state.get("merged", 0)) / total, 3) if total else 0.0,
            "top": [{"id": t["id"], "url": t["url"], "priority": t["priority"], "state": t["state"],
                     "tag": t["query_tag"]} for t in top],
        }


class SqliteUrlStore(UrlStore):
    ph = "?"

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path, timeout=30, isolation_level=None, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA busy_timeout=30000")
        self.ensure_schema()

    def _execute(self, sql: str, params: tuple | list = ()) -> list[dict[str, Any]]:
        cur = self.conn.execute(sql, tuple(params))
        return [dict(r) for r in cur.fetchall()] if cur.description else []

    def _ts(self, dt: datetime) -> str:
        return dt.astimezone(UTC).isoformat()

    def ensure_schema(self) -> None:
        self.conn.executescript(_SQLITE_SCHEMA)

    def claim(self, worker: str, lease_s: float = 300, now: datetime | None = None) -> dict[str, Any] | None:
        now = now or _now()
        self.conn.execute("BEGIN IMMEDIATE")  # blokada zapisu: claim atomowy miedzy procesami
        try:
            rows = self._execute(
                "SELECT id FROM url_store WHERE state = 'queued'"
                " OR (state = 'in_progress' AND locked_until < ?)"
                " ORDER BY priority DESC, first_seen LIMIT 1",
                (self._ts(now),),
            )
            if not rows:
                self.conn.execute("COMMIT")
                return None
            row_id = rows[0]["id"]
            self._execute(
                "UPDATE url_store SET state = 'in_progress', locked_until = ?, locked_by = ?,"
                " attempts = attempts + 1, updated_at = ? WHERE id = ?",
                (self._ts(now + timedelta(seconds=lease_s)), worker, self._ts(now), row_id),
            )
            self.conn.execute("COMMIT")
        except Exception:
            self.conn.execute("ROLLBACK")
            raise
        return self.get(row_id)


class PostgresUrlStore(UrlStore):
    ph = "%s"

    def __init__(self, url: str) -> None:
        import psycopg
        from psycopg.rows import dict_row

        self.conn = psycopg.connect(url, autocommit=True, row_factory=dict_row)
        self.ensure_schema()

    def _json_param(self) -> str:
        return "%s::jsonb"

    def _execute(self, sql: str, params: tuple | list = ()) -> list[dict[str, Any]]:
        with self.conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            return list(cur.fetchall()) if cur.description else []

    def ensure_schema(self) -> None:
        with self.conn.cursor() as cur:
            cur.execute((_SQL_DIR / "url_store.postgres.sql").read_text(encoding="utf-8"))

    def claim(self, worker: str, lease_s: float = 300, now: datetime | None = None) -> dict[str, Any] | None:
        now = now or _now()
        rows = self._execute(
            "UPDATE url_store SET state = 'in_progress', locked_until = %s, locked_by = %s,"
            " attempts = attempts + 1, updated_at = %s"
            " WHERE id = (SELECT id FROM url_store WHERE state = 'queued'"
            " OR (state = 'in_progress' AND locked_until < %s)"
            " ORDER BY priority DESC, first_seen LIMIT 1 FOR UPDATE SKIP LOCKED) RETURNING id",
            (now + timedelta(seconds=lease_s), worker, now, now),
        )
        return self.get(rows[0]["id"]) if rows else None


def open_store(database_url: str | None = None, sqlite_path: str | Path | None = None) -> UrlStore:
    if database_url:
        return PostgresUrlStore(database_url)
    return SqliteUrlStore(sqlite_path or "data/collector/url_store.sqlite")

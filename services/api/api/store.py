"""Magazyn dokumentow i findingow serwisu api.

Dwie implementacje z jednym interfejsem:

- PostgresStore — produkcja i docker-compose. Tabele `documents` i `findings`
  tworzy migracja services/casedb (002_modul1.sql; pgvector, JSONB, INTEGER[]). Ten modul ich NIE tworzy,
  zeby schemat mial jedno zrodlo prawdy.
- SqliteStore — praca bez Dockera (na zadnej maszynie zespolu go nie bylo).
  Ten sam ksztalt kolumn, JSON trzymany jako tekst. Uzywany tez w testach.

Zasada z docs/INTEGRACJA.md: `rule_results` zapisujemy W CALOSCI — panel
kalibracji przelicza flagi po stronie klienta.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from api.contracts import AdDocument, Finding

log = logging.getLogger("api.store")

# Wymiar kolumny documents.embedding w migracji casedb 002_modul1.sql (bge-m3).
EMBEDDING_DIM = 1024


class InvalidId(ValueError):
    """Identyfikator nie pasuje do typu kolumny (Postgres: UUID)."""


_DOC_JSON = ("publisher", "screenshots", "media", "transcript", "render_probe", "scope")
_FINDING_JSON = ("routing", "rule_results", "entities")
# Praca czlowieka nad findingiem (migracja casedb 011_review.sql). Nie naleza do kontraktu Finding.
_REVIEW_COLS = (
    "assignee", "assigned_by", "assigned_at",
    "review_verdict", "review_label", "review_note", "reviewed_by", "reviewed_at",
)
UNSET: Any = object()  # "pole nie przyszlo w PATCH" (rozne od None = wyczysc)


@dataclass
class FindingFilter:
    risk_level: list[str] | None = None
    status: list[str] | None = None
    module: int | None = None
    source: str | None = None
    min_score: float | None = None
    max_score: float | None = None
    q: str | None = None
    limit: int = 100
    offset: int = 0


@dataclass
class UpsertResult:
    created: bool
    previous_risk_level: str | None


def _iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def document_row(doc: AdDocument) -> dict[str, Any]:
    d = doc.model_dump(mode="json")
    row = {k: d[k] for k in ("id", "source", "url", "lang", "title", "text", "html_path", "simhash")}
    row["fetched_at"] = d["fetched_at"]
    for k in _DOC_JSON:
        row[k] = d[k]
    row["embedding"] = (d.get("embedding") or {}).get("vector") or None
    return row


def finding_row(f: Finding) -> dict[str, Any]:
    d = f.model_dump(mode="json")
    return {
        "id": d["id"],
        "document_id": d["document_id"],
        "primary_module": d["primary_module"],
        "modules": d["modules"],
        "routing": d["routing"],
        "risk_score": d["risk_score"],
        "risk_level": d["risk_level"],
        "rule_results": d["rule_results"],
        "entities": d["entities"],
        "knn_score": d["knn_score"],
        "status": d["status"],
        "created_at": d["created_at"],
    }


def _row_to_document(row: dict[str, Any]) -> AdDocument:
    vec = row.pop("embedding", None)
    if vec:
        row["embedding"] = {"model": "bge-m3", "dim": len(vec), "vector": vec}
    return AdDocument.model_validate(row)


# Kolumny dokumentu zwracane razem z findingiem na liscie (lekki podglad).
DOC_PREVIEW = ("source", "url", "title", "publisher", "lang", "text")


class SqlStore:
    """Wspolna logika SQL. Podklasy ustalaja dialekt."""

    ph = "?"
    dialect = "sqlite"

    # --- hooki dialektu ---------------------------------------------------
    def _execute(self, sql: str, params: Iterable[Any] = ()) -> list[dict[str, Any]]:
        raise NotImplementedError

    def _dump_json(self, value: Any) -> Any:
        return None if value is None else json.dumps(value, ensure_ascii=False)

    def _load_json(self, value: Any) -> Any:
        if value is None or not isinstance(value, str):
            return value
        return json.loads(value)

    def _module_clause(self) -> str:
        return f"EXISTS (SELECT 1 FROM json_each(f.modules) WHERE value = {self.ph})"

    def _modules_value(self, modules: list[int]) -> Any:
        return json.dumps(modules)

    def _embedding_value(self, vec: list[float] | None) -> Any:
        return None if vec is None else json.dumps(vec)

    def _embedding_select(self) -> str:
        return "embedding"

    def _embedding_placeholder(self) -> str:
        return self.ph

    def _load_embedding(self, value: Any) -> list[float] | None:
        return self._load_json(value)

    def _load_modules(self, value: Any) -> list[int]:
        return self._load_json(value) or []

    def valid_id(self, value: str) -> bool:
        """Czy identyfikator pasuje do typu kolumny id (SQLite: dowolny tekst)."""
        return True

    def _require_ids(self, *ids: str) -> None:
        bad = [i for i in ids if not self.valid_id(i)]
        if bad:
            raise InvalidId(f"Identyfikator nie jest UUID: {', '.join(bad)}")

    # --- dokumenty --------------------------------------------------------
    def upsert_document(self, doc: AdDocument) -> bool:
        self._require_ids(doc.id)
        row = document_row(doc)
        exists = bool(self._execute(f"SELECT 1 AS x FROM documents WHERE id = {self.ph}", [row["id"]]))
        values = {
            **{k: row[k] for k in ("id", "source", "url", "fetched_at", "lang", "title", "text", "html_path", "simhash")},
            **{k: self._dump_json(row[k]) for k in _DOC_JSON},
        }
        cols = list(values) + ["embedding"]
        params = list(values.values()) + [self._embedding_value(row["embedding"])]
        placeholders = [self.ph] * len(values) + [self._embedding_placeholder()]
        if exists:
            sets = ", ".join(f"{c} = {p}" for c, p in zip(cols[1:], placeholders[1:]))
            self._execute(f"UPDATE documents SET {sets} WHERE id = {self.ph}", params[1:] + [row["id"]])
        else:
            self._execute(
                f"INSERT INTO documents ({', '.join(cols)}) VALUES ({', '.join(placeholders)})", params
            )
        return not exists

    def get_document(self, document_id: str) -> AdDocument | None:
        if not self.valid_id(document_id):
            return None
        cols = "id, source, url, fetched_at, lang, title, text, html_path, simhash, " + ", ".join(_DOC_JSON)
        rows = self._execute(
            f"SELECT {cols}, {self._embedding_select()} AS embedding FROM documents WHERE id = {self.ph}",
            [document_id],
        )
        if not rows:
            return None
        row = rows[0]
        for k in _DOC_JSON:
            row[k] = self._load_json(row[k])
        row["embedding"] = self._load_embedding(row["embedding"])
        row["id"] = str(row["id"])
        return _row_to_document(row)

    def document_exists(self, document_id: str) -> bool:
        if not self.valid_id(document_id):
            return False
        return bool(self._execute(f"SELECT 1 AS x FROM documents WHERE id = {self.ph}", [document_id]))

    # --- findingi ---------------------------------------------------------
    def upsert_finding(self, f: Finding) -> UpsertResult:
        self._require_ids(f.id, f.document_id)
        row = finding_row(f)
        prev = self._execute(
            f"SELECT risk_level, reviewed_by FROM findings WHERE id = {self.ph}", [row["id"]]
        )
        values = {
            **row,
            "modules": self._modules_value(row["modules"]),
            **{k: self._dump_json(row[k]) for k in _FINDING_JSON},
        }
        if prev and prev[0]["reviewed_by"]:
            # Ponowna analiza nie nadpisuje decyzji czlowieka.
            values.pop("status")
        cols = list(values)
        if prev:
            sets = ", ".join(f"{c} = {self.ph}" for c in cols[1:])
            self._execute(
                f"UPDATE findings SET {sets} WHERE id = {self.ph}", list(values.values())[1:] + [row["id"]]
            )
            return UpsertResult(created=False, previous_risk_level=prev[0]["risk_level"])
        self._execute(
            f"INSERT INTO findings ({', '.join(cols)}) VALUES ({', '.join([self.ph] * len(cols))})",
            list(values.values()),
        )
        return UpsertResult(created=True, previous_risk_level=None)

    def _finding_select(self) -> str:
        doc_cols = ", ".join(f"d.{c} AS doc_{c}" for c in DOC_PREVIEW)
        return (
            "SELECT f.id, f.document_id, f.primary_module, f.modules, f.routing, f.risk_score, "
            "f.risk_level, f.rule_results, f.entities, f.knn_score, f.status, f.created_at, "
            + "".join(f"f.{c}, " for c in _REVIEW_COLS)
            + f"{doc_cols} FROM findings f LEFT JOIN documents d ON d.id = f.document_id"
        )

    def _hydrate(self, row: dict[str, Any]) -> dict[str, Any]:
        out = {k: v for k, v in row.items() if not k.startswith("doc_") and k not in _REVIEW_COLS}
        rv = {k: row.get(k) for k in _REVIEW_COLS}
        for k in ("assigned_at", "reviewed_at"):
            if isinstance(rv[k], datetime):
                rv[k] = _iso(rv[k])
        out["id"] = str(out["id"])
        out["document_id"] = str(out["document_id"])
        out["modules"] = self._load_modules(out["modules"])
        for k in _FINDING_JSON:
            out[k] = self._load_json(out[k])
        if isinstance(out["created_at"], datetime):
            out["created_at"] = _iso(out["created_at"])
        finding = Finding.model_validate(out).model_dump(mode="json")
        doc = None
        if row.get("doc_source") is not None:
            text = row.get("doc_text") or ""
            doc = {
                "source": row["doc_source"],
                "url": row["doc_url"],
                "title": row["doc_title"],
                "publisher": self._load_json(row["doc_publisher"]),
                "lang": row["doc_lang"],
                "text_excerpt": text[:400],
            }
        finding["document"] = doc
        finding["assignee"] = rv["assignee"]
        finding["assigned_by"] = rv["assigned_by"]
        finding["assigned_at"] = rv["assigned_at"]
        finding["review"] = (
            {
                "decision": rv["review_verdict"],
                "label": rv["review_label"],
                "note": rv["review_note"],
                "by": rv["reviewed_by"],
                "at": rv["reviewed_at"],
            }
            if rv["reviewed_by"]
            else None
        )
        return finding

    def list_findings(self, flt: FindingFilter) -> tuple[list[dict[str, Any]], int]:
        where, params = [], []
        if flt.risk_level:
            where.append(f"f.risk_level IN ({', '.join([self.ph] * len(flt.risk_level))})")
            params += flt.risk_level
        if flt.status:
            where.append(f"f.status IN ({', '.join([self.ph] * len(flt.status))})")
            params += flt.status
        if flt.module is not None:
            where.append(self._module_clause())
            params.append(flt.module)
        if flt.source:
            where.append(f"d.source = {self.ph}")
            params.append(flt.source)
        if flt.min_score is not None:
            where.append(f"f.risk_score >= {self.ph}")
            params.append(flt.min_score)
        if flt.max_score is not None:
            where.append(f"f.risk_score <= {self.ph}")
            params.append(flt.max_score)
        if flt.q:
            like = f"%{flt.q.lower()}%"
            where.append(
                f"(LOWER(COALESCE(d.title, '')) LIKE {self.ph} OR LOWER(COALESCE(d.text, '')) LIKE {self.ph}"
                f" OR LOWER(COALESCE(d.url, '')) LIKE {self.ph})"
            )
            params += [like, like, like]
        clause = (" WHERE " + " AND ".join(where)) if where else ""
        base_from = " FROM findings f LEFT JOIN documents d ON d.id = f.document_id"
        total = self._execute(f"SELECT COUNT(*) AS n{base_from}{clause}", params)[0]["n"]
        rows = self._execute(
            f"{self._finding_select()}{clause} ORDER BY f.created_at DESC, f.risk_score DESC"
            f" LIMIT {self.ph} OFFSET {self.ph}",
            params + [flt.limit, flt.offset],
        )
        return [self._hydrate(r) for r in rows], int(total)

    def get_finding(self, finding_id: str) -> dict[str, Any] | None:
        if not self.valid_id(finding_id):
            return None
        rows = self._execute(f"{self._finding_select()} WHERE f.id = {self.ph}", [finding_id])
        return self._hydrate(rows[0]) if rows else None

    def update_status(self, finding_id: str, status: str) -> bool:
        if not self.valid_id(finding_id):
            return False
        if not self._execute(f"SELECT 1 AS x FROM findings WHERE id = {self.ph}", [finding_id]):
            return False
        self._execute(f"UPDATE findings SET status = {self.ph} WHERE id = {self.ph}", [status, finding_id])
        return True

    def update_finding(
        self,
        finding_id: str,
        *,
        actor: str | None = None,
        status: str | None = None,
        assignee: Any = UNSET,
        review: dict[str, Any] | None = None,
    ) -> bool:
        """Zmiana statusu, przypisania lub ocena czlowieka + wpis do finding_events."""
        if not self.valid_id(finding_id):
            return False
        if not self._execute(f"SELECT 1 AS x FROM findings WHERE id = {self.ph}", [finding_id]):
            return False
        now = _iso(datetime.now(timezone.utc))
        sets: dict[str, Any] = {}
        events: list[tuple[str, dict[str, Any]]] = []
        if status is not None and review is None:
            sets["status"] = status
            events.append(("status", {"status": status}))
        if assignee is not UNSET:
            sets.update(assignee=assignee, assigned_by="human" if assignee else None,
                        assigned_at=now if assignee else None)
            events.append(("assign", {"assignee": assignee}))
        if review is not None:
            sets.update(status=review["decision"], review_verdict=review["decision"],
                        review_label=review["label"], review_note=review.get("note"),
                        reviewed_by=actor, reviewed_at=now)
            events.append(("review", {k: review.get(k) for k in ("decision", "label", "note")}))
        if not sets:
            return True
        cols = ", ".join(f"{c} = {self.ph}" for c in sets)
        self._execute(f"UPDATE findings SET {cols} WHERE id = {self.ph}", list(sets.values()) + [finding_id])
        if review is not None and assignee is UNSET:
            # Kto ocenil, ten sie tym zajal - jesli nikt nie byl przypisany.
            self._execute(
                f"UPDATE findings SET assignee = {self.ph}, assigned_by = 'human', assigned_at = {self.ph}"
                f" WHERE id = {self.ph} AND assignee IS NULL",
                [actor, now, finding_id],
            )
        for action, detail in events:
            self._execute(
                f"INSERT INTO finding_events (finding_id, at, actor, action, detail)"
                f" VALUES ({self.ph}, {self.ph}, {self.ph}, {self.ph}, {self.ph})",
                [finding_id, now, actor, action, self._dump_json(detail)],
            )
        return True

    def list_events(self, finding_id: str) -> list[dict[str, Any]]:
        if not self.valid_id(finding_id):
            return []
        rows = self._execute(
            f"SELECT at, actor, action, detail FROM finding_events WHERE finding_id = {self.ph} ORDER BY at, id",
            [finding_id],
        )
        return [
            {"at": _iso(r["at"]) if isinstance(r["at"], datetime) else r["at"], "actor": r["actor"],
             "action": r["action"], "detail": self._load_json(r["detail"])}
            for r in rows
        ]

    def all_findings(self) -> list[dict[str, Any]]:
        rows = self._execute(f"{self._finding_select()} ORDER BY f.created_at DESC")
        return [self._hydrate(r) for r in rows]

    def ping(self) -> bool:
        try:
            self._execute("SELECT 1 AS x")
            return True
        except Exception:  # noqa: BLE001 - /health ma odpowiedziec, nie wywrocic sie
            return False


# --------------------------------------------------------------------------- #
# SQLite — dev bez Dockera i testy
# --------------------------------------------------------------------------- #

_SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY, source TEXT NOT NULL, url TEXT NOT NULL, fetched_at TEXT NOT NULL,
    publisher TEXT NOT NULL DEFAULT '{}', lang TEXT NOT NULL DEFAULT 'pl', title TEXT,
    text TEXT NOT NULL DEFAULT '', html_path TEXT, screenshots TEXT NOT NULL DEFAULT '{}',
    media TEXT NOT NULL DEFAULT '[]', transcript TEXT, render_probe TEXT, embedding TEXT,
    simhash TEXT, scope TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS findings (
    id TEXT PRIMARY KEY, document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    primary_module INTEGER, modules TEXT NOT NULL DEFAULT '[]', routing TEXT NOT NULL DEFAULT '{}',
    risk_score REAL NOT NULL, risk_level TEXT NOT NULL, rule_results TEXT NOT NULL DEFAULT '[]',
    entities TEXT NOT NULL DEFAULT '{}', knn_score REAL, status TEXT NOT NULL DEFAULT 'new',
    created_at TEXT NOT NULL, assignee TEXT, assigned_by TEXT, assigned_at TEXT,
    review_verdict TEXT, review_label TEXT, review_note TEXT, reviewed_by TEXT, reviewed_at TEXT
);
CREATE TABLE IF NOT EXISTS finding_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT, finding_id TEXT NOT NULL, at TEXT NOT NULL,
    actor TEXT, action TEXT NOT NULL, detail TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_findings_risk_level ON findings (risk_level);
CREATE INDEX IF NOT EXISTS idx_findings_created_at ON findings (created_at DESC);
"""


class SqliteStore(SqlStore):
    def __init__(self, path: str = ":memory:") -> None:
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.executescript(_SQLITE_SCHEMA)
        # Stary plik dev (sprzed 011_review): dopisz brakujace kolumny.
        have = {r[1] for r in self._conn.execute("PRAGMA table_info(findings)")}
        for col in _REVIEW_COLS:
            if col not in have:
                self._conn.execute(f"ALTER TABLE findings ADD COLUMN {col} TEXT")
        self._conn.commit()
        self._lock = threading.Lock()

    def _execute(self, sql: str, params: Iterable[Any] = ()) -> list[dict[str, Any]]:
        with self._lock:
            cur = self._conn.execute(sql, list(params))
            rows = [dict(r) for r in cur.fetchall()] if cur.description else []
            self._conn.commit()
            return rows


# --------------------------------------------------------------------------- #
# Postgres — schemat z migracji services/casedb
# --------------------------------------------------------------------------- #


class PostgresStore(SqlStore):
    ph = "%s"
    dialect = "postgresql"

    def __init__(self, dsn: str) -> None:
        import psycopg  # import leniwy: SQLite nie potrzebuje sterownika
        from psycopg.rows import dict_row
        from psycopg.types.json import Jsonb

        self._Jsonb = Jsonb
        self._conn = psycopg.connect(dsn, autocommit=True, row_factory=dict_row)
        self._lock = threading.Lock()

    def _execute(self, sql: str, params: Iterable[Any] = ()) -> list[dict[str, Any]]:
        with self._lock, self._conn.cursor() as cur:
            cur.execute(sql, list(params))
            return list(cur.fetchall()) if cur.description else []

    def _dump_json(self, value: Any) -> Any:
        return None if value is None else self._Jsonb(value)

    def _module_clause(self) -> str:
        return f"{self.ph} = ANY(f.modules)"

    def _modules_value(self, modules: list[int]) -> Any:
        return modules

    def _load_modules(self, value: Any) -> list[int]:
        return list(value or [])

    def valid_id(self, value: str) -> bool:
        try:
            uuid.UUID(str(value))
            return True
        except ValueError:
            return False

    # pgvector bez dodatkowego pakietu: literal tekstowy '[a,b,...]' rzutowany na vector.
    def _embedding_value(self, vec: list[float] | None) -> Any:
        if vec is None:
            return None
        if len(vec) != EMBEDDING_DIM:
            # Kolumna ma staly wymiar. Zly wektor nie moze zablokowac zapisu reklamy:
            # zapisujemy dokument bez embeddingu (brak danych, nie blad materialu).
            log.warning("Embedding o wymiarze %d zamiast %d pominiety", len(vec), EMBEDDING_DIM)
            return None
        return "[" + ",".join(repr(float(x)) for x in vec) + "]"

    def _embedding_placeholder(self) -> str:
        return "%s::vector"

    def _embedding_select(self) -> str:
        return "embedding::text"

    def _load_embedding(self, value: Any) -> list[float] | None:
        return None if not value else json.loads(value)


def open_store(database_url: str | None) -> SqlStore:
    """`postgresql://...` -> Postgres, `sqlite:///sciezka` lub brak -> SQLite."""
    url = database_url or "sqlite:///./data/api-dev.sqlite"
    if url.startswith(("postgresql://", "postgres://")):
        return PostgresStore(url)
    if url.startswith("sqlite:///"):
        return SqliteStore(url[len("sqlite:///"):])
    raise ValueError(f"Nieobslugiwany DATABASE_URL: {url.split(':', 1)[0]}://...")

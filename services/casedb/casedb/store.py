"""Zapis i odczyt przypadkow. Jedyne miejsce z SQL-em poza migracjami."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
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


def _jsonb(value: Any) -> Jsonb | None:
    if value is None:
        return None
    return Jsonb(value, dumps=lambda o: json.dumps(o, ensure_ascii=False, default=str))


def _plain(value: Any) -> Any:
    return getattr(value, "value", value)


def _fold(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.casefold().replace("\u0142", "l"))
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def content_hash(doc: dict) -> str:
    """sha256 z tekstu title + text + transcript.text (NFC, casefold, jedna spacja)."""
    transcript = doc.get("transcript") or {}
    raw = " ".join((doc.get("title") or "", doc.get("text") or "", transcript.get("text") or ""))
    norm = " ".join(unicodedata.normalize("NFC", raw).casefold().split())
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


_LEGAL_FORMS = sorted(
    (tuple(f.split()) for f in (
        "sp z o o", "sp z oo", "spolka z ograniczona odpowiedzialnoscia", "spolka akcyjna",
        "sp k", "sp j", "sp komandytowa", "s a", "sa", "ag", "ltd", "limited", "gmbh", "plc",
        "se", "n v", "nv", "b v", "bv", "inc", "llc", "ab", "as", "a s", "oy", "kg", "sarl", "s r l",
    )),
    key=len, reverse=True,
)


def normalize_name(name: str) -> str:
    """Nazwa do porownan: casefold, bez diakrytykow, bez form prawnych i interpunkcji."""
    tokens = re.sub(r"[^a-z0-9]+", " ", _fold(name)).split()
    changed = True
    while changed:
        changed = False
        for form in _LEGAL_FORMS:
            n = len(form)
            if len(tokens) > n and tuple(tokens[-n:]) == form:
                tokens = tokens[:-n]
                changed = True
                break
    return " ".join(tokens)


def record_document(
    conn: psycopg.Connection, doc: dict, *, entity_resolution: dict | None = None,
    extra_content: list[Content] | None = None, qualified: bool = True,
) -> tuple[str, str]:
    """Zapisuje AdDocument; zwraca (case_id, 'new' | 'changed' | 'unchanged')."""
    from casedb.ingest import from_ad_document

    case = from_ad_document(doc)
    case.content.extend(extra_content or [])
    case_id = case.case_id or case_id_for(case.url)
    digest = content_hash(doc)
    status = "new" if qualified else "skipped"
    er = _jsonb(entity_resolution)
    with conn.transaction():
        row = conn.execute(
            "SELECT content_hash FROM cases WHERE case_id = %s FOR UPDATE", (case_id,)
        ).fetchone()
        if row and row["content_hash"] == digest:
            conn.execute(
                "UPDATE cases SET last_seen_at = now(), seen_count = seen_count + 1,"
                " gone_at = NULL, entity_resolution = COALESCE(%s, entity_resolution)"
                " WHERE case_id = %s",
                (er, case_id),
            )
            return case_id, "unchanged"
        save_case(conn, case)
        conn.execute(
            "UPDATE cases SET content_hash = %s, last_seen_at = now(),"
            " seen_count = CASE WHEN %s THEN seen_count + 1 ELSE seen_count END,"
            " gone_at = NULL, status = %s, entity_resolution = COALESCE(%s, entity_resolution)"
            " WHERE case_id = %s",
            (digest, row is not None, status, er, case_id),
        )
    return case_id, "changed" if row else "new"


def get_document(conn: psycopg.Connection, case_id: str) -> dict | None:
    """cases.raw uzupelniony o embedding (lista floatow lub None) i simhash."""
    row = conn.execute(
        "SELECT raw, embedding::text AS embedding, simhash FROM cases WHERE case_id = %s",
        (case_id,),
    ).fetchone()
    if row is None:
        return None
    doc = dict(row["raw"])
    doc["embedding"] = json.loads(row["embedding"]) if row["embedding"] else None
    if row["simhash"] is not None:
        doc["simhash"] = row["simhash"]
    return doc


def save_vectors(
    conn: psycopg.Connection, case_id: str, embedding: list[float] | None, simhash: str | None
) -> None:
    """Zapisuje embedding (vector(1024)) i simhash przypadku."""
    vec = "[" + ",".join(repr(float(x)) for x in embedding) + "]" if embedding else None
    conn.execute(
        "UPDATE cases SET embedding = %s::vector, simhash = %s, updated_at = now()"
        " WHERE case_id = %s",
        (vec, simhash, case_id),
    )


def save_finding(
    conn: psycopg.Connection, finding: dict, document_snapshot: dict | None = None
) -> None:
    """Upsert findingu po id; cases.status='done'; dla 'high' pg_notify('findings_high')."""
    with conn.transaction():
        conn.execute(
            """
            INSERT INTO findings (id, document_id, primary_module, modules, routing, risk_score,
                                  risk_level, rule_results, entities, knn_score, status,
                                  created_at, document_snapshot)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, COALESCE(%s, 'new'),
                    COALESCE(%s, now()), %s)
            ON CONFLICT (id) DO UPDATE SET
                document_id = EXCLUDED.document_id, primary_module = EXCLUDED.primary_module,
                modules = EXCLUDED.modules, routing = EXCLUDED.routing,
                risk_score = EXCLUDED.risk_score, risk_level = EXCLUDED.risk_level,
                rule_results = EXCLUDED.rule_results, entities = EXCLUDED.entities,
                knn_score = EXCLUDED.knn_score, status = EXCLUDED.status,
                created_at = EXCLUDED.created_at,
                document_snapshot = COALESCE(EXCLUDED.document_snapshot, findings.document_snapshot)
            """,
            (finding["id"], finding["document_id"], finding.get("primary_module"),
             list(finding.get("modules") or []), _jsonb(finding.get("routing")),
             finding.get("risk_score"), _plain(finding.get("risk_level")),
             _jsonb(finding.get("rule_results")), _jsonb(finding.get("entities")),
             finding.get("knn_score"), _plain(finding.get("status")), finding.get("created_at"),
             _jsonb(document_snapshot)),
        )
        if document_snapshot:
            _upsert_document(conn, str(finding["document_id"]), document_snapshot)
        conn.execute(
            "UPDATE cases SET status = 'done', last_error = NULL, updated_at = now()"
            " WHERE case_id = %s",
            (finding["document_id"],),
        )
        if _plain(finding.get("risk_level")) == "high":
            conn.execute("SELECT pg_notify('findings_high', %s)", (str(finding["id"]),))


def _upsert_document(conn: psycopg.Connection, document_id: str, snap: dict) -> None:
    """Migawka AdDocument -> tabela `documents` (czyta ja services/api i dashboard).

    Brakujace pola bierzemy z `cases`; bez zrodla, URL-a i daty pobrania wiersz pomijamy.
    Embedding i simhash pochodza z `cases` (zapisuje je save_vectors przed findingiem).
    """
    conn.execute(
        """
        INSERT INTO documents (id, source, url, fetched_at, publisher, lang, title, text,
                               html_path, screenshots, media, transcript, render_probe,
                               embedding, simhash, scope)
        SELECT k.id, COALESCE(%(source)s, c.source), COALESCE(%(url)s, c.url),
               COALESCE(%(fetched_at)s::timestamptz, c.first_seen_at),
               COALESCE(%(publisher)s, '{}'::jsonb), COALESCE(%(lang)s, c.lang, 'pl'),
               COALESCE(%(title)s, c.title), COALESCE(%(text)s, ''), %(html_path)s,
               COALESCE(%(screenshots)s, '{}'::jsonb), COALESCE(%(media)s, '[]'::jsonb),
               %(transcript)s, %(render_probe)s, c.embedding,
               COALESCE(c.simhash, %(simhash)s), COALESCE(%(scope)s, '{}'::jsonb)
        FROM (SELECT %(id)s::uuid AS id) k
        LEFT JOIN cases c ON c.case_id = k.id
        WHERE COALESCE(%(source)s, c.source) IS NOT NULL
          AND COALESCE(%(url)s, c.url) IS NOT NULL
          AND COALESCE(%(fetched_at)s::timestamptz, c.first_seen_at) IS NOT NULL
        ON CONFLICT (id) DO UPDATE SET
            source = EXCLUDED.source, url = EXCLUDED.url, fetched_at = EXCLUDED.fetched_at,
            publisher = EXCLUDED.publisher, lang = EXCLUDED.lang, title = EXCLUDED.title,
            text = EXCLUDED.text, html_path = EXCLUDED.html_path,
            screenshots = EXCLUDED.screenshots, media = EXCLUDED.media,
            transcript = EXCLUDED.transcript, render_probe = EXCLUDED.render_probe,
            embedding = COALESCE(EXCLUDED.embedding, documents.embedding),
            simhash = EXCLUDED.simhash, scope = EXCLUDED.scope
        """,
        {
            "id": document_id, "source": _plain(snap.get("source")), "url": snap.get("url"),
            "fetched_at": snap.get("fetched_at"), "publisher": _jsonb(snap.get("publisher")),
            "lang": snap.get("lang"), "title": snap.get("title"), "text": snap.get("text"),
            "html_path": snap.get("html_path"), "screenshots": _jsonb(snap.get("screenshots")),
            "media": _jsonb(snap.get("media")), "transcript": _jsonb(snap.get("transcript")),
            "render_probe": _jsonb(snap.get("render_probe")), "simhash": snap.get("simhash"),
            "scope": _jsonb(snap.get("scope")),
        },
    )


def latest_finding(conn: psycopg.Connection, case_id: str) -> dict | None:
    """Ostatni finding przypadku (z document_snapshot) albo None."""
    row = conn.execute(
        "SELECT * FROM findings WHERE document_id = %s ORDER BY created_at DESC LIMIT 1",
        (case_id,),
    ).fetchone()
    if row is None:
        return None
    row["id"], row["document_id"] = str(row["id"]), str(row["document_id"])
    row["created_at"] = row["created_at"].isoformat()
    return row


def save_change_event(conn: psycopg.Connection, event: dict) -> None:
    """Zapisuje ChangeEvent (idempotentnie po id)."""
    conn.execute(
        """
        INSERT INTO change_events (id, document_id, kind, detected_at, previous_finding_id,
                                   current_finding_id, rule_diff, similarity, risk_level_from,
                                   risk_level_to, summary)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING
        """,
        (event["id"], event["document_id"], _plain(event["kind"]), event["detected_at"],
         event.get("previous_finding_id"), event.get("current_finding_id"),
         _jsonb(event.get("rule_diff")), _jsonb(event.get("similarity")),
         _plain(event.get("risk_level_from")), _plain(event.get("risk_level_to")),
         event["summary"]),
    )


def mark_gone(conn: psycopg.Connection, case_id: str) -> None:
    """Oznacza przypadek jako znikniety (gone_at), jesli jeszcze nie oznaczony."""
    conn.execute(
        "UPDATE cases SET gone_at = now() WHERE case_id = %s AND gone_at IS NULL", (case_id,)
    )


def cases_for_recheck(
    conn: psycopg.Connection, limit: int, *, source: str | None = None,
    older_than_minutes: int = 0,
) -> list[dict]:
    """Najdawniej widziane niezniklne przypadki: [{case_id, source, url}]."""
    rows = conn.execute(
        """
        SELECT case_id, source, url FROM cases
        WHERE gone_at IS NULL AND (%s::text IS NULL OR source = %s)
          AND last_seen_at <= now() - make_interval(mins => %s)
        ORDER BY last_seen_at ASC
        LIMIT %s
        """,
        (source, source, older_than_minutes, limit),
    ).fetchall()
    return [{**r, "case_id": str(r["case_id"])} for r in rows]


def load_registry(conn: psycopg.Connection, rows: list[dict]) -> int:
    """Upsert wierszy rejestru KNF do authorized_entities; zwraca liczbe wierszy."""
    with conn.transaction():
        for r in rows:
            conn.execute(
                """
                INSERT INTO authorized_entities (knf_id, name, normalized_name, type, country,
                                                 register, aliases, domains, handles, source_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (knf_id) DO UPDATE SET
                    name = EXCLUDED.name, normalized_name = EXCLUDED.normalized_name,
                    type = EXCLUDED.type, country = EXCLUDED.country,
                    register = EXCLUDED.register, aliases = EXCLUDED.aliases,
                    domains = EXCLUDED.domains, handles = EXCLUDED.handles,
                    source_url = EXCLUDED.source_url, updated_at = now()
                """,
                (r["knf_id"], r["name"], normalize_name(r["name"]), r.get("type"),
                 r.get("country"), r.get("register"), list(r.get("aliases") or []),
                 list(r.get("domains") or []), list(r.get("handles") or []),
                 r.get("source_url")),
            )
    return len(rows)


def registry_entries(conn: psycopg.Connection) -> list[dict]:
    """Caly rejestr KNF (bez updated_at), posortowany po knf_id."""
    return conn.execute(
        "SELECT knf_id, name, normalized_name, type, country, register, aliases, domains,"
        " handles, source_url FROM authorized_entities ORDER BY knf_id"
    ).fetchall()


def report_module1(
    conn: psycopg.Connection, *, source: str | None = None, since: datetime | str | None = None,
    limit: int | None = None,
) -> list[dict]:
    """Wiersze widoku module1_report (od najnowszych wg last_seen_at)."""
    rows = conn.execute(
        """
        SELECT * FROM module1_report
        WHERE (%s::text IS NULL OR source = %s) AND (%s::timestamptz IS NULL OR last_seen_at >= %s)
        ORDER BY last_seen_at DESC, case_id
        LIMIT %s
        """,
        (source, source, since, since, limit),
    ).fetchall()
    return [{**r, "case_id": str(r["case_id"])} for r in rows]

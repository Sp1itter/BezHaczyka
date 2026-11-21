"""Polaczenie i migracje. Konfiguracja wylacznie przez DATABASE_URL (.env)."""

from __future__ import annotations

import os
from importlib import resources

import psycopg
from psycopg.rows import dict_row


def connect(url: str | None = None) -> psycopg.Connection:
    url = url or os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("Brak DATABASE_URL")
    return psycopg.connect(url, row_factory=dict_row)


def migrate(conn: psycopg.Connection) -> list[str]:
    """Stosuje pliki migrations/NNN_*.sql w kolejnosci, kazdy raz."""
    conn.execute(
        "CREATE TABLE IF NOT EXISTS casedb_migrations ("
        "version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
    )
    done = {r["version"] for r in conn.execute("SELECT version FROM casedb_migrations")}
    files = sorted(
        f for f in resources.files("casedb.migrations").iterdir() if f.name.endswith(".sql")
    )
    applied = []
    for f in files:
        if f.name in done:
            continue
        with conn.transaction():
            conn.execute(f.read_text(encoding="utf-8"))
            conn.execute("INSERT INTO casedb_migrations (version) VALUES (%s)", (f.name,))
        applied.append(f.name)
    conn.commit()
    return applied

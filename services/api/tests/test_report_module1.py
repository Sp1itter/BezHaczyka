"""Raport Modulu 1: SQLite -> 503; Postgres (schemat z migracji casedb) -> filtry i CSV."""

from __future__ import annotations

import os
import uuid

import pytest
from fastapi.testclient import TestClient

from api.main import create_app
from api.store import PostgresStore, SqliteStore

PG_URL = os.getenv("TEST_DATABASE_URL")


def test_sqlite_returns_503() -> None:
    c = TestClient(create_app(store=SqliteStore(":memory:")))
    for path in ("/reports/module1", "/reports/module1.csv"):
        r = c.get(path)
        assert r.status_code == 503
        assert "Postgres" in r.json()["detail"]


@pytest.fixture()
def pg():
    if not PG_URL:
        pytest.skip("TEST_DATABASE_URL nieustawione")
    casedb = pytest.importorskip("casedb.db")
    conn = casedb.connect(PG_URL)
    conn.execute("DROP VIEW IF EXISTS module1_report, module1_report_base")
    conn.execute(
        "DROP TABLE IF EXISTS change_events, findings, documents, authorized_entities, knf_entities,"
        " ai_results, case_assets, case_content, cases, casedb_migrations CASCADE"
    )
    conn.commit()
    casedb.migrate(conn)
    conn.commit()
    for i, (src, rel, seen) in enumerate([
        ("facebook", "third_party", "2026-11-20T10:00:00+00"),
        ("youtube", "third_party", "2026-11-10T10:00:00+00"),
        ("www", "official", "2026-11-21T10:00:00+00"),
    ]):
        conn.execute(
            "INSERT INTO cases (case_id, source, source_item_id, url, title, last_seen_at, entity_resolution)"
            " VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)",
            (str(uuid.uuid4()), src, f"i{i}", f"https://x.example.invalid/{i}", f"t{i}", seen,
             f'{{"publisher_relation": "{rel}", "mentions_authorized_firm": true}}'),
        )
    conn.commit()
    store = PostgresStore(PG_URL)
    yield TestClient(create_app(store=store)), conn
    conn.close()


def test_report_filters_and_csv(pg) -> None:
    client, _ = pg
    body = client.get("/reports/module1").json()
    assert body["total"] == 3 and len(body["items"]) == 3
    assert body["items"][0]["last_seen_at"].startswith("2026-11-21")  # ISO, najnowsze pierwsze

    assert client.get("/reports/module1?source=facebook").json()["total"] == 1
    assert client.get("/reports/module1?relation=official").json()["total"] == 1
    assert client.get("/reports/module1?since=2026-11-15T00:00:00Z").json()["total"] == 2
    page = client.get("/reports/module1?limit=1&offset=1").json()
    assert page["total"] == 3 and len(page["items"]) == 1
    assert client.get("/reports/module1?limit=5000").status_code == 422

    r = client.get("/reports/module1.csv?source=facebook")
    assert r.headers["content-type"] == "text/csv; charset=utf-8"
    assert r.headers["content-disposition"].startswith('attachment; filename="modul1-raport-')
    assert r.content.startswith(b"\xef\xbb\xbf")
    lines = r.content.decode("utf-8-sig").strip().splitlines()
    assert lines[0].startswith("case_id,source,url") and len(lines) == 2


def test_csv_empty_has_bom_and_header(pg) -> None:
    client, _ = pg
    r = client.get("/reports/module1.csv?source=nieistniejace")
    assert r.status_code == 200 and r.headers["x-total-count"] == "0"
    assert r.content.startswith(b"\xef\xbb\xbf")
    lines = r.content.decode("utf-8-sig").strip().splitlines()
    assert lines[0].startswith("case_id,source,url") and len(lines) == 1


def test_csv_exports_all_rows_beyond_page(pg) -> None:
    client, conn = pg
    for i in range(205):
        conn.execute(
            "INSERT INTO cases (case_id, source, source_item_id, url, entity_resolution)"
            " VALUES (%s, 'www', %s, %s, %s::jsonb)",
            (str(uuid.uuid4()), f"b{i}", f"https://y.example.invalid/{i}", '{"publisher_relation": "third_party"}'),
        )
    conn.commit()
    r = client.get("/reports/module1.csv?limit=5&offset=3")  # limit/offset ignorowane
    assert r.headers["x-total-count"] == "208"
    assert len(r.content.decode("utf-8-sig").strip().splitlines()) == 1 + 208


def test_flag_filter(pg) -> None:
    client, conn = pg
    # brak kolumny m1_flags -> 400
    assert client.get("/reports/module1?flag=x").status_code == 400
    # widok zastepczy z m1_flags (kolumna na koncu)
    conn.execute("ALTER VIEW module1_report RENAME TO module1_report_base")
    conn.execute(
        "CREATE VIEW module1_report AS SELECT b.*, CASE WHEN b.source = 'facebook'"
        " THEN ARRAY['no_disclosure','a']::text[] ELSE ARRAY[]::text[] END AS m1_flags"
        " FROM module1_report_base b"
    )
    conn.commit()
    assert client.get("/reports/module1?flag=no_disclosure").json()["total"] == 1
    assert client.get("/reports/module1?flag=nope").json()["total"] == 0
    csv_text = client.get("/reports/module1.csv?flag=no_disclosure").content.decode("utf-8-sig")
    assert "no_disclosure;a" in csv_text
    conn.execute("DROP VIEW module1_report, module1_report_base")
    conn.commit()

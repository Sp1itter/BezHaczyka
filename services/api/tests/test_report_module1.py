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
    # stary widok bez m1_flags -> 400
    conn.execute("DROP VIEW IF EXISTS module1_report")
    conn.execute("CREATE VIEW module1_report AS SELECT case_id, source, last_seen_at FROM cases")
    conn.commit()
    assert client.get("/reports/module1?flag=x").status_code == 400
    # przywrocenie prawdziwego widoku (najnowsza migracja) i flag z wyniku resolvera
    conn.execute("DROP VIEW module1_report")
    from pathlib import Path

    import casedb

    conn.execute((Path(casedb.__file__).parent / "migrations" / "013_module1_flags_v3.sql").read_text("utf-8"))
    conn.execute("UPDATE cases SET entity_resolution = entity_resolution || '{\"disclosure_found\": false}'"
                 " WHERE source = 'facebook'")
    conn.commit()
    assert client.get("/reports/module1?flag=podmiot_trzeci_bez_ujawnienia").json()["total"] == 2
    assert client.get("/reports/module1?flag=nope").json()["total"] == 0
    csv_text = client.get("/reports/module1.csv?flag=podmiot_trzeci_bez_ujawnienia").content.decode("utf-8-sig")
    assert "podmiot_trzeci_bez_ujawnienia" in csv_text


def test_csv_formula_injection_neutralised(pg) -> None:
    client, conn = pg
    cid = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO cases (case_id, source, source_item_id, url, author_name, entity_resolution)"
        " VALUES (%s, 'www', 'inj', 'https://z.example.invalid/1', %s, %s::jsonb)",
        (cid, "+48 Finfluencer", '{"publisher_relation": "third_party"}'),
    )
    conn.execute("INSERT INTO case_content (case_id, kind, seq, body) VALUES (%s, 'text', 0, %s)",
                 (cid, '=HYPERLINK("x")'))
    conn.commit()
    import csv as _csv
    import io

    text = client.get("/reports/module1.csv?source=www").content.decode("utf-8-sig")
    rows = list(_csv.DictReader(io.StringIO(text)))
    row = next(r for r in rows if r["case_id"] == cid)
    assert row["tresc"] == "'=HYPERLINK(\"x\")" and row["advertiser_name"] == "'+48 Finfluencer"
    assert not any(v[:1] in "=+-@" for r in rows for v in r.values() if v)

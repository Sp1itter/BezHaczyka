"""Alerty WS z bazy (analyzer pisze prosto do Postgresa) i summary w odpowiedziach."""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from api.contracts import Finding
from api.main import create_app, poll_alerts_once
from api.store import PostgresStore, SqliteStore
from tests.test_api import load

PG_URL = os.getenv("TEST_DATABASE_URL")


def _finding(level: str, doc_id: str, shift_s: float = 1) -> Finding:
    d = load("finding.json")
    d.update(id=str(uuid.uuid4()), document_id=doc_id, risk_level=level,
             created_at=(datetime.now(timezone.utc) + timedelta(seconds=shift_s)).isoformat())
    return Finding.model_validate(d)


@pytest.fixture()
def pg(monkeypatch):
    if not PG_URL:
        pytest.skip("TEST_DATABASE_URL nieustawione")
    casedb = pytest.importorskip("casedb.db")
    monkeypatch.setenv("ALERT_POLL_S", "3600")  # petla tla nie przeszkadza; poll wywolujemy recznie
    conn = casedb.connect(PG_URL)
    conn.execute("DROP VIEW IF EXISTS module1_report, module1_report_base")
    conn.execute(
        "DROP TABLE IF EXISTS change_events, finding_events, findings, documents, authorized_entities,"
        " knf_entities, ai_results, case_assets, case_content, cases, casedb_migrations CASCADE"
    )
    conn.commit()
    casedb.migrate(conn)
    conn.commit()
    conn.close()
    app = create_app(store=PostgresStore(PG_URL))
    with TestClient(app) as client:
        doc = load("ad_document.json")
        assert client.post("/documents", json=doc).status_code == 201
        yield app, client, doc["id"]


def _poll(client: TestClient, app) -> int:
    return client.portal.call(poll_alerts_once, app)


def test_direct_db_high_alerts_once(pg) -> None:
    app, client, doc_id = pg
    with client.websocket_connect("/ws/alerts") as ws:
        assert ws.receive_json()["type"] == "hello"
        f = _finding("high", doc_id)
        app.state.store.upsert_finding(f)  # jak analyzer: prosto do bazy
        assert _poll(client, app) == 1
        msg = ws.receive_json()
        assert msg["type"] == "finding.high" and msg["finding_id"] == f.id
        assert _poll(client, app) == 0


def test_low_does_not_alert(pg) -> None:
    app, client, doc_id = pg
    app.state.store.upsert_finding(_finding("low", doc_id))
    assert _poll(client, app) == 0


def test_post_and_poll_do_not_duplicate(pg) -> None:
    app, client, doc_id = pg
    with client.websocket_connect("/ws/alerts") as ws:
        ws.receive_json()
        f = _finding("high", doc_id)
        r = client.post("/findings", json=f.model_dump(mode="json"))
        assert r.json()["alerted_clients"] == 1
        assert ws.receive_json()["finding_id"] == f.id
        assert _poll(client, app) == 0


def test_summary_in_responses(pg) -> None:
    app, client, doc_id = pg
    f = _finding("high", doc_id)
    app.state.store.upsert_finding(f)
    assert client.get(f"/findings/{f.id}").json()["summary"] is None
    app.state.store._execute(
        "UPDATE findings SET summary = %s, summary_engine = %s WHERE id = %s", ["Powod.", "llm", f.id])
    one = client.get(f"/findings/{f.id}").json()
    assert (one["summary"], one["summary_engine"]) == ("Powod.", "llm")
    item = client.get("/findings").json()["items"][0]
    assert item["summary"] == "Powod." and item["summary_engine"] == "llm"


def test_sqlite_no_loop_and_summary_none() -> None:
    app = create_app(store=SqliteStore(":memory:"))
    with TestClient(app) as client:
        assert client.post("/documents", json=load("ad_document.json")).status_code == 201
        assert client.post("/findings", json=load("finding.json")).status_code == 201
        body = client.get("/findings").json()["items"][0]
        assert body["summary"] is None and body["summary_engine"] is None
        assert client.get(f"/findings/{body['id']}").json()["summary"] is None


def test_out_of_order_insert_still_alerts(pg) -> None:
    app, client, doc_id = pg
    b = _finding("high", doc_id, shift_s=-10)
    a = _finding("high", doc_id, shift_s=-60)  # starszy created_at, wstawiony pozniej
    app.state.store.upsert_finding(b)
    assert _poll(client, app) == 1
    app.state.store.upsert_finding(a)
    assert _poll(client, app) == 1
    assert _poll(client, app) == 0


def test_restart_seed_does_not_realert(pg) -> None:
    app, client, doc_id = pg
    app.state.store.upsert_finding(_finding("high", doc_id, shift_s=-5))
    app2 = create_app(store=PostgresStore(PG_URL))
    with TestClient(app2) as c2:  # lifespan zasiewa dedup
        assert c2.portal.call(poll_alerts_once, app2) == 0


def test_low_updated_to_high_alerts_once(pg) -> None:
    app, client, doc_id = pg
    f = _finding("low", doc_id, shift_s=-5)
    app.state.store.upsert_finding(f)
    assert _poll(client, app) == 0
    app.state.store.upsert_finding(f.model_copy(update={"risk_level": "high"}))
    assert _poll(client, app) == 1
    assert _poll(client, app) == 0


def test_bad_env_falls_back(monkeypatch) -> None:
    monkeypatch.setenv("ALERT_LOOKBACK_S", "abc")
    assert create_app(store=SqliteStore(":memory:")).state.alert_lookback_s == 3600

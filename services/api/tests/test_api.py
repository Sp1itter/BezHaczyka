from __future__ import annotations

import copy
import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.main import create_app
from api.seed import seed
from api.store import PostgresStore, SqliteStore

REPO = Path(__file__).resolve().parents[3]
EXAMPLES = REPO / "fixtures" / "contract-examples"
GOLD = REPO / "fixtures" / "gold" / "labels.json"


def load(name: str) -> dict:
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


PG_URL = os.getenv("TEST_DATABASE_URL")


def _postgres_store():
    # Schemat tworzy infra/init.sql. UWAGA: test czysci tabele documents/findings w tej bazie.
    store = PostgresStore(PG_URL)
    store._execute("TRUNCATE findings, documents, finding_events CASCADE")
    return store


@pytest.fixture(params=["sqlite", "postgres"])
def store(request):
    if request.param == "postgres":
        if not PG_URL:
            pytest.skip("TEST_DATABASE_URL nieustawione - Postgres pominiety")
        return _postgres_store()
    return SqliteStore(":memory:")


@pytest.fixture()
def client(store) -> TestClient:
    return TestClient(create_app(store=store, gold_path=GOLD))


@pytest.fixture()
def seeded(client: TestClient) -> TestClient:
    for name in ("ad_document.json", "facebook_ad_document.json"):
        assert client.post("/documents", json=load(name)).status_code == 201
    assert client.post("/findings", json=load("finding.json")).status_code == 201
    return client


def test_health(client: TestClient) -> None:
    body = client.get("/health").json()
    assert body["status"] == "ok" and body["db"] is True


def test_document_roundtrip_is_lossless(client: TestClient) -> None:
    doc = load("facebook_ad_document.json")
    client.post("/documents", json=doc)
    got = client.get(f"/documents/{doc['id']}").json()
    # analyzer waliduje odpowiedz modelem AdDocument — porownujemy pole po polu
    for key in ("source", "url", "text", "publisher", "render_probe", "scope", "media", "screenshots"):
        assert got[key] == doc[key], key


def test_document_upsert_returns_200_second_time(client: TestClient) -> None:
    doc = load("ad_document.json")
    assert client.post("/documents", json=doc).status_code == 201
    doc["title"] = "zmieniony"
    assert client.post("/documents", json=doc).status_code == 200
    assert client.get(f"/documents/{doc['id']}").json()["title"] == "zmieniony"


def test_embedding_survives_roundtrip(client: TestClient) -> None:
    doc = load("ad_document.json")
    vec = [round(i / 1024, 4) - 0.5 for i in range(1024)]  # bge-m3: 1024 wymiary
    doc["embedding"] = {"model": "bge-m3", "dim": 1024, "vector": vec}
    client.post("/documents", json=doc)
    got = client.get(f"/documents/{doc['id']}").json()["embedding"]["vector"]
    assert got == pytest.approx(vec, abs=1e-6)  # pgvector trzyma float4


def test_non_uuid_ids(client: TestClient) -> None:
    doc = load("ad_document.json")
    doc["id"] = "nie-uuid"
    status = client.post("/documents", json=doc).status_code
    # SQLite przyjmuje dowolny tekst; Postgres (UUID) - czytelne 422, nie 500
    assert status in (201, 422)
    assert client.get("/findings/nie-uuid").status_code == 404
    assert client.patch("/findings/nie-uuid", json={"status": "confirmed"}).status_code == 404


def test_wrong_dim_embedding_does_not_block_document(store) -> None:
    from api.contracts import AdDocument
    doc = AdDocument.model_validate(load("ad_document.json"))  # przyklad ma skrocony wektor (3)
    store.upsert_document(doc)
    assert store.document_exists(doc.id)


def test_missing_document_404(client: TestClient) -> None:
    assert client.get("/documents/nie-ma").status_code == 404


def test_invalid_document_422(client: TestClient) -> None:
    assert client.post("/documents", json={"id": "x"}).status_code == 422


def test_finding_for_unknown_document_409(client: TestClient) -> None:
    assert client.post("/findings", json=load("finding.json")).status_code == 409


def test_finding_keeps_full_rule_results(seeded: TestClient) -> None:
    f = load("finding.json")
    got = seeded.get(f"/findings/{f['id']}").json()
    # panel kalibracji wymaga pelnego rule_results, bez okrajania
    assert got["rule_results"] == f["rule_results"]
    assert got["routing"]["reason"] == f["routing"]["reason"]
    assert got["entities"] == f["entities"]
    assert got["document"]["source"] == "instagram"
    assert 0 < got["coverage"] <= 1


def test_list_filters(seeded: TestClient) -> None:
    assert seeded.get("/findings").json()["total"] == 1
    assert seeded.get("/findings", params={"risk_level": "high"}).json()["total"] == 1
    assert seeded.get("/findings", params={"risk_level": ["low", "medium"]}).json()["total"] == 0
    assert seeded.get("/findings", params={"module": 2}).json()["total"] == 1
    assert seeded.get("/findings", params={"module": 3}).json()["total"] == 0
    assert seeded.get("/findings", params={"source": "facebook"}).json()["total"] == 0
    assert seeded.get("/findings", params={"min_score": 80}).json()["total"] == 0
    assert seeded.get("/findings", params={"q": "CFD"}).json()["total"] == 1


def test_patch_status(seeded: TestClient) -> None:
    fid = load("finding.json")["id"]
    assert seeded.patch(f"/findings/{fid}", json={"status": "confirmed"}).status_code == 200
    assert seeded.get(f"/findings/{fid}").json()["status"] == "confirmed"
    assert seeded.get("/findings", params={"status": "new"}).json()["total"] == 0


def test_patch_rejects_unknown_status(seeded: TestClient) -> None:
    fid = load("finding.json")["id"]
    assert seeded.patch(f"/findings/{fid}", json={"status": "zgubiony"}).status_code == 422
    assert seeded.patch("/findings/nie-ma", json={"status": "confirmed"}).status_code == 404


def test_stats(seeded: TestClient) -> None:
    s = seeded.get("/stats").json()
    assert s["total"] == 1
    assert s["by_risk_level"] == {"high": 1}
    assert s["by_module"] == {"1": 1, "2": 1}
    assert {r["rule_id"] for r in s["failed_rules"]} >= {"4", "18"}


def test_calibration_serves_gold_set(client: TestClient) -> None:
    body = client.get("/calibration").json()
    assert body["available"] is True
    assert len(body["items"]) == 8
    assert {"score", "is_violation"} <= set(body["items"][0])


def test_ws_alert_on_new_high_finding_only_once(client: TestClient) -> None:
    client.post("/documents", json=load("ad_document.json"))
    f = load("finding.json")
    with client.websocket_connect("/ws/alerts") as ws:
        assert ws.receive_json() == {"type": "hello"}
        assert client.post("/findings", json=f).json()["alerted_clients"] == 1
        msg = ws.receive_json()
        assert msg["type"] == "finding.high" and msg["finding_id"] == f["id"]
        assert msg["routing_reason"] == f["routing"]["reason"]
        # odswiezenie tego samego 'high' nie spamuje nadzorcy
        assert client.post("/findings", json=f).json()["alerted_clients"] == 0


def test_ws_alert_on_escalation_to_high(client: TestClient) -> None:
    client.post("/documents", json=load("ad_document.json"))
    low = copy.deepcopy(load("finding.json"))
    low["risk_level"] = "low"
    with client.websocket_connect("/ws/alerts") as ws:
        ws.receive_json()
        assert client.post("/findings", json=low).json()["alerted_clients"] == 0
        assert client.post("/findings", json=load("finding.json")).json()["alerted_clients"] == 1
        assert ws.receive_json()["type"] == "finding.high"


def test_seed_loads_contract_examples(store) -> None:
    docs, findings = seed(store, EXAMPLES)
    assert docs == 2 and findings == 1


# --- praca czlowieka: przypisanie, ocena z etykieta, historia -------------------


def test_assign_and_release(seeded: TestClient) -> None:
    fid = load("finding.json")["id"]
    r = seeded.patch(f"/findings/{fid}", json={"assignee": "analityk.a", "actor": "analityk.a"})
    assert r.status_code == 200
    body = r.json()
    assert (body["assignee"], body["assigned_by"]) == ("analityk.a", "human")
    assert body["assigned_at"]
    released = seeded.patch(f"/findings/{fid}", json={"assignee": None, "actor": "analityk.a"}).json()
    assert released["assignee"] is None and released["assigned_by"] is None


def test_review_sets_verdict_label_and_events(seeded: TestClient) -> None:
    fid = load("finding.json")["id"]
    r = seeded.patch(
        f"/findings/{fid}",
        json={"review": {"label": "true_positive_wrong_entity", "note": "zly podmiot"}, "actor": "analityk.b"},
    )
    assert r.status_code == 200
    f = r.json()
    assert f["status"] == "confirmed"
    assert f["review"]["label"] == "true_positive_wrong_entity"
    assert f["review"]["by"] == "analityk.b" and f["review"]["note"] == "zly podmiot"
    assert f["assignee"] == "analityk.b"  # oceniajacy przejmuje nieprzypisany alert
    fp = seeded.patch(f"/findings/{fid}", json={"review": {"label": "false_positive"}, "actor": "analityk.b"})
    assert fp.json()["status"] == "dismissed"
    events = seeded.get(f"/findings/{fid}/events").json()["items"]
    assert [e["action"] for e in events] == ["review", "review"]
    assert events[0]["actor"] == "analityk.b" and events[0]["detail"]["label"] == "true_positive_wrong_entity"


def test_review_requires_actor_and_known_label(seeded: TestClient) -> None:
    fid = load("finding.json")["id"]
    assert seeded.patch(f"/findings/{fid}", json={"review": {"label": "true_positive"}}).status_code == 422
    bad = {"review": {"label": "cos"}, "actor": "x"}
    assert seeded.patch(f"/findings/{fid}", json=bad).status_code == 422
    assert seeded.patch(f"/findings/{fid}", json={}).status_code == 422


def test_reanalysis_keeps_human_decision(seeded: TestClient) -> None:
    f = load("finding.json")
    seeded.patch(f"/findings/{f['id']}", json={"review": {"label": "false_positive"}, "actor": "a"})
    again = copy.deepcopy(f)
    again["status"] = "new"
    assert seeded.post("/findings", json=again).status_code == 200
    got = seeded.get(f"/findings/{f['id']}").json()
    assert got["status"] == "dismissed" and got["review"]["label"] == "false_positive"


def test_review_labels_endpoint(client: TestClient) -> None:
    items = client.get("/review-labels").json()["items"]
    values = {i["value"]: i["verdict"] for i in items}
    assert values["true_positive"] == "confirmed" and values["false_positive"] == "dismissed"

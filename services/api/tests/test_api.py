from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.main import create_app
from api.seed import seed
from api.store import SqliteStore

REPO = Path(__file__).resolve().parents[3]
EXAMPLES = REPO / "fixtures" / "contract-examples"
GOLD = REPO / "fixtures" / "gold" / "labels.json"


def load(name: str) -> dict:
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app(store=SqliteStore(":memory:"), gold_path=GOLD))


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
    doc["embedding"] = {"model": "bge-m3", "dim": 3, "vector": [0.1, -0.2, 0.3]}
    client.post("/documents", json=doc)
    assert client.get(f"/documents/{doc['id']}").json()["embedding"]["vector"] == [0.1, -0.2, 0.3]


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


def test_seed_loads_contract_examples() -> None:
    store = SqliteStore(":memory:")
    docs, findings = seed(store, EXAMPLES)
    assert docs == 2 and findings == 1

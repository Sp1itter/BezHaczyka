"""Endpointy dla panelu (sprint finalowy, etap C1): filtr dat i oceny, statystyki z filtrami,
trend dzienny, zrzut reklamy z S3. Te same testy na SQLite i Postgresie (fikstury z test_api)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import create_app
from tests.test_api import GOLD, client, load, seeded, store  # noqa: F401 - fikstury pytest

FID = load("finding.json")["id"]  # created_at 2026-11-21T14:03:00Z, high, status new


def test_findings_date_range(seeded: TestClient) -> None:  # noqa: F811
    total = lambda **p: seeded.get("/findings", params=p).json()["total"]
    assert total(**{"from": "2026-11-21T00:00:00Z"}) == 1
    assert total(**{"from": "2026-11-22T00:00:00Z"}) == 0
    assert total(to="2026-11-20T23:59:59Z") == 0
    assert total(**{"from": "2026-11-21T00:00:00Z", "to": "2026-11-21T23:59:59Z"}) == 1


def test_findings_reviewed_filter(seeded: TestClient) -> None:  # noqa: F811
    assert seeded.get("/findings", params={"reviewed": "false"}).json()["total"] == 1
    assert seeded.get("/findings", params={"reviewed": "true"}).json()["total"] == 0
    body = {"review": {"label": "true_positive", "note": None}, "actor": "analityk.a"}
    assert seeded.patch(f"/findings/{FID}", json=body).status_code == 200
    assert seeded.get("/findings", params={"reviewed": "true"}).json()["total"] == 1
    assert seeded.get("/findings", params={"reviewed": "false"}).json()["total"] == 0


def test_stats_respects_filters(seeded: TestClient) -> None:  # noqa: F811
    assert seeded.get("/stats").json()["total"] == 1
    assert seeded.get("/stats", params={"risk_level": "low"}).json()["total"] == 0
    assert seeded.get("/stats", params={"from": "2026-11-22T00:00:00Z"}).json()["total"] == 0
    assert seeded.get("/stats", params={"source": "www"}).json()["total"] == 0


def test_stats_trend_by_day(seeded: TestClient) -> None:  # noqa: F811
    body = seeded.get("/stats/trend", params={"bucket": "day"}).json()
    assert body["bucket"] == "day"
    assert body["items"] == [{"date": "2026-11-21", "high": 1, "medium": 0, "low": 0, "total": 1}]
    assert seeded.get("/stats/trend", params={"risk_level": "low"}).json()["items"] == []
    assert seeded.get("/stats/trend", params={"bucket": "week"}).status_code == 422


def test_document_screenshot_proxied_from_s3(store) -> None:  # noqa: F811
    fetched: list[str] = []

    def blob(uri: str) -> tuple[bytes, str]:
        fetched.append(uri)
        return b"\x89PNG-zrzut", "image/png"

    c = TestClient(create_app(store=store, gold_path=GOLD, blob_reader=blob))
    doc = load("ad_document.json")
    c.post("/documents", json=doc)
    r = c.get(f"/documents/{doc['id']}/screenshot")
    assert r.status_code == 200 and r.content == b"\x89PNG-zrzut"
    assert r.headers["content-type"] == "image/png"
    assert fetched[-1] == doc["screenshots"]["mobile"]  # domyslnie widok mobilny (maly, pionowy)
    c.get(f"/documents/{doc['id']}/screenshot", params={"viewport": "desktop"})
    assert fetched[-1] == doc["screenshots"]["desktop"]
    assert c.get(f"/documents/{doc['id']}/screenshot", params={"viewport": "tablet"}).status_code == 422


def test_document_screenshot_errors(store) -> None:  # noqa: F811
    doc = load("ad_document.json")
    no_s3 = TestClient(create_app(store=store, gold_path=GOLD, blob_reader=None))
    no_s3.post("/documents", json=doc)
    assert no_s3.get(f"/documents/{doc['id']}/screenshot").status_code == 503

    def missing(uri: str) -> tuple[bytes, str]:
        raise FileNotFoundError(uri)

    c = TestClient(create_app(store=store, gold_path=GOLD, blob_reader=missing))
    assert c.get(f"/documents/{doc['id']}/screenshot").status_code == 404
    bare = dict(doc, id="22222222-2222-4222-8222-222222222299", screenshots={})
    c.post("/documents", json=bare)
    assert c.get(f"/documents/{bare['id']}/screenshot").status_code == 404


# --- prog alertow (etap C3): PUT /settings/threshold, alerty WS po stronie serwera -----


def test_threshold_default_put_and_validation(client: TestClient) -> None:  # noqa: F811
    assert client.get("/settings/threshold").json() == {"value": None, "rule": "risk_level=high"}
    r = client.put("/settings/threshold", json={"value": 40, "actor": "analityk.a"})
    assert r.status_code == 200 and r.json()["value"] == 40
    assert client.get("/settings/threshold").json() == {"value": 40, "rule": "risk_score>=40"}
    assert client.put("/settings/threshold", json={"value": 150}).status_code == 422
    assert client.put("/settings/threshold", json={"value": -1}).status_code == 422


def test_ws_alert_respects_saved_threshold(client: TestClient) -> None:  # noqa: F811
    import copy
    import uuid

    client.post("/documents", json=load("ad_document.json"))
    base = load("finding.json")  # high, risk_score 78.5

    def finding(level: str, score: float) -> dict:
        f = copy.deepcopy(base)
        f.update(id=str(uuid.uuid4()), risk_level=level, risk_score=score)
        return f

    client.put("/settings/threshold", json={"value": 90})
    with client.websocket_connect("/ws/alerts") as ws:
        ws.receive_json()
        assert client.post("/findings", json=finding("high", 78.5)).json()["alerted_clients"] == 0  # ponizej progu
        client.put("/settings/threshold", json={"value": 50})
        assert client.post("/findings", json=finding("low", 60.0)).json()["alerted_clients"] == 1  # prog > poziom
        assert ws.receive_json()["type"] == "finding.high"
        same = finding("medium", 70.0)
        assert client.post("/findings", json=same).json()["alerted_clients"] == 1
        ws.receive_json()
        assert client.post("/findings", json=same).json()["alerted_clients"] == 0  # odswiezenie, nie nowy alert


# --- etap C4: raport Modulu 3 i proxy panelu operatora ---------------------------------


def _m3_finding() -> dict:
    import copy

    f = copy.deepcopy(load("finding.json"))
    f["modules"] = [3]
    f["entities"]["investment_firm"]["is_authorized"] = False
    f["rule_results"].append({
        "rule_id": "M3", "rule_name": "Doradztwo bez zezwolenia", "engine": "LLM", "verdict": "fail",
        "confidence": 0.9, "severity": 5, "legal_basis": "art. 69 ust. 2 pkt 5 ustawy o obrocie",
        "evidence": {"kind": "quote", "summary": "Oferuje indywidualne rekomendacje bez zezwolenia KNF.",
                     "measured": None, "quote": "kup teraz, sygnał na jutro", "viewport": None,
                     "screenshot_crop": None, "transcript_ts": None},
    })
    return f


def test_report_module3_from_m3_findings(client: TestClient) -> None:  # noqa: F811
    client.post("/documents", json=load("ad_document.json"))
    client.post("/findings", json=load("finding.json"))  # bez M3 -> nie trafia do raportu
    assert client.get("/reports/module3").json() == {"items": [], "total": 0}
    client.post("/findings", json=_m3_finding())
    body = client.get("/reports/module3").json()
    assert body["total"] == 1
    row = body["items"][0]
    assert row["entity"] == "XYZ Dom Maklerski"
    assert row["registry_status"] == "brak zezwolenia KNF"
    assert row["evidence"] == "Oferuje indywidualne rekomendacje bez zezwolenia KNF."
    csv = client.get("/reports/module3.csv")
    assert csv.status_code == 200 and csv.headers["content-type"].startswith("text/csv")
    assert "XYZ Dom Maklerski" in csv.text


def test_ops_scaling_contract_mock(store, monkeypatch) -> None:  # noqa: F811
    monkeypatch.setenv("AUTOSCALER_URL", "atrapa")
    c = TestClient(create_app(store=store, gold_path=GOLD, blob_reader=None))
    s = c.get("/ops/scaling").json()
    assert s["source"] == "atrapa" and s["queues"][0]["name"] == "q:gpu" and s["ollama_parallel"] == 4
    ok = c.put("/ops/scaling", json={"queues": [{"name": "q:gpu", "max": 3, "cpus": 1.5, "memory_mb": 2048}]})
    assert ok.status_code == 200 and ok.json()["queues"][0]["max"] == 3
    bad = c.put("/ops/scaling", json={"queues": [{"name": "q:gpu", "max": 9, "cpus": 1.5, "memory_mb": 2048}]})
    assert bad.status_code == 422 and "OLLAMA_NUM_PARALLEL" in bad.json()["detail"]


def test_ops_scaling_unreachable_autoscaler(store, monkeypatch) -> None:  # noqa: F811
    monkeypatch.setenv("AUTOSCALER_URL", "http://127.0.0.1:9")
    c = TestClient(create_app(store=store, gold_path=GOLD, blob_reader=None))
    r = c.get("/ops/scaling")
    assert r.status_code == 503 and "Autoskaler" in r.json()["detail"]


def test_ops_scaling_without_config(store, monkeypatch) -> None:  # noqa: F811
    monkeypatch.delenv("AUTOSCALER_URL", raising=False)
    c = TestClient(create_app(store=store, gold_path=GOLD, blob_reader=None))
    r = c.get("/ops/scaling")
    assert r.status_code == 503 and "AUTOSCALER_URL" in r.json()["detail"]

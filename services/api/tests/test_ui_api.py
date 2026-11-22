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

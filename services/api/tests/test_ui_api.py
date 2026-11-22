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


def test_local_blob_reader_for_dev(tmp_path) -> None:
    from api.main import local_blob_reader

    (tmp_path / "shots").mkdir()
    (tmp_path / "shots" / "a-390.png").write_bytes(b"PNG-dev")
    read = local_blob_reader(tmp_path)
    assert read("s3://shots/a-390.png") == (b"PNG-dev", "image/png")
    import pytest

    with pytest.raises(FileNotFoundError):
        read("s3://shots/../../etc/passwd")
    with pytest.raises(FileNotFoundError):
        read("s3://shots/brak.png")


# --- media do panelu weryfikacji: zrzut kreacji, film z magazynu, bezpieczne proxy starych adresow ----------


def test_creative_screenshot_viewport(store) -> None:  # noqa: F811
    seen: list[str] = []
    c = TestClient(create_app(store=store, gold_path=GOLD, blob_reader=lambda u: (seen.append(u), (b"img", "image/png"))[1]))
    doc = load("ad_document.json")
    doc["screenshots"] = {**doc["screenshots"], "creative": "s3://shots/11111111-creative.png"}
    c.post("/documents", json=doc)
    assert c.get(f"/documents/{doc['id']}/screenshot", params={"viewport": "creative"}).status_code == 200
    assert seen[-1] == "s3://shots/11111111-creative.png"


def test_document_media_from_store_and_errors(store) -> None:  # noqa: F811
    c = TestClient(create_app(store=store, gold_path=GOLD, blob_reader=lambda u: (b"mp4-bytes", "application/octet-stream")))
    doc = load("ad_document.json")
    doc["media"] = [{"kind": "video", "path": "s3://media/11111111.mp4", "duration_s": 12.0}]
    c.post("/documents", json=doc)
    r = c.get(f"/documents/{doc['id']}/media/0")
    assert r.status_code == 200 and r.content == b"mp4-bytes" and r.headers["content-type"] == "video/mp4"
    assert c.get(f"/documents/{doc['id']}/media/5").status_code == 404


def test_media_proxy_only_allowlisted_https(store, monkeypatch) -> None:  # noqa: F811
    import api.main as m

    calls: list[str] = []
    monkeypatch.setattr(m, "_fetch_external_media", lambda url: (calls.append(url), (b"jpg", "image/jpeg"))[1])
    # Atrapy adresow tylko w domenie example.invalid; pobieranie zamockowane.
    c = TestClient(create_app(store=store, gold_path=GOLD, blob_reader=None))
    doc = load("ad_document.json")
    doc["media"] = [
        {"kind": "image", "path": "https://example.invalid/obraz.jpg", "duration_s": None},
        {"kind": "image", "path": "http://example.invalid/plain-http.jpg", "duration_s": None},
    ]
    c.post("/documents", json=doc)
    monkeypatch.setenv("MEDIA_PROXY_HOSTS", "nginx")  # host dokumentu spoza listy
    assert c.get(f"/documents/{doc['id']}/media/0").status_code == 403
    monkeypatch.delenv("MEDIA_PROXY_HOSTS")  # domyslnie proxy wylaczone
    assert c.get(f"/documents/{doc['id']}/media/0").status_code == 403
    monkeypatch.setenv("MEDIA_PROXY_HOSTS", "example.invalid")
    ok = c.get(f"/documents/{doc['id']}/media/0")
    assert ok.status_code == 200 and ok.content == b"jpg" and len(calls) == 1
    assert c.get(f"/documents/{doc['id']}/media/1").status_code == 403  # tylko https
    assert len(calls) == 1


# --- kadry YouTube: id z adresu, pobranie raz do magazynu, dopisanie do media ------------------------------


def test_youtube_video_id_forms() -> None:
    from api.main import youtube_video_id

    assert youtube_video_id("https://www.youtube.com/watch?v=uoqQDGYnVI8") == "uoqQDGYnVI8"
    assert youtube_video_id("https://youtu.be/uoqQDGYnVI8?t=3") == "uoqQDGYnVI8"
    assert youtube_video_id("https://www.youtube.com/shorts/uoqQDGYnVI8") == "uoqQDGYnVI8"
    assert youtube_video_id("https://www.youtube.com/@kanal") is None


def test_backfill_frames(store, monkeypatch, tmp_path) -> None:  # noqa: F811
    import api.main as m
    from api.main import local_blob_reader, local_blob_writer

    fetched: list[str] = []

    def fake_fetch(url: str):
        fetched.append(url)
        if "hq" in url:
            raise OSError("brak hq")  # pierwszy szablon zawodzi -> nastepny
        return b"JPEG", "image/jpeg"

    monkeypatch.setattr(m, "_fetch_external_media", fake_fetch)
    c = TestClient(create_app(store=store, gold_path=GOLD, blob_reader=local_blob_reader(tmp_path),
                              blob_writer=local_blob_writer(tmp_path)))
    doc = load("ad_document.json")
    doc.update(source="youtube", url="https://www.youtube.com/watch?v=uoqQDGYnVI8", media=[], screenshots={})
    c.post("/documents", json=doc)

    assert c.post("/documents/frames/backfill").json()["enabled"] is False  # domyslnie wylaczone
    monkeypatch.setenv("YOUTUBE_FRAME_URLS", "https://example.invalid/vi/{id}/hq.jpg,https://example.invalid/vi/{id}/mq.jpg")
    monkeypatch.setenv("MEDIA_PROXY_HOSTS", "example.invalid")
    r = c.post("/documents/frames/backfill").json()
    assert r == {"enabled": True, "checked": 1, "added": 1, "failed": 0}
    assert fetched == ["https://example.invalid/vi/uoqQDGYnVI8/hq.jpg", "https://example.invalid/vi/uoqQDGYnVI8/mq.jpg"]
    media = c.get(f"/documents/{doc['id']}").json()["media"]
    assert media == [{"kind": "image", "path": f"s3://media/{doc['id']}-frame.jpg", "duration_s": None}]
    img = c.get(f"/documents/{doc['id']}/media/0")
    assert img.status_code == 200 and img.content == b"JPEG"
    assert c.post("/documents/frames/backfill").json()["checked"] == 0  # idempotentne


def test_backfill_frames_rejects_host_off_allowlist(store, monkeypatch, tmp_path) -> None:  # noqa: F811
    import api.main as m
    from api.main import local_blob_writer

    monkeypatch.setattr(m, "_fetch_external_media", lambda url: (_ for _ in ()).throw(AssertionError("bez pobierania")))
    monkeypatch.setenv("YOUTUBE_FRAME_URLS", "https://example.invalid/vi/{id}/hq.jpg")
    monkeypatch.setenv("MEDIA_PROXY_HOSTS", "nginx")
    c = TestClient(create_app(store=store, gold_path=GOLD, blob_reader=None, blob_writer=local_blob_writer(tmp_path)))
    assert c.post("/documents/frames/backfill").json()["enabled"] is False

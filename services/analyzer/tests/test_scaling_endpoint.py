"""Testy endpointu /scaling - bez nasluchiwania na porcie."""

import io
import json
from dataclasses import replace

import pytest

from analyzer import health
from analyzer.scaling import DEFAULT_SCALING_CONFIG, QueueState, scaling_payload

CFG = DEFAULT_SCALING_CONFIG


def _get(path: str):
    """Wywolaj _Handler.do_GET na gole obiekt, bez gniazda. Zwraca (status, cialo)."""
    h = health._Handler.__new__(health._Handler)
    h.path = path
    h.wfile = io.BytesIO()
    h.request_version = "HTTP/1.1"
    h.requestline = f"GET {path} HTTP/1.1"
    h.client_address = ("127.0.0.1", 0)
    h.command = "GET"
    h._headers_buffer = []
    h.do_GET()
    raw = b"".join(h._headers_buffer) + h.wfile.getvalue()
    head, _, body = raw.partition(b"\r\n\r\n")
    status = int(head.split(b" ", 2)[1])
    return status, body


@pytest.fixture(autouse=True)
def _przywroc_provider():
    oryginal = health.STATE_PROVIDER
    yield
    health.STATE_PROVIDER = oryginal


def test_payload_ma_decyzje_dla_kazdej_kolejki():
    stany = [QueueState("q:ingest", 12, 1, 0), QueueState("q:render", 0, 1, 0)]
    p = scaling_payload(stany, CFG)
    assert p["executor"] == "compose"
    assert p["hard_max_total"] == 16
    assert [q["name"] for q in p["queues"]] == ["q:ingest", "q:render"]
    ingest = p["queues"][0]
    assert ingest["backlog"] == 12 and ingest["workers"] == 1 and ingest["desired"] == 2
    assert ingest["reason"] and ingest["capped_by"] is None


def test_payload_jest_serializowalny_do_json():
    p = scaling_payload([QueueState("q:gpu", 50, 1, 0.5)], CFG)
    assert json.loads(json.dumps(p))["queues"][0]["desired"] == 2


def test_endpoint_scaling_zwraca_200_i_json():
    health.STATE_PROVIDER = lambda: [QueueState("q:ingest", 12, 1, 0)]
    status, body = _get("/scaling")
    assert status == 200
    assert json.loads(body)["queues"][0]["desired"] == 2


def test_brak_dostepu_do_kolejek_daje_pusta_liste_nie_blad():
    def _pada():
        raise ConnectionError("valkey nie odpowiada")

    health.STATE_PROVIDER = _pada
    status, body = _get("/scaling")
    assert status == 200
    assert json.loads(body)["queues"] == []


def test_domyslny_provider_daje_pusta_liste():
    status, body = _get("/scaling")
    assert status == 200 and json.loads(body)["queues"] == []


def test_nieznana_sciezka_nadal_daje_404():
    assert _get("/cokolwiek")[0] == 404
    assert _get("/scaling/x")[0] == 404
    assert _get("/")[0] == 404


def test_health_dalej_dziala(monkeypatch):
    monkeypatch.setattr(health, "health_payload", lambda *a, **k: {"status": "ok"})
    status, body = _get("/health")
    assert status == 200 and json.loads(body) == {"status": "ok"}


def test_niepoprawna_konfiguracja_nie_wywala_handlera(monkeypatch):
    from analyzer import scaling

    def _zla(*a, **k):
        raise scaling.ScalingConfigError("sprzeczna konfiguracja")

    monkeypatch.setattr(scaling, "load_scaling_config", _zla)
    status, body = _get("/scaling")
    assert status == 500
    assert "sprzeczna" in json.loads(body)["error"]


def test_payload_respektuje_podana_konfiguracje():
    cfg = replace(CFG, hard_max_total=3)
    p = scaling_payload([QueueState("q:ingest", 20, 4, 0), QueueState("q:render", 9, 2, 0)], cfg)
    assert sum(q["desired"] for q in p["queues"]) <= 3

"""Testy warstwy wykonawczej: worker, klient API, /health. Bez RQ i bez Ollamy."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import httpx
import pytest

from analyzer.api_client import ApiClient, ApiError
from analyzer.contracts import Finding
from analyzer.health import health_payload
from analyzer.llm import OllamaClient
from analyzer.worker import handle_job

DOC = {
    "id": "11111111-1111-4111-8111-111111111111",
    "source": "web",
    "url": "https://example.invalid/x",
    "fetched_at": "2026-11-21T14:03:00Z",
    "text": "Zyski do 18% rocznie! Handluj CFD na Bitcoina.",
}


def _api(get_status=200, post_status=200, posted=None, doc=DOC) -> ApiClient:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            assert request.url.path == f"/documents/{DOC['id']}"
            return httpx.Response(get_status, json=doc)
        assert request.url.path == "/findings"
        if posted is not None:
            posted.append(json.loads(request.content))
        return httpx.Response(post_status, json={})

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://fake")
    return ApiClient(base_url="http://api:8000", client=client)


def test_happy_path_end_to_end():
    posted: list = []
    finding = handle_job({"document_id": DOC["id"]}, api=_api(posted=posted))
    assert isinstance(finding, Finding)
    assert len(posted) == 1
    assert posted[0]["document_id"] == DOC["id"]
    assert posted[0]["id"] == finding.id


@pytest.mark.parametrize("payload", [{}, {"document_id": ""}, {"document_id": None}])
def test_payload_without_document_id(payload):
    assert handle_job(payload, api=_api()) is None


def test_without_entity_resolution_goes_to_triage():
    finding = handle_job({"document_id": DOC["id"]}, api=_api())
    assert finding.status == "triage"
    assert finding.routing.rule == "R4"


def test_with_entity_resolution_is_used():
    payload = {
        "document_id": DOC["id"],
        "entity_resolution": {
            "publisher_relation": "third_party",
            "publisher_name": "@finfluencer_pl",
            "firm_name_in_ad": "XYZ Dom Maklerski",
            "registry_knf_id": "DM-123",
            "registry_score": 0.94,
        },
    }
    finding = handle_job(payload, api=_api())
    assert finding.entities.advertiser.name == "@finfluencer_pl"
    assert finding.entities.investment_firm.registry_match.knf_id == "DM-123"


def test_unknown_entity_resolution_keys_ignored():
    payload = {
        "document_id": DOC["id"],
        "entity_resolution": {
            "publisher_name": "x",
            "nieznane_pole": 1,
            "publisher_relation": "dziwna",
        },
    }
    finding = handle_job(payload, api=_api())
    assert finding is not None
    assert finding.entities.advertiser.name == "x"


def test_api_error_on_get_returns_none():
    assert handle_job({"document_id": DOC["id"]}, api=_api(get_status=500)) is None


def test_invalid_document_returns_none():
    assert handle_job({"document_id": DOC["id"]}, api=_api(doc={"zly": 1})) is None


def test_api_error_on_post_returns_none():
    assert handle_job({"document_id": DOC["id"]}, api=_api(post_status=503)) is None


def test_get_document_raises_api_error():
    with pytest.raises(ApiError):
        _api(get_status=404).get_document(DOC["id"])


def test_external_base_url_rejected():
    with pytest.raises(ApiError):
        ApiClient(base_url="https://api.example.com")  # compliance:allow - probka naruszenia
    ApiClient(base_url="http://localhost:8000")
    ApiClient(base_url="http://api:8000")


def _llm(up: bool) -> OllamaClient:
    def handler(request: httpx.Request) -> httpx.Response:
        if not up:
            raise httpx.ConnectError("brak", request=request)
        return httpx.Response(200, json={"models": [{"name": "bge-m3"}]})

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://fake")
    return OllamaClient(client=client)


def test_health_ollama_up(monkeypatch):
    monkeypatch.setenv("PROFILE", "gpu8")
    assert health_payload(_llm(True)) == {
        "status": "ok",
        "ollama": True,
        "models": ["bge-m3"],
        "profile": "gpu8",
    }


def test_health_ollama_down_is_degraded_not_fatal():
    p = health_payload(_llm(False))
    assert p["status"] == "degraded"
    assert p["ollama"] is False and p["models"] == []


def test_worker_imports_without_rq():
    """Modul worker.py musi importowac sie bez rq i redis (importy leniwe).

    `cwd` podajemy JAWNIE: bez tego podproces dziedziczyl katalog roboczy
    wolajacego i test przechodzil tylko wtedy, gdy pytest odpalono z
    services/analyzer. Z katalogu glownego repo padal na ModuleNotFoundError,
    co uderzyloby w kazdego, kto uruchamia testy inaczej niz my (osoba C, CI).
    """
    code = (
        "import sys; sys.modules['rq']=None; sys.modules['redis']=None;"
        "import analyzer.worker"
    )
    analyzer_root = Path(__file__).resolve().parents[1]
    subprocess.run([sys.executable, "-c", code], check=True, cwd=analyzer_root)


# --- ksztalty payloadu: document / flat, fallback FINDINGS_OUT_DIR ---------- #


def _api_no_get(posted=None, post_status=200) -> ApiClient:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST", "get_document nie powinien byc wolany"
        if posted is not None:
            posted.append(json.loads(request.content))
        return httpx.Response(post_status, json={})

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://fake")
    return ApiClient(base_url="http://api:8000", client=client)


@pytest.mark.parametrize("payload", [{"document": DOC}, dict(DOC)])
def test_payload_z_pelnym_dokumentem_bez_wolania_api(payload):
    posted: list = []
    finding = handle_job(payload, api=_api_no_get(posted))
    assert isinstance(finding, Finding)
    assert posted[0]["document_id"] == DOC["id"]


def test_flat_payload_z_det_results():
    payload = {**DOC, "det_results": []}
    finding = handle_job(payload, api=_api_no_get())
    assert finding is not None
    assert [r.rule_id for r in finding.rule_results] == ["4", "5", "6", "7", "8"]


@pytest.mark.parametrize("payload", [{"document": {"id": "x"}}, {"id": "x", "url": "u"}])
def test_niepoprawny_dokument_w_payloadzie_daje_none(payload):
    assert handle_job(payload, api=_api_no_get()) is None


def test_findings_out_dir_zapisuje_json_nawet_gdy_api_pada(tmp_path, monkeypatch):
    monkeypatch.setenv("FINDINGS_OUT_DIR", str(tmp_path))
    assert handle_job(dict(DOC), api=_api_no_get(post_status=500)) is None
    saved = json.loads((tmp_path / f"{DOC['id']}.json").read_text(encoding="utf-8"))
    assert saved["document_id"] == DOC["id"]

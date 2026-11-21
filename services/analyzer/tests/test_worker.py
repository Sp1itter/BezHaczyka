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
from analyzer.pipeline import EntityResolution
from analyzer.worker import analyze_document, handle_job, make_store

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


def _api_no_get(posted=None, post_status=200, doc_status=201, calls=None) -> ApiClient:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST", "get_document nie powinien byc wolany"
        if calls is not None:
            calls.append(request.url.path)
        if request.url.path == "/documents":
            return httpx.Response(doc_status, json={})
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


def test_flat_zapisuje_dokument_przed_findingiem():
    calls: list = []
    assert handle_job(dict(DOC), api=_api_no_get(calls=calls)) is not None
    assert calls == ["/documents", "/findings"]


def test_document_id_nie_wola_post_document():
    paths: list = []

    def handler(request: httpx.Request) -> httpx.Response:
        paths.append((request.method, request.url.path))
        if request.method == "GET":
            return httpx.Response(200, json=DOC)
        return httpx.Response(201, json={})

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://fake")
    api = ApiClient(base_url="http://api:8000", client=client)
    assert handle_job({"document_id": DOC["id"]}, api=api) is not None
    assert ("POST", "/documents") not in paths


def test_blad_post_document_daje_none_bez_findingu():
    calls: list = []
    assert handle_job(dict(DOC), api=_api_no_get(doc_status=500, calls=calls)) is None
    assert calls == ["/documents"]


@pytest.mark.parametrize("status", [200, 201])
def test_post_document_sukces(status):
    from analyzer.contracts import AdDocument

    api = _api_no_get(doc_status=status)
    api.post_document(AdDocument.model_validate(DOC))


def test_post_document_500_to_api_error():
    from analyzer.contracts import AdDocument

    with pytest.raises(ApiError):
        _api_no_get(doc_status=500).post_document(AdDocument.model_validate(DOC))


def test_findings_out_dir_zapisuje_json_nawet_gdy_api_pada(tmp_path, monkeypatch):
    monkeypatch.setenv("FINDINGS_OUT_DIR", str(tmp_path))
    assert handle_job(dict(DOC), api=_api_no_get(post_status=500)) is None
    saved = json.loads((tmp_path / f"{DOC['id']}.json").read_text(encoding="utf-8"))
    assert saved["document_id"] == DOC["id"]
# --- magazyn db, kontrakt zadania, change detection, status error ----------- #


class FakeStore:
    """Atrapa DbStore: rejestruje wywolania."""

    def __init__(self, prev=None, fail_get=False):
        from analyzer.contracts import AdDocument

        self.doc = AdDocument.model_validate(DOC)
        self.prev = prev
        self.fail_get = fail_get
        self.calls: list = []

    def get_document(self, document_id):
        self.calls.append(("get_document", document_id))
        if self.fail_get:
            raise ApiError("x")
        return self.doc

    def previous(self, document_id):
        self.calls.append(("previous", document_id))
        return self.prev

    def save_vectors(self, doc):
        self.calls.append(("save_vectors", doc.id))

    def post_finding(self, finding, document=None):
        self.calls.append(("post_finding", finding.id, document is not None))

    def save_change_event(self, event):
        self.calls.append(("save_change_event", event.kind.value))

    def set_status(self, document_id, status, error=None):
        self.calls.append(("set_status", document_id, status, error))


def test_new_payload_contract_with_store():
    store = FakeStore()
    payload = {
        "document_id": DOC["id"],
        "enqueued_at": "2026-11-21T14:03:00Z",
        "entity_resolution": {"publisher_name": "x"},
        "det_results": [],
    }
    assert handle_job(payload, api=store) is not None
    names = [c[0] for c in store.calls]
    assert names == ["get_document", "previous", "save_vectors", "post_finding"]
    assert store.calls[-1][2] is True  # document_snapshot przekazany


def test_legacy_flat_payload_with_store_uses_payload_document():
    # Plaski AdDocument (stary format scrapera) jest analizowany wprost z payloadu,
    # bez pobierania z magazynu; zapis i tak idzie do magazynu (db).
    store = FakeStore()
    finding = handle_job(dict(DOC), api=store)
    assert finding is not None and finding.document_id == DOC["id"]
    names = [c[0] for c in store.calls]
    assert "get_document" not in names
    assert names[-1] == "post_finding"


def test_change_event_saved_when_previous_exists():
    from analyzer.pipeline import analyze

    first = FakeStore()
    prev_doc = first.doc.model_copy(update={"text": "Zyski gwarantowane! Brak ryzyka."})
    prev_finding = analyze(prev_doc)
    # poprzednio ryzyko wyzsze/nizsze - wymuszamy roznice poziomu ryzyka
    prev_finding = prev_finding.model_copy(update={"risk_level": "low"})
    store = FakeStore(prev=(prev_finding, prev_doc))
    finding = handle_job({"document_id": DOC["id"]}, api=store)
    assert finding is not None
    # kolejnosc: previous przed post_finding
    names = [c[0] for c in store.calls]
    assert names.index("previous") < names.index("post_finding")
    from analyzer.change_detect import detect_change

    expected = detect_change(prev_finding, finding, previous_doc=prev_doc, current_doc=store.doc)
    assert ("save_change_event" in names) == (expected is not None)


def test_change_event_saved_with_forced_event(monkeypatch):
    import analyzer.worker as w
    from analyzer.contracts import ChangeEvent

    ev = ChangeEvent(
        id="e1", document_id=DOC["id"], kind="TRESC_ZMIENIONA",
        detected_at="2026-11-21T14:03:00Z", previous_finding_id="p", summary="s",
    )
    monkeypatch.setattr(w, "detect_change", lambda *a, **k: ev)
    store = FakeStore()
    finding = w.analyze(store.doc)
    store.prev = (finding, store.doc)
    handle_job({"document_id": DOC["id"]}, api=store)
    assert ("save_change_event", "TRESC_ZMIENIONA") in store.calls


def test_change_detect_failure_does_not_fail_job(monkeypatch):
    import analyzer.worker as w

    def boom(*a, **k):
        raise RuntimeError("x")

    monkeypatch.setattr(w, "detect_change", boom)
    store = FakeStore()
    store.prev = (w.analyze(store.doc), store.doc)
    assert handle_job({"document_id": DOC["id"]}, api=store) is not None


def test_analysis_exception_sets_error_status_and_reraises(monkeypatch):
    import analyzer.worker as w

    def boom(*a, **k):
        raise ValueError("kaput")

    monkeypatch.setattr(w, "analyze", boom)
    store = FakeStore()
    with pytest.raises(ValueError):
        handle_job({"document_id": DOC["id"]}, api=store)
    assert ("set_status", DOC["id"], "error", "kaput") in store.calls


def test_store_selection_from_env(monkeypatch):
    from analyzer.db_store import DbStore

    monkeypatch.delenv("ANALYZER_STORE", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert isinstance(make_store(), ApiClient)
    monkeypatch.setenv("DATABASE_URL", "postgresql://x")
    assert isinstance(make_store(), DbStore)
    monkeypatch.setenv("ANALYZER_STORE", "api")
    assert isinstance(make_store(), ApiClient)
    monkeypatch.setenv("ANALYZER_STORE", "db")
    assert isinstance(make_store(), DbStore)
    monkeypatch.setenv("ANALYZER_STORE", "zly")
    with pytest.raises(ValueError):
        make_store()


def test_analyze_document_closes_store(monkeypatch):
    import analyzer.worker as w

    closed = []
    store = FakeStore()
    store.close = lambda: closed.append(1)
    monkeypatch.setattr(w, "make_store", lambda: store)
    assert analyze_document({"document_id": DOC["id"]}) is True
    assert closed == [1]


def test_firm_authorized_regression():
    # publisher autoryzowany NIE znaczy, ze firma jest autoryzowana
    e = EntityResolution(publisher_is_authorized=True).to_entities()
    assert e.investment_firm.is_authorized is False
    assert EntityResolution(firm_is_authorized=True).to_entities().investment_firm.is_authorized
    # wpis w rejestrze KNF = zezwolenie
    assert EntityResolution(registry_knf_id="DM-1").to_entities().investment_firm.is_authorized

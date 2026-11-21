"""Testy DbStore na atrapie modulu casedb (bez Postgresa i bez psycopg)."""

from __future__ import annotations

import subprocess
import sys
import types
from pathlib import Path

import pytest

from analyzer.api_client import ApiError
from analyzer.contracts import AdDocument
from analyzer.db_store import DbStore, StoreError
from analyzer.pipeline import analyze

DOC = {
    "id": "11111111-1111-4111-8111-111111111111",
    "source": "web",
    "url": "https://example.invalid/x",
    "fetched_at": "2026-11-21T14:03:00Z",
    "text": "Zyski do 18% rocznie! Handluj CFD na Bitcoina.",
}


class FakeConn:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0
        self.closed = False

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed = True


@pytest.fixture
def fake_casedb(monkeypatch):
    """Wstrzykuje atrape casedb.db/store; zwraca slownik rejestrujacy wywolania."""
    calls: dict = {"log": [], "conn": FakeConn(), "fail": None, "latest": None, "doc": dict(DOC)}

    def rec(name):
        def fn(conn, *a, **kw):
            calls["log"].append((name, a, kw))
            if calls["fail"] == name:
                raise RuntimeError("boom")
            return None

        return fn

    store = types.ModuleType("casedb.store")
    for n in ("save_vectors", "save_finding", "save_change_event", "set_status"):
        setattr(store, n, rec(n))
    store.get_document = lambda conn, cid: (
        calls["log"].append(("get_document", (cid,), {})) or calls["doc"]
    )
    store.latest_finding = lambda conn, cid: calls["latest"]
    db = types.ModuleType("casedb.db")
    db.connect = lambda url=None: calls["conn"]
    pkg = types.ModuleType("casedb")
    pkg.db, pkg.store = db, store
    monkeypatch.setitem(sys.modules, "casedb", pkg)
    monkeypatch.setitem(sys.modules, "casedb.db", db)
    monkeypatch.setitem(sys.modules, "casedb.store", store)
    return calls


def test_imports_without_casedb():
    code = "import sys; sys.modules['casedb']=None; import analyzer.db_store"
    root = Path(__file__).resolve().parents[1]
    subprocess.run([sys.executable, "-c", code], check=True, cwd=root)


def test_missing_casedb_gives_store_error(monkeypatch):
    monkeypatch.setitem(sys.modules, "casedb", None)
    with pytest.raises(ApiError):
        DbStore().get_document("x")


def test_store_error_is_api_error():
    assert issubclass(StoreError, ApiError)


def test_get_document_and_commit(fake_casedb):
    doc = DbStore(url="postgresql://x").get_document(DOC["id"])
    assert isinstance(doc, AdDocument) and doc.id == DOC["id"]
    assert fake_casedb["conn"].commits == 1


def test_get_document_list_embedding_normalized(fake_casedb):
    fake_casedb["doc"] = {**DOC, "embedding": [0.1, 0.2], "simhash": "ff"}
    doc = DbStore().get_document(DOC["id"])
    assert doc.embedding.vector == [0.1, 0.2] and doc.simhash == "ff"


def test_get_document_missing(fake_casedb):
    fake_casedb["doc"] = None
    with pytest.raises(StoreError):
        DbStore().get_document(DOC["id"])


def test_get_document_invalid(fake_casedb):
    fake_casedb["doc"] = {"zly": 1}
    with pytest.raises(StoreError):
        DbStore().get_document(DOC["id"])


def test_post_finding_passes_snapshot(fake_casedb):
    doc = AdDocument.model_validate(DOC)
    finding = analyze(doc)
    DbStore().post_finding(finding, doc)
    name, args, _ = fake_casedb["log"][-1]
    assert name == "save_finding"
    assert args[0]["id"] == finding.id and args[1]["id"] == DOC["id"]


def test_error_wrapped_with_rollback(fake_casedb):
    fake_casedb["fail"] = "save_finding"
    doc = AdDocument.model_validate(DOC)
    with pytest.raises(StoreError):
        DbStore().post_finding(analyze(doc), doc)
    assert fake_casedb["conn"].rollbacks == 1


def test_previous_none_and_present(fake_casedb):
    store = DbStore()
    assert store.previous(DOC["id"]) is None
    doc = AdDocument.model_validate(DOC)
    f = analyze(doc).model_dump(mode="json")
    fake_casedb["latest"] = {**f, "document_snapshot": DOC}
    prev = store.previous(DOC["id"])
    assert prev is not None and prev[0].id == f["id"] and prev[1].id == DOC["id"]
    fake_casedb["latest"] = {**f, "document_snapshot": None}
    assert store.previous(DOC["id"]) is None


def test_save_vectors_and_status(fake_casedb):
    doc = AdDocument.model_validate(
        {**DOC, "embedding": {"vector": [1.0, 2.0]}, "simhash": "ab"}
    )
    store = DbStore()
    store.save_vectors(doc)
    store.set_status(DOC["id"], "error", "x")
    log = fake_casedb["log"]
    assert log[0] == ("save_vectors", (DOC["id"], [1.0, 2.0], "ab"), {})
    assert log[1] == ("set_status", (DOC["id"], "error", "x"), {})


def test_close(fake_casedb):
    store = DbStore()
    store.get_document(DOC["id"])
    store.close()
    assert fake_casedb["conn"].closed

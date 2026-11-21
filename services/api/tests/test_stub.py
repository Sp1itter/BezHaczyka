"""Stub API na GATE 1: kontrakt zgodny z worker analyzera i jobs.py scrapera."""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

REPO = Path(__file__).resolve().parents[3]
GOLDEN = REPO / "fixtures" / "contract-examples" / "facebook_ad_document.json"
FINDING = REPO / "fixtures" / "contract-examples" / "finding.json"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("API_DATA_DIR", str(tmp_path))
    import main

    importlib.reload(main)
    return TestClient(main.app)


def test_document_roundtrip(client):
    doc = json.loads(GOLDEN.read_text(encoding="utf-8"))
    r = client.post("/documents", json=doc)
    assert r.status_code == 201 and r.json() == {"id": doc["id"]}
    got = client.get(f"/documents/{doc['id']}")
    assert got.status_code == 200 and got.json() == doc


def test_missing_document_is_404(client):
    assert client.get("/documents/nie-ma").status_code == 404


def test_document_without_required_fields_is_422(client):
    assert client.post("/documents", json={"id": "x"}).status_code == 422
    assert client.post("/documents", json={"source": "facebook", "url": "u"}).status_code == 422


def test_path_traversal_id_rejected(client):
    assert client.get("/documents/..%2F..%2Fsecret").status_code in (404, 422)
    assert client.post("/documents", json={"id": "../x", "source": "s", "url": "u"}).status_code == 422


def test_finding_saved_and_listed(client):
    finding = json.loads(FINDING.read_text(encoding="utf-8"))
    assert client.post("/findings", json=finding).status_code == 201
    listed = client.get("/findings").json()
    assert [f["id"] for f in listed] == [finding["id"]]
    assert client.get("/health").json()["findings"] == 1


def test_finding_requires_document_id(client):
    assert client.post("/findings", json={"id": "f1"}).status_code == 422

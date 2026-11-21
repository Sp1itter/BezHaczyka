"""Stub API InvestWatch na GATE 1 (docs/INTEGRACJA.md).

Cel: scraper ma gdzie zapisac dokument, a worker analyzera skad go pobrac
i dokad wyslac Finding. Pelne API (Postgres, filtry, status, WebSocket)
zastapi ten plik po GATE 1b.

Endpointy:
    POST /documents         zapis AdDocument  -> 201 {"id": ...}
    GET  /documents/{id}    odczyt AdDocument -> 200 / 404
    POST /findings          zapis Finding     -> 201 {"id": ...}
    GET  /findings          lista Findingow (podglad na GATE)
    GET  /health            stan stubu

Dane: pliki JSON w API_DATA_DIR (domyslnie services/api/data/), zeby restart
stubu nie gubil wynikow przebiegu.

Start (PowerShell, z services\\api):
    .venv\\Scripts\\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import json
import os
import re
import threading
from pathlib import Path
from typing import Annotated, Any

from fastapi import Body, FastAPI, HTTPException, status

DATA_DIR = Path(os.getenv("API_DATA_DIR", Path(__file__).resolve().parent / "data"))
_ID_RE = re.compile(r"^[A-Za-z0-9_.:\-]{1,128}$")
_lock = threading.Lock()
UNPROCESSABLE = 422  # stala liczbowa: nazwa w Starlette zmienila sie miedzy wersjami
JsonBody = Annotated[dict, Body()]

app = FastAPI(title="InvestWatch API (stub GATE 1)", version="0.1.0")


def _dir(kind: str) -> Path:
    path = DATA_DIR / kind
    path.mkdir(parents=True, exist_ok=True)
    return path


def _check_id(value: Any, field: str = "id") -> str:
    if not isinstance(value, str) or not _ID_RE.match(value):
        raise HTTPException(UNPROCESSABLE, f"pole '{field}' musi byc niepustym id")
    return value


def _save(kind: str, item_id: str, data: dict) -> None:
    target = _dir(kind) / f"{item_id}.json"
    tmp = target.with_suffix(".json.tmp")
    with _lock:
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(target)


def _load(kind: str, item_id: str) -> dict | None:
    path = _dir(kind) / f"{item_id}.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "mode": "stub",
        "documents": len(list(_dir("documents").glob("*.json"))),
        "findings": len(list(_dir("findings").glob("*.json"))),
    }


@app.post("/documents", status_code=status.HTTP_201_CREATED)
def post_document(doc: JsonBody) -> dict:
    doc_id = _check_id(doc.get("id"))
    for field in ("source", "url"):
        if not isinstance(doc.get(field), str) or not doc[field]:
            raise HTTPException(UNPROCESSABLE, f"brak pola '{field}' (kontrakt AdDocument)")
    _save("documents", doc_id, doc)
    return {"id": doc_id}


@app.get("/documents/{document_id}")
def get_document(document_id: str) -> dict:
    _check_id(document_id, "document_id")
    doc = _load("documents", document_id)
    if doc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"brak dokumentu {document_id}")
    return doc


@app.post("/findings", status_code=status.HTTP_201_CREATED)
def post_finding(finding: JsonBody) -> dict:
    finding_id = _check_id(finding.get("id"))
    _check_id(finding.get("document_id"), "document_id")
    _save("findings", finding_id, finding)
    return {"id": finding_id}


@app.get("/findings")
def list_findings() -> list[dict]:
    items = [json.loads(p.read_text(encoding="utf-8")) for p in _dir("findings").glob("*.json")]
    return sorted(items, key=lambda f: str(f.get("created_at", "")), reverse=True)

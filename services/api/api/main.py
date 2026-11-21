"""Serwis api (osoba C): zapis dokumentow i findingow, odczyt dla dashboardu, alerty.

Kontrakt przeplywu: docs/INTEGRACJA.md.
- scraper (A)  -> POST /documents
- analyzer (B) -> GET /documents/{id}, POST /findings
- web (C)      -> GET /findings, GET /stats, GET /calibration, PATCH /findings/{id}, WS /ws/alerts

API NIE przelicza progow ryzyka — `risk_level` liczy analyzer. `high` to sygnal
do broadcastu WebSocket.

Uruchomienie lokalne (bez Dockera, SQLite):
    uvicorn api.main:app --reload --port 8000
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from collections import Counter
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Query, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from api.contracts import AdDocument, Finding
from api.store import FindingFilter, SqlStore, open_store

log = logging.getLogger("api")

# W repo: <root>/services/api/api/main.py. W kontenerze sciezke podaje GOLD_LABELS_PATH.
_PARENTS = Path(__file__).resolve().parents
DEFAULT_GOLD = (_PARENTS[3] if len(_PARENTS) > 3 else _PARENTS[-1]) / "fixtures" / "gold" / "labels.json"

Status = Literal["new", "in_review", "confirmed", "dismissed", "triage"]


class StatusPatch(BaseModel):
    status: Status


class AlertHub:
    """Rozglasza alerty do podlaczonych dashboardow. Martwe gniazda usuwa po cichu."""

    def __init__(self) -> None:
        self._clients: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._clients.add(ws)

    async def disconnect(self, ws: WebSocket) -> None:
        async with self._lock:
            self._clients.discard(ws)

    async def broadcast(self, message: dict[str, Any]) -> int:
        async with self._lock:
            clients = list(self._clients)
        sent = 0
        for ws in clients:
            try:
                await ws.send_json(message)
                sent += 1
            except Exception:  # noqa: BLE001 - rozlaczony klient nie moze zatrzymac zapisu
                await self.disconnect(ws)
        return sent

    @property
    def size(self) -> int:
        return len(self._clients)


def coverage(rule_results: list[dict[str, Any]]) -> float:
    """Odsetek regul, ktore udalo sie ocenic. `not_applicable` to NIE naruszenie."""
    if not rule_results:
        return 0.0
    judged = sum(1 for r in rule_results if r.get("verdict") != "not_applicable")
    return round(judged / len(rule_results), 3)


def alert_payload(finding: dict[str, Any]) -> dict[str, Any]:
    doc = finding.get("document") or {}
    return {
        "type": "finding.high",
        "finding_id": finding["id"],
        "document_id": finding["document_id"],
        "risk_score": finding["risk_score"],
        "risk_level": finding["risk_level"],
        "primary_module": finding["primary_module"],
        "routing_reason": finding["routing"]["reason"],
        "title": doc.get("title"),
        "source": doc.get("source"),
        "failed_rules": [r["rule_id"] for r in finding["rule_results"] if r["verdict"] == "fail"],
    }


def create_app(store: SqlStore | None = None, gold_path: Path | None = None) -> FastAPI:
    app = FastAPI(title="InvestWatch API", version="0.1.0")
    app.state.store = store or open_store(os.getenv("DATABASE_URL"))
    app.state.hub = AlertHub()
    app.state.gold_path = gold_path or Path(os.getenv("GOLD_LABELS_PATH", str(DEFAULT_GOLD)))

    # Front w trybie dev (vite, :5173) wola API z innego originu. W compose idzie przez nginx.
    origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["*"], allow_headers=["*"])

    def st() -> SqlStore:
        return app.state.store

    @app.get("/health")
    async def health() -> dict[str, Any]:
        db = await run_in_threadpool(st().ping)
        return {"status": "ok" if db else "degraded", "db": db, "dialect": st().dialect,
                "ws_clients": app.state.hub.size}

    # --- dokumenty (scraper -> api, analyzer <- api) -------------------------
    @app.post("/documents", status_code=201)
    async def post_document(doc: AdDocument, response: Response) -> dict[str, Any]:
        created = await run_in_threadpool(st().upsert_document, doc)
        if not created:
            response.status_code = 200
        return {"id": doc.id, "created": created}

    @app.get("/documents/{document_id}")
    async def get_document(document_id: str) -> dict[str, Any]:
        doc = await run_in_threadpool(st().get_document, document_id)
        if doc is None:
            raise HTTPException(404, f"Brak dokumentu {document_id}")
        return doc.model_dump(mode="json")

    # --- findingi (analyzer -> api -> web) -------------------------------------
    @app.post("/findings", status_code=201)
    async def post_finding(finding: Finding, response: Response) -> dict[str, Any]:
        if not await run_in_threadpool(st().document_exists, finding.document_id):
            # FK w schemacie i tak by odrzucil; czytelny blad dla analyzera.
            raise HTTPException(409, f"Finding odwoluje sie do nieznanego dokumentu {finding.document_id}")
        result = await run_in_threadpool(st().upsert_finding, finding)
        if not result.created:
            response.status_code = 200
        # Alert przy nowym 'high' albo przy eskalacji do 'high' — nie przy kazdym odswiezeniu.
        alerted = 0
        if finding.risk_level.value == "high" and result.previous_risk_level != "high":
            stored = await run_in_threadpool(st().get_finding, finding.id)
            alerted = await app.state.hub.broadcast(alert_payload(stored))
        return {"id": finding.id, "created": result.created, "alerted_clients": alerted}

    @app.get("/findings")
    async def list_findings(
        risk_level: list[str] | None = Query(None),
        status: list[str] | None = Query(None),
        module: int | None = None,
        source: str | None = None,
        min_score: float | None = None,
        max_score: float | None = None,
        q: str | None = None,
        limit: int = Query(100, ge=1, le=500),
        offset: int = Query(0, ge=0),
    ) -> dict[str, Any]:
        flt = FindingFilter(risk_level=risk_level, status=status, module=module, source=source,
                            min_score=min_score, max_score=max_score, q=q, limit=limit, offset=offset)
        items, total = await run_in_threadpool(st().list_findings, flt)
        for it in items:
            it["coverage"] = coverage(it["rule_results"])
        return {"items": items, "total": total, "limit": limit, "offset": offset}

    @app.get("/findings/{finding_id}")
    async def get_finding(finding_id: str) -> dict[str, Any]:
        f = await run_in_threadpool(st().get_finding, finding_id)
        if f is None:
            raise HTTPException(404, f"Brak findingu {finding_id}")
        f["coverage"] = coverage(f["rule_results"])
        return f

    @app.patch("/findings/{finding_id}")
    async def patch_finding(finding_id: str, body: StatusPatch) -> dict[str, Any]:
        if not await run_in_threadpool(st().update_status, finding_id, body.status):
            raise HTTPException(404, f"Brak findingu {finding_id}")
        return {"id": finding_id, "status": body.status}

    # --- agregaty dla wykresow --------------------------------------------------
    @app.get("/stats")
    async def stats() -> dict[str, Any]:
        items = await run_in_threadpool(st().all_findings)
        failed = Counter()
        rule_names: dict[str, str] = {}
        for f in items:
            for r in f["rule_results"]:
                if r["verdict"] == "fail":
                    failed[r["rule_id"]] += 1
                    rule_names[r["rule_id"]] = r["rule_name"]
        return {
            "total": len(items),
            "by_risk_level": dict(Counter(f["risk_level"] for f in items)),
            "by_status": dict(Counter(f["status"] for f in items)),
            "by_module": dict(Counter(str(m) for f in items for m in f["modules"])),
            "by_source": dict(Counter((f["document"] or {}).get("source") or "?" for f in items)),
            "failed_rules": [{"rule_id": k, "rule_name": rule_names[k], "count": v}
                             for k, v in failed.most_common()],
        }

    # --- panel kalibracji: zbior zloty, progi liczy front --------------------
    @app.get("/calibration")
    async def calibration() -> dict[str, Any]:
        path: Path = app.state.gold_path
        if not path.exists():
            return {"items": [], "source": str(path.name), "available": False}
        data = json.loads(path.read_text(encoding="utf-8"))
        items = [
            {k: it.get(k) for k in ("id", "score", "is_violation", "coverage", "has_render_probe",
                                    "failed_rules", "note")}
            for it in data.get("items", [])
        ]
        return {"items": items, "source": path.name, "available": True}

    # --- alerty na zywo -----------------------------------------------------------
    @app.websocket("/ws/alerts")
    async def ws_alerts(ws: WebSocket) -> None:
        await app.state.hub.connect(ws)
        try:
            await ws.send_json({"type": "hello"})
            while True:  # klient nic nie musi wysylac; czekamy na rozlaczenie
                await ws.receive_text()
        except WebSocketDisconnect:
            pass
        finally:
            await app.state.hub.disconnect(ws)

    return app


app = create_app()

"""Serwis api (osoba C): zapis dokumentow i findingow, odczyt dla dashboardu, alerty.

Kontrakt przeplywu: docs/INTEGRACJA.md.
- scraper (A)  -> POST /documents
- analyzer (B) -> GET /documents/{id}, POST /findings
- web (C)      -> GET /findings, GET /stats, GET /calibration, PATCH /findings/{id}, WS /ws/alerts
- dashboard    -> jw. + GET /findings/{id}/events, GET /review-labels (ocena i przypisanie przez czlowieka)

API NIE przelicza progow ryzyka — `risk_level` liczy analyzer. `high` to sygnal
do broadcastu WebSocket.

Uruchomienie lokalne (bez Dockera, SQLite):
    uvicorn api.main:app --reload --port 8000
"""

from __future__ import annotations

import asyncio
import csv
import io
import json
import logging
import os
from collections import Counter, OrderedDict
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Query, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from api.contracts import AdDocument, Finding
from api.review import ReviewLabel, labels_payload, verdict_for
from api.store import UNSET, FindingFilter, FlagsUnavailable, InvalidId, ReportUnavailable, SqlStore, open_store

log = logging.getLogger("api")

# W repo: <root>/services/api/api/main.py. W kontenerze sciezke podaje GOLD_LABELS_PATH.
_PARENTS = Path(__file__).resolve().parents
DEFAULT_GOLD = (_PARENTS[3] if len(_PARENTS) > 3 else _PARENTS[-1]) / "fixtures" / "gold" / "labels.json"

ALERT_DEDUP_MAX = 5000  # ile ostatnio wyslanych id pamietamy (dedup POST /findings vs poll)

CSV_MAX_ROWS = 50000  # twardy limit eksportu CSV

Status = Literal["new", "in_review", "confirmed", "dismissed", "triage"]


class ReviewIn(BaseModel):
    label: ReviewLabel
    note: str | None = Field(None, max_length=2000)


class FindingPatch(BaseModel):
    """PATCH /findings/{id}. Stary klient (web) wysyla samo {status}.

    - assignee: przypisanie/przejecie ("Zajmuje sie") przez czlowieka; null zwalnia.
    - review: ocena czlowieka; status wynika z etykiety (confirmed/dismissed).
    - actor: zalogowany analityk; wymagany przy review.
    """

    status: Status | None = None
    assignee: str | None = Field(None, max_length=120)
    actor: str | None = Field(None, max_length=120)
    review: ReviewIn | None = None


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


def _mark_alerted(app: FastAPI, finding_id: str) -> bool:
    """True, gdy id jeszcze nie alarmowal (i zapamietuje go). Bez await - atomowe w petli zdarzen."""
    seen: OrderedDict[str, None] = app.state.alerted
    if finding_id in seen:
        return False
    seen[finding_id] = None
    while len(seen) > ALERT_DEDUP_MAX:
        seen.popitem(last=False)
    return True


def _env_float(name: str, default: float) -> float:
    """Liczba dodatnia z env; zla wartosc = domyslna (start nie moze sie wywrocic)."""
    try:
        v = float(os.getenv(name, default))
        return v if v > 0 else default
    except ValueError:
        return default


async def poll_alerts_once(app: FastAPI, seed: bool = False) -> int:
    """Alerty o `high` z okna ALERT_LOOKBACK_S zapisanych prosto do bazy; zwraca liczbe wyslanych.

    seed=True tylko zapamietuje istniejace id (start API), niczego nie rozglasza.
    """
    rows = await run_in_threadpool(app.state.store.new_high_findings, app.state.alert_lookback_s)
    sent = 0
    for f in rows:
        if _mark_alerted(app, f["id"]) and not seed:
            await app.state.hub.broadcast(alert_payload(f))
            sent += 1
    return sent


async def _alert_loop(app: FastAPI, every: float) -> None:
    while True:
        try:
            await poll_alerts_once(app)
        except Exception:  # noqa: BLE001 - blad bazy nie moze zabic petli
            log.exception("Odpytywanie bazy o alerty nie powiodlo sie")
        await asyncio.sleep(every)


def _csv_cell(v: Any) -> Any:
    """Komorka CSV; tekst zaczynajacy sie od =,+,-,@, tab, CR dostaje prefiks ' (formula injection)."""
    if v is None:
        return ""
    if isinstance(v, list):
        v = ";".join(str(x) for x in v)
    if isinstance(v, str) and v[:1] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + v
    return v


def create_app(store: SqlStore | None = None, gold_path: Path | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(a: FastAPI):
        task = None
        if a.state.store.dialect == "postgresql":  # findingi analyzera ida prosto do Postgresa
            try:
                await poll_alerts_once(a, seed=True)  # restart nie powtarza starych alertow
            except Exception:  # noqa: BLE001
                log.exception("Nie udalo sie wstepnie wczytac findingow high")
            task = asyncio.create_task(_alert_loop(a, _env_float("ALERT_POLL_S", 3)))
        try:
            yield
        finally:
            if task:
                task.cancel()

    app = FastAPI(title="InvestWatch API", version="0.1.0", lifespan=lifespan)
    app.state.store = store or open_store(os.getenv("DATABASE_URL"))
    app.state.hub = AlertHub()
    app.state.alerted = OrderedDict()
    app.state.alert_lookback_s = _env_float("ALERT_LOOKBACK_S", 3600)
    app.state.gold_path = gold_path or Path(os.getenv("GOLD_LABELS_PATH", str(DEFAULT_GOLD)))

    # Front w trybie dev (vite, :5173) wola API z innego originu. W compose idzie przez nginx.
    origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["*"], allow_headers=["*"])

    def st() -> SqlStore:
        return app.state.store

    @app.exception_handler(InvalidId)
    async def invalid_id(_request, exc: InvalidId) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

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
            if _mark_alerted(app, finding.id):
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
    async def patch_finding(finding_id: str, body: FindingPatch) -> dict[str, Any]:
        review = None
        if body.review is not None:
            if not body.actor:
                raise HTTPException(422, "Ocena wymaga osoby (actor) - decyzje podejmuje czlowiek")
            review = {"decision": verdict_for(body.review.label), "label": body.review.label,
                      "note": body.review.note}
        if body.status is None and review is None and "assignee" not in body.model_fields_set:
            raise HTTPException(422, "Podaj status, assignee lub review")
        ok = await run_in_threadpool(
            lambda: st().update_finding(
                finding_id,
                actor=body.actor,
                status=body.status,
                assignee=body.assignee if "assignee" in body.model_fields_set else UNSET,
                review=review,
            )
        )
        if not ok:
            raise HTTPException(404, f"Brak findingu {finding_id}")
        f = await run_in_threadpool(st().get_finding, finding_id)
        f["coverage"] = coverage(f["rule_results"])
        return f

    @app.get("/findings/{finding_id}/events")
    async def finding_events(finding_id: str) -> dict[str, Any]:
        if await run_in_threadpool(st().get_finding, finding_id) is None:
            raise HTTPException(404, f"Brak findingu {finding_id}")
        return {"items": await run_in_threadpool(st().list_events, finding_id)}

    @app.get("/review-labels")
    async def review_labels() -> dict[str, Any]:
        return {"items": labels_payload()}

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

    # --- raport Modulu 1 (JSON + CSV) ---------------------------------------------
    async def _report(source, relation, flag, since, limit, offset):
        try:
            return await run_in_threadpool(
                lambda: st().module1_report(source=source, relation=relation, flag=flag,
                                            since=since, limit=limit, offset=offset))
        except ReportUnavailable as e:
            raise HTTPException(503, str(e))
        except FlagsUnavailable as e:
            raise HTTPException(400, str(e))

    @app.get("/reports/module1")
    async def report_module1(
        source: str | None = None,
        relation: str | None = None,
        flag: str | None = None,
        since: datetime | None = None,
        limit: int = Query(200, ge=1, le=1000),
        offset: int = Query(0, ge=0),
    ) -> dict[str, Any]:
        items, total = await _report(source, relation, flag, since, limit, offset)
        return {"items": items, "total": total}

    @app.get("/reports/module1.csv")
    async def report_module1_csv(
        source: str | None = None,
        relation: str | None = None,
        flag: str | None = None,
        since: datetime | None = None,
    ) -> Response:
        # CSV = wszystkie pasujace wiersze (bez stronicowania), twardy limit bezpieczenstwa.
        items, total = await _report(source, relation, flag, since, CSV_MAX_ROWS, 0)
        try:
            cols = await run_in_threadpool(st().module1_columns)
        except ReportUnavailable as e:
            raise HTTPException(503, str(e))
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(cols)
        for it in items:
            w.writerow([_csv_cell(v) for v in (it.get(c) for c in cols)])
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
        return Response(
            content="﻿" + buf.getvalue(),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="modul1-raport-{stamp}.csv"',
                     "X-Total-Count": str(total)},
        )

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

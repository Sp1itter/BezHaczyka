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

from fastapi import Depends, FastAPI, HTTPException, Query, Response, WebSocket, WebSocketDisconnect
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
    threshold = await run_in_threadpool(app.state.store.alert_threshold)
    rows = await run_in_threadpool(app.state.store.new_high_findings, app.state.alert_lookback_s, threshold)
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


# --------------------------------------------------------------------------- #
# Filtry listy wspolne dla /findings, /stats i /stats/trend
# --------------------------------------------------------------------------- #


def finding_filter(
    risk_level: list[str] | None = Query(None),
    status: list[str] | None = Query(None),
    module: int | None = None,
    source: str | None = None,
    min_score: float | None = None,
    max_score: float | None = None,
    q: str | None = None,
    date_from: str | None = Query(None, alias="from", description="ISO 8601, wlacznie"),
    date_to: str | None = Query(None, alias="to", description="ISO 8601, wlacznie"),
    reviewed: bool | None = None,
) -> FindingFilter:
    return FindingFilter(risk_level=risk_level, status=status, module=module, source=source,
                         min_score=min_score, max_score=max_score, q=q,
                         date_from=date_from, date_to=date_to, reviewed=reviewed)


# --------------------------------------------------------------------------- #
# Zrzuty reklam z SeaweedFS (S3). URI w AdDocument: s3://<bucket>/<klucz>.
# --------------------------------------------------------------------------- #

BlobReader = Any  # Callable[[str], tuple[bytes, str]]; FileNotFoundError gdy brak obiektu
_FROM_ENV = object()


def s3_reader_from_env() -> BlobReader | None:
    """Czytnik zrzutow z S3_ENDPOINT/S3_ACCESS_KEY/S3_SECRET_KEY; bez konfiguracji None (503)."""
    endpoint = os.getenv("S3_ENDPOINT")
    if not endpoint or not os.getenv("S3_ACCESS_KEY") or not os.getenv("S3_SECRET_KEY"):
        return None
    import boto3  # import leniwy: testy i dev bez S3 nie wymagaja boto3
    from botocore.exceptions import ClientError

    client = boto3.client("s3", endpoint_url=endpoint, aws_access_key_id=os.environ["S3_ACCESS_KEY"],
                          aws_secret_access_key=os.environ["S3_SECRET_KEY"],
                          region_name=os.getenv("S3_REGION", "us-east-1"))

    def read(uri: str) -> tuple[bytes, str]:
        bucket, _, key = uri.removeprefix("s3://").partition("/")
        try:
            obj = client.get_object(Bucket=bucket, Key=key)
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in ("NoSuchKey", "NoSuchBucket", "404"):
                raise FileNotFoundError(uri) from exc
            raise
        return obj["Body"].read(), obj.get("ContentType") or "image/png"

    return read


def meets_alert(level: str | None, score: float | None, threshold: float | None) -> bool:
    """Warunek alertu: bez progu `high` z analyzera, z progiem z kalibracji `risk_score >= prog`."""
    if threshold is None:
        return level == "high"
    return score is not None and score >= threshold


class ThresholdIn(BaseModel):
    value: float = Field(ge=0, le=100)
    actor: str | None = None


# --------------------------------------------------------------------------- #
# Modul 3: doradztwo bez zezwolenia (RuleResult M3 z analyzera)
# --------------------------------------------------------------------------- #

M3_COLUMNS = ("created_at", "entity", "registry_status", "source", "publisher", "url", "offer_text",
              "evidence", "quote", "risk_level", "risk_score", "finding_id")


def module3_row(f: dict[str, Any]) -> dict[str, Any] | None:
    """Wiersz raportu M3 z findingu, w ktorym regula M3 ma werdykt fail; inaczej None."""
    m3 = next((r for r in f.get("rule_results") or [] if r.get("rule_id") == "M3" and r.get("verdict") == "fail"), None)
    if m3 is None:
        return None
    firm = (f.get("entities") or {}).get("investment_firm") or {}
    adv = (f.get("entities") or {}).get("advertiser") or {}
    doc = f.get("document") or {}
    pub = doc.get("publisher") or {}
    publisher = pub if isinstance(pub, str) else (pub.get("display_name") or pub.get("handle") or "")
    if firm.get("is_authorized") is True:
        registry = "zezwolenie KNF"
    elif firm.get("is_authorized") is False:
        registry = "brak zezwolenia KNF"
    else:
        registry = "brak w rejestrze KNF"
    ev = m3.get("evidence") or {}
    return {
        "finding_id": f["id"], "created_at": f["created_at"],
        "entity": firm.get("name_in_ad") or adv.get("name") or publisher or None,
        "registry_status": registry, "source": doc.get("source"), "publisher": publisher or None,
        "url": doc.get("url"), "offer_text": doc.get("text_excerpt"),
        "evidence": ev.get("summary"), "quote": ev.get("quote"),
        "risk_level": f.get("risk_level"), "risk_score": f.get("risk_score"),
    }


# --------------------------------------------------------------------------- #
# Panel operatora: proxy do autoskalera osoby B (kontrakt w planie, par. 6)
# --------------------------------------------------------------------------- #

def _contract_mock() -> dict[str, Any]:
    """Atrapa GET /scaling z kontraktu B<->C, do czasu gotowosci autoskalera (AUTOSCALER_URL=atrapa)."""
    return {
        "source": "atrapa", "executor": "compose", "ollama_parallel": 4,
        "queues": [{"name": "q:gpu", "backlog": 12, "running": 2, "min": 1, "max": 4,
                    "cpus": 2.0, "memory_mb": 3072, "scale_up_backlog": 3}],
        "workers": [{"id": "analyzer-1", "queue": "q:gpu", "state": "busy", "job": None, "since": None},
                    {"id": "analyzer-2", "queue": "q:gpu", "state": "idle", "job": None, "since": None}],
        "throughput_per_min": 7.5,
    }


def _autoscaler_call(base: str, method: str, body: dict[str, Any] | None) -> tuple[int, Any]:
    import urllib.error
    import urllib.request

    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{base.rstrip('/')}/scaling", data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:  # noqa: S310 - adres z konfiguracji compose
            return resp.status, json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as exc:
        try:
            return exc.code, json.loads(exc.read() or b"{}")
        except ValueError:
            return exc.code, {"detail": f"Autoskaler: HTTP {exc.code}"}


class ScalingQueueIn(BaseModel):
    name: str
    max: int = Field(ge=0)
    cpus: float = Field(gt=0)
    memory_mb: int = Field(gt=0)


class ScalingIn(BaseModel):
    queues: list[ScalingQueueIn]


def create_app(store: SqlStore | None = None, gold_path: Path | None = None,
               blob_reader: BlobReader | None = _FROM_ENV) -> FastAPI:
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
    app.state.blob_reader = s3_reader_from_env() if blob_reader is _FROM_ENV else blob_reader

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

    @app.get("/documents/{document_id}/screenshot")
    async def document_screenshot(
        document_id: str, viewport: Literal["mobile", "desktop"] = "mobile",
    ) -> Response:
        """Zrzut reklamy z S3 przez API (przegladarka nie widzi SeaweedFS). Domyslnie maly widok mobilny."""
        doc = await run_in_threadpool(st().get_document, document_id)
        if doc is None:
            raise HTTPException(404, f"Brak dokumentu {document_id}")
        uri = (doc.screenshots or {}).get(viewport)
        if not uri or not str(uri).startswith("s3://"):
            raise HTTPException(404, f"Dokument nie ma zrzutu ({viewport})")
        reader = app.state.blob_reader
        if reader is None:
            raise HTTPException(503, "Magazyn zrzutow (S3) nie jest skonfigurowany")
        try:
            data, content_type = await run_in_threadpool(reader, uri)
        except FileNotFoundError:
            raise HTTPException(404, "Zrzut nie istnieje w magazynie") from None
        except Exception:  # noqa: BLE001 - blad magazynu nie moze wywrocic API
            log.exception("Nie udalo sie pobrac zrzutu %s", uri)
            raise HTTPException(502, "Magazyn zrzutow nie odpowiada") from None
        return Response(content=data, media_type=content_type, headers={"Cache-Control": "private, max-age=3600"})

    # --- findingi (analyzer -> api -> web) -------------------------------------
    @app.post("/findings", status_code=201)
    async def post_finding(finding: Finding, response: Response) -> dict[str, Any]:
        if not await run_in_threadpool(st().document_exists, finding.document_id):
            # FK w schemacie i tak by odrzucil; czytelny blad dla analyzera.
            raise HTTPException(409, f"Finding odwoluje sie do nieznanego dokumentu {finding.document_id}")
        result = await run_in_threadpool(st().upsert_finding, finding)
        if not result.created:
            response.status_code = 200
        # Alert przy nowym wyniku spelniajacym warunek albo przy przejsciu przez prog - nie przy odswiezeniu.
        alerted = 0
        threshold = await run_in_threadpool(st().alert_threshold)
        now_meets = meets_alert(finding.risk_level.value, finding.risk_score, threshold)
        before = (not result.created) and meets_alert(result.previous_risk_level, result.previous_risk_score, threshold)
        if now_meets and not before:
            if _mark_alerted(app, finding.id):
                stored = await run_in_threadpool(st().get_finding, finding.id)
                alerted = await app.state.hub.broadcast(alert_payload(stored))
        return {"id": finding.id, "created": result.created, "alerted_clients": alerted}

    @app.get("/findings")
    async def list_findings(
        flt: FindingFilter = Depends(finding_filter),
        limit: int = Query(100, ge=1, le=500),
        offset: int = Query(0, ge=0),
    ) -> dict[str, Any]:
        flt.limit, flt.offset = limit, offset
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
    async def stats(flt: FindingFilter = Depends(finding_filter)) -> dict[str, Any]:
        items = await run_in_threadpool(st().query_findings, flt)
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

    @app.get("/stats/trend")
    async def stats_trend(
        flt: FindingFilter = Depends(finding_filter), bucket: Literal["day"] = "day",
    ) -> dict[str, Any]:
        """Liczba wynikow na dzien (UTC) wg poziomu ryzyka, z tymi samymi filtrami co lista."""
        items = await run_in_threadpool(st().query_findings, flt)
        days: dict[str, dict[str, Any]] = {}
        for f in items:
            day = str(f["created_at"])[:10]
            row = days.setdefault(day, {"date": day, "high": 0, "medium": 0, "low": 0, "total": 0})
            row[f["risk_level"]] = row.get(f["risk_level"], 0) + 1
            row["total"] += 1
        return {"bucket": bucket, "items": [days[d] for d in sorted(days)]}

    @app.get("/settings/threshold")
    async def get_threshold() -> dict[str, Any]:
        value = await run_in_threadpool(st().alert_threshold)
        return {"value": value, "rule": "risk_level=high" if value is None else f"risk_score>={value:g}"}

    @app.put("/settings/threshold")
    async def put_threshold(body: ThresholdIn) -> dict[str, Any]:
        """Prog alertow z panelu kalibracji. Alerty WS (POST i odpytywanie bazy) liczone wg niego."""
        await run_in_threadpool(st().set_setting, "alert_threshold", f"{body.value:g}", body.actor)
        return {"value": body.value, "rule": f"risk_score>={body.value:g}"}

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

    # --- raport Modulu 3 ----------------------------------------------------------
    async def _module3_rows() -> list[dict[str, Any]]:
        items = await run_in_threadpool(st().query_findings, FindingFilter())
        rows = [r for r in (module3_row(f) for f in items) if r]
        return sorted(rows, key=lambda r: str(r["created_at"]), reverse=True)

    @app.get("/reports/module3")
    async def report_module3(limit: int = Query(500, ge=1, le=5000)) -> dict[str, Any]:
        rows = await _module3_rows()
        return {"items": rows[:limit], "total": len(rows)}

    @app.get("/reports/module3.csv")
    async def report_module3_csv() -> Response:
        rows = (await _module3_rows())[:CSV_MAX_ROWS]
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(M3_COLUMNS)
        for r in rows:
            w.writerow([_csv_cell(r.get(c)) for c in M3_COLUMNS])
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
        return Response(content="\ufeff" + buf.getvalue(), media_type="text/csv; charset=utf-8",
                        headers={"Content-Disposition": f'attachment; filename="modul3-raport-{stamp}.csv"',
                                 "X-Total-Count": str(len(rows))})

    # --- panel operatora (proxy do autoskalera) ------------------------------------
    def _autoscaler() -> str:
        return os.getenv("AUTOSCALER_URL", "http://autoscaler:8090")

    @app.get("/ops/scaling")
    async def ops_scaling() -> Any:
        base = _autoscaler()
        if base == "atrapa":
            app.state.ops_mock = getattr(app.state, "ops_mock", None) or _contract_mock()
            return app.state.ops_mock
        try:
            status, body = await run_in_threadpool(_autoscaler_call, base, "GET", None)
        except OSError:
            raise HTTPException(503, f"Autoskaler niedostępny ({base})") from None
        return JSONResponse(body, status_code=status)

    @app.put("/ops/scaling")
    async def ops_scaling_put(body: ScalingIn) -> Any:
        base = _autoscaler()
        if base == "atrapa":
            state = getattr(app.state, "ops_mock", None) or _contract_mock()
            for q in body.queues:
                if q.max > state["ollama_parallel"]:
                    raise HTTPException(422, f"max > OLLAMA_NUM_PARALLEL ({state['ollama_parallel']})")
            for q in body.queues:
                for cur in state["queues"]:
                    if cur["name"] == q.name:
                        cur.update(max=q.max, cpus=q.cpus, memory_mb=q.memory_mb)
            app.state.ops_mock = state
            return state
        try:
            status, resp = await run_in_threadpool(_autoscaler_call, base, "PUT", body.model_dump())
        except OSError:
            raise HTTPException(503, f"Autoskaler niedostępny ({base})") from None
        return JSONResponse(resp, status_code=status)

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

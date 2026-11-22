"""Autoskaler kontenerow analyzer: petla decyzyjna + HTTP /scaling (port 8090).

Uruchomienie: `python -m analyzer.autoscaler`.

Co robi:
  - co AUTOSCALER_INTERVAL_S (domyslnie 5 s) czyta stan `q:gpu` z Valkeya, liczy
    bezczynnosc (klucz `ops:idle:<kolejka>` = chwila ostatniego niepustego stanu),
    wola `scaling.decide()` i wykonuje decyzje executorem (compose / dry-run / pool),
  - wystawia GET/PUT /scaling dla panelu operatora i GET /health,
  - konfiguracja operatora zyje w Valkey (klucz `ops:scaling`, JSON) i nadpisuje
    scaling.yaml oraz zmienne ANALYZER_*.

Skalowany jest TYLKO `q:gpu` (serwis `analyzer`). `q:ingest` i `q:render` pokazujemy
w /scaling tylko do odczytu.
"""

from __future__ import annotations

import json
import logging
import os
import signal
import socket
import threading
import time
from collections.abc import Callable
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Protocol

from analyzer import pool
from analyzer.scaling import (
    GPU_QUEUE,
    QueueState,
    ScalingConfig,
    ScalingConfigError,
    apply_overrides,
    decide,
    env_overrides,
    load_scaling_config,
)

log = logging.getLogger("analyzer.autoscaler")

OVERRIDES_KEY = "ops:scaling"
IDLE_KEY_PREFIX = "ops:idle:"
THROUGHPUT_WINDOW_S = 300
DEFAULT_PORT = 8090


class Backend(Protocol):
    """Dostep do Valkeya/RQ; w testach podmieniany atrapa."""

    def backlog(self, queue: str) -> int: ...
    def running(self, queue: str) -> int: ...
    def workers(self, queue: str) -> list[dict[str, Any]]: ...
    def finished_since(self, queue: str, seconds: int) -> int: ...
    def get(self, key: str) -> str | None: ...
    def set(self, key: str, value: str) -> None: ...


def _iso(ts: datetime | None) -> str:
    if ts is None:
        return datetime.now(timezone.utc).isoformat()
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.isoformat()


class ValkeyBackend:
    """Prawdziwy odczyt z Valkeya przez RQ."""

    def __init__(self, url: str) -> None:
        from redis import Redis

        self.conn = Redis.from_url(url, decode_responses=False)

    def _queue(self, name: str):
        from rq import Queue

        return Queue(name, connection=self.conn)

    def backlog(self, queue: str) -> int:
        return int(self._queue(queue).count)

    def running(self, queue: str) -> int:
        return int(self._queue(queue).started_job_registry.count)

    def workers(self, queue: str) -> list[dict[str, Any]]:
        from rq import Worker

        out: list[dict[str, Any]] = []
        for w in Worker.all(connection=self.conn):
            if queue not in w.queue_names():
                continue
            busy = w.get_state() == "busy"
            job_id = w.get_current_job_id() if busy else None
            since = w.last_heartbeat or w.birth_date
            if busy and job_id:
                try:
                    job = self._queue(queue).fetch_job(job_id)
                    if job is not None and job.started_at:
                        since = job.started_at
                except Exception:  # noqa: BLE001
                    pass
            host = w.hostname.decode() if isinstance(w.hostname, bytes) else (w.hostname or w.name)
            out.append(
                {
                    "id": host or w.name,
                    "queue": queue,
                    "state": "busy" if busy else "idle",
                    "job": job_id,
                    "since": _iso(since),
                }
            )
        return sorted(out, key=lambda x: x["id"])

    def finished_since(self, queue: str, seconds: int) -> int:
        from rq.job import Job

        ids = self._queue(queue).finished_job_registry.get_job_ids(0, 500)
        if not ids:
            return 0
        cutoff = datetime.now(timezone.utc).timestamp() - seconds
        n = 0
        for job in Job.fetch_many(ids, connection=self.conn):
            ended = getattr(job, "ended_at", None) if job else None
            if ended is not None:
                if ended.tzinfo is None:
                    ended = ended.replace(tzinfo=timezone.utc)
                if ended.timestamp() >= cutoff:
                    n += 1
        return n

    def get(self, key: str) -> str | None:
        raw = self.conn.get(key)
        return raw.decode() if isinstance(raw, bytes) else raw

    def set(self, key: str, value: str) -> None:
        self.conn.set(key, value)


class Autoscaler:
    """Stan i logika autoskalera, niezalezne od HTTP i od Dockera (testowalne)."""

    def __init__(
        self,
        backend: Backend,
        executor: Any,
        base_config: ScalingConfig,
        env_over: dict[str, dict[str, Any]] | None = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.backend = backend
        self.executor = executor
        self.base_config = base_config
        self.env_over = env_over or {}
        self.clock = clock
        self._lock = threading.RLock()

    # --- konfiguracja ---------------------------------------------------
    def _stored_overrides(self) -> dict[str, dict[str, Any]]:
        raw = self.backend.get(OVERRIDES_KEY)
        if not raw:
            return {}
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ScalingConfigError("Klucz ops:scaling nie zawiera slownika.")
        return data

    def effective_config(self) -> ScalingConfig:
        """yaml + ANALYZER_* + ops:scaling. Uszkodzone ops:scaling => ostrzezenie i pomijamy."""
        cfg = self.base_config
        if self.env_over:
            cfg = apply_overrides(cfg, self.env_over)
        try:
            return apply_overrides(cfg, self._stored_overrides())
        except (ScalingConfigError, ValueError) as exc:
            log.warning("Pomijam nadpisania operatora z %s: %s", OVERRIDES_KEY, exc)
            return cfg

    def update(self, body: Any) -> ScalingConfig:
        """PUT /scaling: zlacz zmiany z zapisanymi, zwaliduj calosc, zapisz. ScalingConfigError => 422."""
        if not isinstance(body, dict) or not isinstance(body.get("queues"), list):
            raise ScalingConfigError('Oczekiwano {"queues": [{"name": "q:gpu", ...}]}.')
        with self._lock:
            try:
                stored = self._stored_overrides()
            except (ScalingConfigError, ValueError):
                stored = {}
            for item in body["queues"]:
                if not isinstance(item, dict) or not isinstance(item.get("name"), str):
                    raise ScalingConfigError('Kazda kolejka musi miec pole "name".')
                merged = dict(stored.get(item["name"], {}))
                merged.update({k: v for k, v in item.items() if k != "name"})
                stored[item["name"]] = merged
            cfg = self.base_config
            if self.env_over:
                cfg = apply_overrides(cfg, self.env_over)
            result = apply_overrides(cfg, stored)  # waliduje; nic nie zapisane przy bledzie
            self.backend.set(OVERRIDES_KEY, json.dumps(stored))
            return result

    # --- bezczynnosc ----------------------------------------------------
    def _idle_seconds(self, queue: str, nonempty: bool, now: float) -> float:
        key = IDLE_KEY_PREFIX + queue
        if nonempty:
            self.backend.set(key, repr(now))
            return 0.0
        raw = self.backend.get(key)
        if raw is None:
            self.backend.set(key, repr(now))
            return 0.0
        try:
            return max(0.0, now - float(raw))
        except ValueError:
            self.backend.set(key, repr(now))
            return 0.0

    # --- jeden obieg petli ---------------------------------------------
    def tick(self) -> dict[str, int]:
        """Odczytaj stan q:gpu, zdecyduj, wykonaj. Nie rzuca (awarie logujemy)."""
        with self._lock:
            try:
                cfg = self.effective_config()
                now = self.clock()
                backlog = self.backend.backlog(GPU_QUEUE)
                running = self.backend.running(GPU_QUEUE)
                idle = self._idle_seconds(GPU_QUEUE, backlog > 0 or running > 0, now)
                count = getattr(self.executor, "count", None)
                workers = count() if callable(count) else len(self.backend.workers(GPU_QUEUE))
                decisions = decide([QueueState(GPU_QUEUE, backlog, workers, idle)], cfg)
                for d in decisions:
                    if d.desired != d.current:
                        log.info("q:gpu %d -> %d: %s", d.current, d.desired, d.reason)
                result = self.executor.apply(decisions)
                if any(d.desired < d.current for d in decisions):
                    # Histereza: kolejny worker zejdzie dopiero po kolejnym scale_down_idle_s.
                    self.backend.set(IDLE_KEY_PREFIX + GPU_QUEUE, repr(now))
                return result
            except Exception as exc:  # noqa: BLE001 - petla nie moze umrzec
                log.warning("Obieg autoskalera nieudany: %s", exc)
                return {}

    # --- payload /scaling ----------------------------------------------
    def payload(self) -> dict[str, Any]:
        cfg = self.effective_config()
        queues: list[dict[str, Any]] = []
        workers: list[dict[str, Any]] = []
        names = [GPU_QUEUE] + [n for n in cfg.queues if n != GPU_QUEUE]
        for name in names:
            p = cfg.queues.get(name)
            if p is None:
                continue
            scalable = name == GPU_QUEUE
            try:
                backlog = self.backend.backlog(name)
                running = self.backend.running(name)
                workers.extend(self.backend.workers(name))
            except Exception as exc:  # noqa: BLE001 - /scaling nie pada, gdy kolejka nie odpowiada
                log.warning("Odczyt kolejki %s nieudany: %s", name, exc)
                backlog = running = 0
            queues.append(
                {
                    "name": name,
                    "backlog": backlog,
                    "running": running,
                    "min": p.min_workers,
                    "max": p.max_workers,
                    "cpus": p.cpus if scalable else None,
                    "memory_mb": p.memory_mb if scalable else None,
                    "scale_up_backlog": p.scale_up_backlog,
                }
            )
        try:
            done = self.backend.finished_since(GPU_QUEUE, THROUGHPUT_WINDOW_S)
        except Exception as exc:  # noqa: BLE001
            log.warning("Odczyt przepustowosci nieudany: %s", exc)
            done = 0
        return {
            "executor": cfg.executor,
            "ollama_parallel": cfg.ollama_parallel,
            "queues": queues,
            "workers": workers,
            "throughput_per_min": round(done / (THROUGHPUT_WINDOW_S / 60), 2),
        }


# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #


def make_handler(scaler: Autoscaler) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def _send(self, status: int, payload: Any) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/health":
                self._send(200, {"ok": True})
            elif self.path == "/scaling":
                try:
                    self._send(200, scaler.payload())
                except Exception as exc:  # noqa: BLE001
                    log.warning("GET /scaling: %s", exc)
                    self._send(500, {"detail": str(exc)})
            else:
                self._send(404, {"detail": "not found"})

        def do_PUT(self) -> None:  # noqa: N802
            if self.path != "/scaling":
                self._send(404, {"detail": "not found"})
                return
            try:
                length = int(self.headers.get("Content-Length") or 0)
                body = json.loads(self.rfile.read(length) or b"null")
            except (ValueError, UnicodeDecodeError):
                self._send(422, {"detail": "Cialo zadania nie jest poprawnym JSON."})
                return
            try:
                scaler.update(body)
                self._send(200, scaler.payload())
            except ScalingConfigError as exc:
                self._send(422, {"detail": str(exc)})
            except Exception as exc:  # noqa: BLE001
                log.warning("PUT /scaling: %s", exc)
                self._send(500, {"detail": str(exc)})

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
            return

    return Handler


def serve(scaler: Autoscaler, port: int = DEFAULT_PORT) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("0.0.0.0", port), make_handler(scaler))  # noqa: S104 - siec compose
    return server


# --------------------------------------------------------------------------- #
# Uruchomienie
# --------------------------------------------------------------------------- #


def build_executor(kind: str, scaler_cfg: ScalingConfig, limits: Callable[[], tuple[float, int]]):
    if kind == "dry-run":
        return pool.DryRunExecutor(scaler_cfg)
    if kind == "pool":
        return pool.PoolExecutor(scaler_cfg)
    if kind == "compose":
        import docker

        client = docker.from_env()
        project = pool.detect_project(
            client, socket.gethostname(), fallback=os.getenv("AUTOSCALER_PROJECT", "")
        )
        if not project:
            raise SystemExit("Nie znam projektu compose (ustaw AUTOSCALER_PROJECT).")
        log.info("Executor compose: projekt '%s', serwis analyzer", project)
        return pool.ComposeExecutor(client, project, limits=limits)
    raise SystemExit(f"Nieznany executor: {kind}")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    base = load_scaling_config()
    kind = os.getenv("AUTOSCALER_EXECUTOR") or base.executor
    from dataclasses import replace

    base = replace(base, executor=kind)
    env_over = env_overrides()
    apply_overrides(base, env_over)  # glosny blad przy sprzecznej konfiguracji startowej

    backend = ValkeyBackend(os.getenv("VALKEY_URL", "redis://valkey:6379/0"))
    holder: dict[str, Autoscaler] = {}

    def limits() -> tuple[float, int]:
        p = holder["a"].effective_config().queues[GPU_QUEUE]
        return p.cpus, p.memory_mb

    executor = build_executor(kind, base, limits)
    scaler = Autoscaler(backend, executor, base, env_over)
    holder["a"] = scaler

    interval = float(os.getenv("AUTOSCALER_INTERVAL_S", "5"))
    stop = threading.Event()

    def loop() -> None:
        while not stop.is_set():
            scaler.tick()
            stop.wait(interval)

    threading.Thread(target=loop, name="autoscaler-loop", daemon=True).start()
    port = int(os.getenv("AUTOSCALER_PORT", str(DEFAULT_PORT)))
    server = serve(scaler, port)
    signal.signal(signal.SIGTERM, lambda *_: threading.Thread(target=server.shutdown).start())
    log.info("Autoskaler: executor=%s, interwal=%ss, port=%s", kind, interval, port)
    try:
        server.serve_forever()
    finally:
        stop.set()
        executor.shutdown()


if __name__ == "__main__":
    main()

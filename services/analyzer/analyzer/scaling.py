"""Autoskaler puli workerow: konfiguracja, funkcja decyzyjna, payload /scaling.

Zmierzono, ze CALY czas analizy dokumentu (18,4 s) to warstwa modelu, a etapy
CPU zajmuja 3,7 ms. Dlatego liczba workerow `q:gpu` nie moze przekraczac liczby
endpointow Ollamy: workery bez modeli to puste krzesla i nie daja przepustowosci.

Roznica celowa: BRAK konfiguracji degraduje do domyslnej (z ostrzezeniem),
ale konfiguracja wewnetrznie SPRZECZNA to blad operatora - ScalingConfigError.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

log = logging.getLogger(__name__)

logger = logging.getLogger(__name__)

DEFAULT_SCALING_PATH = Path(__file__).resolve().parent / "config" / "scaling.yaml"

VALID_EXECUTORS = frozenset({"dry-run", "pool", "compose"})


class ScalingConfigError(ValueError):
    """Konfiguracja skalowania jest wewnetrznie sprzeczna."""


class _ShapeError(Exception):
    """Zly ksztalt pliku - traktowany jak uszkodzony plik, nie jak sprzecznosc."""


@dataclass(frozen=True)
class QueuePolicy:
    name: str
    min_workers: int
    max_workers: int
    scale_up_backlog: int
    scale_down_idle_s: int


@dataclass(frozen=True)
class ScalingConfig:
    executor: str
    hard_max_total: int
    queues: dict[str, QueuePolicy]
    ollama_endpoints: tuple[str, ...]


# Kopia wartosci z scaling.yaml - fallback, gdy plik nie istnieje.
DEFAULT_SCALING_CONFIG = ScalingConfig(
    executor="dry-run",
    hard_max_total=6,
    queues={
        "ingest": QueuePolicy("ingest", 1, 4, 10, 300),
        "render": QueuePolicy("render", 1, 2, 5, 300),
        "gpu": QueuePolicy("gpu", 1, 1, 3, 600),
    },
    ollama_endpoints=("http://host.docker.internal:11434",),
)


def _int(value: Any, what: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ScalingConfigError(f"Pole {what} musi byc liczba calkowita, a jest: {value!r}.")
    return value


def validate_scaling_config(config: ScalingConfig) -> None:
    """Sprawdz niezmienniki konfiguracji. Rzuca ScalingConfigError z komunikatem po polsku."""
    if config.executor not in VALID_EXECUTORS:
        raise ScalingConfigError(
            f"Nieznany executor '{config.executor}'; dozwolone: {', '.join(sorted(VALID_EXECUTORS))}."
        )
    for p in config.queues.values():
        if p.min_workers > p.max_workers:
            raise ScalingConfigError(
                f"Kolejka '{p.name}': min ({p.min_workers}) jest wieksze od max ({p.max_workers})."
            )
    gpu = config.queues.get("gpu")
    if gpu is not None and gpu.max_workers > len(config.ollama_endpoints):
        raise ScalingConfigError(
            f"Kolejka gpu pozwala na {gpu.max_workers} workerow, ale jest tylko "
            f"{len(config.ollama_endpoints)} endpointow Ollamy; worker bez modelu nie daje "
            "przepustowosci (caly czas analizy to model)."
        )
    suma_min = sum(p.min_workers for p in config.queues.values())
    if config.hard_max_total < suma_min:
        raise ScalingConfigError(
            f"hard_max_total ({config.hard_max_total}) jest mniejszy od sumy minimow kolejek ({suma_min})."
        )


def _parse(loaded: dict) -> ScalingConfig:
    raw = loaded.get("scaling", loaded)
    if not isinstance(raw, dict):
        raise _ShapeError("sekcja 'scaling' nie jest slownikiem")
    d = DEFAULT_SCALING_CONFIG
    queues = dict(d.queues)
    if "queues" in raw:
        rq = raw["queues"]
        if not isinstance(rq, dict):
            raise ScalingConfigError("Pole 'queues' musi byc slownikiem kolejek.")
        queues = {}
        for name, body in rq.items():
            if not isinstance(body, dict):
                raise ScalingConfigError(f"Kolejka '{name}' musi byc slownikiem.")
            base = d.queues.get(name)
            queues[name] = QueuePolicy(
                name=str(name),
                min_workers=_int(body.get("min", base.min_workers if base else 1), f"{name}.min"),
                max_workers=_int(body.get("max", base.max_workers if base else 1), f"{name}.max"),
                scale_up_backlog=_int(
                    body.get("scale_up_backlog", base.scale_up_backlog if base else 10),
                    f"{name}.scale_up_backlog",
                ),
                scale_down_idle_s=_int(
                    body.get("scale_down_idle_s", base.scale_down_idle_s if base else 300),
                    f"{name}.scale_down_idle_s",
                ),
            )
    endpoints = raw.get("ollama_endpoints", d.ollama_endpoints)
    if not isinstance(endpoints, (list, tuple)):
        raise ScalingConfigError("Pole 'ollama_endpoints' musi byc lista adresow.")
    return ScalingConfig(
        executor=str(raw.get("executor", d.executor)),
        hard_max_total=_int(raw.get("hard_max_total", d.hard_max_total), "hard_max_total"),
        queues=queues,
        ollama_endpoints=tuple(str(e) for e in endpoints),
    )


def load_scaling_config(path: str | Path | None = None) -> ScalingConfig:
    """Wczytaj konfiguracje skalowania.

    Brak pliku albo uszkodzony YAML => DEFAULT_SCALING_CONFIG z ostrzezeniem.
    Konfiguracja sprzeczna (niezmienniki) => ScalingConfigError, glosno.
    """
    target = Path(path) if path is not None else DEFAULT_SCALING_PATH
    try:
        with target.open("r", encoding="utf-8") as fh:
            loaded = yaml.safe_load(fh)
    except FileNotFoundError:
        logger.warning("Brak pliku skalowania %s - uzywam konfiguracji domyslnej", target)
        return DEFAULT_SCALING_CONFIG
    except Exception as exc:  # noqa: BLE001 - uszkodzony plik nie moze zabic serwisu
        logger.warning("Nie mozna odczytac %s (%s) - uzywam konfiguracji domyslnej", target, exc)
        return DEFAULT_SCALING_CONFIG
    if loaded is None:
        return DEFAULT_SCALING_CONFIG
    if not isinstance(loaded, dict):
        logger.warning("Plik %s nie zawiera slownika - uzywam konfiguracji domyslnej", target)
        return DEFAULT_SCALING_CONFIG
    try:
        config = _parse(loaded)
    except _ShapeError as exc:
        logger.warning("Plik %s: %s - uzywam konfiguracji domyslnej", target, exc)
        return DEFAULT_SCALING_CONFIG
    validate_scaling_config(config)
    return config


# ---------------------------------------------------------------------------
# Funkcja decyzyjna - czysta, bez efektow ubocznych
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class QueueState:
    """Zmierzony stan jednej kolejki."""

    name: str
    backlog: int
    workers: int
    idle_s: float


@dataclass(frozen=True)
class ScalingDecision:
    """Decyzja dla jednej kolejki. `reason` to zdanie dla operatora."""

    queue: str
    current: int
    desired: int
    reason: str
    capped_by: str | None


def decide(states: list[QueueState], config: ScalingConfig) -> list[ScalingDecision]:
    """Zamien stan kolejek i konfiguracje na decyzje. Deterministyczna, nie rzuca.

    Kolejnosc krokow: wzrost przy backlogu >= progu; spadek TYLKO gdy backlog == 0
    ORAZ bezczynnosc >= progu (histereza - bez niej autoskaler oscyluje); przyciecie
    do [min, max]; limit endpointow Ollamy dla gpu; limit globalny hard_max_total
    (zdejmujemy z kolejki o najmniejszym backlogu, remis -> nazwa alfabetycznie).
    Kolejki spoza konfiguracji sa pomijane.
    """
    rows: list[dict[str, Any]] = []
    for s in states:
        policy = config.queues.get(s.name)
        if policy is None:
            logger.warning("Kolejka '%s' nie jest skonfigurowana - pomijam", s.name)
            continue
        current = s.workers
        raw = current
        reason = f"backlog {s.backlog}, workerow {current}, bez zmian"
        if s.backlog >= policy.scale_up_backlog:
            raw = current + 1
            reason = f"backlog {s.backlog} >= progu {policy.scale_up_backlog}, zwiekszam z {current} do {raw}"
        elif s.backlog == 0 and s.idle_s >= policy.scale_down_idle_s:
            raw = current - 1
            reason = (
                f"kolejka pusta od {int(s.idle_s)} s (prog {policy.scale_down_idle_s} s), "
                f"zmniejszam z {current} do {raw}"
            )

        desired = max(policy.min_workers, min(raw, policy.max_workers))
        capped_by: str | None = None
        if raw > policy.max_workers:
            capped_by = "max_workers"
        if s.name == "gpu" and raw > len(config.ollama_endpoints):
            # Limit endpointow ma pierwszenstwo w opisie: to on jest przyczyna biznesowa.
            desired = min(desired, len(config.ollama_endpoints))
            capped_by = "ollama_endpoints"
        if raw < policy.min_workers:
            reason = (
                f"kolejka pusta od {int(s.idle_s)} s, ale limit min_workers="
                f"{policy.min_workers} - zostaje {desired}"
            )
        if capped_by == "max_workers":
            reason = (
                f"backlog {s.backlog} wymaga wiecej workerow, ale limit "
                f"max_workers={policy.max_workers}, zostaje {desired}"
            )
        elif capped_by == "ollama_endpoints":
            reason = (
                f"backlog {s.backlog} wymaga wiecej workerow, ale endpointow Ollamy jest "
                f"{len(config.ollama_endpoints)}, zostaje {desired}"
            )
        rows.append(
            {"state": s, "policy": policy, "desired": desired, "reason": reason, "capped_by": capped_by}
        )

    # Limit globalny - petla konczy sie, bo kazda iteracja zmniejsza sume o 1.
    while sum(r["desired"] for r in rows) > config.hard_max_total:
        candidates = [r for r in rows if r["desired"] > r["policy"].min_workers]
        if not candidates:
            break  # same minima - walidacja konfiguracji wyklucza ten przypadek
        victim = min(candidates, key=lambda r: (r["state"].backlog, r["state"].name))
        victim["desired"] -= 1
        victim["capped_by"] = "hard_max_total"
        victim["reason"] = (
            f"limit globalny hard_max_total={config.hard_max_total} osiagniety, zostaje {victim['desired']}"
        )

    return [
        ScalingDecision(
            queue=r["state"].name,
            current=r["state"].workers,
            desired=r["desired"],
            reason=r["reason"],
            capped_by=r["capped_by"],
        )
        for r in rows
    ]


def scaling_payload(states: list[QueueState], config: ScalingConfig) -> dict:
    """Ksztalt odpowiedzi /scaling: konfiguracja ogolna plus decyzja per kolejka."""
    by_name = {s.name: s for s in states}
    queues = []
    for d in decide(states, config):
        s = by_name[d.queue]
        queues.append(
            {
                "name": d.queue,
                "backlog": s.backlog,
                "workers": d.current,
                "desired": d.desired,
                "reason": d.reason,
                "capped_by": d.capped_by,
            }
        )
    return {"executor": config.executor, "hard_max_total": config.hard_max_total, "queues": queues}


# --------------------------------------------------------------------------- #
# Odczyt stanu kolejek z Valkeya
# --------------------------------------------------------------------------- #


def read_queue_states(
    config: ScalingConfig,
    *,
    backlog_reader: "Callable[[str], int] | None" = None,
    worker_counter: "Callable[[str], int] | None" = None,
) -> list[QueueState]:
    """Stan kolejek do podania w `decide` i w /scaling.

    `backlog` i `workers` czytamy z RQ, czyli sa PRAWDZIWE.

    `idle_s` zostaje 0.0 i jest to swiadome: czas bezczynnosci kolejki wymaga
    trwalego licznika, ktory utrzymuje PETLA ORKIESTRATORA — a ta jest poza
    zakresem (wymaga dzialajacego Valkeya, czego nie da sie tu zweryfikowac,
    patrz plan, sekcja "Poza zakresem"). Konsekwencja jest bezpieczna:
    przy idle_s = 0 warunek skalowania W DOL nigdy nie jest spelniony, wiec
    /scaling nie zaproponuje wygaszenia workera na podstawie danych,
    ktorych nie ma. Skalowanie W GORE dziala w pelni, bo opiera sie na backlogu.

    Czytniki sa wstrzykiwane, zeby testy nie potrzebowaly Valkeya.
    Awaria odczytu pojedynczej kolejki daje dla niej zera, nie wyjatek —
    /scaling nie moze padac, gdy kolejka nie odpowiada.
    """
    read_backlog = backlog_reader or _rq_backlog_reader()
    count_workers = worker_counter or _rq_worker_counter()

    states: list[QueueState] = []
    for name in config.queues:
        try:
            backlog = int(read_backlog(name))
        except Exception as exc:  # noqa: BLE001
            log.warning("Nie udalo sie odczytac backlogu kolejki %s: %s", name, exc)
            backlog = 0
        try:
            workers = int(count_workers(name))
        except Exception as exc:  # noqa: BLE001
            log.warning("Nie udalo sie policzyc workerow kolejki %s: %s", name, exc)
            workers = 0
        states.append(QueueState(name=name, backlog=backlog, workers=workers, idle_s=0.0))
    return states


def _connection():
    """Polaczenie z Valkeyem. Import leniwy — modul musi dzialac bez redisa."""
    import os

    from redis import Redis

    return Redis.from_url(os.getenv("VALKEY_URL", "redis://valkey:6379/0"))


def _rq_backlog_reader() -> "Callable[[str], int]":
    def _read(name: str) -> int:
        from rq import Queue

        return Queue(name, connection=_connection()).count

    return _read


def _rq_worker_counter() -> "Callable[[str], int]":
    def _count(name: str) -> int:
        from rq import Queue, Worker

        conn = _connection()
        queue = Queue(name, connection=conn)
        return len(Worker.all(queue=queue))

    return _count


def make_valkey_state_provider(
    config: ScalingConfig | None = None,
) -> "Callable[[], list[QueueState]]":
    """Dostawca stanu do podstawienia w `health.STATE_PROVIDER`.

    Worker instaluje go u siebie przy starcie; domyslny dostawca w health.py
    zwraca pusta liste, zeby /scaling dzialalo takze bez Valkeya (testy, demo).
    """

    def _provider() -> list[QueueState]:
        cfg = config or load_scaling_config()
        try:
            return read_queue_states(cfg)
        except Exception as exc:  # noqa: BLE001
            log.warning("Odczyt stanu kolejek nieudany: %s", exc)
            return []

    return _provider

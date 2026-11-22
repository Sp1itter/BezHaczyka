"""Autoskaler puli workerow: konfiguracja, funkcja decyzyjna, payload /scaling.

Zmierzono, ze CALY czas analizy dokumentu (18,4 s) to warstwa modelu, a etapy
CPU zajmuja 3,7 ms. Jedna Ollama z OLLAMA_NUM_PARALLEL=N obsluguje N rownoleglych
zadan, wiec liczba workerow `q:gpu` nie moze przekraczac N * liczba endpointow:
worker ponad te pojemnosc to puste krzesla i nie daje przepustowosci.
Nazwy kolejek sa nazwami RQ (`q:gpu`, `q:ingest`, `q:render`).

Roznica celowa: BRAK konfiguracji degraduje do domyslnej (z ostrzezeniem),
ale konfiguracja wewnetrznie SPRZECZNA to blad operatora - ScalingConfigError.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

log = logging.getLogger(__name__)

logger = logging.getLogger(__name__)

DEFAULT_SCALING_PATH = Path(__file__).resolve().parent / "config" / "scaling.yaml"

GPU_QUEUE = "q:gpu"
DEFAULT_OLLAMA_PARALLEL = 4

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
    # Limity zasobow KLONOW (dodatkowych kontenerow); 0 = bez limitu.
    cpus: float = 0.0
    memory_mb: int = 0


@dataclass(frozen=True)
class ScalingConfig:
    executor: str
    hard_max_total: int
    queues: dict[str, QueuePolicy]
    ollama_endpoints: tuple[str, ...]
    # Ile rownoleglych zadan obsluguje jedna Ollama (OLLAMA_NUM_PARALLEL).
    ollama_parallel: int = DEFAULT_OLLAMA_PARALLEL

    @property
    def gpu_capacity(self) -> int:
        """Maksymalna sensowna liczba workerow q:gpu."""
        return self.ollama_parallel * max(1, len(self.ollama_endpoints))


# Kopia wartosci z scaling.yaml - fallback, gdy plik nie istnieje.
DEFAULT_SCALING_CONFIG = ScalingConfig(
    executor="compose",
    hard_max_total=16,
    queues={
        "q:ingest": QueuePolicy("q:ingest", 1, 4, 10, 300),
        "q:render": QueuePolicy("q:render", 1, 2, 5, 300),
        "q:gpu": QueuePolicy("q:gpu", 1, 4, 3, 60, cpus=2.0, memory_mb=3072),
    },
    ollama_endpoints=("http://host.docker.internal:11434",),
    ollama_parallel=DEFAULT_OLLAMA_PARALLEL,
)


def _int(value: Any, what: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ScalingConfigError(f"Pole {what} musi byc liczba calkowita, a jest: {value!r}.")
    return value


def _num(value: Any, what: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ScalingConfigError(f"Pole {what} musi byc liczba, a jest: {value!r}.")
    return float(value)


def env_ollama_parallel() -> int:
    """OLLAMA_NUM_PARALLEL ze srodowiska (domyslnie 4); smieci => domyslna."""
    try:
        return int(os.getenv("OLLAMA_NUM_PARALLEL", str(DEFAULT_OLLAMA_PARALLEL)))
    except ValueError:
        return DEFAULT_OLLAMA_PARALLEL


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
    for p in config.queues.values():
        if p.cpus < 0 or p.memory_mb < 0:
            raise ScalingConfigError(f"Kolejka '{p.name}': cpus i memory_mb nie moga byc ujemne.")
    if config.ollama_parallel < 1:
        raise ScalingConfigError("ollama_parallel musi byc >= 1.")
    gpu = config.queues.get(GPU_QUEUE)
    if gpu is not None and gpu.max_workers > config.gpu_capacity:
        n_end = len(config.ollama_endpoints)
        limit = (
            f"OLLAMA_NUM_PARALLEL ({config.ollama_parallel})"
            if n_end <= 1
            else f"OLLAMA_NUM_PARALLEL ({config.ollama_parallel}) * endpointy ({n_end})"
        )
        raise ScalingConfigError(f"max > {limit}")
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
                cpus=_num(body.get("cpus", base.cpus if base else 0.0), f"{name}.cpus"),
                memory_mb=_int(
                    body.get("memory_mb", base.memory_mb if base else 0), f"{name}.memory_mb"
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
        ollama_parallel=_int(
            raw.get("ollama_parallel", env_ollama_parallel()), "ollama_parallel"
        ),
    )


# Pola kolejki, ktore operator moze zmieniac (PUT /scaling, klucz Valkey ops:scaling).
OVERRIDABLE_FIELDS = {
    "min": ("min_workers", _int),
    "max": ("max_workers", _int),
    "scale_up_backlog": ("scale_up_backlog", _int),
    "scale_down_idle_s": ("scale_down_idle_s", _int),
    "cpus": ("cpus", _num),
    "memory_mb": ("memory_mb", _int),
}


def apply_overrides(config: ScalingConfig, overrides: dict[str, dict[str, Any]]) -> ScalingConfig:
    """Nalozenie nadpisan operatora na konfiguracje i WALIDACJA wyniku.

    `overrides`: {"q:gpu": {"max": 2, "cpus": 1.5, ...}}. Skaluje sie tylko `q:gpu`;
    pozostale kolejki sa tylko do odczytu. Rzuca ScalingConfigError (=> HTTP 422).
    """
    from dataclasses import replace

    queues = dict(config.queues)
    for name, fields in overrides.items():
        if name not in queues:
            raise ScalingConfigError(f"Nieznana kolejka '{name}'.")
        if name != GPU_QUEUE:
            raise ScalingConfigError(f"Kolejka '{name}' jest tylko do odczytu; skalowac mozna {GPU_QUEUE}.")
        if not isinstance(fields, dict):
            raise ScalingConfigError(f"Nadpisania kolejki '{name}' musza byc slownikiem.")
        changes: dict[str, Any] = {}
        for key, value in fields.items():
            if key == "name":
                continue
            if key not in OVERRIDABLE_FIELDS:
                raise ScalingConfigError(f"Nieznane pole '{key}' kolejki '{name}'.")
            attr, parser = OVERRIDABLE_FIELDS[key]
            changes[attr] = parser(value, f"{name}.{key}")
        queues[name] = replace(queues[name], **changes)
    result = replace(config, queues=queues)
    validate_scaling_config(result)
    return result


def env_overrides(environ: "os._Environ[str] | dict[str, str] | None" = None) -> dict[str, dict[str, Any]]:
    """Nadpisania q:gpu ze zmiennych ANALYZER_* (compose / .env). Puste = nieustawione."""
    env = os.environ if environ is None else environ
    mapping = {
        "ANALYZER_MIN_REPLICAS": ("min", int),
        "ANALYZER_MAX_REPLICAS": ("max", int),
        "ANALYZER_SCALE_UP_BACKLOG": ("scale_up_backlog", int),
        "ANALYZER_SCALE_DOWN_IDLE_S": ("scale_down_idle_s", int),
        "ANALYZER_EXTRA_CPUS": ("cpus", float),
        "ANALYZER_EXTRA_MEM_MB": ("memory_mb", int),
    }
    fields: dict[str, Any] = {}
    for var, (key, cast) in mapping.items():
        raw = str(env.get(var, "")).strip()
        if not raw:
            continue
        try:
            fields[key] = cast(raw)
        except ValueError:
            raise ScalingConfigError(f"Zmienna {var}={raw!r} nie jest liczba.") from None
    return {GPU_QUEUE: fields} if fields else {}


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
        if s.name == GPU_QUEUE and desired > config.gpu_capacity:
            # Pojemnosc Ollamy (gdy to ona jest ciasniejsza niz max) ma pierwszenstwo w opisie.
            desired = config.gpu_capacity
            capped_by = "ollama_parallel"
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
        elif capped_by == "ollama_parallel":
            reason = (
                f"backlog {s.backlog} wymaga wiecej workerow, ale Ollama obsluguje rownolegle "
                f"{config.gpu_capacity} zadan (OLLAMA_NUM_PARALLEL), zostaje {desired}"
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
    idle_reader: "Callable[[str], float] | None" = None,
) -> list[QueueState]:
    """Stan kolejek do podania w `decide` i w /scaling.

    `backlog` i `workers` czytamy z RQ, czyli sa PRAWDZIWE.

    `idle_s` pochodzi z `idle_reader` (autoskaler trzyma znacznik ostatniej
    niepustej chwili w Valkey, klucz `ops:idle:<kolejka>`). Bez czytnika zostaje
    0.0, czyli skalowanie W DOL z powodu bezczynnosci sie nie odpali.

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
        idle_s = 0.0
        if idle_reader is not None:
            try:
                idle_s = float(idle_reader(name))
            except Exception as exc:  # noqa: BLE001
                log.warning("Nie udalo sie odczytac bezczynnosci kolejki %s: %s", name, exc)
        states.append(QueueState(name=name, backlog=backlog, workers=workers, idle_s=idle_s))
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

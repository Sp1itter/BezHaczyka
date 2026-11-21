"""Autoskaler puli workerow: konfiguracja, funkcja decyzyjna, payload /scaling.

Zmierzono, ze CALY czas analizy dokumentu (18,4 s) to warstwa modelu, a etapy
CPU zajmuja 3,7 ms. Dlatego liczba workerow `q:gpu` nie moze przekraczac liczby
endpointow Ollamy: workery bez modeli to puste krzesla i nie daja przepustowosci.

Roznica celowa: BRAK konfiguracji degraduje do domyslnej (z ostrzezeniem),
ale konfiguracja wewnetrznie SPRZECZNA to blad operatora - ScalingConfigError.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

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

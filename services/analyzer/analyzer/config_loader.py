"""Loader progow liczbowych z analyzer/config/thresholds.yaml.

Zasada nadrzedna: BRAK KONFIGURACJI NIE MOZE ZABIC SERWISU. Ta funkcja nigdy
nie rzuca wyjatkiem - przy braku pliku, uszkodzonym YAML-u albo zlym ksztalcie
danych wraca do wartosci domyslnych (DEFAULT_THRESHOLDS) i loguje ostrzezenie.

Wartosci domyslne musza byc zgodne z plikiem YAML i z kodem (scoring.py,
embeddings.py) - pilnuje tego tests/test_config.py.
"""

from __future__ import annotations

import copy
import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

DEFAULT_THRESHOLDS_PATH = Path(__file__).resolve().parent / "config" / "thresholds.yaml"

# Fallback uzywany, gdy plik nie istnieje albo jest uszkodzony.
# Kopia wartosci z thresholds.yaml - celowo zduplikowana, zeby serwis mial
# sensowne progi nawet bez pliku konfiguracyjnego.
DEFAULT_THRESHOLDS: dict[str, Any] = {
    "rules": {
        "rule_4": {"min_ratio": 0.9},
        "rule_5": {"min_contrast": 4.5},
        "rule_6": {"footer_position_fraction": 0.85},
        "rule_8": {"min_mobile_font_px": 9},
    },
    "scoring": {
        "flag_threshold": 50.0,
        "high_threshold": 70.0,
        "medium_threshold": 40.0,
    },
    "dedup": {
        "near_duplicate_cosine": 0.95,
        "same_campaign_cosine": 0.88,
        "simhash_max_distance": 6,
    },
}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Nakladka `override` na `base` rekurencyjnie. Brakujace klucze bierze z base."""
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_thresholds(path: str | Path | None = None) -> dict:
    """Wczytaj progi z YAML-a. Nigdy nie rzuca wyjatkiem.

    Parametry:
        path: sciezka do pliku YAML; domyslnie analyzer/config/thresholds.yaml.

    Zwraca:
        Slownik progow. Klucze brakujace w pliku sa uzupelniane wartosciami
        domyslnymi. Gdy plik nie istnieje, jest uszkodzony albo nie jest
        slownikiem na najwyzszym poziomie - zwracane sa same wartosci domyslne.
    """
    target = Path(path) if path is not None else DEFAULT_THRESHOLDS_PATH

    try:
        with target.open("r", encoding="utf-8") as fh:
            loaded = yaml.safe_load(fh)
    except FileNotFoundError:
        logger.warning("Brak pliku progow %s - uzywam wartosci domyslnych", target)
        return copy.deepcopy(DEFAULT_THRESHOLDS)
    except Exception as exc:  # noqa: BLE001 - celowo: zadna awaria konfiguracji nie moze zabic serwisu
        logger.warning(
            "Nie mozna odczytac progow z %s (%s) - uzywam wartosci domyslnych",
            target,
            exc,
        )
        return copy.deepcopy(DEFAULT_THRESHOLDS)

    if loaded is None:
        # Pusty plik - to nie jest blad, po prostu same wartosci domyslne.
        return copy.deepcopy(DEFAULT_THRESHOLDS)

    if not isinstance(loaded, dict):
        logger.warning(
            "Plik progow %s nie zawiera slownika na najwyzszym poziomie - uzywam wartosci domyslnych",
            target,
        )
        return copy.deepcopy(DEFAULT_THRESHOLDS)

    return _deep_merge(DEFAULT_THRESHOLDS, loaded)


def get_threshold(dotted_key: str, default: Any = None) -> Any:
    """Odczytaj prog po sciezce z kropkami, np. "scoring.flag_threshold".

    Zwraca `default`, gdy klucza nie ma albo po drodze trafia sie na wartosc,
    ktora nie jest slownikiem. Nigdy nie rzuca wyjatkiem.
    """
    try:
        node: Any = load_thresholds()
        for part in dotted_key.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node
    except Exception:  # noqa: BLE001 - odczyt progu nie moze wywrocic analizy
        return default

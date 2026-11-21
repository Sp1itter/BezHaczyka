"""Executory autoskalera: wykonuja decyzje z scaling.decide().

Funkcja decyzyjna jest czysta; tutaj sa efekty uboczne. Dwa executory o tym
samym interfejsie:
  - DryRunExecutor - tylko loguje, nic nie startuje (domyslny, bezpieczny),
  - PoolExecutor   - trzyma lokalne procesy workerow i uzgadnia ich liczbe.

`spawn` jest wstrzykiwany, zeby testy nie uruchamialy procesow. Awaria
pojedynczego workera nigdy nie przewraca executora - logujemy i jedziemy dalej.
"""

from __future__ import annotations

import logging
import subprocess
import sys
from collections.abc import Callable

from analyzer.scaling import ScalingConfig, ScalingDecision

logger = logging.getLogger(__name__)

# Ile sekund czekamy na zakonczenie workera po terminate(), zanim odpuscimy.
_STOP_TIMEOUT_S = 10


def _default_spawn(queue: str) -> subprocess.Popen:
    """Uruchom workera RQ dla danej kolejki jako osobny proces."""
    return subprocess.Popen([sys.executable, "-m", "analyzer.worker", "--queue", queue])


class DryRunExecutor:
    """Executor, ktory tylko loguje decyzje. Zwraca niezmieniona liczbe workerow."""

    def __init__(self, config: ScalingConfig) -> None:
        self.config = config

    def apply(self, decisions: list[ScalingDecision]) -> dict[str, int]:
        result: dict[str, int] = {}
        for d in decisions:
            if d.desired != d.current:
                logger.info(
                    "[dry-run] kolejka %s: z %d na %d workerow (%s)", d.queue, d.current, d.desired, d.reason
                )
            result[d.queue] = d.current
        return result

    def shutdown(self) -> None:
        return None


class PoolExecutor:
    """Executor trzymajacy lokalne procesy workerow, po jednej liscie na kolejke."""

    def __init__(self, config: ScalingConfig, spawn: Callable[[str], object] | None = None) -> None:
        self.config = config
        self._spawn = spawn or _default_spawn
        self._workers: dict[str, list[object]] = {}

    @staticmethod
    def _alive(handle: object) -> bool:
        poll = getattr(handle, "poll", None)
        if poll is None:
            return True
        try:
            return poll() is None
        except Exception:  # noqa: BLE001 - nie wiemy, wiec zakladamy, ze zyje
            return True

    @staticmethod
    def _stop(handle: object) -> None:
        try:
            terminate = getattr(handle, "terminate", None)
            if terminate is not None:
                terminate()
            wait = getattr(handle, "wait", None)
            if wait is not None:
                wait(timeout=_STOP_TIMEOUT_S)
        except Exception as exc:  # noqa: BLE001 - zamykanie jednego workera nie moze zatrzymac reszty
            logger.warning("Nie udalo sie czysto zamknac workera: %s", exc)

    def apply(self, decisions: list[ScalingDecision]) -> dict[str, int]:
        """Uzgodnij liczbe workerow z decyzjami. Idempotentne. Zwraca stan faktyczny."""
        result: dict[str, int] = {}
        for d in decisions:
            handles = [h for h in self._workers.get(d.queue, []) if self._alive(h)]
            while len(handles) < d.desired:
                try:
                    handles.append(self._spawn(d.queue))
                except Exception as exc:  # noqa: BLE001 - nieudany start nie przewraca executora
                    logger.warning("Nie mozna uruchomic workera kolejki %s: %s", d.queue, exc)
                    break
            while len(handles) > d.desired:
                self._stop(handles.pop())
            self._workers[d.queue] = handles
            result[d.queue] = len(handles)
        return result

    def shutdown(self) -> None:
        """Zamknij wszystkie workery. Nie rzuca."""
        for handles in self._workers.values():
            for h in handles:
                self._stop(h)
        self._workers = {}

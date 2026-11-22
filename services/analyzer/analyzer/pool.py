"""Executory autoskalera: wykonuja decyzje z scaling.decide().

Funkcja decyzyjna jest czysta; tutaj sa efekty uboczne. Trzy executory o tym
samym interfejsie:
  - DryRunExecutor  - tylko loguje, nic nie startuje (bezpieczny),
  - PoolExecutor    - trzyma lokalne procesy workerow i uzgadnia ich liczbe,
  - ComposeExecutor - klonuje/usuwa kontenery serwisu compose `analyzer` przez Docker SDK
                      (za docker-socket-proxy); zarzadza WYLACZNIE kontenerami
                      wlasnego projektu compose.

`spawn` jest wstrzykiwany, zeby testy nie uruchamialy procesow. Awaria
pojedynczego workera nigdy nie przewraca executora - logujemy i jedziemy dalej.
"""

from __future__ import annotations

import logging
import subprocess
import sys
from collections.abc import Callable

from analyzer.scaling import GPU_QUEUE, ScalingConfig, ScalingDecision

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


# --------------------------------------------------------------------------- #
# ComposeExecutor - kontenery serwisu `analyzer` przez Docker SDK
# --------------------------------------------------------------------------- #

LABEL_PROJECT = "com.docker.compose.project"
LABEL_SERVICE = "com.docker.compose.service"
LABEL_NUMBER = "com.docker.compose.container-number"
# Znacznik klonow tworzonych przez autoskaler; kontenery bez niego (bazowe z compose)
# NIGDY nie sa zdejmowane.
LABEL_AUTOSCALED = "investwatch.autoscaled"

# Warm shutdown RQ: SIGTERM (docker stop) i czekanie tyle sekund na dokonczenie zadania.
STOP_TIMEOUT_S = 30

_ACTIVE_STATES = frozenset({"running", "created", "restarting"})


def _number(container) -> int:
    try:
        return int(container.labels.get(LABEL_NUMBER, "0"))
    except (TypeError, ValueError):
        return 0


class ComposeExecutor:
    """Skaluje serwis compose `analyzer`: dodaje klony i zdejmuje najwyzej numerowane.

    `client` to docker.DockerClient (albo atrapa w testach), `limits` zwraca
    (cpus, memory_mb) klonow z aktualnej konfiguracji operatora (0 = bez limitu).
    Filtr po etykietach projektu i serwisu gwarantuje, ze nie dotykamy cudzych
    kontenerow (np. innego projektu compose na tym samym demonie).
    """

    def __init__(
        self,
        client,
        project: str,
        service: str = "analyzer",
        limits: Callable[[], tuple[float, int]] | None = None,
        stop_timeout_s: int = STOP_TIMEOUT_S,
    ) -> None:
        self.client = client
        self.project = project
        self.service = service
        self._limits = limits or (lambda: (0.0, 0))
        self.stop_timeout_s = stop_timeout_s

    # --- odczyt ---------------------------------------------------------
    def _all(self) -> list:
        return list(
            self.client.containers.list(
                all=True,
                filters={"label": [f"{LABEL_PROJECT}={self.project}", f"{LABEL_SERVICE}={self.service}"]},
            )
        )

    def containers(self) -> list:
        """Zywe (running/created/restarting) kontenery serwisu, rosnaco po numerze."""
        return sorted((c for c in self._all() if c.status in _ACTIVE_STATES), key=_number)

    def count(self) -> int:
        return len(self.containers())

    def _reap_dead_clones(self) -> None:
        """Usun zatrzymane klony (np. po crashu) - nie sa juz workerami."""
        for c in self._all():
            if c.status not in _ACTIVE_STATES and c.labels.get(LABEL_AUTOSCALED) == "1":
                try:
                    c.remove(force=True)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Nie mozna usunac martwego klona %s: %s", c.name, exc)

    # --- zapis ----------------------------------------------------------
    @staticmethod
    def _template(active: list):
        bases = [c for c in active if c.labels.get(LABEL_AUTOSCALED) != "1"]
        return (bases or active or [None])[0]

    @staticmethod
    def _next_number(containers: list) -> int:
        used = {_number(c) for c in containers}
        n = 1
        while n in used:
            n += 1
        return n

    def _clone(self, template, number: int):
        cfg = template.attrs.get("Config", {})
        host = template.attrs.get("HostConfig", {})
        nets = list((template.attrs.get("NetworkSettings", {}).get("Networks") or {}).keys())
        labels = dict(cfg.get("Labels") or {})
        labels[LABEL_NUMBER] = str(number)
        labels[LABEL_AUTOSCALED] = "1"
        cpus, memory_mb = self._limits()
        kwargs: dict = {
            "image": cfg.get("Image") or template.attrs.get("Image"),
            "command": cfg.get("Cmd"),
            "entrypoint": cfg.get("Entrypoint"),
            "environment": list(cfg.get("Env") or []),
            "labels": labels,
            "name": f"{self.project}-{self.service}-{number}",
            "detach": True,
            "network": nets[0] if nets else None,
            "extra_hosts": host.get("ExtraHosts") or None,
            "user": cfg.get("User") or None,
            "working_dir": cfg.get("WorkingDir") or None,
        }
        if cfg.get("Healthcheck"):
            kwargs["healthcheck"] = cfg["Healthcheck"]
        if cpus and cpus > 0:
            kwargs["nano_cpus"] = int(cpus * 1_000_000_000)
        if memory_mb and memory_mb > 0:
            kwargs["mem_limit"] = f"{int(memory_mb)}m"
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        return self.client.containers.run(**kwargs)

    def _stop_and_remove(self, container) -> None:
        try:
            container.stop(timeout=self.stop_timeout_s)  # SIGTERM -> warm shutdown RQ
        except Exception as exc:  # noqa: BLE001
            logger.warning("Zatrzymanie %s nieudane: %s", container.name, exc)
        try:
            container.remove(force=True)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Usuniecie %s nieudane: %s", container.name, exc)

    def apply(self, decisions: list[ScalingDecision]) -> dict[str, int]:
        """Uzgodnij liczbe kontenerow analyzer z decyzja dla q:gpu. Zwraca stan faktyczny."""
        result: dict[str, int] = {}
        for d in decisions:
            if d.queue != GPU_QUEUE:
                continue  # skalujemy tylko analyzer; reszta tylko do odczytu
            try:
                self._reap_dead_clones()
                active = self.containers()
                while len(active) < d.desired:
                    template = self._template(active)
                    if template is None:
                        logger.warning("Brak bazowego kontenera %s - nie mam z czego klonowac", self.service)
                        break
                    before = len(active)
                    self._clone(template, self._next_number(active))
                    active = self.containers()
                    if len(active) <= before:
                        break  # klon nie wystartowal - nie kreci sie w kolko
                while len(active) > d.desired:
                    extras = [c for c in active if c.labels.get(LABEL_AUTOSCALED) == "1"]
                    if not extras:
                        break  # zostaje tylko bazowy kontener compose
                    self._stop_and_remove(max(extras, key=_number))
                    active = self.containers()
                result[d.queue] = len(active)
            except Exception as exc:  # noqa: BLE001 - awaria Dockera nie przewraca petli
                logger.warning("ComposeExecutor: %s", exc)
                result[d.queue] = d.current
        return result

    def shutdown(self) -> None:
        """Klony zostaja przy zamknieciu autoskalera (kolejka moze jeszcze byc obslugiwana)."""
        return None


def detect_project(client, hostname: str, fallback: str = "") -> str:
    """Nazwa projektu compose z etykiet WLASNEGO kontenera (hostname = id), potem fallback."""
    try:
        me = client.containers.get(hostname)
        found = (me.labels or {}).get(LABEL_PROJECT, "")
        if found:
            return found
    except Exception as exc:  # noqa: BLE001
        logger.warning("Nie moge odczytac etykiet wlasnego kontenera (%s): %s", hostname, exc)
    return fallback

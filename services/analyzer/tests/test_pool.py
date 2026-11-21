"""Testy executorow autoskalera - bez uruchamiania procesow (spawn wstrzykiwany)."""

from analyzer.pool import DryRunExecutor, PoolExecutor
from analyzer.scaling import DEFAULT_SCALING_CONFIG, ScalingDecision

CFG = DEFAULT_SCALING_CONFIG


class FakeWorker:
    def __init__(self, queue: str):
        self.queue = queue
        self.terminated = False

    def terminate(self) -> None:
        self.terminated = True

    def wait(self, timeout=None) -> int:
        return 0

    def poll(self):
        return 0 if self.terminated else None


class FakeSpawn:
    def __init__(self):
        self.calls: list[str] = []
        self.workers: list[FakeWorker] = []

    def __call__(self, queue: str) -> FakeWorker:
        self.calls.append(queue)
        w = FakeWorker(queue)
        self.workers.append(w)
        return w


def _d(queue: str, current: int, desired: int) -> ScalingDecision:
    return ScalingDecision(queue, current, desired, "decyzja testowa dla operatora", None)


def test_apply_startuje_brakujace_workery():
    spawn = FakeSpawn()
    ex = PoolExecutor(CFG, spawn=spawn)
    wynik = ex.apply([_d("ingest", 0, 3), _d("gpu", 0, 1)])
    assert wynik == {"ingest": 3, "gpu": 1}
    assert spawn.calls.count("ingest") == 3 and spawn.calls.count("gpu") == 1


def test_apply_zamyka_nadmiarowe_workery():
    spawn = FakeSpawn()
    ex = PoolExecutor(CFG, spawn=spawn)
    ex.apply([_d("ingest", 0, 3)])
    wynik = ex.apply([_d("ingest", 3, 1)])
    assert wynik == {"ingest": 1}
    assert sum(w.terminated for w in spawn.workers) == 2


def test_apply_jest_idempotentne():
    spawn = FakeSpawn()
    ex = PoolExecutor(CFG, spawn=spawn)
    ex.apply([_d("ingest", 0, 2)])
    liczba = len(spawn.calls)
    wynik = ex.apply([_d("ingest", 2, 2)])
    assert wynik == {"ingest": 2}
    assert len(spawn.calls) == liczba
    assert not any(w.terminated for w in spawn.workers)


def test_padniety_worker_nie_przewraca_executora():
    def _pada(queue):
        raise OSError("nie mozna uruchomic procesu")

    ex = PoolExecutor(CFG, spawn=_pada)
    assert ex.apply([_d("ingest", 0, 2)]) == {"ingest": 0}


def test_martwy_worker_jest_zastepowany():
    spawn = FakeSpawn()
    ex = PoolExecutor(CFG, spawn=spawn)
    ex.apply([_d("ingest", 0, 2)])
    spawn.workers[0].terminated = True  # proces sam sie zakonczyl
    assert ex.apply([_d("ingest", 1, 2)]) == {"ingest": 2}
    assert len(spawn.calls) == 3


def test_shutdown_zamyka_wszystkie():
    spawn = FakeSpawn()
    ex = PoolExecutor(CFG, spawn=spawn)
    ex.apply([_d("ingest", 0, 2), _d("gpu", 0, 1)])
    ex.shutdown()
    assert all(w.terminated for w in spawn.workers)
    assert ex.apply([]) == {}


def test_shutdown_znosi_blad_zamykania_workera():
    class Uparty(FakeWorker):
        def terminate(self):
            raise OSError("odmawia")

    ex = PoolExecutor(CFG, spawn=lambda q: Uparty(q))
    ex.apply([_d("ingest", 0, 1)])
    ex.shutdown()  # nie rzuca


def test_dry_run_nic_nie_startuje():
    spawn = FakeSpawn()
    ex = DryRunExecutor(CFG)
    wynik = ex.apply([_d("ingest", 1, 3)])
    assert wynik == {"ingest": 1}
    assert spawn.calls == []
    ex.shutdown()

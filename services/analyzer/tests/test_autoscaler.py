"""Testy autoskalera: petla decyzyjna, idle w Valkey, nadpisania operatora, HTTP /scaling.

Bez Dockera i bez Valkeya: backend i executor to atrapy.
"""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request

import pytest

from analyzer import autoscaler
from analyzer.autoscaler import Autoscaler
from analyzer.scaling import (
    GPU_QUEUE,
    DEFAULT_SCALING_CONFIG,
    QueueState,
    ScalingConfigError,
    apply_overrides,
    env_overrides,
    read_queue_states,
)

CFG = DEFAULT_SCALING_CONFIG


class FakeBackend:
    def __init__(self) -> None:
        self.kv: dict[str, str] = {}
        self.q = {"q:gpu": (0, 0), "q:ingest": (5, 1), "q:render": (0, 0)}
        self.finished = 0
        self.w = [
            {"id": "abc", "queue": "q:gpu", "state": "busy", "job": "j1", "since": "2026-11-22T10:00:00+00:00"}
        ]

    def backlog(self, queue):
        return self.q[queue][0]

    def running(self, queue):
        return self.q[queue][1]

    def workers(self, queue):
        return [w for w in self.w if w["queue"] == queue]

    def finished_since(self, queue, seconds):
        return self.finished

    def get(self, key):
        return self.kv.get(key)

    def set(self, key, value):
        self.kv[key] = value


class FakeExecutor:
    def __init__(self, count=1) -> None:
        self._count = count
        self.applied = []

    def count(self):
        return self._count

    def apply(self, decisions):
        self.applied.append(decisions)
        for d in decisions:
            self._count = d.desired
        return {d.queue: d.desired for d in decisions}

    def shutdown(self):
        pass


class Clock:
    def __init__(self, t=1000.0) -> None:
        self.t = t

    def __call__(self):
        return self.t


def _make(count=1):
    be, ex, clk = FakeBackend(), FakeExecutor(count), Clock()
    return Autoscaler(be, ex, CFG, clock=clk), be, ex, clk


# --- nazwy kolejek i idle ---------------------------------------------------


def test_domyslna_konfiguracja_uzywa_nazw_rq():
    assert set(CFG.queues) == {"q:ingest", "q:render", "q:gpu"}


def test_read_queue_states_uzywa_czytnika_idle():
    stany = read_queue_states(
        CFG, backlog_reader=lambda n: 0, worker_counter=lambda n: 1, idle_reader=lambda n: 42.0
    )
    assert all(s.idle_s == 42.0 for s in stany)


def test_scale_up_przy_backlogu_o_jeden_na_obieg_do_max():
    a, be, ex, _ = _make(count=1)
    be.q["q:gpu"] = (20, 1)
    seen = []
    for _ in range(6):
        a.tick()
        seen.append(ex._count)
    assert seen == [2, 3, 4, 4, 4, 4]  # max 4


def test_scale_down_dopiero_po_progu_bezczynnosci_i_o_jeden():
    a, be, ex, clk = _make(count=3)
    be.q["q:gpu"] = (0, 0)
    a.tick()  # pierwszy odczyt: ustawia znacznik, idle 0
    assert ex._count == 3
    clk.t += 59
    a.tick()
    assert ex._count == 3
    clk.t += 2  # 61 s od znacznika
    a.tick()
    assert ex._count == 2
    clk.t += 30  # histereza: znacznik zresetowany po zejsciu
    a.tick()
    assert ex._count == 2
    clk.t += 31
    a.tick()
    assert ex._count == 1
    clk.t += 500
    a.tick()
    assert ex._count == 1  # min 1


def test_niepusta_kolejka_resetuje_znacznik_idle():
    a, be, ex, clk = _make(count=2)
    be.q["q:gpu"] = (0, 1)  # zadanie w toku
    a.tick()
    assert be.kv["ops:idle:q:gpu"] == repr(clk.t)
    clk.t += 100
    a.tick()  # nadal running=1 -> brak zejscia
    assert ex._count == 2


def test_tick_nie_rzuca_gdy_backend_pada():
    a, be, ex, _ = _make()
    be.backlog = lambda q: (_ for _ in ()).throw(RuntimeError("valkey padl"))
    assert a.tick() == {}


# --- konfiguracja operatora -------------------------------------------------


def test_update_zapisuje_nadpisania_i_zmienia_konfiguracje_efektywna():
    a, be, ex, _ = _make()
    a.update({"queues": [{"name": "q:gpu", "max": 2, "cpus": 1.5, "memory_mb": 2048}]})
    assert json.loads(be.kv["ops:scaling"])["q:gpu"]["max"] == 2
    p = a.effective_config().queues["q:gpu"]
    assert (p.max_workers, p.cpus, p.memory_mb) == (2, 1.5, 2048)


def test_update_laczy_kolejne_zmiany():
    a, be, ex, _ = _make()
    a.update({"queues": [{"name": "q:gpu", "max": 2}]})
    a.update({"queues": [{"name": "q:gpu", "cpus": 3.0}]})
    p = a.effective_config().queues["q:gpu"]
    assert p.max_workers == 2 and p.cpus == 3.0


def test_update_max_powyzej_ollama_parallel_to_blad_422_i_nic_nie_zapisuje():
    a, be, ex, _ = _make()
    with pytest.raises(ScalingConfigError, match=r"max > OLLAMA_NUM_PARALLEL \(4\)"):
        a.update({"queues": [{"name": "q:gpu", "max": 5}]})
    assert "ops:scaling" not in be.kv


@pytest.mark.parametrize(
    "body",
    [
        None,
        {"queues": "x"},
        {"queues": [{"max": 2}]},
        {"queues": [{"name": "q:gpu", "max": "dwa"}]},
        {"queues": [{"name": "q:gpu", "min": 3, "max": 2}]},
        {"queues": [{"name": "q:ingest", "max": 2}]},
        {"queues": [{"name": "q:nieznana", "max": 2}]},
        {"queues": [{"name": "q:gpu", "bogus": 1}]},
    ],
)
def test_update_odrzuca_zle_dane(body):
    a, *_ = _make()
    with pytest.raises(ScalingConfigError):
        a.update(body)


def test_uszkodzone_ops_scaling_jest_pomijane():
    a, be, ex, _ = _make()
    be.kv["ops:scaling"] = "{nie json"
    assert a.effective_config() == CFG


def test_env_overrides_i_walidacja():
    over = env_overrides({"ANALYZER_MAX_REPLICAS": "3", "ANALYZER_EXTRA_CPUS": "1.5", "ANALYZER_MIN_REPLICAS": ""})
    assert over == {GPU_QUEUE: {"max": 3, "cpus": 1.5}}
    assert apply_overrides(CFG, over).queues[GPU_QUEUE].max_workers == 3
    with pytest.raises(ScalingConfigError):
        env_overrides({"ANALYZER_MAX_REPLICAS": "abc"})


# --- payload i HTTP -----------------------------------------------------------


def test_payload_ma_dokladny_kontrakt_z_ui():
    a, be, ex, _ = _make()
    be.q["q:gpu"] = (12, 2)
    be.finished = 10
    p = a.payload()
    assert set(p) == {"executor", "ollama_parallel", "queues", "workers", "throughput_per_min"}
    assert p["executor"] == "compose" and p["ollama_parallel"] == 4
    gpu = p["queues"][0]
    assert gpu == {
        "name": "q:gpu", "backlog": 12, "running": 2, "min": 1, "max": 4,
        "cpus": 2.0, "memory_mb": 3072, "scale_up_backlog": 3,
    }
    assert [q["name"] for q in p["queues"]] == ["q:gpu", "q:ingest", "q:render"]
    ingest = p["queues"][1]
    assert ingest["backlog"] == 5 and ingest["running"] == 1
    assert set(p["workers"][0]) == {"id", "queue", "state", "job", "since"}
    assert p["throughput_per_min"] == 2.0  # 10 zadan / 5 min
    json.dumps(p)


def test_payload_nie_pada_gdy_kolejka_nie_odpowiada():
    a, be, ex, _ = _make()
    be.backlog = lambda q: (_ for _ in ()).throw(RuntimeError("x"))
    p = a.payload()
    assert all(q["backlog"] == 0 for q in p["queues"])


@pytest.fixture()
def server():
    a, be, ex, clk = _make()
    srv = autoscaler.serve(a, port=0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield a, be, f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()
    srv.server_close()


def _req(method, url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def test_http_health(server):
    _, _, url = server
    assert _req("GET", url + "/health") == (200, {"ok": True})


def test_http_get_scaling(server):
    _, be, url = server
    be.q["q:gpu"] = (7, 1)
    status, body = _req("GET", url + "/scaling")
    assert status == 200 and body["queues"][0]["backlog"] == 7


def test_http_put_scaling_200_zwraca_pelny_payload(server):
    _, _, url = server
    status, body = _req("PUT", url + "/scaling", {"queues": [{"name": "q:gpu", "max": 2, "cpus": 1.0, "memory_mb": 1024}]})
    assert status == 200
    gpu = body["queues"][0]
    assert (gpu["max"], gpu["cpus"], gpu["memory_mb"]) == (2, 1.0, 1024)
    assert "workers" in body and "throughput_per_min" in body


def test_http_put_scaling_422_z_detail(server):
    _, _, url = server
    status, body = _req("PUT", url + "/scaling", {"queues": [{"name": "q:gpu", "max": 9}]})
    assert status == 422
    assert body == {"detail": "max > OLLAMA_NUM_PARALLEL (4)"}


def test_http_put_zly_json_to_422(server):
    _, _, url = server
    req = urllib.request.Request(url + "/scaling", data=b"{zle", method="PUT")
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(req, timeout=5)
    assert e.value.code == 422


def test_http_nieznana_sciezka_404(server):
    _, _, url = server
    assert _req("GET", url + "/nic")[0] == 404

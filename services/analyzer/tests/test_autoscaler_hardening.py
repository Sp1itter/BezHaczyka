"""Utwardzenie autoskalera (fix round 1): granice, busy-aware scale down, brak locka, Valkey down."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

import pytest

from analyzer.pool import LABEL_NUMBER, STOP_TIMEOUT_S, ComposeExecutor
from analyzer.scaling import ScalingConfigError, ScalingDecision
from tests.test_autoscaler import _make, server  # noqa: F401 (fixture)
from tests.test_compose_executor import FakeContainer, FakeDocker, _d

# --- granice -------------------------------------------------------------------


@pytest.mark.parametrize(
    "fields",
    [
        {"cpus": float("nan")},
        {"cpus": float("inf")},
        {"cpus": 0},
        {"cpus": 0.1},
        {"cpus": 9},
        {"cpus": 1e9},
        {"memory_mb": 0},
        {"memory_mb": 255},
        {"memory_mb": 16385},
        {"memory_mb": 10**9},
        {"min": 0},
        {"min": -1},
    ],
)
def test_update_odrzuca_wartosci_poza_granicami(fields):
    a, be, *_ = _make()
    with pytest.raises(ScalingConfigError):
        a.update({"queues": [{"name": "q:gpu", **fields}]})
    assert "ops:scaling" not in be.kv


def test_update_przyjmuje_wartosci_graniczne():
    a, *_ = _make()
    a.update({"queues": [{"name": "q:gpu", "cpus": 0.25, "memory_mb": 256}]})
    a.update({"queues": [{"name": "q:gpu", "cpus": 8, "memory_mb": 16384}]})


def test_nan_w_json_przez_http_to_422(server):  # noqa: F811
    _, _, url = server
    req = urllib.request.Request(url + "/scaling", data=b'{"queues":[{"name":"q:gpu","cpus":NaN}]}', method="PUT")
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(req, timeout=5)
    assert e.value.code == 422


# --- kolejki tylko do odczytu ----------------------------------------------------


def test_update_ignoruje_kolejki_tylko_do_odczytu():
    a, be, *_ = _make()
    a.update(a.payload())  # UI odsyla caly payload (cpus=None dla q:ingest)
    stored = json.loads(be.kv["ops:scaling"])
    assert "q:ingest" not in stored and "q:render" not in stored
    assert "q:gpu" in stored


# --- Valkey niedostepny ------------------------------------------------------------


def test_payload_bez_valkeya_jest_zdegradowany_a_nie_500():
    from redis.exceptions import ConnectionError as RedisConnectionError

    a, be, *_ = _make()

    def pada(*_a, **_k):
        raise RedisConnectionError("valkey padl")

    for n in ("get", "backlog", "running", "workers", "finished_since"):
        setattr(be, n, pada)
    p = a.payload()
    assert p["queues"][0]["max"] == 4 and p["queues"][0]["backlog"] == 0


# --- tick ------------------------------------------------------------------------------


def test_tick_przekazuje_id_zajetych_workerow_do_executora():
    a, be, ex, _ = _make(count=3)
    seen = {}

    def apply(decisions, busy_ids=()):
        seen["busy"] = set(busy_ids)
        return {}

    ex.apply = apply
    a.tick()
    assert seen["busy"] == {"abc"}  # FakeBackend: jeden worker busy


def test_apply_nie_trzyma_locka():
    a, be, ex, _ = _make(count=1)
    be.q["q:gpu"] = (20, 1)
    held = []

    def apply(decisions, busy_ids=()):
        got = a._lock.acquire(blocking=False)
        if got:
            a._lock.release()
        held.append(not got)
        return {}

    ex.apply = apply
    a.tick()
    assert held == [False]


# --- executor: busy-aware ----------------------------------------------------------


def _setup(extra):
    client = FakeDocker([])
    client.items.append(FakeContainer(client, 1))
    for n in extra:
        client.items.append(FakeContainer(client, n, autoscaled=True))
    for c in client.items:
        c.id = f"{int(c.labels[LABEL_NUMBER])}" * 64
    return client, ComposeExecutor(client, "iw", limits=lambda: (2.0, 3072))


def names(client):
    return [c.name for c in client.items]


def test_stop_timeout_180():
    assert STOP_TIMEOUT_S == 180


def test_scale_down_zdejmuje_bezczynny_zamiast_zajetego_o_wyzszym_numerze():
    client, ex = _setup((2, 3, 4))
    ex.apply([_d(3, current=4)], busy_ids={client.items[3].id[:12]})  # 4 zajety
    assert names(client) == ["iw-analyzer-1", "iw-analyzer-2", "iw-analyzer-4"]  # zszedl bezczynny 3


def test_zajete_zdejmowane_gdy_brak_bezczynnych_ale_nie_wiecej_niz_roznica():
    client, ex = _setup((2, 3))
    busy = {c.id[:12] for c in client.items}
    ex.apply([_d(2, current=3)], busy_ids=busy)
    assert names(client) == ["iw-analyzer-1", "iw-analyzer-2"]


def test_bez_busy_ids_zachowanie_jak_dawniej():
    client, ex = _setup((2, 3, 4))
    ex.apply([_d(3, current=4)])
    assert names(client) == ["iw-analyzer-1", "iw-analyzer-2", "iw-analyzer-3"]


def test_stop_uzywa_180_s():
    client, ex = _setup((2,))
    victim = client.items[1]
    ex.apply([ScalingDecision("q:gpu", 2, 1, "x", None)])
    assert victim.stopped_with == 180

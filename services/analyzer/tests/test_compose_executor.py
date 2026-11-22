"""ComposeExecutor z atrapa klienta Dockera (bez prawdziwego Dockera)."""

from __future__ import annotations

from analyzer.pool import (
    LABEL_AUTOSCALED,
    LABEL_NUMBER,
    LABEL_PROJECT,
    LABEL_SERVICE,
    ComposeExecutor,
    detect_project,
)
from analyzer.scaling import ScalingDecision


class FakeContainer:
    def __init__(self, client, number, project="iw", service="analyzer", autoscaled=False, status="running"):
        labels = {LABEL_PROJECT: project, LABEL_SERVICE: service, LABEL_NUMBER: str(number)}
        if autoscaled:
            labels[LABEL_AUTOSCALED] = "1"
        self.labels = labels
        self.status = status
        self.name = f"{project}-{service}-{number}"
        self.client = client
        self.stopped_with = None
        self.attrs = {
            "Config": {
                "Image": "iw-analyzer",
                "Cmd": ["python", "-m", "analyzer.worker"],
                "Entrypoint": None,
                "Env": ["VALKEY_URL=redis://valkey:6379/0"],
                "Labels": dict(labels),
                "Healthcheck": {"Test": ["CMD", "true"]},
                "User": "analyzer",
            },
            "HostConfig": {"ExtraHosts": ["host.docker.internal:host-gateway"]},
            "NetworkSettings": {"Networks": {"iw_default": {}}},
        }

    def stop(self, timeout=10):
        self.stopped_with = timeout
        self.status = "exited"

    def remove(self, force=False):
        self.client.items.remove(self)


class FakeContainers:
    def __init__(self, client):
        self.client = client
        self.run_calls = []

    def list(self, all=False, filters=None, _all=all):
        wanted = dict(x.split("=", 1) for x in filters["label"])
        return [
            c for c in self.client.items
            if all or c.status == "running"
            if _all(c.labels.get(k) == v for k, v in wanted.items())
        ]

    def run(self, **kw):
        self.run_calls.append(kw)
        labels = kw["labels"]
        c = FakeContainer(
            self.client, int(labels[LABEL_NUMBER]), labels[LABEL_PROJECT], labels[LABEL_SERVICE], autoscaled=True
        )
        self.client.items.append(c)
        return c

    def get(self, ident):
        for c in self.client.items:
            if c.name == ident:
                return c
        raise KeyError(ident)


class FakeDocker:
    def __init__(self, items):
        self.items = items
        self.containers = FakeContainers(self)


def _d(desired, current=1):
    return ScalingDecision("q:gpu", current, desired, "test", None)


def _setup(extra=()):
    client = FakeDocker([])
    client.items.append(FakeContainer(client, 1))
    for n in extra:
        client.items.append(FakeContainer(client, n, autoscaled=True))
    return client, ComposeExecutor(client, "iw", limits=lambda: (2.0, 3072), stop_timeout_s=30)


def test_scale_up_klonuje_z_limitami_i_etykietami():
    client, ex = _setup()
    assert ex.apply([_d(3)]) == {"q:gpu": 3}
    calls = client.containers.run_calls
    assert len(calls) == 2
    kw = calls[0]
    assert kw["image"] == "iw-analyzer" and kw["network"] == "iw_default"
    assert kw["nano_cpus"] == 2_000_000_000 and kw["mem_limit"] == "3072m"
    assert kw["labels"][LABEL_NUMBER] == "2" and kw["labels"][LABEL_AUTOSCALED] == "1"
    assert kw["labels"][LABEL_PROJECT] == "iw" and kw["labels"][LABEL_SERVICE] == "analyzer"
    assert kw["environment"] == ["VALKEY_URL=redis://valkey:6379/0"]
    assert kw["extra_hosts"] == ["host.docker.internal:host-gateway"]
    assert calls[1]["labels"][LABEL_NUMBER] == "3"


def test_bez_limitow_nie_ustawia_nano_cpus_ani_mem():
    client, _ = _setup()
    ex = ComposeExecutor(client, "iw", limits=lambda: (0.0, 0))
    ex.apply([_d(2)])
    kw = client.containers.run_calls[0]
    assert "nano_cpus" not in kw and "mem_limit" not in kw


def test_scale_down_zdejmuje_najwyzej_numerowanego_klona_z_sigterm_30s():
    client, ex = _setup(extra=(2, 3, 4))
    victim = client.items[-1]
    assert ex.apply([_d(3, current=4)]) == {"q:gpu": 3}
    assert victim.stopped_with == 30
    assert victim not in client.items
    assert {c.name for c in client.items} == {"iw-analyzer-1", "iw-analyzer-2", "iw-analyzer-3"}


def test_nigdy_nie_zdejmuje_bazowego_kontenera():
    client, ex = _setup(extra=(2,))
    assert ex.apply([_d(0, current=2)]) == {"q:gpu": 1}
    assert [c.name for c in client.items] == ["iw-analyzer-1"]


def test_nie_dotyka_kontenerow_innego_projektu_ani_serwisu():
    client, ex = _setup()
    cudzy = FakeContainer(client, 2, project="investwatch", autoscaled=True)
    inny_serwis = FakeContainer(client, 3, service="api", autoscaled=True)
    client.items.extend([cudzy, inny_serwis])
    ex.apply([_d(1, current=3)])
    assert cudzy in client.items and inny_serwis in client.items
    ex.apply([_d(2)])
    assert len(client.containers.run_calls) == 1
    assert client.containers.run_calls[0]["labels"][LABEL_PROJECT] == "iw"


def test_pomija_kolejki_inne_niz_gpu():
    client, ex = _setup()
    assert ex.apply([ScalingDecision("q:ingest", 1, 4, "x", None)]) == {}
    assert client.containers.run_calls == []


def test_sprzata_martwe_klony():
    client, ex = _setup()
    martwy = FakeContainer(client, 2, autoscaled=True, status="exited")
    client.items.append(martwy)
    ex.apply([_d(1)])
    assert martwy not in client.items


def test_awaria_dockera_nie_rzuca():
    client, ex = _setup()
    client.containers.run = lambda **kw: (_ for _ in ()).throw(RuntimeError("proxy 403"))
    assert ex.apply([_d(2)]) == {"q:gpu": 1}


def test_count_liczy_tylko_zywe():
    client, ex = _setup(extra=(2,))
    client.items.append(FakeContainer(client, 3, autoscaled=True, status="exited"))
    assert ex.count() == 2


def test_detect_project_z_etykiet_wlasnego_kontenera():
    client = FakeDocker([])
    me = FakeContainer(client, 1, project="moj", service="autoscaler")
    me.name = "abc123"
    client.items.append(me)
    assert detect_project(client, "abc123", fallback="x") == "moj"
    assert detect_project(client, "brak", fallback="fb") == "fb"

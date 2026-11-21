"""Testy warstwy crawlera: rotacja UA/proxy, limiter, circuit breaker, dedup.

Bez sieci (httpx.MockTransport, atrapy stron) i bez Valkey (FakeRedis ponizej,
z wlasnym zegarem — TTL bez realnego czekania). Adresy wylacznie *.example.invalid.
"""

from __future__ import annotations

from itertools import pairwise

import httpx
import pytest

import jobs
import net
from net import Rotator
from sources import www as www_mod
from sources.base import SourceBlocked, SourceError
from sources.facebook import FacebookAdsSource, FacebookConfig
from sources.meta_json import canonical_ad_url
from sources.www import WebPageSource
from sources.youtube import YouTubeSource
from state import CircuitBreaker, RateLimiter, SeenSet

BASE = "https://crawl.example.invalid"
PROXIES = ["http://proxy1.example.invalid:3128", "http://proxy2.example.invalid:3128"]


class FakeClock:
    def __init__(self) -> None:
        self.t = 1000.0
        self.slept: list[float] = []

    def __call__(self) -> float:
        return self.t

    def sleep(self, s: float) -> None:
        self.slept.append(s)
        self.t += s


class FakeRedis:
    """Podzbior API redis-py uzywany przez state.py; TTL liczony wg FakeClock."""

    def __init__(self, clock: FakeClock) -> None:
        self.clock = clock
        self.data: dict[str, object] = {}
        self.exp: dict[str, float] = {}

    def _alive(self, key: str) -> bool:
        if key in self.exp and self.clock() >= self.exp[key]:
            self.data.pop(key, None)
            self.exp.pop(key, None)
        return key in self.data

    def set(self, key, value, nx=False, px=None, ex=None):
        if nx and self._alive(key):
            return None
        self.data[key] = value
        self.exp.pop(key, None)
        if px is not None:
            self.exp[key] = self.clock() + px / 1000
        if ex is not None:
            self.exp[key] = self.clock() + ex
        return True

    def pttl(self, key):
        if not self._alive(key):
            return -2
        if key not in self.exp:
            return -1
        return int((self.exp[key] - self.clock()) * 1000)

    def exists(self, key):
        return int(self._alive(key))

    def incr(self, key):
        value = int(self.data[key]) + 1 if self._alive(key) else 1
        self.data[key] = value
        return value

    def expire(self, key, seconds):
        if self._alive(key):
            self.exp[key] = self.clock() + seconds
            return True
        return False

    def delete(self, *keys):
        n = 0
        for k in keys:
            if self._alive(k):
                n += 1
            self.data.pop(k, None)
            self.exp.pop(k, None)
        return n

    def sadd(self, key, *members):
        if not self._alive(key):
            self.data[key] = set()
        s = self.data[key]
        added = sum(1 for m in members if m not in s)
        s.update(members)
        return added


# --------------------------------------------------------------------------- #
# Rotacja User-Agent i proxy
# --------------------------------------------------------------------------- #


def test_rotator_from_env_rotates_ua_and_proxy_per_call(monkeypatch):
    env = {"SCRAPER_USER_AGENTS": "UA-A || UA-B", "SCRAPER_PROXIES": " || ".join(PROXIES)}
    rot = Rotator.from_env(env)
    picks = iter([0, 1, 1, 0])
    monkeypatch.setattr(net.random, "choice", lambda seq: seq[next(picks)])
    assert [rot.user_agent(), rot.user_agent()] == ["UA-A", "UA-B"]
    assert [rot.proxy(), rot.proxy()] == [PROXIES[1], PROXIES[0]]


def test_rotator_copies_input_lists():
    uas = ["UA-A"]
    rot = Rotator(uas, list(PROXIES))
    uas.append("UA-ZMIANA")
    assert {rot.user_agent() for _ in range(50)} == {"UA-A"}


def test_www_sends_rotated_ua_and_proxy_per_request(monkeypatch):
    """Bez wstrzyknietego klienta WebPageSource tworzy httpx.Client z proxy z rotatora."""
    proxies_used: list[str | None] = []
    uas_seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        uas_seen.append(request.headers["User-Agent"])
        return httpx.Response(200, text="<html><title>t</title><body>tresc</body></html>",
                              headers={"content-type": "text/html"})

    real_client = httpx.Client

    def fake_client(**kw):
        proxies_used.append(kw.get("proxy"))
        return real_client(transport=httpx.MockTransport(handler))

    monkeypatch.setattr(www_mod.httpx, "Client", fake_client)
    src = WebPageSource(rotator=Rotator(["UA-1", "UA-2"], list(PROXIES)), respect_robots=False)
    for i in range(40):
        src.fetch(f"{BASE}/strona-{i}")
    assert set(proxies_used) == set(PROXIES)
    assert set(uas_seen) == {"UA-1", "UA-2"}


def test_www_direct_connection_without_proxies(monkeypatch):
    proxies_used: list[str | None] = []
    real_client = httpx.Client

    def fake_client(**kw):
        proxies_used.append(kw.get("proxy"))
        return real_client(transport=httpx.MockTransport(lambda r: httpx.Response(200, text="<p>x</p>")))

    monkeypatch.setattr(www_mod.httpx, "Client", fake_client)
    WebPageSource(rotator=Rotator(["UA"], []), respect_robots=False).fetch(f"{BASE}/a")
    assert proxies_used == [None]


def test_youtube_options_use_rotator():
    dictionary = [{"type": "company", "value": "Firma Testowa"}]
    yt = YouTubeSource(dictionary, rotator=Rotator(["UA-YT"], [PROXIES[0]]))
    opts = yt._ydl_options()
    assert opts["http_headers"]["User-Agent"] == "UA-YT"
    assert opts["proxy"] == PROXIES[0]
    assert "proxy" not in YouTubeSource(dictionary, rotator=Rotator(["UA-YT"], []))._ydl_options()


# --------------------------------------------------------------------------- #
# Limiter (minimalny odstep) — bez realnego sleep
# --------------------------------------------------------------------------- #


def test_limiter_memory_enforces_min_interval():
    clock = FakeClock()
    lim = RateLimiter(3, sleep=clock.sleep, clock=clock)
    stamps = []
    for _ in range(4):
        lim.acquire()
        stamps.append(clock.t)
    assert all(b - a >= 3 for a, b in pairwise(stamps))
    assert clock.slept == [3, 3, 3]


def test_limiter_no_wait_when_interval_already_passed():
    clock = FakeClock()
    lim = RateLimiter(3, sleep=clock.sleep, clock=clock)
    lim.acquire()
    clock.t += 10
    lim.acquire()
    assert clock.slept == []


def test_limiter_zero_interval_never_sleeps():
    clock = FakeClock()
    lim = RateLimiter(0, sleep=clock.sleep, clock=clock)
    for _ in range(5):
        lim.acquire()
    assert clock.slept == []


def test_limiter_redis_shared_between_workers():
    """Dwa limitery (dwa workery) na wspolnym Valkey — drugi czeka na TTL klucza."""
    clock = FakeClock()
    redis = FakeRedis(clock)
    a = RateLimiter(2, redis=redis, key="t:rl", sleep=clock.sleep, clock=clock)
    b = RateLimiter(2, redis=redis, key="t:rl", sleep=clock.sleep, clock=clock)
    a.acquire()
    assert clock.slept == []
    b.acquire()
    assert sum(clock.slept) == pytest.approx(2.0)
    assert redis.pttl("t:rl") == 2000


# --------------------------------------------------------------------------- #
# Circuit breaker — reakcja na blokade
# --------------------------------------------------------------------------- #


def test_breaker_redis_opens_after_threshold_and_closes_after_cooldown():
    clock = FakeClock()
    redis = FakeRedis(clock)
    br = CircuitBreaker(threshold=2, window_s=600, cooldown_s=1800, redis=redis, prefix="t:br")
    br.record_failure()
    assert not br.is_open()
    br.record_failure()
    assert br.is_open()
    assert not redis.exists("t:br:failures")
    clock.t += 1799
    assert br.is_open()
    clock.t += 2
    assert not br.is_open()


def test_breaker_redis_window_and_success_reset():
    clock = FakeClock()
    redis = FakeRedis(clock)
    br = CircuitBreaker(threshold=2, window_s=600, cooldown_s=1800, redis=redis, prefix="t:br")
    br.record_failure()
    clock.t += 601  # licznik wygasa z oknem
    br.record_failure()
    assert not br.is_open()
    br.record_success()
    br.record_failure()
    assert not br.is_open()


def test_breaker_shared_between_workers_via_redis():
    clock = FakeClock()
    redis = FakeRedis(clock)
    w1 = CircuitBreaker(threshold=2, redis=redis, prefix="t:br")
    w2 = CircuitBreaker(threshold=2, redis=redis, prefix="t:br")
    w1.record_failure()
    w2.record_failure()
    assert w1.is_open() and w2.is_open()


class FakePage:
    def __init__(self, url: str, text: str = "") -> None:
        self.url = url
        self.text = text

    def evaluate(self, _script):
        return self.text


@pytest.mark.parametrize(
    "url,text",
    [
        (f"{BASE}/checkpoint/?next=x", ""),
        (f"{BASE}/login/?next=x", ""),
        (f"{BASE}/ads/library/", "Zostales tymczasowo zablokowany"),
        (f"{BASE}/ads/library/", "Security check\nPlease solve this CAPTCHA to continue"),
        (f"{BASE}/ads/library/", "We detected unusual activity"),
    ],
)
def test_facebook_detects_block_pages(url, text):
    with pytest.raises(SourceBlocked):
        FacebookAdsSource._raise_if_blocked(FakePage(url, text), deep=True)


def test_facebook_normal_page_is_not_block():
    FacebookAdsSource._raise_if_blocked(FakePage(f"{BASE}/ads/library/", "Biblioteka reklam"), deep=True)


def _fb(breaker: CircuitBreaker) -> FacebookAdsSource:
    return FacebookAdsSource(config=FacebookConfig(mode="live"), store=object(), breaker=breaker,
                             limiter=RateLimiter(0))


def test_facebook_block_opens_breaker_and_stops_live_requests():
    clock = FakeClock()
    br = CircuitBreaker(threshold=2, cooldown_s=1800, clock=clock)
    src = _fb(br)
    calls = []

    def blocked(query, *a):
        calls.append(query)
        raise SourceBlocked("checkpoint")

    src._discover_nodes_live = blocked
    for _ in range(2):
        with pytest.raises(SourceBlocked):
            src.discover("fraza")
    assert br.is_open() and len(calls) == 2
    with pytest.raises(SourceBlocked):
        src.discover("fraza")
    with pytest.raises(SourceBlocked):
        src.discover_nodes("fraza")
    assert len(calls) == 2  # przy otwartym breakerze zero ruchu do platformy

    clock.t += 1801
    src._discover_nodes_live = lambda q, *a: {"1234567890123": {"ad_archive_id": "1234567890123"}}
    assert src.discover("fraza") == [canonical_ad_url("1234567890123")]
    assert not br.is_open()


def test_facebook_generic_error_does_not_open_breaker():
    clock = FakeClock()
    br = CircuitBreaker(threshold=1, clock=clock)
    src = _fb(br)

    def broken(*a):
        raise RuntimeError("timeout")

    src._discover_nodes_live = broken
    with pytest.raises(SourceError) as e:
        src.discover("fraza")
    assert not isinstance(e.value, SourceBlocked)
    assert not br.is_open()


@pytest.mark.parametrize("status", [403, 429])
def test_www_block_statuses_raise_source_blocked(status):
    client = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(status, text="")))
    src = WebPageSource(rotator=Rotator(["UA"], []), client=client, respect_robots=False)
    with pytest.raises(SourceBlocked):
        src.fetch(f"{BASE}/x")


# --------------------------------------------------------------------------- #
# Dedup (seen)
# --------------------------------------------------------------------------- #


def test_seen_set_redis_dedup():
    redis = FakeRedis(FakeClock())
    a = SeenSet(redis=redis, key="t:seen")
    b = SeenSet(redis=redis, key="t:seen")  # drugi worker / wznowienie
    assert a.add(f"{BASE}/1")
    assert not a.add(f"{BASE}/1")
    assert not b.add(f"{BASE}/1")
    assert b.add(f"{BASE}/2")


class FakeQueue:
    enqueued: list[tuple]

    def __init__(self, name, connection=None) -> None:
        self.name = name

    def enqueue(self, func, *args, **kwargs):
        FakeQueue.enqueued.append((self.name, args, kwargs))


class ListSource:
    def __init__(self, urls: list[str]) -> None:
        self.urls = urls

    def discover(self, query):
        return list(self.urls)


@pytest.fixture
def discover_env(monkeypatch):
    import rq

    redis = FakeRedis(FakeClock())
    FakeQueue.enqueued = []
    monkeypatch.setattr(rq, "Queue", FakeQueue)
    monkeypatch.setattr(jobs, "_redis", lambda: redis)
    return monkeypatch


def test_discover_job_enqueues_each_url_once(discover_env):
    urls = [f"{BASE}/a", f"{BASE}/b", f"{BASE}/a"]
    discover_env.setattr(jobs, "build_source", lambda *a, **k: ListSource(urls))
    assert jobs.discover_job("www", BASE) == 2
    assert jobs.discover_job("www", BASE) == 0  # drugi przebieg: nic nowego
    assert [args[1] for _, args, _ in FakeQueue.enqueued] == [f"{BASE}/a", f"{BASE}/b"]
    job_ids = [kw["job_id"] for _, _, kw in FakeQueue.enqueued]
    assert len(set(job_ids)) == 2


def test_discover_job_facebook_dedups_by_ad_id(discover_env):
    urls = [canonical_ad_url("1111111111111"), canonical_ad_url("1111111111111") + "&country=PL", canonical_ad_url("2222222222222")]
    discover_env.setattr(jobs, "build_source", lambda *a, **k: ListSource(urls))
    assert jobs.discover_job("facebook", "fraza") == 2


def test_discover_job_seen_is_per_source(discover_env):
    discover_env.setattr(jobs, "build_source", lambda *a, **k: ListSource([f"{BASE}/a"]))
    assert jobs.discover_job("www", BASE) == 1
    assert jobs.discover_job("youtube", BASE) == 1

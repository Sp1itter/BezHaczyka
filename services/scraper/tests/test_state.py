from __future__ import annotations

from state import CircuitBreaker, NodeCache, RateLimiter, SeenSet


class FakeClock:
    def __init__(self) -> None:
        self.t = 0.0
        self.slept: list[float] = []

    def __call__(self) -> float:
        return self.t

    def sleep(self, s: float) -> None:
        self.slept.append(s)
        self.t += s


def test_rate_limiter_spaces_requests():
    clock = FakeClock()
    lim = RateLimiter(5, sleep=clock.sleep, clock=clock)
    lim.acquire()
    lim.acquire()
    clock.t += 2
    lim.acquire()
    assert clock.slept == [5, 3]


def test_breaker_opens_after_threshold_and_closes_after_cooldown():
    clock = FakeClock()
    br = CircuitBreaker(threshold=2, window_s=600, cooldown_s=1800, clock=clock)
    br.record_failure()
    assert not br.is_open()
    br.record_failure()
    assert br.is_open()
    clock.t += 1801
    assert not br.is_open()


def test_breaker_window_forgets_old_failures():
    clock = FakeClock()
    br = CircuitBreaker(threshold=2, window_s=600, clock=clock)
    br.record_failure()
    clock.t += 601
    br.record_failure()
    assert not br.is_open()


def test_success_resets_failures():
    br = CircuitBreaker(threshold=2)
    br.record_failure()
    br.record_success()
    br.record_failure()
    assert not br.is_open()


def test_seen_set_and_node_cache_in_memory():
    seen = SeenSet()
    assert seen.add("1") and not seen.add("1")
    cache = NodeCache()
    cache["1"] = {"a": 1}
    assert cache["1"] == {"a": 1} and list(cache) == ["1"] and len(cache) == 1

"""Stan wspoldzielony miedzy workerami RQ: limiter, circuit breaker, cache, dedup.

Kazda klasa dziala w dwoch trybach:
  * `redis=<klient>` — Valkey, wspolny dla wszystkich workerow `q:ingest` (n=4)
    i `q:render` (n=2). Limiter MUSI byc globalny: cztery workery z osobnymi
    limiterami to czterokrotnie wiekszy ruch do Meta z jednego IP.
  * `redis=None` — w pamieci procesu (testy, uruchomienie lokalne).

Lekcja z kevinzg/facebook-scraper (README: „If you scrape too much, Facebook
might temporarily ban your IP"): ban jest stanem, nie wyjatkiem do ponowienia.
Stad circuit breaker zamiast retry w petli.
"""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Callable, Iterator, MutableMapping
from typing import Any


class RateLimiter:
    """Minimalny odstep miedzy zapytaniami do platformy (globalnie)."""

    def __init__(
        self,
        min_interval_s: float,
        redis: Any = None,
        key: str = "fb:ratelimit",
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.min_interval_s = max(0.0, min_interval_s)
        self.redis = redis
        self.key = key
        self._sleep = sleep
        self._clock = clock
        self._lock = threading.Lock()
        self._last: float | None = None

    def acquire(self) -> None:
        if self.min_interval_s <= 0:
            return
        if self.redis is not None:
            ms = int(self.min_interval_s * 1000)
            while not self.redis.set(self.key, "1", nx=True, px=ms):
                ttl = self.redis.pttl(self.key)
                self._sleep(max(ttl if ttl and ttl > 0 else 50, 50) / 1000)
            return
        with self._lock:
            now = self._clock()
            if self._last is not None:
                wait = self._last + self.min_interval_s - now
                if wait > 0:
                    self._sleep(wait)
                    now = self._clock()
            self._last = now


class CircuitBreaker:
    """Po `threshold` blokadach w oknie `window_s` zrodlo jest wylaczone na `cooldown_s`."""

    def __init__(
        self,
        threshold: int = 2,
        window_s: float = 600,
        cooldown_s: float = 1800,
        redis: Any = None,
        prefix: str = "fb:breaker",
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.threshold = threshold
        self.window_s = window_s
        self.cooldown_s = cooldown_s
        self.redis = redis
        self.prefix = prefix
        self._clock = clock
        self._failures: list[float] = []
        self._open_until = 0.0

    def is_open(self) -> bool:
        if self.redis is not None:
            return bool(self.redis.exists(f"{self.prefix}:open"))
        return self._clock() < self._open_until

    def record_failure(self) -> None:
        if self.redis is not None:
            key = f"{self.prefix}:failures"
            count = self.redis.incr(key)
            if count == 1:
                self.redis.expire(key, int(self.window_s))
            if count >= self.threshold:
                self.redis.set(f"{self.prefix}:open", "1", ex=int(self.cooldown_s))
                self.redis.delete(key)
            return
        now = self._clock()
        self._failures = [t for t in self._failures if now - t < self.window_s] + [now]
        if len(self._failures) >= self.threshold:
            self._open_until = now + self.cooldown_s
            self._failures.clear()

    def record_success(self) -> None:
        if self.redis is not None:
            self.redis.delete(f"{self.prefix}:failures")
            return
        self._failures.clear()


class NodeCache(MutableMapping[str, dict]):
    """Surowe wezly reklam z discover() dla fetch() (Valkey `fb:meta:<id>`, TTL).

    Cache wewnatrz serwisu — kontrakt `Source` (discover zwraca tylko URL-e)
    zostaje nienaruszony.
    """

    def __init__(self, redis: Any = None, prefix: str = "fb:meta", ttl_s: int = 86400) -> None:
        self.redis = redis
        self.prefix = prefix
        self.ttl_s = ttl_s
        self._mem: dict[str, dict] = {}

    def _k(self, key: str) -> str:
        return f"{self.prefix}:{key}"

    def __getitem__(self, key: str) -> dict:
        if self.redis is None:
            return self._mem[key]
        raw = self.redis.get(self._k(key))
        if raw is None:
            raise KeyError(key)
        return json.loads(raw)

    def __setitem__(self, key: str, value: dict) -> None:
        if self.redis is None:
            self._mem[key] = value
        else:
            self.redis.set(self._k(key), json.dumps(value, ensure_ascii=False), ex=self.ttl_s)

    def __delitem__(self, key: str) -> None:
        if self.redis is None:
            del self._mem[key]
        else:
            self.redis.delete(self._k(key))

    def __iter__(self) -> Iterator[str]:
        if self.redis is None:
            return iter(list(self._mem))
        n = len(self.prefix) + 1
        return (k.decode()[n:] if isinstance(k, bytes) else k[n:] for k in self.redis.scan_iter(f"{self.prefix}:*"))

    def __len__(self) -> int:
        return sum(1 for _ in self)


class SeenSet:
    """Dedup na poziomie `ad_archive_id` (Valkey SET `fb:seen`) — wznowienie po przerwie."""

    def __init__(self, redis: Any = None, key: str = "fb:seen") -> None:
        self.redis = redis
        self.key = key
        self._mem: set[str] = set()

    def add(self, item: str) -> bool:
        """True, jesli element jest nowy."""
        if self.redis is None:
            if item in self._mem:
                return False
            self._mem.add(item)
            return True
        return bool(self.redis.sadd(self.key, item))

    def contains(self, item: str) -> bool:
        if self.redis is None:
            return item in self._mem
        return bool(self.redis.sismember(self.key, item))

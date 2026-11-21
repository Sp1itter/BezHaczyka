"""Wspolna rotacja User-Agent i proxy dla wszystkich zrodel (facebook, youtube, www).

Konfiguracja z `.env`: `SCRAPER_USER_AGENTS` i `SCRAPER_PROXIES` (separator `||`);
`SCRAPER_PROXY` (pojedyncze) zostaje jako zgodny wstecz fallback. Pusta lista proxy
oznacza ruch bezposredni. Losowanie, nie round-robin: workery RQ sa niezalezne,
a wspolny licznik wymagalby Valkey bez realnej korzysci.
"""

from __future__ import annotations

import os
import random
from collections.abc import Mapping

SEPARATOR = "||"
ACCEPT_LANGUAGE = "pl-PL,pl;q=0.9,en;q=0.5"

DEFAULT_USER_AGENTS: list[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:142.0) Gecko/20100101 Firefox/142.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:142.0) Gecko/20100101 Firefox/142.0",
]


def _split(raw: str) -> list[str]:
    return [p.strip() for p in raw.split(SEPARATOR) if p.strip()]


def user_agents(env: Mapping[str, str] = os.environ) -> list[str]:
    return _split(env.get("SCRAPER_USER_AGENTS", "")) or list(DEFAULT_USER_AGENTS)


def proxies(env: Mapping[str, str] = os.environ) -> list[str]:
    found = _split(env.get("SCRAPER_PROXIES", ""))
    if found:
        return found
    single = env.get("SCRAPER_PROXY", "").strip()
    return [single] if single else []


class Rotator:
    """Losuje User-Agent i proxy; wspolny dla wszystkich zrodel."""

    def __init__(self, user_agents: list[str] | None = None, proxies: list[str] | None = None) -> None:
        self._user_agents = list(user_agents) if user_agents else list(DEFAULT_USER_AGENTS)
        self._proxies = list(proxies or [])

    @classmethod
    def from_env(cls, env: Mapping[str, str] = os.environ) -> Rotator:
        return cls(user_agents(env), proxies(env))

    @property
    def has_proxies(self) -> bool:
        return bool(self._proxies)

    def user_agent(self) -> str:
        return random.choice(self._user_agents)

    def proxy(self) -> str | None:
        return random.choice(self._proxies) if self._proxies else None

    def headers(self) -> dict[str, str]:
        return {"User-Agent": self.user_agent(), "Accept-Language": ACCEPT_LANGUAGE}

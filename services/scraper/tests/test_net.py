# compliance:allow-file - testowe adresy w danych wejsciowych (ruch sieciowy zamockowany)
from __future__ import annotations

import net
from net import Rotator


def test_user_agents_from_env_and_default():
    assert net.user_agents({"SCRAPER_USER_AGENTS": "A || B ||"}) == ["A", "B"]
    defaults = net.user_agents({})
    assert len(defaults) == 5 and all(u.startswith("Mozilla/5.0") for u in defaults)
    assert net.user_agents({"SCRAPER_USER_AGENTS": "  "}) == defaults


def test_proxies_list_fallback_and_empty():
    assert net.proxies({"SCRAPER_PROXIES": "http://127.0.0.1:3128||http://127.0.0.2:3128"}) == ["http://127.0.0.1:3128", "http://127.0.0.2:3128"]
    assert net.proxies({"SCRAPER_PROXY": "http://127.0.0.3:3128"}) == ["http://127.0.0.3:3128"]
    assert net.proxies({"SCRAPER_PROXIES": "http://127.0.0.1:3128", "SCRAPER_PROXY": "http://127.0.0.3:3128"}) == ["http://127.0.0.1:3128"]
    assert net.proxies({}) == []


def test_rotator_picks_from_lists():
    r = Rotator(["UA1", "UA2"], ["p1", "p2"])
    assert {r.user_agent() for _ in range(100)} == {"UA1", "UA2"}
    assert {r.proxy() for _ in range(100)} == {"p1", "p2"}
    assert r.has_proxies


def test_rotator_without_proxy_and_headers():
    r = Rotator(["UA"], [])
    assert r.proxy() is None and not r.has_proxies
    assert r.headers() == {"User-Agent": "UA", "Accept-Language": "pl-PL,pl;q=0.9,en;q=0.5"}
    assert Rotator().user_agent() in net.DEFAULT_USER_AGENTS


def test_from_env():
    r = Rotator.from_env({"SCRAPER_USER_AGENTS": "X", "SCRAPER_PROXIES": "http://p:1"})
    assert r.user_agent() == "X" and r.proxy() == "http://p:1"

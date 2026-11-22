"""Jedna przegladarka Chromium na proces workera (zamiast startu Chromium dla kazdej reklamy).

Wlaczane przez `SCRAPER_SHARED_BROWSER=1` (ustawia je worker.py dla procesow SimpleWorker).
Izolacja reklam zostaje: kazde pobranie dostaje WLASNY `browser.new_context()` (bez cookies),
zamykany po zadaniu. Przegladarka jest odnawiana po `SCRAPER_BROWSER_RECYCLE` uzyciach
(domyslnie 100) albo gdy sie rozlaczy (crash), zeby nie kumulowac wyciekow pamieci.
"""

from __future__ import annotations

import atexit
import contextlib
import logging
import os
import threading
from collections.abc import Iterator
from typing import Any

log = logging.getLogger("scraper.browser")

_lock = threading.RLock()
_state: dict[str, Any] = {"pw": None, "browser": None, "key": None, "uses": 0}


def enabled() -> bool:
    return os.getenv("SCRAPER_SHARED_BROWSER", "0") == "1"


def _close() -> None:
    browser, pw = _state["browser"], _state["pw"]
    _state.update(browser=None, pw=None, key=None, uses=0)
    with contextlib.suppress(Exception):
        if browser is not None:
            browser.close()
    with contextlib.suppress(Exception):
        if pw is not None:
            pw.stop()


atexit.register(_close)


def _get(launch: dict[str, Any]) -> Any:
    from playwright.sync_api import sync_playwright

    key = repr(sorted(launch.items()))
    recycle = int(os.getenv("SCRAPER_BROWSER_RECYCLE", "100"))
    browser = _state["browser"]
    if browser is not None and (_state["key"] != key or _state["uses"] >= recycle or not browser.is_connected()):
        log.info("odnawiam wspolna przegladarke (uzycia=%d)", _state["uses"])
        _close()
        browser = None
    if browser is None:
        pw = sync_playwright().start()
        try:
            browser = pw.chromium.launch(**launch)
        except Exception:
            pw.stop()
            raise
        _state.update(pw=pw, browser=browser, key=key, uses=0)
        log.info("wspolna przegladarka uruchomiona (pid procesu %d)", os.getpid())
    _state["uses"] += 1
    return browser


@contextlib.contextmanager
def shared_browser(launch: dict[str, Any]) -> Iterator[Any]:
    """Przegladarka wspolna dla procesu. Blad w trakcie uzycia -> przy nastepnym wywolaniu nowa."""
    with _lock:
        browser = _get(launch)
        try:
            yield browser
        except BaseException as exc:
            from sources.base import SourceError

            # SourceError = czysty blad zrodla (np. brak kreacji). Cokolwiek innego, zwlaszcza
            # JobTimeoutException z SIGALRM w srodku wywolania Playwrighta, zostawia sync API
            # w niepewnym stanie: bezpieczniej zaczac nastepne zadanie od nowej przegladarki.
            if not isinstance(exc, SourceError) or not browser.is_connected():
                _close()
            raise


def reset() -> None:
    with _lock:
        _close()

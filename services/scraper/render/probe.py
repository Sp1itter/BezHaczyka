"""RenderProbe — cienka warstwa Pythona nad render/probe.js.

Interfejs celowo waski (`run_probe(page, scope_selector)`), zeby osoba A mogla
podmienic implementacje sondy bez ruszania zrodel danych.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from contracts import ViewportProbe

_HERE = Path(__file__).resolve().parent
PROBE_JS = (_HERE / "probe.js").read_text(encoding="utf-8")
NEUTRALIZE_JS = (_HERE / "neutralize.js").read_text(encoding="utf-8")
FREEZE_JS = (_HERE / "freeze.js").read_text(encoding="utf-8")
MARK_CREATIVE_JS = (_HERE / "creative.js").read_text(encoding="utf-8")

# Trzy viewporty z par. 6.2. Tablet jest MIERZONY w RenderProbe, ale nie trafia
# do AdDocument.screenshots (kontrakt par. 6.1: tylko desktop i mobile).
VIEWPORTS: dict[str, tuple[int, int]] = {
    "desktop": (1920, 1080),
    "tablet": (768, 1024),
    "mobile": (390, 844),
}
SCREENSHOT_VIEWPORTS: dict[str, str] = {"desktop": "1920", "mobile": "390"}

CHROMIUM_ARGS = ["--disable-gpu"]


def run_probe(page: Any, scope_selector: str | None = None, max_nodes: int = 400) -> ViewportProbe | None:
    """Sonda geometrii jednego viewportu. None, gdy scope_selector nic nie trafil."""
    result = page.evaluate(PROBE_JS, {"scopeSelector": scope_selector, "maxNodes": max_nodes})
    return ViewportProbe.model_validate(result) if result else None


def neutralize_overlays(page: Any, keep_selector: str | None) -> list[str]:
    """Usuwa nakladki logowania/cookies bez klikania. Zwraca ich rodzaje."""
    return list(page.evaluate(NEUTRALIZE_JS, {"keepSelector": keep_selector}) or [])


@dataclass
class NavigationGuard:
    """Blokada nawigacji (par. 6.2.1).

    Faza 1 (ladowanie): przepuszczamy nawigacje ramki glownej tylko pod
    `allowed_prefix` — Meta przekierowuje `?id=` na wariant z parametrami
    strony reklamodawcy, wiec jedno sztywne URL nie wystarczy.
    Faza 2 (`lock()`, na czas sondowania): KAZDA nawigacja jest przerywana.
    Nawigacje w ramkach podrzednych (iframe'y sledzace) przerywamy zawsze.
    Strumienie wideo (`media`) tez — nie sa potrzebne do sondy ani zrzutu,
    a mp4 pobieramy osobno z bezposredniego URL-a.

    Zadania, ktore przepuszczamy, ida przez `route.fallback()`, zeby trafily do
    wczesniej zarejestrowanych tras (odtwarzanie HAR / fixture).
    """

    allowed_prefix: str
    locked: bool = False
    blocked: list[str] = field(default_factory=list)
    _page: Any = None

    def install(self, page: Any) -> NavigationGuard:
        self._page = page
        page.route("**/*", self._handle)
        return self

    def lock(self) -> None:
        self.locked = True

    def _handle(self, route: Any) -> None:
        req = route.request
        if req.resource_type == "media":
            route.abort()
            return
        if req.is_navigation_request():
            main = self._page is not None and req.frame == self._page.main_frame
            if not main or self.locked or not req.url.startswith(self.allowed_prefix):
                self.blocked.append(req.url)
                # NIE route.abort(): przerwana nawigacja ramki glownej podmienia
                # dokument na chrome-error://chromewebdata/ i sonda traci strone.
                # HTTP 204 dla nawigacji = przegladarka zostaje na obecnym dokumencie.
                route.fulfill(status=204, body="")
                return
        route.fallback()

"""LocalCorpusSource — deterministyczny korpus demo z fixtures/demo-ads/*.html.

Plan 24 h, blok T+1: pierwsze zrodlo osoby A. Strony sa pisane recznie, kazda
lamie inny wymog (etykiety w <nazwa>.labels.json), wiec demo dziala offline
i zawsze tak samo (design doc par. 10).

URL-e:
  * bez DEMO_CORPUS_BASE_URL — `file:///.../demo-001.html` (testy, praca lokalna),
  * z DEMO_CORPUS_BASE_URL=http://nginx — strony serwowane przez nginx z compose.

Id dokumentu zalezy od NAZWY pliku, nie od URL-a, wiec ta sama strona
z file:// i z nginx daje ten sam AdDocument.id.
"""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

from contracts import AdDocument, RenderProbe, ViewportProbe
from render.probe import CHROMIUM_ARGS, SCREENSHOT_VIEWPORTS, VIEWPORTS, run_probe
from sources.base import SourceError
from storage import BlobStore, LocalBlobStore

DEFAULT_CORPUS = Path(__file__).resolve().parents[3] / "fixtures" / "demo-ads"
MAX_SCROLL_STEPS = 10  # par. 6.2.1: przewiniecie przed sonda, zeby doladowac lazy content


class LocalCorpusSource:
    name = "web"

    def __init__(self, corpus_dir: Path | None = None, store: BlobStore | None = None,
                 base_url: str | None = None, nav_timeout_s: float = 15.0) -> None:
        self.corpus_dir = Path(corpus_dir or os.getenv("DEMO_CORPUS_DIR", DEFAULT_CORPUS))
        self.store = store or LocalBlobStore("data/blobs")
        self.base_url = (base_url if base_url is not None else os.getenv("DEMO_CORPUS_BASE_URL", "")).rstrip("/")
        self.nav_timeout_s = nav_timeout_s

    # ------------------------------------------------------------- discover --

    def pages(self) -> list[Path]:
        return sorted(self.corpus_dir.glob("demo-*.html"))

    def discover(self, query: str = "") -> list[str]:
        """URL-e stron korpusu. `query` filtruje po nazwie pliku (pusty = wszystkie)."""
        out = []
        for page in self.pages():
            if query and query.lower() not in page.stem.lower():
                continue
            out.append(f"{self.base_url}/{page.name}" if self.base_url else page.resolve().as_uri())
        return out

    # ---------------------------------------------------------------- fetch --

    @staticmethod
    def _page_name(url: str) -> str:
        return Path(urlparse(url).path).name

    def fetch(self, url: str) -> AdDocument:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import sync_playwright

        name = self._page_name(url)
        if not name.endswith(".html"):
            raise SourceError(f"to nie jest strona korpusu demo: {url}")
        doc_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"investwatch:demo-ads/{name}"))
        probes: dict[str, ViewportProbe] = {}
        shots: dict[str, str] = {}
        html_path = title = None
        text = ""

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True, args=CHROMIUM_ARGS)
            try:
                for vp, (width, height) in VIEWPORTS.items():
                    ctx = browser.new_context(viewport={"width": width, "height": height}, locale="pl-PL")
                    try:
                        page = ctx.new_page()
                        try:
                            page.goto(url, wait_until="load", timeout=self.nav_timeout_s * 1000)
                        except PlaywrightError as exc:
                            raise SourceError(f"nie udalo sie otworzyc {url}: {exc}") from exc
                        self._scroll_to_bottom(page)
                        probe = run_probe(page, None)
                        if probe is not None:
                            probes[vp] = probe
                        if vp == "desktop":
                            html = page.content()
                            html_path = self.store.put("raw", f"{doc_id}.html", html.encode("utf-8"),
                                                       "text/html; charset=utf-8")
                            title = page.evaluate("() => (document.querySelector('h1') || {}).innerText || document.title")
                            text = page.evaluate("() => document.body.innerText")
                        if vp in SCREENSHOT_VIEWPORTS:
                            key = f"{doc_id}-{SCREENSHOT_VIEWPORTS[vp]}.png"
                            shots[vp] = self.store.put("shots", key, page.screenshot(full_page=True), "image/png")
                    finally:
                        ctx.close()
            finally:
                browser.close()

        return AdDocument(
            id=doc_id,
            source=self.name,
            url=url,
            fetched_at=datetime.now(UTC),
            lang="pl",
            title=(title or "").strip() or None,
            text="\n".join(line.strip() for line in text.splitlines() if line.strip()),
            html_path=html_path,
            screenshots=shots,
            render_probe=RenderProbe(viewports=probes) if probes else None,
        )

    @staticmethod
    def _scroll_to_bottom(page) -> None:
        for _ in range(MAX_SCROLL_STEPS):
            at_bottom = page.evaluate(
                "() => { window.scrollBy(0, window.innerHeight);"
                " return window.innerHeight + window.scrollY >= document.body.scrollHeight - 1; }"
            )
            if at_bottom:
                break
        page.evaluate("() => window.scrollTo(0, 0)")

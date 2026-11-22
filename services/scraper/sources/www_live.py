"""LiveWebSource (`www_live`) — prawdziwy internet dla Modulu 3 (shadow advisory) i M2.

  discover(fraza)  wyszukiwarka (ddgs, region pl-pl, bez platnego API) -> URL-e po filtrze:
                   bez szumu (encyklopedie, media spolecznosciowe, urzedy, uczelnie), bez domen
                   firm z rejestru KNF (to materialy M2 z wlasnych kanalow) i bez plikow binarnych.
  fetch(url)       curl_cffi (odcisk TLS Chrome) -> trafilatura (tresc glowna, tytul, serwis),
                   linki zewnetrzne dopisane na koncu (resolver widzi linki afiliacyjne/komunikatory).
                   Gdy tresc wyglada na oferte finansowa (`is_candidate`): Playwright, RenderProbe
                   w 3 viewportach i zrzuty desktop/mobile -> reguly DET 4-8 i 13 poza Facebookiem.

Grzecznosc: robots.txt (cache w Valkey 24 h), limiter per domena we wspolnym Valkey.
"""

from __future__ import annotations

import contextlib
import logging
import os
import re
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urldefrag, urljoin, urlsplit
from urllib.robotparser import RobotFileParser

from contracts import AdDocument, Publisher, RenderProbe, ViewportProbe
from net import Rotator
from storage import BlobStore

from sources.base import SourceBlocked, SourceError, SourceGone
from sources.www import BINARY_EXT, MAX_BYTES, _Page

log = logging.getLogger("scraper.www_live")

TIMEOUT_S = 15
RESULTS_PER_QUERY = 20
DEFAULT_QUERIES = (
    "doradztwo inwestycyjne", "family office", "zarządzanie majątkiem", "sygnały giełdowe",
    "portfel modelowy", "konsultacje inwestycyjne", "wealth management Polska",
)
NOISE_DOMAINS = frozenset({
    "wikipedia.org", "youtube.com", "facebook.com", "instagram.com", "linkedin.com", "x.com", "twitter.com",
    "tiktok.com", "reddit.com", "gov.pl", "edu.pl", "europa.eu", "gpw.pl", "pracuj.pl", "olx.pl",
    "allegro.pl", "amazon.com", "google.com", "goworking.pl", "indeed.com", "glassdoor.com",
})
NOISE_TLD_LABELS = ("uw.edu.pl", ".edu", ".gov")
_CANDIDATE_RE = re.compile(
    r"\b(?:inwest\w*|portfel\w*|sygna\w*\s+(?:giełd|trans|kup)\w*|rekomendac\w*|doradztw\w*|doradc\w*|"
    r"konsultac\w*|majątk\w*|kapitał\w*|zysk\w*|stop\w*\s+zwrotu|akcj[ie]|obligacj\w*|forex|kryptowalut\w*|"
    r"wealth|trading|abonament\w*|subskrypc\w*)",
    re.IGNORECASE,
)
MIN_SIGNALS = 3
# Warianty frazy: ddgs zwraca ~10 wynikow na zapytanie, warianty daja nowe domeny (oferty, cenniki, miasta).
DEFAULT_SUFFIXES = ("", "oferta", "cennik", "opinie", "Warszawa", "Kraków")


def host_of(url: str) -> str:
    return (urlsplit(url).hostname or "").lower().removeprefix("www.")


def _on(host: str, domain: str) -> bool:
    return host == domain or host.endswith("." + domain)


def keep_url(url: str, registry_domains: set[str]) -> bool:
    """Czy URL z wyszukiwarki warto pobrac."""
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        return False
    if any(parts.path.lower().endswith(ext) for ext in BINARY_EXT):
        return False
    host = host_of(url)
    if any(_on(host, d) for d in NOISE_DOMAINS) or any(host.endswith(s) for s in NOISE_TLD_LABELS):
        return False
    return not any(_on(host, d) for d in registry_domains)


def is_candidate(text: str) -> bool:
    """Tresc wyglada na oferte inwestycyjna (wtedy robimy kosztowny render + RenderProbe)."""
    return len({m.group(0).lower()[:6] for m in _CANDIDATE_RE.finditer(text or "")}) >= MIN_SIGNALS


def ddgs_search(query: str, max_results: int) -> list[str]:
    from ddgs import DDGS
    from ddgs.exceptions import DDGSException

    try:
        results = DDGS(timeout=TIMEOUT_S).text(query, region="pl-pl", safesearch="off", max_results=max_results)
    except DDGSException as exc:
        if "no results" in str(exc).lower():
            return []
        raise
    return [r["href"] for r in results or [] if r.get("href")]


def _curl_session() -> Any:
    from curl_cffi import requests as curl_requests

    return curl_requests.Session(impersonate="chrome", timeout=TIMEOUT_S)


class LiveWebSource:
    name = "www_live"

    def __init__(
        self,
        *,
        search: Callable[[str, int], list[str]] = ddgs_search,
        session: Any = None,
        store: BlobStore | None = None,
        registry_domains: set[str] | None = None,
        render: bool | None = None,
        respect_robots: bool = True,
        redis: Any = None,
        rotator: Rotator | None = None,
        results_per_query: int = RESULTS_PER_QUERY,
        suffixes: tuple[str, ...] | None = None,
    ) -> None:
        self.search = search
        self._session = session
        self.store = store
        self.registry_domains = registry_domains or set()
        self.render = (os.getenv("WWW_RENDER", "1") == "1") if render is None else render
        self.respect_robots = respect_robots
        self.redis = redis
        self.rotator = rotator or Rotator.from_env()
        self.results_per_query = results_per_query
        if suffixes is None:
            env = os.getenv("WWW_QUERY_SUFFIXES")
            suffixes = tuple(x.strip() for x in env.split(",")) if env is not None else DEFAULT_SUFFIXES
        self.suffixes = suffixes or ("",)
        self._robots: dict[str, RobotFileParser | None] = {}
        self.last_meta: dict[str, Any] = {}

    # ------------------------------------------------------------- siec --

    @property
    def session(self) -> Any:
        if self._session is None:
            self._session = _curl_session()
        return self._session

    def _wait_domain(self, host: str) -> None:
        if self.redis is None:
            return
        from state import RateLimiter

        RateLimiter(float(os.getenv("WWW_DOMAIN_INTERVAL_S", "1")), redis=self.redis, key=f"www:rl:{host}").acquire()

    def _get(self, url: str) -> Any:
        self._wait_domain(host_of(url))
        kwargs: dict[str, Any] = {"allow_redirects": True}
        proxy = self.rotator.proxy()
        if proxy:
            kwargs["proxies"] = {"http": proxy, "https": proxy}
        try:
            response = self.session.get(url, **kwargs)
        except Exception as exc:  # noqa: BLE001 — curl_cffi rzuca wlasne wyjatki sieciowe
            raise SourceError(f"blad pobierania {url}: {exc}") from exc
        status = response.status_code
        if status in (404, 410):
            raise SourceGone(f"{status}: {url}")
        if status in (403, 429, 503):
            raise SourceBlocked(f"{status} (blokada/limit): {url}")
        if status >= 400:
            raise SourceError(f"HTTP {status}: {url}")
        if len(response.content or b"") > MAX_BYTES:
            raise SourceError(f"odpowiedz ponad {MAX_BYTES} B: {url}")
        return response

    def _robots_parser(self, origin: str) -> RobotFileParser | None:
        if origin in self._robots:
            return self._robots[origin]
        body: str | None = None
        key = f"www:robots:{origin}"
        if self.redis is not None:
            cached = self.redis.get(key)
            if cached is not None:
                body = cached.decode() if isinstance(cached, bytes) else cached
        if body is None:
            try:
                body = self._get(origin + "/robots.txt").text
            except SourceError:
                body = ""  # brak robots / blad = wolno
            if self.redis is not None:
                self.redis.set(key, body, ex=86400)
        parser: RobotFileParser | None = None
        if body.strip():
            parser = RobotFileParser()
            parser.parse(body.splitlines())
        self._robots[origin] = parser
        return parser

    def _allowed(self, url: str) -> bool:
        if not self.respect_robots:
            return True
        parts = urlsplit(url)
        parser = self._robots_parser(f"{parts.scheme}://{parts.netloc}")
        return True if parser is None else parser.can_fetch("*", url)

    # -------------------------------------------------------- interfejs --

    def discover(self, query: str) -> list[str]:
        found: list[str] = []
        errors = []
        for suffix in self.suffixes:
            q = f"{query} {suffix}".strip()
            try:
                found += self.search(q, self.results_per_query)
            except Exception as exc:  # noqa: BLE001 — jeden wariant nie blokuje reszty
                errors.append(exc)
        if errors and not found:
            raise SourceError(f"wyszukiwarka: {query!r}: {errors[0]}") from errors[0]
        urls: dict[str, None] = {}
        for url in found:
            url = urldefrag(url)[0]
            if keep_url(url, self.registry_domains):
                urls.setdefault(url)
        log.info("www_live: discover(%r) -> %d z %d", query, len(urls), len(found))
        return list(urls)

    def fetch(self, url: str) -> AdDocument:
        url = urldefrag(url)[0]
        if not self._allowed(url):
            raise SourceGone(f"robots.txt zabrania: {url}")  # trwale: nie ponawiamy
        response = self._get(url)
        html = response.text
        final_url = urldefrag(str(getattr(response, "url", "") or url))[0]
        page = _Page()
        page.feed(html)
        text, title, site = self._extract(html, url)
        text = text or page.text
        title = title or (page.meta.get("og:title") or page.title).strip() or None

        domain = host_of(final_url)
        external: dict[str, None] = {}
        for href in page.links:
            link = urldefrag(urljoin(final_url, href))[0]
            if link.startswith(("http://", "https://")) and host_of(link) != domain:
                external.setdefault(link)
        if external:
            text += "\n\nLinki zewnetrzne:\n" + "\n".join(list(external)[:60])

        doc_id = str(uuid.uuid5(uuid.NAMESPACE_URL, url))
        html_path = self.store.put("raw", f"{doc_id}.html", html.encode("utf-8", "replace"),
                                   "text/html; charset=utf-8") if self.store else None
        candidate = is_candidate(text)
        probes: dict[str, ViewportProbe] = {}
        shots: dict[str, str] = {}
        if self.render and candidate:
            try:
                probes, shots = self._render(url, doc_id)
            except Exception as exc:  # noqa: BLE001 — brak renderu nie blokuje analizy tekstu
                log.warning("www_live %s: render nieudany (%s) — tylko tekst", url, exc)
        self.last_meta = {"candidate": candidate, "final_url": final_url,
                          "render": "ok" if probes else ("skipped" if not candidate else "missing")}
        return AdDocument(
            id=doc_id,
            source=self.name,
            url=url,
            fetched_at=datetime.now(UTC),
            publisher=Publisher(handle=domain, display_name=site or domain,
                                profile_url=f"{urlsplit(final_url).scheme}://{urlsplit(final_url).netloc}"),
            lang=(page.meta.get("og:locale") or "pl")[:2].lower(),
            title=re.sub(r"\s+", " ", title) if title else None,
            text=text,
            html_path=html_path,
            screenshots=shots,
            render_probe=RenderProbe(viewports=probes) if probes else None,
        )

    # ------------------------------------------------------------ pomocnicze --

    @staticmethod
    def _extract(html: str, url: str) -> tuple[str, str | None, str | None]:
        try:
            import trafilatura

            text = trafilatura.extract(html, url=url, favor_recall=True, include_comments=False,
                                       include_tables=True, deduplicate=True) or ""
            meta = trafilatura.extract_metadata(html, default_url=url)
        except Exception:  # noqa: BLE001
            return "", None, None
        return text.strip(), (meta.title if meta else None), (meta.sitename if meta else None)

    def _render(self, url: str, doc_id: str) -> tuple[dict[str, ViewportProbe], dict[str, str]]:
        from render import browser_pool
        from render.probe import CHROMIUM_ARGS, SCREENSHOT_VIEWPORTS, VIEWPORTS, neutralize_overlays, run_probe

        launch = {"headless": True, "args": CHROMIUM_ARGS}
        probes: dict[str, ViewportProbe] = {}
        shots: dict[str, str] = {}

        @contextlib.contextmanager
        def browser_cm():
            if browser_pool.enabled():
                with browser_pool.shared_browser(launch) as b:
                    yield b
                return
            from playwright.sync_api import sync_playwright

            with sync_playwright() as pw:
                b = pw.chromium.launch(**launch)
                try:
                    yield b
                finally:
                    b.close()

        first = next(iter(VIEWPORTS))
        width, height = VIEWPORTS[first]
        with browser_cm() as browser:
            ctx = browser.new_context(viewport={"width": width, "height": height}, locale="pl-PL",
                                      user_agent=self.rotator.user_agent())
            try:
                ctx.route("**/*", lambda r: r.abort() if r.request.resource_type == "media" else r.continue_())
                page = ctx.new_page()
                page.goto(url, wait_until="domcontentloaded", timeout=25_000)
                with contextlib.suppress(Exception):
                    page.wait_for_load_state("networkidle", timeout=5_000)
                for vp, (w, h) in VIEWPORTS.items():
                    if vp != first:
                        page.set_viewport_size({"width": w, "height": h})
                        page.wait_for_timeout(300)
                    neutralize_overlays(page, None)
                    probe = run_probe(page, "body")
                    if probe is not None:
                        probes[vp] = probe
                    if vp in SCREENSHOT_VIEWPORTS and self.store is not None:
                        shots[vp] = self.store.put("shots", f"{doc_id}-{SCREENSHOT_VIEWPORTS[vp]}.png",
                                                   page.screenshot(full_page=False), "image/png")
            finally:
                ctx.close()
        return probes, shots

"""WebPageSource — dowolne strony WWW (blogi finfluencerow, landing page'e).

`discover(seed_url)` zwraca strone startowa i linki z tej samej domeny; `fetch(url)`
zwraca widoczny tekst, a linki zewnetrzne dopisuje na koncu (resolver widzi dzieki
temu linki afiliacyjne). Szanuje robots.txt, limit rozmiaru i timeout; rotacja UA/proxy
przez `net.Rotator`.
"""

from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime
from html.parser import HTMLParser
from urllib.parse import urldefrag, urljoin, urlsplit
from urllib.robotparser import RobotFileParser

import httpx
from contracts import AdDocument, Publisher
from net import Rotator
from storage import BlobStore

from sources.base import SourceBlocked, SourceError, SourceGone

TIMEOUT_S = 20.0
MAX_BYTES = 2 * 1024 * 1024
BINARY_EXT = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".ico", ".pdf", ".zip", ".gz", ".rar", ".7z",
    ".mp3", ".mp4", ".avi", ".mov", ".webm", ".wav", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".css", ".js", ".json", ".xml", ".woff", ".woff2", ".ttf", ".exe", ".dmg", ".apk",
}
SKIP_TAGS = {"script", "style", "noscript", "template", "svg"}
BLOCK_TAGS = {"p", "div", "section", "article", "li", "ul", "ol", "br", "h1", "h2", "h3", "h4", "h5", "h6",
              "tr", "table", "header", "footer", "main", "nav", "blockquote", "pre", "hr", "form"}


class _Page(HTMLParser):
    """Jednoprzebiegowy parser: tytul, meta og:*, widoczny tekst z akapitami, linki."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.meta: dict[str, str] = {}
        self.links: list[str] = []
        self._chunks: list[str] = []
        self._skip = 0
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k: v or "" for k, v in attrs}
        if tag == "meta" and (key := a.get("property") or a.get("name")):
            self.meta.setdefault(key.lower(), a.get("content", ""))
        elif tag == "a" and a.get("href"):
            self.links.append(a["href"].strip())
        if tag == "title":
            self._in_title = True
        if tag in SKIP_TAGS:
            self._skip += 1
        elif tag in BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        if tag in SKIP_TAGS:
            self._skip = max(0, self._skip - 1)
        elif tag in BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data
        elif not self._skip:
            self._chunks.append(data)

    @property
    def text(self) -> str:
        lines = (re.sub(r"[ \t\r\f\v\xa0]+", " ", line).strip() for line in "".join(self._chunks).split("\n"))
        return re.sub(r"\n{2,}", "\n\n", "\n".join(lines)).strip()


def _origin(url: str) -> str:
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}"


def _is_page_link(url: str) -> bool:
    parts = urlsplit(url)
    return parts.scheme in ("http", "https") and bool(parts.netloc) and not any(parts.path.lower().endswith(e) for e in BINARY_EXT)


class WebPageSource:
    name = "www"

    def __init__(
        self,
        *,
        rotator: Rotator | None = None,
        store: BlobStore | None = None,
        max_pages: int = 20,
        respect_robots: bool = True,
        client: httpx.Client | None = None,
    ) -> None:
        self.rotator = rotator or Rotator.from_env()
        self.store = store
        self.max_pages = max_pages
        self.respect_robots = respect_robots
        self._client = client  # wstrzykiwany w testach (httpx.MockTransport)
        self._robots: dict[str, RobotFileParser | None] = {}

    # ------------------------------------------------------------- siec --

    def _get(self, url: str) -> httpx.Response:
        proxy = self.rotator.proxy()
        try:
            if self._client is not None:
                response = self._client.get(url, headers=self.rotator.headers())
            else:
                with httpx.Client(timeout=TIMEOUT_S, follow_redirects=True, proxy=proxy) as client:
                    response = self._stream(client, url)
        except httpx.HTTPError as exc:
            raise SourceError(f"blad pobierania {url}: {exc}") from exc
        if response.status_code in (404, 410):
            raise SourceGone(f"{response.status_code}: {url}")
        if response.status_code in (403, 429):
            raise SourceBlocked(f"{response.status_code} (blokada/limit): {url}")
        if response.status_code >= 400:
            raise SourceError(f"HTTP {response.status_code}: {url}")
        if len(response.content) > MAX_BYTES:
            raise SourceError(f"odpowiedz ponad {MAX_BYTES} B: {url}")
        return response

    def _stream(self, client: httpx.Client, url: str) -> httpx.Response:
        """Czyta odpowiedz strumieniowo i przerywa po przekroczeniu limitu rozmiaru."""
        with client.stream("GET", url, headers=self.rotator.headers()) as response:
            body = bytearray()
            for chunk in response.iter_bytes():
                body += chunk
                if len(body) > MAX_BYTES:
                    break
            return httpx.Response(response.status_code, headers=response.headers, content=bytes(body), request=response.request)

    def _allowed(self, url: str) -> bool:
        if not self.respect_robots:
            return True
        origin = _origin(url)
        if origin not in self._robots:
            parser: RobotFileParser | None = RobotFileParser()
            try:
                response = self._get(origin + "/robots.txt")
                parser.parse(response.text.splitlines())  # type: ignore[union-attr]
            except SourceError:
                parser = None  # blad pobrania robots = pozwalamy
            self._robots[origin] = parser
        parser = self._robots[origin]
        return True if parser is None else parser.can_fetch("*", url)

    # -------------------------------------------------------- interfejs --

    def discover(self, seed_url: str) -> list[str]:
        seed = urldefrag(seed_url)[0]
        if not _is_page_link(seed):
            raise SourceError(f"zly URL startowy: {seed_url}")
        page = _Page()
        page.feed(self._get(seed).text)
        domain = urlsplit(seed).netloc.lower()
        urls: dict[str, None] = {seed: None}
        for href in page.links:
            url = urldefrag(urljoin(seed, href))[0]
            if _is_page_link(url) and urlsplit(url).netloc.lower() == domain:
                urls.setdefault(url)
            if len(urls) >= self.max_pages:
                break
        return [u for u in urls if self._allowed(u)]

    def fetch(self, url: str) -> AdDocument:
        url = urldefrag(url)[0]
        if not _is_page_link(url):
            raise SourceError(f"zly URL: {url}")
        if not self._allowed(url):
            raise SourceError(f"robots.txt zabrania: {url}")
        response = self._get(url)
        html = response.text
        page = _Page()
        page.feed(html)

        domain = urlsplit(url).netloc.lower()
        external: dict[str, None] = {}
        for href in page.links:
            link = urldefrag(urljoin(url, href))[0]
            if link.startswith(("http://", "https://")) and urlsplit(link).netloc.lower() != domain:
                external.setdefault(link)
        text = page.text
        if external:
            text += "\n\nLinki zewnetrzne:\n" + "\n".join(external)

        doc_id = str(uuid.uuid5(uuid.NAMESPACE_URL, url))
        html_path = None
        if self.store is not None:
            html_path = self.store.put("html", f"{doc_id}.html", response.content, "text/html; charset=utf-8")
        title = (page.meta.get("og:title") or page.title).strip() or None
        return AdDocument(
            id=doc_id,
            source=self.name,
            url=url,
            fetched_at=datetime.now(UTC),
            publisher=Publisher(handle=domain, display_name=page.meta.get("og:site_name", "").strip() or domain,
                                profile_url=_origin(url)),
            lang=(page.meta.get("og:locale") or "pl")[:2].lower(),
            title=re.sub(r"\s+", " ", title) if title else None,
            text=text,
            html_path=html_path,
        )

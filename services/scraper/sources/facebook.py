"""FacebookAdsSource — reklamy z Meta Ad Library (Facebook/Instagram), rynek PL.

Decyzje (Faza 1, zaakceptowane):
  * discover(): natywny Playwright, bez zadnej biblioteki scrapujacej.
    Wezly reklam zbieramy z inline JSON dokumentu (pierwsza strona wynikow)
    oraz z odpowiedzi `/api/graphql/` (kolejne strony) przez page.on("response").
  * fetch(): widok pojedynczej reklamy `?id=<ad_archive_id>`. Meta pokazuje ja
    w role="dialog" nad lista reklam strony; scope_root sondy to kontener
    kreacji wewnatrz tego dialogu.
  * Tekst z JSON-a (kompletny, bez ucinania „Zobacz wiecej"), geometria z DOM.
  * Zero logowania, cookies sesyjnych, fingerprintingu i captcha (design doc par. 2,
    Nie-cele). User-Agent i proxy losowane NA KONTEKST przez `net.Rotator`
    (`SCRAPER_USER_AGENTS`, `SCRAPER_PROXIES`), wspolnie z pozostalymi zrodlami.

Tryby (`FB_MODE`):
  * `live`   — tylko siec,
  * `replay` — tylko korpus offline `fixtures/demo-ads/facebook/<ad_archive_id>/`,
  * `auto`   — siec, a przy blokadzie / bledzie / otwartym breakerze korpus.
"""

from __future__ import annotations

import contextlib
import gzip
import json
import logging
import os
import re
import time
import uuid
from collections.abc import Iterator, MutableMapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from contracts import AdDocument, MediaItem, Publisher, RenderProbe, ViewportProbe
from net import Rotator
from render.probe import (
    CHROMIUM_ARGS,
    MARK_CREATIVE_JS,
    SCREENSHOT_VIEWPORTS,
    VIEWPORTS,
    NavigationGuard,
    neutralize_overlays,
    run_probe,
)
from sources.base import SourceBlocked, SourceError
from sources.meta_json import (
    AD_LIBRARY_URL,
    ad_id_from_url,
    ad_text,
    ad_title,
    ads_from_graphql,
    ads_from_html,
    canonical_ad_url,
    has_video,
    merge_nodes,
    primary_body,
    publisher_from,
    search_url,
    video_urls,
)
from state import CircuitBreaker, NodeCache, RateLimiter
from storage import BlobStore, LocalBlobStore

log = logging.getLogger("scraper.facebook")

# Kreacja reklamodawcy wewnatrz dialogu „Link do reklamy". Wyszukuje ja i oznacza
# render/creative.js (data-testid kontenera istnieje TYLKO w reklamach DCO —
# ustalone na zywo 21.11.2026), a sonda i zrzuty uzywaja tego oznaczenia.
CREATIVE_TESTID = "ad-library-dynamic-content-container"
SCOPE_SELECTOR = '[data-iw-creative="1"]'
DIALOG_SELECTOR = '[role="dialog"]:has([data-iw-creative="1"])'

# Sygnaly blokady sprawdzane TYLKO gdy nie znalezlismy karty / wynikow —
# inaczej tekst samej reklamy mogl by wywolac falszywy alarm.
_BLOCK_URL_MARKERS = ("/checkpoint", "/login")
_BLOCK_TEXT_MARKERS = (
    "tymczasowo zablokowan",
    "temporarily blocked",
    "nietypową aktywność",
    "unusual activity",
    "zaloguj się, aby kontynuować",
    "log in to continue",
    "you must log in",
    "captcha",
)

DEFAULT_FIXTURES = Path(__file__).resolve().parents[3] / "fixtures" / "demo-ads" / "facebook"

# --------------------------------------------------------------------------- #
# Reguly 5, 7, 8 — decyzje zespolu dla zrodla facebook (konsumuje rules_det)
# --------------------------------------------------------------------------- #

PLATFORM_TYPOGRAPHY_REASON = "typografia platformy (Meta Ad Library)"
PLATFORM_TYPOGRAPHY_RULES = frozenset({"4", "5", "8"})
FEED_FOLD_CHARS = 125

# FRAZY OSTRZEGAWCZE, nie samo slowo „ryzyko". Golym `ryzyk\w*` zlapalismy na
# nagraniu pytanie retoryczne „Czy inwestuja w ryzykowne aktywa?" — falszywy
# alarm R7 dokladnie tego rodzaju, przed ktorym ostrzega par. 6.2.1.
_RISK_RE = re.compile(
    r"\bryzyk\w*\s+(?:utraty|straty|inwestycyjn\w*|inwestowania|związan\w*|kursow\w*|walutow\w*)"
    r"|\b(?:wiąż\w*\s+się|obarczon\w*|niesie|niosą)\s+(?:\w+\s+){0,2}?ryzyk\w*"
    r"|\butrat\w*\s+(?:\w+\s+){0,2}?(?:kapitał\w*|środk\w*|pieniędzy|inwestycji|części|całości)"
    r"|\bnie\s+gwarantuj\w*"
    r"|\brachunk\w*\s+inwestorów\s+detalicznych"
    r"|\bwyniki\s+(?:historyczne|osiągnięte\s+w\s+przeszłości)\s+nie"
    r"|\b(?:capital\s+at\s+risk|lose\s+money|losing\s+money|risk\s+warning|involves?\s+(?:a\s+)?(?:high\s+)?risk)\b",
    re.IGNORECASE,
)
# Koniec zdania: [.!?] przed wielka litera / cyfra / koncem tekstu albo nowa linia,
# zeby „np.", „m.in.", „tj." w srodku zdania nie ucinaly cytatu.
_SENTENCE_END_RE = re.compile(r"[.!?](?=\s+[A-ZĄĆĘŁŃÓŚŹŻ0-9]|\s*$)|\n")


def platform_rule_override(rule_id: str, source: str) -> tuple[str, str] | None:
    """Werdykt narzucony dla regul 4, 5 i 8 przy zrodle `facebook`.

    W Ad Library CALY tekst w DOM (takze wewnatrz kreacji) jest skladany
    typografia Meta — rozmiar fontu, kolor i lamanie wierszy nie sa decyzja
    reklamodawcy. Tekst, ktory reklamodawca naprawde kontroluje, jest WTOPIONY
    w grafike/wideo i nie istnieje w DOM. Dlatego reguly 4 (rozmiar czcionki),
    5 (kontrast) i 8 (RWD) zwracaja `not_applicable` z powodem, a nie `pass`
    czy `fail` — i NIE wchodza do mianownika scoringu (par. 9).
    Tekst na grafice/wideo i tak ma `background_confidence: "unknown"`
    (krok 3b RenderProbe), wiec niezaleznie od tego regula 5 nie da `fail`.

    Zwraca (verdict, reason) albo None, gdy regula liczy sie normalnie.
    """
    if source == "facebook" and str(rule_id) in PLATFORM_TYPOGRAPHY_RULES:
        return ("not_applicable", PLATFORM_TYPOGRAPHY_REASON)
    return None


@dataclass(frozen=True)
class FeedFoldEvidence:
    """Dowod HYBRID dla reguly 7 — NIE jest to twardy werdykt DET.

    W feedzie Meta tresc glowna jest ucinana po ok. 125 znakach przyciskiem
    „Zobacz wiecej". Ostrzezenie zaczynajace sie dalej jest dla realnego
    odbiorcy prawdopodobnie ukryte za kliknieciem.
    """

    risk_offset_chars: int
    fold_chars: int
    beyond_fold: bool
    quote: str

    def measured(self) -> dict[str, float]:
        """Postac dla `Evidence.measured` (dict[str, float])."""
        return {
            "risk_offset_chars": float(self.risk_offset_chars),
            "fold_chars": float(self.fold_chars),
            "beyond_fold": 1.0 if self.beyond_fold else 0.0,
        }


def feed_fold_evidence(body: str | None, fold_chars: int = FEED_FOLD_CHARS) -> FeedFoldEvidence | None:
    """Pozycja pierwszego ostrzezenia o ryzyku w tresci glownej reklamy.

    `body` = tresc glowna. Dla zrodla facebook `AdDocument.text` zaczyna sie od
    tresci glownej (patrz `meta_json.ad_text`), wiec mozna podac `doc.text`.
    None, gdy w tresci nie ma zadnej frazy o ryzyku (wtedy regula 7 opiera sie
    na innych dowodach — brak ostrzezenia to sprawa regul LLM).
    """
    if not body:
        return None
    match = _RISK_RE.search(body)
    if not match:
        return None
    start = max((m.end() for m in _SENTENCE_END_RE.finditer(body, 0, match.start())), default=0)
    nxt = _SENTENCE_END_RE.search(body, match.end())
    end = nxt.end() if nxt else len(body)
    return FeedFoldEvidence(
        risk_offset_chars=match.start(),
        fold_chars=fold_chars,
        beyond_fold=match.start() > fold_chars,
        quote=body[start:end].strip(),
    )


def collect_ads_from_dom(page: Any, sink: dict[str, dict], timeout_s: float, poll_ms: int = 700) -> int:
    """Czeka, az w DOM pojawi sie inline JSON z reklamami, i dokleja je do `sink`.

    Ustalone na zywo: Meta po `goto` wykonuje PRAWDZIWA nawigacje na
    skanonizowany URL wyszukiwania (dokleja `sort_data`, `is_targeted_country`),
    a wyniki trafiaja do DOM ok. 2 s pozniej. Pojedyncze `page.content()` po
    stalym odczekaniu widzialo strone posrednia (0 reklam) albo rzucalo
    „page is navigating". Dlatego polling z tolerancja na nawigacje w toku.
    Zwraca liczbe nowych wezlow; konczy tez, gdy GraphQL juz cos dostarczyl.
    """
    from playwright.sync_api import Error as PlaywrightError

    deadline = time.monotonic() + timeout_s
    added = 0
    while True:
        try:
            added += merge_nodes(sink, ads_from_html(page.content()).items())
        except PlaywrightError:
            pass  # nawigacja w toku — sprobuj za chwile
        if sink or time.monotonic() >= deadline:
            return added
        page.wait_for_timeout(poll_ms)


# --------------------------------------------------------------------------- #
# Konfiguracja
# --------------------------------------------------------------------------- #

Mode = Literal["auto", "live", "replay"]


@dataclass
class FacebookConfig:
    mode: Mode = "auto"
    country: str = "PL"
    max_ads_per_run: int = 25
    max_scrolls: int = 3
    min_interval_s: float = 5.0
    nav_timeout_s: float = 30.0
    card_timeout_s: float = 20.0
    settle_ms: int = 1500
    resize_settle_ms: int = 400
    video_max_mb: int = 50
    fixtures_dir: Path = DEFAULT_FIXTURES
    record_dir: Path | None = None
    rotator: Rotator = field(default_factory=Rotator)
    breaker_threshold: int = 2
    breaker_cooldown_s: int = 1800

    @classmethod
    def from_env(cls, env: MutableMapping[str, str] | None = None) -> FacebookConfig:
        env = os.environ if env is None else env
        mode = env.get("FB_MODE", "auto")
        if mode not in ("auto", "live", "replay"):
            raise ValueError(f"FB_MODE musi byc auto|live|replay, jest {mode!r}")
        record = env.get("FB_RECORD_DIR")
        return cls(
            mode=mode,  # type: ignore[arg-type]
            country=env.get("FB_COUNTRY", "PL"),
            max_ads_per_run=int(env.get("FB_MAX_ADS_PER_RUN", 25)),
            max_scrolls=int(env.get("FB_MAX_SCROLLS", 3)),
            min_interval_s=float(env.get("FB_MIN_INTERVAL_S", 5)),
            nav_timeout_s=float(env.get("FB_NAV_TIMEOUT_S", 30)),
            card_timeout_s=float(env.get("FB_CARD_TIMEOUT_S", 20)),
            settle_ms=int(env.get("FB_SETTLE_MS", 1500)),
            resize_settle_ms=int(env.get("FB_RESIZE_SETTLE_MS", 400)),
            video_max_mb=int(env.get("FB_VIDEO_MAX_MB", 50)),
            fixtures_dir=Path(env.get("FB_FIXTURES_DIR", str(DEFAULT_FIXTURES))),
            record_dir=Path(record) if record else None,
            rotator=Rotator.from_env(env),
            breaker_threshold=int(env.get("FB_BREAKER_THRESHOLD", 2)),
            breaker_cooldown_s=int(env.get("FB_BREAKER_COOLDOWN_S", 1800)),
        )


# --------------------------------------------------------------------------- #
# Zrodlo
# --------------------------------------------------------------------------- #


class FacebookAdsSource:
    name = "facebook"

    def __init__(
        self,
        config: FacebookConfig | None = None,
        store: BlobStore | None = None,
        limiter: RateLimiter | None = None,
        breaker: CircuitBreaker | None = None,
        node_cache: MutableMapping[str, dict] | None = None,
    ) -> None:
        self.config = config or FacebookConfig.from_env()
        self.store = store or LocalBlobStore("data/blobs")
        self.limiter = limiter or RateLimiter(self.config.min_interval_s)
        self.breaker = breaker or CircuitBreaker(
            threshold=self.config.breaker_threshold, cooldown_s=self.config.breaker_cooldown_s
        )
        self.node_cache = node_cache if node_cache is not None else NodeCache()

    # ------------------------------------------------------------ discover --

    def discover(self, query: str) -> list[str]:
        """Kanoniczne URL-e `?id=<ad_archive_id>` reklam aktywnych w PL dla frazy."""
        mode = self.config.mode
        if mode == "replay":
            return self._discover_replay()
        if self.breaker.is_open():
            if mode == "auto":
                log.warning("facebook: breaker otwarty — discover z korpusu offline")
                return self._discover_replay()
            raise SourceBlocked("circuit breaker otwarty — zrodlo facebook wstrzymane")
        try:
            urls = self._discover_live(query)
        except SourceBlocked:
            self.breaker.record_failure()
            if mode == "auto":
                log.warning("facebook: blokada przy discover — korpus offline", exc_info=True)
                return self._discover_replay()
            raise
        except Exception as exc:
            if mode == "auto":
                log.warning("facebook: blad discover (%s) — korpus offline", exc)
                return self._discover_replay()
            raise SourceError(f"discover nieudany: {exc}") from exc
        self.breaker.record_success()
        return urls

    def _discover_replay(self) -> list[str]:
        root = self.config.fixtures_dir
        if not root.is_dir():
            return []
        ids = sorted(p.name for p in root.iterdir() if p.is_dir() and p.name.isdigit())
        return [canonical_ad_url(i) for i in ids[: self.config.max_ads_per_run]]

    def discover_nodes(self, query: str, search_type: str = "keyword_unordered") -> dict[str, dict]:
        """Weze reklam (ad_archive_id -> wezel JSON Meta) dla frazy — dla collectora.

        Zawsze na zywo: przy blokadzie podnosi SourceBlocked i otwiera breaker,
        NIGDY nie wraca do korpusu offline (collector nie moze wstawic fixtures
        do magazynu URL-i jako swiezych trafien).
        """
        if self.breaker.is_open():
            raise SourceBlocked("circuit breaker otwarty — zrodlo facebook wstrzymane")
        try:
            nodes = self._discover_nodes_live(query, search_type)
        except SourceBlocked:
            self.breaker.record_failure()
            raise
        except Exception as exc:
            raise SourceError(f"discover nieudany: {exc}") from exc
        self.breaker.record_success()
        return nodes

    def _discover_live(self, query: str) -> list[str]:
        nodes = self._discover_nodes_live(query)
        for ad_id, node in nodes.items():
            self.node_cache[ad_id] = node
        log.info("facebook: discover(%r) -> %d reklam", query, len(nodes))
        return [canonical_ad_url(i) for i in nodes]

    def _discover_nodes_live(self, query: str, search_type: str = "keyword_unordered") -> dict[str, dict]:
        collected: dict[str, dict] = {}
        with self._browser() as browser:
            ctx = self._new_context(browser, "desktop")
            try:
                page = ctx.new_page()
                NavigationGuard(AD_LIBRARY_URL).install(page)
                page.on("response", lambda r: self._collect_graphql(r, collected))
                self.limiter.acquire()
                page.goto(
                    search_url(query, self.config.country, search_type),
                    wait_until="domcontentloaded",
                    timeout=self.config.nav_timeout_s * 1000,
                )
                collect_ads_from_dom(page, collected, timeout_s=self.config.card_timeout_s)
                if not collected:
                    self._raise_if_blocked(page, deep=True)

                for _ in range(self.config.max_scrolls):
                    if len(collected) >= self.config.max_ads_per_run:
                        break
                    before = len(collected)
                    self.limiter.acquire()  # kazdy scroll = zapytanie GraphQL do Meta
                    page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(self.config.settle_ms * 2)
                    if len(collected) == before:
                        break
            finally:
                ctx.close()

        ids = list(collected)[: self.config.max_ads_per_run]
        return {ad_id: collected[ad_id] for ad_id in ids}

    # --------------------------------------------------------------- fetch --

    def fetch(self, url: str) -> AdDocument:
        ad_id = ad_id_from_url(url)
        mode = self.config.mode
        if mode == "replay":
            return self._fetch_once(ad_id, replay=True)
        if self.breaker.is_open():
            if mode == "auto" and self._has_fixture(ad_id):
                return self._fetch_once(ad_id, replay=True)
            raise SourceBlocked("circuit breaker otwarty — zrodlo facebook wstrzymane")
        try:
            doc = self._fetch_once(ad_id, replay=False)
        except SourceBlocked:
            self.breaker.record_failure()
            if mode == "auto" and self._has_fixture(ad_id):
                log.warning("facebook: blokada przy fetch %s — korpus offline", ad_id)
                return self._fetch_once(ad_id, replay=True)
            raise
        except Exception as exc:
            if mode == "auto" and self._has_fixture(ad_id):
                log.warning("facebook: blad fetch %s (%s) — korpus offline", ad_id, exc)
                return self._fetch_once(ad_id, replay=True)
            if isinstance(exc, SourceError):
                raise
            raise SourceError(f"fetch {ad_id} nieudany: {exc}") from exc
        self.breaker.record_success()
        return doc

    def _fetch_once(self, ad_id: str, replay: bool) -> AdDocument:
        from playwright.sync_api import TimeoutError as PlaywrightTimeout

        canonical = canonical_ad_url(ad_id)
        doc_id = str(uuid.uuid5(uuid.NAMESPACE_URL, canonical))
        node = self._known_node(ad_id, replay)
        probes: dict[str, ViewportProbe] = {}
        shots: dict[str, str] = {}
        html_path: str | None = None
        media: list[MediaItem] = []
        dom_has_video = False

        # JEDNO zaladowanie strony reklamy (= jedno zapytanie do Meta przez limiter), potem
        # trzy viewporty przez page.set_viewport_size na tej samej stronie. Wczesniej: swiezy
        # kontekst + goto na kazdy viewport = 3 zapytania i ~15 s na reklame przy FB_MIN_INTERVAL_S=5.
        # Izolacja z par. 6.2.1 zostaje: osobny kontekst (bez cookies) na kazda reklame, guard
        # zablokowany na czas sond wszystkich viewportow, nakladki usuwane po kazdej zmianie rozmiaru.
        with self._browser() as browser:
            first = next(iter(VIEWPORTS))
            ctx = self._new_context(browser, first, replay=replay, ad_id=ad_id)
            try:
                page = ctx.new_page()
                guard = NavigationGuard(AD_LIBRARY_URL).install(page)
                gql: dict[str, dict] = {}
                page.on("response", lambda r, sink=gql: self._collect_graphql(r, sink))
                if not replay:
                    self.limiter.acquire()
                try:
                    page.goto(canonical, wait_until="domcontentloaded",
                              timeout=self.config.nav_timeout_s * 1000)
                except PlaywrightTimeout:
                    # Przekierowanie zablokowane w trakcie ladowania potrafi
                    # „zawiesic" goto, choc dokument jest juz wyrenderowany.
                    # O sukcesie decyduje obecnosc kreacji ponizej, nie goto.
                    log.info("facebook %s: goto timeout — sprawdzam karte", ad_id)
                self._wait_for_creative(page, ad_id, self.config.card_timeout_s)
                self._wait_for_images(page)
                html = page.content()
                node = node or ads_from_html(html).get(ad_id) or gql.get(ad_id)
                if self.config.record_dir and not replay:
                    # PRZED neutralizacja: replay ma cwiczyc te same pulapki co zywa strona.
                    self._record_snapshot(page, ctx, ad_id)
                html_path = self.store.put("raw", f"{doc_id}.html", html.encode("utf-8"),
                                           "text/html; charset=utf-8")
                if node is not None and not replay:
                    media = self._download_direct(ctx, node, doc_id)

                for vp, (width, height) in VIEWPORTS.items():
                    if vp != first:
                        page.set_viewport_size({"width": width, "height": height})
                        page.wait_for_timeout(self.config.resize_settle_ms)
                        # React Meta potrafi przebudowac dialog po zmianie breakpointu —
                        # creative.js jest idempotentny i oznacza kreacje ponownie.
                        self._wait_for_creative(page, ad_id, self.config.card_timeout_s / 2)
                        self._wait_for_images(page)
                    removed = neutralize_overlays(page, SCOPE_SELECTOR)
                    guard.lock()  # od teraz zadna nawigacja nie przejdzie
                    probe = run_probe(page, SCOPE_SELECTOR)
                    if probe is not None:
                        probes[vp] = probe
                    if removed or guard.blocked:
                        log.info("facebook %s [%s]: nakladki=%s, zablokowane nawigacje=%d",
                                 ad_id, vp, removed, len(guard.blocked))
                    if vp == first:
                        dom_has_video = page.locator(f"{SCOPE_SELECTOR} video").count() > 0
                    if vp in SCREENSHOT_VIEWPORTS:
                        key = f"{doc_id}-{SCREENSHOT_VIEWPORTS[vp]}.png"
                        shots[vp] = self.store.put("shots", key, self._screenshot(page), "image/png")
            finally:
                ctx.close()

        if not media and not replay and (dom_has_video or (node is not None and has_video(node))):
            media = self._download_ytdlp(canonical, doc_id)
        if replay and not media:
            media = self._replay_video(ad_id, doc_id)
        if node is not None and self.config.record_dir and not replay:
            self._record_node(ad_id, node)

        if node is not None:
            text, title, publisher = ad_text(node), ad_title(node), publisher_from(node)
        else:
            # Graceful degrade: JSON Meta niedostepny -> tekst z DOM kreacji.
            log.warning("facebook %s: brak wezla JSON — tekst z DOM", ad_id)
            desktop = probes.get("desktop")
            text = "\n".join(n.text for n in desktop.nodes if n.visible) if desktop else ""
            title, publisher = None, Publisher()

        return AdDocument(
            id=doc_id,
            source=self.name,
            url=canonical,
            fetched_at=datetime.now(UTC),
            publisher=publisher,
            lang="pl",
            title=title,
            text=text,
            html_path=html_path,
            screenshots=shots,
            media=media,
            transcript=None,  # analyzer: faster-whisper
            render_probe=RenderProbe(viewports=probes) if probes else None,
            embedding=None,  # analyzer: bge-m3
            simhash=None,  # analyzer: simhash na znormalizowanym tekscie (wlasciciel: osoba B)
        )

    # ------------------------------------------------------------- pomocnicze --

    @contextlib.contextmanager
    def _browser(self) -> Iterator[Any]:
        from playwright.sync_api import sync_playwright

        launch: dict[str, Any] = {"headless": True, "args": CHROMIUM_ARGS}
        if self.config.rotator.has_proxies:
            # Playwright wymaga proxy na poziomie launch, by moc je ustawic per kontekst
            launch["proxy"] = {"server": "http://per-context"}  # compliance:allow (placeholder Playwrighta, nie adres)
        with sync_playwright() as pw:
            browser = pw.chromium.launch(**launch)
            try:
                yield browser
            finally:
                browser.close()

    def _new_context(self, browser: Any, vp: str, replay: bool = False, ad_id: str | None = None) -> Any:
        width, height = VIEWPORTS[vp]
        kwargs: dict[str, Any] = {
            "viewport": {"width": width, "height": height},
            "locale": "pl-PL",
            "timezone_id": "Europe/Warsaw",
        }
        kwargs["user_agent"] = self.config.rotator.user_agent()
        proxy = self.config.rotator.proxy()
        if proxy:
            kwargs["proxy"] = {"server": proxy}
        ctx = browser.new_context(**kwargs)
        if replay and ad_id:
            self._install_replay(ctx, ad_id, vp)
        return ctx

    def _fixture_dir(self, ad_id: str) -> Path:
        return self.config.fixtures_dir / ad_id

    def _has_fixture(self, ad_id: str) -> bool:
        return (self._fixture_dir(ad_id) / "page.html").is_file()

    def _install_replay(self, ctx: Any, ad_id: str, vp: str) -> None:
        """Korpus offline: zamrozony snapshot `page.html` (render/freeze.js).

        Serwujemy go pod kanonicznym URL-em, a WSZYSTKIE pozostale zadania sa
        przerywane — replay nie dotyka sieci. HAR celowo nie jest wspierany:
        aplikacja Meta nie renderuje sie z nagrania (patrz render/freeze.js).
        """
        d = self._fixture_dir(ad_id)
        page_html = d / "page.html"
        if not page_html.is_file():
            raise SourceError(f"brak korpusu offline dla reklamy {ad_id} w {d}")
        body = page_html.read_text(encoding="utf-8")

        def handler(route: Any) -> None:
            req = route.request
            if req.resource_type == "document" and req.url.startswith(AD_LIBRARY_URL):
                route.fulfill(status=200, content_type="text/html; charset=utf-8", body=body)
            else:
                route.abort()

        ctx.route("**/*", handler)

    def _known_node(self, ad_id: str, replay: bool) -> dict | None:
        try:
            return self.node_cache[ad_id]
        except KeyError:
            pass
        if replay:
            path = self._fixture_dir(ad_id) / "node.json.gz"
            if path.is_file():
                return json.loads(gzip.decompress(path.read_bytes()))
        return None

    def _record_node(self, ad_id: str, node: dict) -> None:
        assert self.config.record_dir is not None
        target = self.config.record_dir / ad_id
        target.mkdir(parents=True, exist_ok=True)
        # gzip: wezel zawiera adresy Meta/fbcdn — to DANE nagrania, nie wywolania
        # sieciowe w kodzie, tak samo jak zamrozony page.html.
        (target / "node.json.gz").write_bytes(gzip.compress(json.dumps(node, ensure_ascii=False).encode()))

    def _record_snapshot(self, page: Any, ctx: Any, ad_id: str, max_img_bytes: int = 3_000_000) -> None:
        """FB_RECORD_DIR: zamrozony snapshot strony do korpusu offline (render/freeze.js)."""
        import base64

        from render.probe import FREEZE_JS

        assert self.config.record_dir is not None
        refs = page.evaluate(FREEZE_JS, {"stage": "collect", "keepSelector": DIALOG_SELECTOR})
        css: dict[str, str] = {}
        for href in refs.get("css", [])[:80]:
            with contextlib.suppress(Exception):
                resp = ctx.request.get(href, timeout=15_000)
                if resp.ok:
                    css[href] = resp.text()
        imgs: dict[str, str] = {}
        for src in refs.get("imgs", [])[:40]:
            with contextlib.suppress(Exception):
                resp = ctx.request.get(src, timeout=15_000)
                body = resp.body() if resp.ok else b""
                if 0 < len(body) <= max_img_bytes:
                    ctype = resp.headers.get("content-type", "image/jpeg").split(";")[0]
                    imgs[src] = f"data:{ctype};base64,{base64.b64encode(body).decode()}"
        html = page.evaluate(FREEZE_JS, {
            "stage": "build", "keepSelector": DIALOG_SELECTOR, "css": css, "imgs": imgs,
            "keepJsonContaining": f'"ad_archive_id":"{ad_id}"',
        })
        target = self.config.record_dir / ad_id
        target.mkdir(parents=True, exist_ok=True)
        (target / "page.html").write_text(html, encoding="utf-8")
        log.info("facebook %s: snapshot offline %d KB (css=%d, obrazy=%d)",
                 ad_id, len(html) // 1024, len(css), len(imgs))

    @staticmethod
    def _collect_graphql(response: Any, sink: dict[str, dict]) -> None:
        if "/api/graphql" not in response.url or response.status != 200:
            return
        try:
            body = response.text()
        except Exception:  # noqa: BLE001 — odpowiedz bywa juz zwolniona
            return
        merge_nodes(sink, ads_from_graphql(body).items())

    @staticmethod
    def _raise_if_blocked(page: Any, deep: bool = False) -> None:
        url = page.url or ""
        if any(m in url for m in _BLOCK_URL_MARKERS):
            raise SourceBlocked(f"Meta przekierowala na {url}")
        if not deep:
            return
        try:
            head = page.evaluate(
                "() => (document.title + '\\n' + (document.body ? document.body.innerText.slice(0, 3000) : ''))"
            ).lower()
        except Exception:  # noqa: BLE001
            return
        for marker in _BLOCK_TEXT_MARKERS:
            if marker in head:
                raise SourceBlocked(f"Meta: {marker!r}")

    def _wait_for_creative(self, page: Any, ad_id: str, timeout_s: float) -> None:
        """Czeka na kreacje reklamy (creative.js ja oznacza); brak = blokada albo zmiana DOM."""
        from playwright.sync_api import TimeoutError as PlaywrightTimeout

        try:
            page.wait_for_function(MARK_CREATIVE_JS, arg=ad_id, timeout=timeout_s * 1000, polling=500)
        except PlaywrightTimeout as exc:
            self._raise_if_blocked(page, deep=True)
            raise SourceError(f"brak kreacji reklamy {ad_id} w widoku ?id= (zmiana DOM Meta?)") from exc

    @staticmethod
    def _wait_for_images(page: Any) -> None:
        with contextlib.suppress(Exception):
            page.wait_for_function(
                "sel => [...document.querySelectorAll(sel + ' img')].every(i => i.complete)",
                arg=SCOPE_SELECTOR,
                timeout=5000,
            )

    @staticmethod
    def _screenshot(page: Any) -> bytes:
        """Zrzut dialogu z reklama (kreacja + metadane biblioteki jako kontekst dowodowy)."""
        for selector in (DIALOG_SELECTOR, SCOPE_SELECTOR):
            loc = page.locator(selector)
            if loc.count():
                with contextlib.suppress(Exception):
                    return loc.last.screenshot(timeout=10_000)
        return page.screenshot(full_page=False)

    def _store_video(self, data: bytes, doc_id: str) -> list[MediaItem]:
        from media import probe_duration

        path = self.store.put("media", f"{doc_id}.mp4", data, "video/mp4")
        return [MediaItem(kind="video", path=path, duration_s=probe_duration(data))]

    def _download_direct(self, ctx: Any, node: dict, doc_id: str) -> list[MediaItem]:
        from media import download_direct

        max_bytes = self.config.video_max_mb * 1024 * 1024
        for url in video_urls(node)[:1]:
            data = download_direct(ctx.request, url, max_bytes)
            if data:
                return self._store_video(data, doc_id)
        return []

    def _download_ytdlp(self, canonical: str, doc_id: str) -> list[MediaItem]:
        from media import download_ytdlp

        self.limiter.acquire()
        data = download_ytdlp(canonical, self.config.video_max_mb * 1024 * 1024)
        return self._store_video(data, doc_id) if data else []

    def _replay_video(self, ad_id: str, doc_id: str) -> list[MediaItem]:
        path = self._fixture_dir(ad_id) / "video.mp4"  # *.mp4 jest w .gitignore — tylko lokalnie
        return self._store_video(path.read_bytes(), doc_id) if path.is_file() else []


__all__ = [
    "PLATFORM_TYPOGRAPHY_REASON",
    "PLATFORM_TYPOGRAPHY_RULES",
    "SCOPE_SELECTOR",
    "FacebookAdsSource",
    "FacebookConfig",
    "FeedFoldEvidence",
    "feed_fold_evidence",
    "platform_rule_override",
    "primary_body",
]

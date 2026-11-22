"""WWW na zywo (A2): odkrywanie wyszukiwarka, filtr domen, ekstrakcja tresci, decyzja o renderze."""

from __future__ import annotations

import pytest
from sources.base import SourceBlocked, SourceGone
from sources.www_live import LiveWebSource, is_candidate, keep_url

HTML = """<html><head><title>Sygnały giełdowe premium</title>
<meta property="og:site_name" content="Super Sygnały"></head><body>
<nav>menu</nav><article><h1>Sygnały giełdowe premium</h1>
<p>Dołącz do naszego portfela modelowego i zarabiaj 30% rocznie na akcjach. Nasze rekomendacje
inwestycyjne wysyłamy codziennie SMS-em. Abonament 199 zł miesięcznie, pierwsze konsultacje
inwestycyjne gratis. Zespół analityków z wieloletnim doświadczeniem na GPW.</p>
<p>Kontakt: <a href="https://t.me/supersygnaly">Telegram</a> <a href="/cennik">Cennik</a></p>
</article><footer>stopka</footer></body></html>"""


class FakeResponse:
    def __init__(self, status=200, text=HTML, url="https://supersygnaly.pl/oferta"):
        self.status_code, self.text, self.url = status, text, url
        self.content = text.encode()
        self.headers = {"content-type": "text/html; charset=utf-8"}


class FakeSession:
    def __init__(self, responses):
        self.responses, self.calls = responses, []

    def get(self, url, **kw):
        self.calls.append(url)
        r = self.responses.get(url)
        if r is None:
            return FakeResponse(404, "", url)
        return r


def _source(session, search=None, render=False, registry_domains=(), suffixes=("",)):
    return LiveWebSource(search=search or (lambda q, n: []), session=session, store=None,
                         registry_domains=set(registry_domains), render=render, respect_robots=False,
                         suffixes=suffixes)


def test_keep_url_drops_noise_registry_and_binary():
    reg = {"mbank.pl"}
    assert keep_url("https://supersygnaly.pl/oferta", reg)
    assert not keep_url("https://pl.wikipedia.org/wiki/Doradztwo", reg)
    assert not keep_url("https://www.mbank.pl/inwestycje/", reg)
    assert not keep_url("https://www.youtube.com/watch?v=x", reg)
    assert not keep_url("https://example.pl/regulamin.pdf", reg)
    assert not keep_url("https://www.knf.gov.pl/x", reg)


def test_discover_uses_search_and_filters():
    search = lambda q, n: ["https://supersygnaly.pl/oferta", "https://pl.wikipedia.org/wiki/X",  # noqa: E731
                           "https://supersygnaly.pl/oferta#top", "https://wealth.example.pl/"]
    src = _source(FakeSession({}), search=search)
    assert src.discover("sygnały giełdowe") == ["https://supersygnaly.pl/oferta", "https://wealth.example.pl/"]


def test_fetch_extracts_main_text_title_and_external_links():
    url = "https://supersygnaly.pl/oferta"
    doc = _source(FakeSession({url: FakeResponse()})).fetch(url)
    assert doc.source == "www_live" and doc.url == url
    assert doc.title == "Sygnały giełdowe premium"
    assert "portfela modelowego" in doc.text and "menu" not in doc.text.split("Linki zewnetrzne")[0]
    assert "https://t.me/supersygnaly" in doc.text
    assert doc.publisher.handle == "supersygnaly.pl"
    assert doc.render_probe is None  # render wylaczony


def test_fetch_maps_http_errors():
    url = "https://x.pl/a"
    with pytest.raises(SourceGone):
        _source(FakeSession({url: FakeResponse(404, "")})).fetch(url)
    with pytest.raises(SourceBlocked):
        _source(FakeSession({url: FakeResponse(403, "")})).fetch(url)


def test_candidate_needs_financial_offer_signals():
    assert is_candidate("Portfel modelowy i sygnały giełdowe, konsultacje inwestycyjne, abonament")
    assert not is_candidate("Przepis na sernik z rodzynkami i kruszonką")


def test_jobs_build_www_live_with_registry_domains(monkeypatch):
    import jobs
    from resolver import Registry

    monkeypatch.delenv("S3_ENDPOINT", raising=False)
    rows = [{"knf_id": "BM-MBANK", "name": "mBank S.A.", "aliases": [], "domains": ["https://www.mbank.pl"], "handles": []}]
    src = jobs.build_source("www_live", registry=Registry.from_rows(rows))
    assert src.name == "www_live" and "mbank.pl" in src.registry_domains
    assert jobs.render_queue_for("www_live") == "q:fetch:www"


def test_schedule_has_live_www_job():
    import scheduler

    spec = next(s for s in scheduler.load_schedule() if s.name == "www-live")
    assert spec.source == "www_live" and spec.enabled and len(spec.queries) >= 7


def test_discover_queries_variants_and_dedups():
    asked = []

    def search(q, n):
        asked.append(q)
        return ["https://a.pl/", f"https://{len(asked)}.example.pl/"]

    src = _source(FakeSession({}), search=search, suffixes=("", "cennik"))
    assert src.discover("family office") == ["https://a.pl/", "https://1.example.pl/", "https://2.example.pl/"]
    assert asked == ["family office", "family office cennik"]

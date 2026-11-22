"""Test kontraktu zrodel: kazde zrodlo z `jobs.SOURCES`, zbudowane przez `jobs.build_source`,
zwraca z `fetch` poprawny AdDocument. Offline: siec zastepuja fixture'y.

Nowe zrodlo = nowy wpis w ADAPTERS (inaczej `test_every_source_has_adapter` nie przejdzie).
"""

from __future__ import annotations

import json

import httpx
import jobs
import pytest
from contracts import AdDocument
from sources import Source

from tests.conftest import FIXTURES, REPO_ROOT

REGISTRY = [{"knf_id": "DM-XTB", "name": "XTB S.A.", "aliases": ["XTB"], "domains": ["xtb.com"], "handles": []}]
WWW_BASE = "https://blog.example.invalid"
WWW_DIR = REPO_ROOT / "fixtures" / "demo-ads" / "www"


def _facebook(monkeypatch, request):
    request.getfixturevalue("chromium_available")  # pomija, gdy brak Chromium
    monkeypatch.setenv("FB_MODE", "replay")
    monkeypatch.setenv("FB_FIXTURES_DIR", str(FIXTURES / "facebook"))
    monkeypatch.setenv("FB_MIN_INTERVAL_S", "0")  # tylko w tescie: replay nie pyta Mety
    return jobs.build_source("facebook"), "inwestycje"


def _youtube(monkeypatch, request):
    data = json.loads((FIXTURES / "youtube" / "aaaaaaaaaaa.json").read_text(encoding="utf-8"))
    src = jobs.build_source("youtube", registry=REGISTRY)
    monkeypatch.setattr(src, "_metadata", lambda vid: data["info"])
    monkeypatch.setattr(src, "_transcript", lambda vid: list(data["captions"]))
    monkeypatch.setattr(src, "discover", lambda q: [f"https://www.youtube.com/watch?v={data['info']['id']}"])
    return src, "XTB kod polecający"


def _www(monkeypatch, request):
    def handler(req: httpx.Request) -> httpx.Response:
        page = WWW_DIR / (req.url.path.lstrip("/") or "index.html")
        if not page.is_file():
            return httpx.Response(404, text="")
        return httpx.Response(200, text=page.read_text(encoding="utf-8"),
                              headers={"content-type": "text/html; charset=utf-8"})

    src = jobs.build_source("www")
    src._client = httpx.Client(transport=httpx.MockTransport(handler))
    return src, f"{WWW_BASE}/index.html"


def _tiktok(monkeypatch, request):
    monkeypatch.setenv("TIKTOK_MODE", "replay")
    return jobs.build_source("tiktok"), "inwestycje"


def _www_live(monkeypatch, request):
    class Resp:
        status_code, url = 200, f"{WWW_BASE}/index.html"

        def __init__(self, text):
            self.text, self.content = text, text.encode()

    class Session:
        def get(self, url, **kw):
            page = WWW_DIR / (url.removeprefix(WWW_BASE).lstrip("/") or "index.html")
            if not page.is_file():
                r = Resp("")
                r.status_code = 404
                return r
            return Resp(page.read_text(encoding="utf-8"))

    src = jobs.build_source("www_live", registry=REGISTRY)
    src._session, src.render = Session(), False
    src.search = lambda q, n: [f"{WWW_BASE}/index.html"]
    return src, "doradztwo inwestycyjne"


ADAPTERS = {"facebook": _facebook, "youtube": _youtube, "www": _www, "tiktok": _tiktok, "www_live": _www_live}


@pytest.fixture(autouse=True)
def _offline_env(monkeypatch, tmp_path):
    monkeypatch.delenv("S3_ENDPOINT", raising=False)
    monkeypatch.setenv("SCRAPER_DATA_DIR", str(tmp_path / "blobs"))
    monkeypatch.setenv("PROXY_LIST", "")


def test_every_source_has_adapter():
    assert set(ADAPTERS) == set(jobs.SOURCES)


@pytest.mark.parametrize("name", jobs.SOURCES)
def test_source_contract(name, monkeypatch, request):
    src, query = ADAPTERS[name](monkeypatch, request)
    assert isinstance(src, Source) and src.name == name

    urls = list(src.discover(query))
    assert urls and all(u.startswith("https://") for u in urls)

    doc = src.fetch(urls[0])
    assert isinstance(doc, AdDocument)
    assert doc.source == name and doc.url.startswith("https://")
    assert doc.id and doc.fetched_at.tzinfo is not None
    assert doc.analyzable_text.strip()
    # przechodzi przez serializacje tak, jak w jobs.fetch_job -> casedb
    assert AdDocument.model_validate(json.loads(doc.model_dump_json())) == doc


def test_fetch_path_used_by_jobs(monkeypatch, request):
    """jobs._fetch (wspolna sciezka q:render) dziala dla zrodel bez specjalnej obslugi."""
    src, query = _tiktok(monkeypatch, request)
    doc, qualified, extra = jobs._fetch(src, "tiktok", src.discover(query)[0])
    assert doc.source == "tiktok" and qualified and extra == []

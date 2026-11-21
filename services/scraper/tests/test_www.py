# compliance:allow-file - testowe adresy w danych wejsciowych (ruch sieciowy zamockowany)
from __future__ import annotations

from pathlib import Path

import httpx
import pytest
from net import Rotator
from sources.base import SourceError, SourceGone
from sources.www import WebPageSource
from storage import LocalBlobStore

DEMO = Path(__file__).resolve().parents[3] / "fixtures" / "demo-ads" / "www"
BASE = "https://blog.example"


def make(pages: dict[str, tuple[int, str]], **kw) -> tuple[WebPageSource, list[httpx.Request]]:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        status, body = pages.get(str(request.url), (404, ""))
        return httpx.Response(status, text=body, headers={"content-type": "text/html; charset=utf-8"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    return WebPageSource(rotator=Rotator(["UA-test"], []), client=client, **kw), seen


HTML = """<html><head><title>Tytul strony</title><meta property="og:site_name" content="Blog Przyklad">
<style>.x{}</style><script>var secret=1;</script></head>
<body><h1>Naglowek</h1><p>Pierwszy akapit.</p><p>Drugi <b>akapit</b>.</p>
<noscript>brak js</noscript><svg><text>ikona</text></svg>
<a href="/a#kotwica">A</a> <a href="/b.pdf">pdf</a> <a href="mailto:x@y.pl">m</a>
<a href="https://xtb.com/pl?ref=1">XTB</a> <a href="https://blog.example/c">C</a></body></html>"""


def test_fetch_text_links_publisher_and_ua():
    src, seen = make({f"{BASE}/p": (200, HTML)}, respect_robots=False)
    doc = src.fetch(f"{BASE}/p#x")
    assert doc.source == "www" and doc.url == f"{BASE}/p" and doc.title == "Tytul strony"
    assert "Pierwszy akapit." in doc.text and "Drugi akapit." in doc.text
    assert "\n\n" in doc.text
    assert "secret" not in doc.text and "ikona" not in doc.text and "brak js" not in doc.text
    assert doc.text.rstrip().endswith("https://xtb.com/pl?ref=1")
    assert "blog.example/c" not in doc.text.split("Linki zewnetrzne:")[1]
    assert doc.publisher.handle == "blog.example" and doc.publisher.display_name == "Blog Przyklad"
    assert doc.publisher.profile_url == BASE
    assert seen[0].headers["user-agent"] == "UA-test"
    assert doc.id == src.fetch(f"{BASE}/p").id


def test_status_mapping():
    src, _ = make({f"{BASE}/gone": (410, ""), f"{BASE}/err": (500, "")}, respect_robots=False)
    with pytest.raises(SourceGone):
        src.fetch(f"{BASE}/gone")
    with pytest.raises(SourceGone):
        src.fetch(f"{BASE}/missing")
    with pytest.raises(SourceError) as e:
        src.fetch(f"{BASE}/err")
    assert not isinstance(e.value, SourceGone)


def test_discover_same_domain_limited_no_binaries():
    src, _ = make({f"{BASE}/": (200, HTML)}, respect_robots=False)
    assert src.discover(f"{BASE}/") == [f"{BASE}/", f"{BASE}/a", f"{BASE}/c"]
    small, _ = make({f"{BASE}/": (200, HTML)}, respect_robots=False, max_pages=2)
    assert len(small.discover(f"{BASE}/")) == 2


def test_robots_disallow_and_robots_error_allows():
    robots = "User-agent: *\nDisallow: /secret\n"
    src, _ = make({f"{BASE}/robots.txt": (200, robots), f"{BASE}/secret": (200, "x"), f"{BASE}/ok": (200, "<p>ok</p>")})
    with pytest.raises(SourceError):
        src.fetch(f"{BASE}/secret")
    assert src.fetch(f"{BASE}/ok").text == "ok"
    open_src, _ = make({f"{BASE}/robots.txt": (500, ""), f"{BASE}/ok": (200, "<p>ok</p>")})
    assert open_src.fetch(f"{BASE}/ok").text == "ok"


def test_size_limit_and_html_stored(tmp_path):
    big, _ = make({f"{BASE}/big": (200, "x" * (2 * 1024 * 1024 + 1))}, respect_robots=False)
    with pytest.raises(SourceError):
        big.fetch(f"{BASE}/big")
    store = LocalBlobStore(tmp_path)
    src, _ = make({f"{BASE}/p": (200, HTML)}, respect_robots=False, store=store)
    doc = src.fetch(f"{BASE}/p")
    assert doc.html_path == f"s3://html/{doc.id}.html"
    assert store.path_of(doc.html_path).read_text("utf-8") == HTML


def test_rejects_non_http():
    src, _ = make({}, respect_robots=False)
    with pytest.raises(SourceError):
        src.fetch("ftp://x/y")
    with pytest.raises(SourceError):
        src.discover("javascript:alert(1)")


def test_demo_fixture_pages():
    pages = {f"{BASE}/{p.name}": (200, p.read_text("utf-8")) for p in DEMO.glob("*.html")}
    pages[f"{BASE}/"] = pages[f"{BASE}/index.html"]
    src, _ = make(pages, respect_robots=False)
    found = src.discover(f"{BASE}/")
    assert f"{BASE}/finfluencer-xtb.html" in found and f"{BASE}/poradnik-neutralny.html" in found
    ad = src.fetch(f"{BASE}/finfluencer-xtb.html")
    assert "https://www.xtb.com/pl?ref=demo123" in ad.text and "pewny zysk" in ad.text
    assert ad.title == "Jak zarabiam 5000 zl miesiecznie na rynkach"
    assert "xtb" not in src.fetch(f"{BASE}/poradnik-neutralny.html").text.lower()

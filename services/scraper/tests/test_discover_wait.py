"""Regresja z nagrywania 21.11.2026: discover('inwestycje') zwracal 0 reklam.

Meta po goto nawiguje na skanonizowany URL wyszukiwania, a inline JSON z
wynikami pojawia sie w DOM dopiero pozniej. Odtwarzamy to offline.
"""

from __future__ import annotations

import json

from sources.facebook import collect_ads_from_dom

AD = {"ad_archive_id": "5555555555555555", "page_name": "X", "snapshot": {"body": {"text": "Zysk"}}}

PAGES = {
    # 1) strona startowa: po 150 ms prawdziwa nawigacja na wersje kanoniczna
    "https://example.invalid/search": "<p>start</p><script>setTimeout(()=>location.replace('/search2'),150)</script>",
    # 2) wersja kanoniczna: wyniki „dochodza" do DOM po 600 ms (jak strumieniowanie Meta)
    "https://example.invalid/search2": (
        "<p>wyniki</p><script>setTimeout(()=>{const s=document.createElement('script');"
        "s.type='application/json';s.textContent=" + json.dumps(json.dumps({"r": [AD]})) + ";"
        "document.body.appendChild(s)},600)</script>"
    ),
}


def _serve(ctx):
    ctx.route(
        "https://example.invalid/**",
        lambda route: route.fulfill(status=200, content_type="text/html", body=PAGES.get(route.request.url, "")),
    )


def test_waits_through_navigation_until_results_arrive(browser):
    ctx = browser.new_context()
    _serve(ctx)
    page = ctx.new_page()
    page.goto("https://example.invalid/search", wait_until="domcontentloaded")
    sink: dict[str, dict] = {}
    added = collect_ads_from_dom(page, sink, timeout_s=10, poll_ms=100)
    assert added == 1 and list(sink) == ["5555555555555555"]
    assert page.url.endswith("/search2")
    ctx.close()


def test_gives_up_after_timeout_without_results(browser):
    ctx = browser.new_context()
    _serve(ctx)
    page = ctx.new_page()
    page.goto("https://example.invalid/search", wait_until="domcontentloaded")
    page.evaluate("() => { window.stop(); }")
    sink: dict[str, dict] = {}
    PAGES_EMPTY = "https://example.invalid/none"
    ctx.route(PAGES_EMPTY, lambda r: r.fulfill(status=200, content_type="text/html", body="<p>pusto</p>"))
    page.goto(PAGES_EMPTY)
    assert collect_ads_from_dom(page, sink, timeout_s=0.5, poll_ms=100) == 0
    assert sink == {}
    ctx.close()

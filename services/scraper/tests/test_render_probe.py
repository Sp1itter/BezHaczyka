"""RenderProbe: scope_root, krok 3b (media pod tekstem), sygnaly ukrycia, blokada nawigacji."""

from __future__ import annotations

import pytest
from render.probe import NavigationGuard, neutralize_overlays, run_probe

SVG = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='200'%3E"  # compliance:allow — namespace SVG
    "%3Crect width='400' height='200' fill='%23224488'/%3E%3C/svg%3E"
)


@pytest.fixture
def page(browser):
    ctx = browser.new_context(viewport={"width": 800, "height": 600})
    p = ctx.new_page()
    yield p
    ctx.close()


def _node(probe, text):
    matches = [n for n in probe.nodes if n.text == text]
    assert matches, f"brak wezla {text!r} w {[n.text for n in probe.nodes]}"
    return matches[0]


def test_scope_root_ignores_dialog_above_it(page):
    page.set_content(
        """<div role="dialog"><div id="scope"><p>Treść reklamy</p></div></div>
           <p>Poza zakresem</p>"""
    )
    probe = run_probe(page, "#scope")
    assert [n.text for n in probe.nodes] == ["Treść reklamy"]
    assert probe.nodes[0].behind_interaction is None  # bez scope_root bylby "modal"
    # dla porownania: bez zakresu dialog jest wykrywany zgodnie z par. 6.2.1
    full = run_probe(page)
    assert _node(full, "Treść reklamy").behind_interaction == "modal"


def test_scope_selector_miss_returns_none(page):
    page.set_content("<p>x</p>")
    assert run_probe(page, "#nie-ma") is None


def test_text_over_img_is_unknown_even_with_pointer_events_none(page):
    page.set_content(
        f"""<div id="s" style="background:#fff">
              <div style="position:relative">
                <img src="{SVG}" style="display:block;width:400px;height:200px">
                <span style="position:absolute;left:10px;top:80px;color:#fff;pointer-events:none">Na grafice</span>
              </div>
              <p style="color:#111">Na białym</p>
            </div>"""
    )
    probe = run_probe(page, "#s")
    over = _node(probe, "Na grafice")
    assert over.background_confidence == "unknown"
    assert over.background_source == "media:img"
    assert over.contrast_ratio is None  # regula 5 -> not_applicable, nigdy fail
    white = _node(probe, "Na białym")
    assert white.background_confidence == "resolved"
    assert white.background_effective == "#ffffff"
    assert white.contrast_ratio and white.contrast_ratio > 15


def test_media_check_below_viewport_after_scroll(page):
    page.set_content(
        f"""<div id="s" style="background:#fff">
              <div style="height:1500px">spacer</div>
              <div style="position:relative">
                <img src="{SVG}" style="display:block;width:400px;height:200px">
                <span style="position:absolute;left:10px;top:80px;color:#fff">Daleko w dół</span>
              </div>
            </div>"""
    )
    probe = run_probe(page, "#s")
    assert _node(probe, "Daleko w dół").background_confidence == "unknown"
    assert page.evaluate("() => scrollY") == 0  # sonda przywraca przewiniecie


def test_background_alpha_composition_and_assumed_canvas(page):
    page.set_content(
        """<div id="s"><div style="background:#000"><div style="background:rgba(255,255,255,0.5)">
             <span style="color:#000">Pół</span></div></div><p>Kanwa</p></div>"""
    )
    probe = run_probe(page, "#s")
    half = _node(probe, "Pół")
    assert half.background_confidence == "resolved"
    assert half.background_effective in ("#808080", "#7f7f7f")
    assert _node(probe, "Kanwa").background_confidence == "assumed_canvas"


def test_cta_block_link_is_not_behind_interaction_but_text_link_is(page):
    page.set_content(
        f"""<div id="s">
              <a href="/cel"><img src="{SVG}" style="width:100px;height:50px"><div>Ryzyko utraty kapitału</div></a>
              <a href="/ryzyko">Zobacz ostrzeżenie o ryzyku</a>
            </div>"""
    )
    probe = run_probe(page, "#s")
    assert _node(probe, "Ryzyko utraty kapitału").behind_interaction is None
    link = _node(probe, "Zobacz ostrzeżenie o ryzyku")
    assert link.behind_interaction == "link"


def test_collapsed_signals(page):
    page.set_content(
        """<div id="s">
             <details><summary>Więcej</summary><p>W details</p></details>
             <div style="display:none"><p>Ukryte</p></div>
             <div style="max-height:0;overflow:hidden"><p>Akordeon</p></div>
             <button aria-controls="panel" aria-expanded="false">Rozwiń</button>
             <div id="panel"><p>Sterowany</p></div>
           </div>"""
    )
    probe = run_probe(page, "#s")
    assert _node(probe, "W details").behind_interaction == "details"
    assert _node(probe, "Więcej").behind_interaction is None  # summary jest widoczne
    assert _node(probe, "Ukryte").behind_interaction == "hidden"
    assert _node(probe, "Ukryte").visible is False
    assert _node(probe, "Akordeon").behind_interaction == "accordion"
    assert _node(probe, "Sterowany").behind_interaction == "accordion"
    assert _node(probe, "Rozwiń").behind_interaction is None


def test_clipped_by_ellipsis(page):
    page.set_content(
        """<div id="s"><p style="width:60px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">
           Bardzo długi tekst ostrzeżenia</p></div>"""
    )
    assert run_probe(page, "#s").nodes[0].clipped is True


def test_neutralize_removes_login_and_cookies_but_keeps_scope(page):
    page.set_content(
        """<body style="overflow:hidden">
           <div role="dialog" id="ad"><div id="scope">Reklama</div></div>
           <div role="dialog" aria-modal="true"><input name="email">Zaloguj się</div>
           <div data-cookiebanner="x" style="position:fixed;bottom:0;height:200px">Pliki cookie</div>
           <div role="dialog">Zwykłe okno bez sygnatury</div></body>"""
    )
    removed = neutralize_overlays(page, "#scope")
    assert sorted(removed) == ["cookie", "login"]
    assert page.locator("#ad").count() == 1
    assert page.locator("text=Zwykłe okno bez sygnatury").count() == 1
    assert page.evaluate("() => getComputedStyle(document.body).overflow") == "visible"


def test_navigation_guard_blocks_redirect_and_locks(browser):
    ctx = browser.new_context()
    pages = {
        "https://example.invalid/a": "<p>A</p><script>setTimeout(()=>location.href='/b',50)</script>",
        "https://example.invalid/b": "<p>B</p>",
    }
    ctx.route(
        "https://example.invalid/**",
        lambda route: route.fulfill(status=200, content_type="text/html", body=pages.get(route.request.url, "")),
    )
    page = ctx.new_page()
    guard = NavigationGuard("https://example.invalid/a").install(page)
    page.goto("https://example.invalid/a")
    page.wait_for_timeout(300)
    assert page.url == "https://example.invalid/a"
    assert "https://example.invalid/b" in guard.blocked
    guard.lock()
    page.evaluate("() => { location.href = '/a?again=1' }")
    page.wait_for_timeout(200)
    assert page.locator("text=A").count() == 1
    assert any("again=1" in u for u in guard.blocked)
    ctx.close()

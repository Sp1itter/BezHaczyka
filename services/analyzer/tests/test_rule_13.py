"""Testy reguly 13 — dominacja wynikow historycznych.

Art. 44 ust. 4 lit. a rozporzadzenia del. 2017/565: wyniki historyczne nie
moga byc najbardziej wyeksponowanym elementem informacji. Pomiar: czy wezel
z wynikiem historycznym ma najwieksza czcionke (a przy remisie lezy najwyzej).
"""

from __future__ import annotations

from datetime import datetime, timezone

from analyzer.contracts import (
    AdDocument,
    BBox,
    Engine,
    EvidenceKind,
    RenderProbe,
    TextNode,
    Verdict,
    ViewportProbe,
)
from analyzer.rules_hybrid import RULE_13_META, assess_rule_13, rule_13_runner

HIST = "Zysk 34% w 2023 roku"
PRODUKT = "Fundusz Akcji Plus dla kazdego"
TRESC = "Zaloz rachunek i zacznij inwestowac juz dzis."
OSTRZEZENIE = "Inwestowanie wiaze sie z ryzykiem utraty kapitalu."


def _node(text: str, font: float, y: float = 0.0, visible: bool = True) -> TextNode:
    return TextNode(
        text=text,
        font_px=font,
        color="#111111",
        bbox=BBox(x=24, y=y, w=342, h=40),
        dom_path="x",
        visible=visible,
    )


def _doc(nodes: list[TextNode] | None, text: str | None = None) -> AdDocument:
    probe = None
    if nodes is not None:
        probe = RenderProbe(
            viewports={
                "mobile": ViewportProbe(
                    dominant_font_px=max((n.font_px for n in nodes), default=16.0),
                    page_height_px=2000.0,
                    nodes=nodes,
                )
            }
        )
    return AdDocument(
        id="t",
        source="web",
        url="https://example.invalid/a",
        fetched_at=datetime(2026, 11, 21, tzinfo=timezone.utc),
        text=text if text is not None else " ".join(n.text for n in (nodes or [])),
        render_probe=probe,
    )


def test_meta():
    assert RULE_13_META == (
        "Dominacja wyników historycznych",
        3,
        "art. 44 ust. 4 lit. a rozporządzenia del. 2017/565",
    )


def test_brak_wynikow_historycznych_to_not_applicable():
    r = assess_rule_13(_doc([_node(PRODUKT, 32), _node(TRESC, 16)]))
    assert r.verdict is Verdict.NOT_APPLICABLE
    assert r.evidence.kind is EvidenceKind.ABSENCE
    assert r.confidence == 1.0
    assert r.rule_id == "13"
    assert r.engine is Engine.HYBRID


def test_wyniki_historyczne_bez_render_probe_to_not_applicable_nie_fail():
    r = assess_rule_13(_doc(None, text=HIST))
    assert r.verdict is Verdict.NOT_APPLICABLE
    assert "RenderProbe" in r.evidence.summary
    assert r.confidence == 1.0


def test_wynik_tylko_w_tekscie_bez_pasujacego_wezla_to_not_applicable():
    r = assess_rule_13(_doc([_node(PRODUKT, 32)], text=f"{PRODUKT} {HIST}"))
    assert r.verdict is Verdict.NOT_APPLICABLE


def test_naglowek_z_wynikiem_najwiekszy_to_fail():
    doc = _doc([_node(HIST, 48, 10), _node(TRESC, 16, 100), _node(OSTRZEZENIE, 12, 200)])
    r = assess_rule_13(doc)
    assert r.verdict is Verdict.FAIL
    assert r.confidence == 0.9
    assert r.evidence.kind is EvidenceKind.MEASUREMENT
    assert r.evidence.quote == HIST
    assert r.evidence.viewport == "mobile"
    m = r.evidence.measured
    assert m["font_wyniku_hist_px"] == 48
    assert m["max_font_innych_px"] == 16
    assert m["dominant_font_px"] == 48
    assert m["stosunek"] == 3.0
    assert m["prog"] == 1.0
    assert "48 px" in r.evidence.summary and "16 px" in r.evidence.summary


def test_wynik_mniejszy_niz_naglowek_produktu_to_pass():
    r = assess_rule_13(_doc([_node(PRODUKT, 32, 10), _node(HIST, 16, 100)]))
    assert r.verdict is Verdict.PASS
    assert r.confidence == 0.9
    assert r.evidence.measured["stosunek"] == 0.5


def test_remis_czcionki_wyzszy_wynik_to_fail():
    r = assess_rule_13(_doc([_node(HIST, 24, 10), _node(PRODUKT, 24, 100)]))
    assert r.verdict is Verdict.FAIL


def test_remis_czcionki_nizszy_wynik_to_pass():
    r = assess_rule_13(_doc([_node(PRODUKT, 24, 10), _node(HIST, 24, 100)]))
    assert r.verdict is Verdict.PASS


def test_wynik_jako_jedyny_widoczny_to_brak_danych_nie_fail():
    # Probe z jednym wezlem to niepelny pomiar, nie dowod dominacji.
    r = assess_rule_13(_doc([_node(HIST, 20)]))
    assert r.verdict is Verdict.NOT_APPLICABLE


def test_niewidoczny_wezel_jest_ignorowany():
    ukryty = _node(PRODUKT, 60, 5, visible=False)
    r = assess_rule_13(_doc([_node(HIST, 24, 10), ukryty, _node(TRESC, 16, 50)]))
    assert r.verdict is Verdict.FAIL
    assert r.evidence.measured["max_font_innych_px"] == 16


def test_niewidoczny_wezel_historyczny_nie_liczy_sie():
    ukryty = _node(HIST, 60, 5, visible=False)
    r = assess_rule_13(_doc([ukryty, _node(PRODUKT, 32, 50)], text=HIST))
    assert r.verdict is Verdict.NOT_APPLICABLE


def test_prog_z_konfiguracji_wplywa_na_wynik(monkeypatch):
    import analyzer.rules_hybrid as rh

    doc = _doc([_node(HIST, 48, 100), _node(PRODUKT, 24, 10)])
    assert assess_rule_13(doc).verdict is Verdict.FAIL

    monkeypatch.setattr(
        rh,
        "get_threshold",
        lambda key, default=None: 3.0 if key == "rules.rule_13.dominance_ratio" else default,
    )
    r = assess_rule_13(doc)
    assert r.verdict is Verdict.PASS
    assert r.evidence.measured["prog"] == 3.0


def test_prog_domyslny_z_yaml():
    from analyzer.config_loader import get_threshold

    assert get_threshold("rules.rule_13.dominance_ratio", None) == 1.0


def test_cytat_to_doslowny_tekst_wezla():
    tekst = "Zysk 34% w 2023 roku — nasz fundusz wygral rynek " + "x" * 400
    r = assess_rule_13(_doc([_node(tekst, 48), _node(TRESC, 16, 100)], text=tekst))
    assert r.evidence.quote == tekst[:300]


def test_runner_zwraca_jeden_wynik():
    out = rule_13_runner(_doc([_node(HIST, 48)]))
    assert len(out) == 1 and out[0].rule_id == "13"

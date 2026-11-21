"""Testy reguly 3 — czy ostrzezenie o ryzyku TOWARZYSZY obietnicy zysku.

Art. 44 ust. 2 lit. b rozporzadzenia del. 2017/565. To jest pierwsze pytanie
mentorow UKNF (czy reklama jest rzetelna) i jednoczesnie pytanie MIERZALNE:
ostrzezenie wepchniete 4000 pikseli nizej formalnie istnieje, ale niczemu
nie towarzyszy.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from analyzer.contracts import (
    AdDocument,
    BBox,
    Engine,
    EvidenceKind,
    RenderProbe,
    TextNode,
    Transcript,
    TranscriptSegment,
    Verdict,
    ViewportProbe,
)
from analyzer.rules_hybrid import (
    assess_rule_3,
    measure_geometry,
    measure_proximity,
    measure_text,
    measure_timeline,
)

ZYSK = "Zyski do 18% rocznie!"
RYZYKO = "Inwestowanie wiaze sie z ryzykiem utraty kapitalu."


def _node(text: str, y: float, h: float = 40.0) -> TextNode:
    return TextNode(
        text=text, font_px=16.0, color="#111111", bbox=BBox(x=24, y=y, w=342, h=h), dom_path="x"
    )


def _doc(
    nodes: list[TextNode] | None = None,
    text: str | None = None,
    segments: list[TranscriptSegment] | None = None,
) -> AdDocument:
    probe = None
    if nodes is not None:
        probe = RenderProbe(
            viewports={
                "mobile": ViewportProbe(
                    dominant_font_px=16.0, page_height_px=4210.0, nodes=nodes
                )
            }
        )
    transcript = None
    if segments is not None:
        transcript = Transcript(
            engine="test", lang="pl", text=" ".join(s.text for s in segments), segments=segments
        )
    return AdDocument(
        id="t",
        source="web",
        url="https://example.invalid/a",
        fetched_at=datetime(2026, 11, 21, tzinfo=timezone.utc),
        text=text if text is not None else " ".join(n.text for n in (nodes or [])),
        render_probe=probe,
        transcript=transcript,
    )


class TestOsiGeometrii:
    """Najmocniejszy dowod: co odbiorca FAKTYCZNIE widzi na ekranie."""

    def test_ostrzezenie_w_stopce_to_naruszenie(self):
        doc = _doc([_node(ZYSK, 310), _node(RYZYKO, 4080, 9)])
        r = assess_rule_3(doc)
        assert r.verdict is Verdict.FAIL
        assert r.engine is Engine.HYBRID
        assert r.severity == 5
        assert r.evidence.kind is EvidenceKind.MEASUREMENT
        assert r.evidence.measured is not None
        assert r.evidence.measured["odleglosc"] > 3000
        assert "art. 44 ust. 2 lit. b" in r.legal_basis

    def test_ostrzezenie_obok_jest_ok(self):
        doc = _doc([_node(ZYSK, 310), _node(RYZYKO, 360)])
        r = assess_rule_3(doc)
        assert r.verdict is Verdict.PASS
        assert r.evidence.measured["odleglosc"] < 100

    def test_dokladnie_na_progu_przechodzi(self):
        doc = _doc([_node(ZYSK, 0, 0), _node(RYZYKO, 600, 0)])
        assert assess_rule_3(doc).verdict is Verdict.PASS

    def test_tuz_za_progiem_nie_przechodzi(self):
        doc = _doc([_node(ZYSK, 0, 0), _node(RYZYKO, 601, 0)])
        assert assess_rule_3(doc).verdict is Verdict.FAIL

    def test_brak_ostrzezenia_to_naruszenie_z_powodu_braku(self):
        doc = _doc([_node("Zyski do 18% rocznie! Zaloz rachunek.", 310)])
        r = assess_rule_3(doc)
        assert r.verdict is Verdict.FAIL
        assert r.evidence.kind is EvidenceKind.ABSENCE
        assert "NIE ZAWIERA" in r.evidence.summary

    def test_bierze_najblizsza_pare(self):
        """Gdy ostrzezen jest kilka, liczy sie najblizsze."""
        doc = _doc([_node(ZYSK, 310), _node(RYZYKO, 4080, 9), _node(RYZYKO, 400)])
        r = assess_rule_3(doc)
        assert r.verdict is Verdict.PASS

    def test_niewidoczne_wezly_sa_pomijane(self):
        """Ostrzezenie w `display:none` nie towarzyszy niczemu."""
        ukryte = _node(RYZYKO, 360)
        ukryte = ukryte.model_copy(update={"visible": False})
        doc = _doc([_node(ZYSK, 310), ukryte])
        r = assess_rule_3(doc)
        assert r.verdict is Verdict.FAIL
        assert r.evidence.kind is EvidenceKind.ABSENCE


class TestOsiCzasu:
    """Reklama wideo: liczy sie sekunda, nie piksel."""

    def test_ostrzezenie_na_koncu_materialu_to_naruszenie(self):
        segs = [
            TranscriptSegment(start=4.2, end=8.1, text="zarobisz osiemnascie procent rocznie"),
            TranscriptSegment(start=33.8, end=34.2, text="inwestowanie wiaze sie z ryzykiem"),
        ]
        r = assess_rule_3(_doc(nodes=None, text="", segments=segs))
        assert r.verdict is Verdict.FAIL
        assert r.evidence.measured["odleglosc"] == pytest.approx(29.6, abs=0.2)

    def test_ostrzezenie_zaraz_po_obietnicy_jest_ok(self):
        segs = [
            TranscriptSegment(start=4.0, end=6.0, text="zarobisz osiemnascie procent"),
            TranscriptSegment(start=6.5, end=9.0, text="pamietaj o ryzyku utraty kapitalu"),
        ]
        assert assess_rule_3(_doc(nodes=None, text="", segments=segs)).verdict is Verdict.PASS


class TestOsiTekstu:
    """Gdy nie ma ani RenderProbe, ani transkrypcji."""

    def test_ostrzezenie_daleko_w_tekscie_to_naruszenie(self):
        text = ZYSK + " " + ("wypelniacz " * 60) + RYZYKO
        r = assess_rule_3(_doc(nodes=None, text=text))
        assert r.verdict is Verdict.FAIL
        assert r.evidence.measured["odleglosc"] > 300

    def test_ostrzezenie_blisko_w_tekscie_jest_ok(self):
        r = assess_rule_3(_doc(nodes=None, text=f"{ZYSK} {RYZYKO}"))
        assert r.verdict is Verdict.PASS


class TestWarunkowosci:
    def test_brak_obietnicy_zysku_daje_not_applicable(self):
        """Regula jest warunkowa: bez twierdzen o zyskach nie ma czego
        obudowywac ostrzezeniem."""
        doc = _doc([_node("Oferujemy rachunek maklerski bez oplat.", 100)])
        r = assess_rule_3(doc)
        assert r.verdict is Verdict.NOT_APPLICABLE
        assert "nie zawiera twierdzen o potencjalnych zyskach" in r.evidence.summary

    def test_not_applicable_nie_podnosi_score(self):
        from analyzer.scoring import risk_score

        doc = _doc([_node("Oferujemy rachunek maklerski bez oplat.", 100)])
        assert risk_score([assess_rule_3(doc)]) == 0.0

    def test_pusty_dokument_nie_wywraca(self):
        r = assess_rule_3(_doc(nodes=None, text=""))
        assert r.verdict is Verdict.NOT_APPLICABLE


class TestWyboruOsi:
    def test_geometria_ma_pierwszenstwo_nad_tekstem(self):
        doc = _doc([_node(ZYSK, 310), _node(RYZYKO, 360)])
        assert measure_proximity(doc).axis == "geometria"

    def test_bez_geometrii_uzywa_czasu(self):
        segs = [
            TranscriptSegment(start=1.0, end=2.0, text="zarobisz duzo"),
            TranscriptSegment(start=2.0, end=3.0, text="ryzyko straty"),
        ]
        assert measure_proximity(_doc(nodes=None, text="", segments=segs)).axis == "czas"

    def test_bez_geometrii_i_czasu_uzywa_tekstu(self):
        assert measure_proximity(_doc(nodes=None, text=f"{ZYSK} {RYZYKO}")).axis == "tekst"

    def test_mierniki_zwracaja_none_bez_danych(self):
        pusty = _doc(nodes=None, text="")
        assert measure_geometry(pusty) is None
        assert measure_timeline(pusty) is None
        assert measure_text(pusty) is None


class TestProgowZKonfiguracji:
    def test_progi_pochodza_z_thresholds_yaml(self):
        from analyzer.config_loader import get_threshold

        assert get_threshold("rules.rule_3.max_distance_px", None) == 600
        assert get_threshold("rules.rule_3.max_offset_chars", None) == 300
        assert get_threshold("rules.rule_3.max_gap_seconds", None) == 5.0


class TestProporcjonalnosciCzcionki:
    """Os geometrii: dowod proporcji ryzyko/zysk (nie zmienia werdyktu)."""

    @staticmethod
    def _n(text: str, y: float, font: float) -> TextNode:
        return _node(text, y).model_copy(update={"font_px": font})

    def test_pass_zawiera_miary_czcionek(self):
        r = assess_rule_3(_doc([self._n(ZYSK, 310, 32), self._n(RYZYKO, 360, 9)]))
        assert r.verdict is Verdict.PASS
        m = r.evidence.measured
        assert m["font_zysku_px"] == 32
        assert m["font_ryzyka_px"] == 9
        assert m["proporcja_font_ryzyko_do_zysku"] == 0.28
        assert "9 px wobec 32 px" in r.evidence.summary
        assert "0,28" in r.evidence.summary

    def test_fail_zawiera_miary_czcionek(self):
        r = assess_rule_3(_doc([self._n(ZYSK, 310, 32), self._n(RYZYKO, 4080, 9)]))
        assert r.verdict is Verdict.FAIL
        assert r.evidence.measured["proporcja_font_ryzyko_do_zysku"] == 0.28
        assert "0,28" in r.evidence.summary

    def test_werdykt_nie_zalezy_od_czcionki(self):
        r = assess_rule_3(_doc([self._n(ZYSK, 310, 32), self._n(RYZYKO, 360, 1)]))
        assert r.verdict is Verdict.PASS

    def test_inne_osie_nie_maja_pol_czcionek(self):
        r = assess_rule_3(_doc(nodes=None, text=f"{ZYSK} {RYZYKO}"))
        assert "font_zysku_px" not in r.evidence.measured
        assert "Czcionka ostrzezenia" not in r.evidence.summary
        p = measure_text(_doc(nodes=None, text=f"{ZYSK} {RYZYKO}"))
        assert p.profit_font_px is None and p.risk_font_px is None

    def test_proximity_geometrii_niesie_czcionki(self):
        p = measure_geometry(_doc([self._n(ZYSK, 310, 32), self._n(RYZYKO, 360, 9)]))
        assert p.profit_font_px == 32 and p.risk_font_px == 9


class TestWykluczeniaObietnicyZysku:
    def test_zastrzezenie_nie_jest_obietnica_zysku(self):
        doc = _doc(nodes=None, text="Jestesmy pod nadzorem KNF, co nie oznacza gwarancji zysku.")
        assert measure_text(doc) is None

    def test_stawka_podatku_nie_jest_obietnica_zysku(self):
        doc = _doc(nodes=None, text="Podatek od zyskow kapitalowych z ETF wynosi obecnie 19%.")
        assert measure_text(doc) is None

    def test_prawdziwa_obietnica_nadal_wykryta(self):
        assert measure_text(_doc(nodes=None, text="Bez ryzyka zarobisz 10%")) is not None

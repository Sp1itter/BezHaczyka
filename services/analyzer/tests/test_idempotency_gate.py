"""Testy bramy idempotencji przed kolejka GPU."""

from __future__ import annotations

from datetime import datetime, timezone

from analyzer.change_detect import GateDecision, should_analyze
from analyzer.contracts import AdDocument
from analyzer.embeddings import simhash_hex

_TEKST = "Inwestuj w obligacje i zarabiaj stabilnie, bez zadnego ryzyka dla Ciebie"


def _doc(text: str, with_hash: bool = True) -> AdDocument:
    return AdDocument(
        id="doc-1",
        source="test",
        url="http://localhost/x",
        fetched_at=datetime(2026, 11, 22, tzinfo=timezone.utc),
        text=text,
        simhash=simhash_hex(text) if with_hash else None,
    )


def test_pierwsze_zetkniecie_zawsze_analizujemy():
    # Review Focus 4: brak poprzednika to nie wyjatek i nie "zmiana".
    d = should_analyze(None, _doc(_TEKST))
    assert d == GateDecision(
        analyze=True, reason="pierwsze zetkniecie z materialem", kind=None
    )


def test_identyczny_material_nie_idzie_na_gpu():
    d = should_analyze(_doc(_TEKST), _doc(_TEKST))
    assert d.analyze is False
    assert d.reason == "material bez zmian, podbijam last_seen"


def test_zmieniony_material_idzie_na_gpu_z_powodem():
    d = should_analyze(_doc(_TEKST), _doc("Kup kryptowaluty, nowa oferta tylko dzis"))
    assert d.analyze is True
    assert "simhash" in d.reason


def test_brak_simhasha_nie_wywraca_bramy():
    # Brama sama dolicza simhash z tekstu.
    assert should_analyze(_doc(_TEKST, with_hash=False), _doc(_TEKST)).analyze is False
    assert should_analyze(_doc(_TEKST), _doc("inna tresc reklamy", with_hash=False)).analyze is True
    assert should_analyze(None, _doc(_TEKST, with_hash=False)).analyze is True


def test_reason_zawsze_niepusty():
    for prev, cur in [
        (None, _doc(_TEKST)),
        (_doc(_TEKST), _doc(_TEKST)),
        (_doc(_TEKST), _doc("zupelnie co innego")),
        (_doc(""), _doc("")),
    ]:
        assert should_analyze(prev, cur).reason.strip()

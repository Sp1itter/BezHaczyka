"""Testy Modulu 3 (shadow advisory). httpx.MockTransport — bez Ollamy."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import httpx

from analyzer.contracts import AdDocument, EvidenceKind, Verdict
from analyzer.llm import OllamaClient
from analyzer.module3 import (
    advisory_signals,
    assess_shadow_advisory,
    mentions_financial_instrument,
)

ADVICE = "Rekomendujemy akcje Alfa, sygnały kupna są jednoznaczne. Kupuj teraz!"


def _doc(text: str) -> AdDocument:
    return AdDocument(
        id="t",
        source="web",
        url="https://example.invalid/x",
        fetched_at=datetime(2026, 11, 21, tzinfo=timezone.utc),
        text=text,
    )


def _client(handler, calls: list | None = None) -> OllamaClient:
    def wrapped(request):
        if calls is not None:
            calls.append(request)
        return handler(request)

    return OllamaClient(
        client=httpx.Client(transport=httpx.MockTransport(wrapped), base_url="http://fake")
    )


def _ok(payload: dict):
    def handler(request):
        return httpx.Response(200, json={"response": json.dumps(payload, ensure_ascii=False)})

    return handler


def _boom(request):
    raise httpx.ConnectError("down")


FAIL = {
    "verdict": "fail",
    "confidence": 0.9,
    "summary": "Rekomendacja nabycia akcji.",
    "quote": "Rekomendujemy akcje Alfa",
}


def test_autoryzowany_nie_jest_fail():
    calls: list = []
    r = assess_shadow_advisory(
        _doc(ADVICE), publisher_is_authorized=True, client=_client(_ok(FAIL), calls)
    )
    assert r.verdict is Verdict.NOT_APPLICABLE
    assert "zezwolenie" in r.evidence.summary
    assert calls == []


def test_brak_sygnalow_model_nie_wolany():
    calls: list = []
    r = assess_shadow_advisory(
        _doc("Prowadzimy kawiarnię w Gdańsku."),
        publisher_is_authorized=False,
        client=_client(_ok(FAIL), calls),
    )
    assert r.verdict is Verdict.NOT_APPLICABLE
    assert calls == []


def test_family_office_bez_rekomendacji():
    calls: list = []
    r = assess_shadow_advisory(
        _doc("Butik family office i wealth management dla zamożnych rodzin."),
        publisher_is_authorized=False,
        client=_client(_ok(FAIL), calls),
    )
    assert r.verdict is Verdict.NOT_APPLICABLE
    assert calls == []


def test_rekomendacja_nieautoryzowany_fail_z_cytatem():
    r = assess_shadow_advisory(
        _doc(ADVICE), publisher_is_authorized=False, client=_client(_ok(FAIL))
    )
    assert r.rule_id == "M3"
    assert r.verdict is Verdict.FAIL
    assert r.severity == 5
    assert r.legal_basis == "art. 76 ustawy o obrocie instrumentami finansowymi"
    assert r.evidence.kind is EvidenceKind.QUOTE
    assert r.evidence.quote == "Rekomendujemy akcje Alfa"
    assert r.confidence == 0.9


def test_zmyslony_cytat_obniza_confidence():
    bad = {**FAIL, "quote": "Kupcie wszystko, gwarantujemy milion"}
    r = assess_shadow_advisory(
        _doc(ADVICE), publisher_is_authorized=False, client=_client(_ok(bad))
    )
    assert r.verdict is Verdict.FAIL
    assert r.confidence < 0.5
    assert r.evidence.quote is None
    assert "weryfikacji" in r.evidence.summary


def test_awaria_modelu_to_not_applicable():
    r = assess_shadow_advisory(
        _doc(ADVICE), publisher_is_authorized=False, client=_client(_boom)
    )
    assert r.verdict is Verdict.NOT_APPLICABLE


def test_nieznany_werdykt_to_not_applicable():
    r = assess_shadow_advisory(
        _doc(ADVICE),
        publisher_is_authorized=False,
        client=_client(_ok({"verdict": "maybe"})),
    )
    assert r.verdict is Verdict.NOT_APPLICABLE


def test_fleksja_sygnalow():
    for txt in ("Rekomendujemy to", "Nasza rekomendacja brzmi", "Rekomendacje tygodnia. Jest."):
        assert advisory_signals(txt), txt
    assert advisory_signals("Nasze sygnały kupna rosną")


def test_falszywy_przyjaciel_newsletter():
    assert advisory_signals("Polecamy nasz newsletter o rynkach") == []
    assert advisory_signals("Polecamy akcje Alfa")


def test_wykrywanie_instrumentu():
    assert mentions_financial_instrument("Kupuj akcje Alfa")
    assert mentions_financial_instrument("Handel kontraktami CFD")
    assert not mentions_financial_instrument("Akcja promocyjna w sklepie")

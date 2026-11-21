"""Testy reguly 10 (spojnosc jezykowa) rozstrzyganej deterministycznie.

Regresja na realny blad znaleziony na ZYWYM modelu: Bielik 4.5B uznawal
"Risk warning: investing involves risk and you may lose your capital"
w polskiej reklamie za zgodny z glownym przekazem. Dwie proby doprecyzowania
promptu nie pomogly, a zadanie jest w pelni mierzalne.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import httpx
import pytest

from analyzer.contracts import AdDocument, Engine, Verdict
from analyzer.llm import OllamaClient
from analyzer.rules_llm.batch_2 import RULE_META, evaluate_batch_2
from analyzer.rules_llm.lang_consistency import (
    assess_rule_10,
    detect_language,
    risk_sentences,
)

META_10 = RULE_META["10"]

POLSKA_Z_ANGIELSKIM_OSTRZEZENIEM = (
    "Inwestuj z nami i zarabiaj na rynku akcji oraz obligacji. "
    "Otworz rachunek w naszym domu maklerskim juz dzis. "
    "Risk warning: investing involves risk and you may lose all of your capital."
)
POLSKA_Z_POLSKIM_OSTRZEZENIEM = (
    "Inwestuj z nami i zarabiaj na rynku akcji oraz obligacji. "
    "Otworz rachunek w naszym domu maklerskim juz dzis. "
    "Inwestowanie wiaze sie z ryzykiem utraty kapitalu."
)


def _doc(text: str) -> AdDocument:
    return AdDocument(
        id="t",
        source="web",
        url="https://example.invalid/x",
        fetched_at=datetime(2026, 11, 21, tzinfo=timezone.utc),
        text=text,
    )


def _client(verdict_for_10: str) -> OllamaClient:
    payload = {
        "results": [
            {"rule_id": "9", "verdict": "pass", "confidence": 0.9, "summary": "ok"},
            {
                "rule_id": "10",
                "verdict": verdict_for_10,
                "confidence": 0.9,
                "summary": "model tak uznal",
            },
            {"rule_id": "11", "verdict": "pass", "confidence": 0.9, "summary": "ok"},
        ]
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"response": json.dumps(payload)})

    return OllamaClient(
        client=httpx.Client(transport=httpx.MockTransport(handler), base_url="http://fake")
    )


class TestDetectLanguage:
    def test_polski(self) -> None:
        assert detect_language("Inwestowanie wiaze sie z ryzykiem utraty kapitalu") == "pl"

    def test_angielski(self) -> None:
        assert detect_language("investing involves risk and you may lose your capital") == "en"

    def test_za_krotki_tekst_jest_niepewny(self) -> None:
        """Przy niepewnym pomiarze NIE wolno zwrocic fail."""
        assert detect_language("CFD") == "unknown"
        assert detect_language("") == "unknown"


class TestRiskSentences:
    def test_znajduje_polskie_ostrzezenie(self) -> None:
        assert any("ryzykiem" in s for s in risk_sentences(POLSKA_Z_POLSKIM_OSTRZEZENIEM))

    def test_znajduje_angielskie_ostrzezenie(self) -> None:
        assert any("Risk warning" in s for s in risk_sentences(POLSKA_Z_ANGIELSKIM_OSTRZEZENIEM))

    def test_brak_ostrzezenia(self) -> None:
        assert risk_sentences("Kup akcje naszej spolki i otworz rachunek.") == []


class TestAssessRule10:
    def test_angielskie_ostrzezenie_w_polskiej_reklamie_to_naruszenie(self) -> None:
        """Sedno naprawy — to jest przypadek, ktorego model nie lapal."""
        r = assess_rule_10(POLSKA_Z_ANGIELSKIM_OSTRZEZENIEM, META_10)
        assert r is not None
        assert r.verdict is Verdict.FAIL
        assert r.engine is Engine.HYBRID
        assert "art. 44 ust. 2 lit. f" in r.legal_basis
        assert r.evidence.quote is not None
        assert "Risk warning" in r.evidence.quote

    def test_polskie_ostrzezenie_w_polskiej_reklamie_jest_ok(self) -> None:
        r = assess_rule_10(POLSKA_Z_POLSKIM_OSTRZEZENIEM, META_10)
        assert r is not None
        assert r.verdict is Verdict.PASS

    def test_brak_ostrzezenia_oddaje_decyzje_modelowi(self) -> None:
        """Brak ostrzezenia to sprawa reguly 3, nie 10."""
        assert assess_rule_10("Kup akcje i otworz rachunek.", META_10) is None

    def test_niepewny_pomiar_oddaje_decyzje_modelowi(self) -> None:
        assert assess_rule_10("risk", META_10) is None


class TestOverrideWBatch2:
    def test_deterministyczny_fail_nadpisuje_pass_modelu(self) -> None:
        results = evaluate_batch_2(
            _doc(POLSKA_Z_ANGIELSKIM_OSTRZEZENIEM), _client("pass")
        )
        r10 = next(r for r in results if r.rule_id == "10")
        assert r10.verdict is Verdict.FAIL, (
            "deterministyczny pomiar musi miec pierwszenstwo nad werdyktem modelu"
        )
        assert r10.engine is Engine.HYBRID

    def test_deterministyczny_pass_nadpisuje_fail_modelu(self) -> None:
        """Dziala w obie strony — chroni tez przed falszywym alarmem modelu."""
        results = evaluate_batch_2(
            _doc(POLSKA_Z_POLSKIM_OSTRZEZENIEM), _client("fail")
        )
        r10 = next(r for r in results if r.rule_id == "10")
        assert r10.verdict is Verdict.PASS

    def test_pozostale_reguly_wsadu_zostaja_od_modelu(self) -> None:
        results = evaluate_batch_2(
            _doc(POLSKA_Z_ANGIELSKIM_OSTRZEZENIEM), _client("pass")
        )
        assert [r.rule_id for r in results] == ["9", "10", "11"]
        for r in results:
            if r.rule_id != "10":
                assert r.engine is Engine.LLM

    def test_niepewny_pomiar_zachowuje_werdykt_modelu(self) -> None:
        # ryzyko jest, ale material za krotki na pomiar jezyka -> werdykt modelu
        results = evaluate_batch_2(_doc("Kup. Ryzyko."), _client("fail"))
        r10 = next(r for r in results if r.rule_id == "10")
        assert r10.verdict is Verdict.FAIL
        assert r10.engine is Engine.LLM

    def test_brak_ryzyka_wymusza_not_applicable(self) -> None:
        results = evaluate_batch_2(_doc("Kup akcje teraz."), _client("pass"))
        r10 = next(r for r in results if r.rule_id == "10")
        assert r10.verdict is Verdict.NOT_APPLICABLE

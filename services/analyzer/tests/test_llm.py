"""Testy klienta Ollamy i promptu wsadowego nr 1.

Wszystko na httpx.MockTransport, wiec dziala BEZ zainstalowanej Ollamy
i bez pobranych modeli. Gdy modele sie pobiora, zostanie tylko smoke test
na zywo (tools/smoke_llm.py).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import httpx
import pytest

from analyzer.contracts import AdDocument, EvidenceKind, Verdict
from analyzer.llm import LlmError, OllamaClient
from analyzer.rules_llm.batch_1 import (
    RULE_META,
    evaluate_batch_1,
    quote_is_verifiable,
)

MATERIAL = (
    "Nasza inwestycja jest w pełni bezpieczna — spełniamy rygorystyczne "
    "wymogi nadzorcze KNF. Zyski do 18% rocznie."
)


def _doc(text: str = MATERIAL) -> AdDocument:
    return AdDocument(
        id="test-id",
        source="web",
        url="https://example.invalid/x",
        fetched_at=datetime(2026, 11, 21, tzinfo=timezone.utc),
        text=text,
    )


def _client(handler) -> OllamaClient:
    transport = httpx.MockTransport(handler)
    return OllamaClient(
        client=httpx.Client(transport=transport, base_url="http://fake")
    )


def _generate_handler(model_payload: dict, status: int = 200):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/generate"
        body = json.loads(request.content)
        # kontrakt z Ollama: wymuszony JSON i brak streamingu
        assert body["format"] == "json"
        assert body["stream"] is False
        return httpx.Response(
            status, json={"response": json.dumps(model_payload, ensure_ascii=False)}
        )

    return handler


# --------------------------------------------------------------------------- #
# Klient
# --------------------------------------------------------------------------- #


class TestOllamaClient:
    def test_generate_json_parsuje_odpowiedz(self):
        client = _client(_generate_handler({"results": []}))
        assert client.generate_json("prompt") == {"results": []}

    def test_niedostepna_ollama_daje_llmerror(self):
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("brak polaczenia")

        with pytest.raises(LlmError, match="niedostepna"):
            _client(handler).generate_json("prompt")

    def test_niepoprawny_json_od_modelu_daje_llmerror(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"response": "to nie jest json {{{"})

        with pytest.raises(LlmError, match="niepoprawny JSON"):
            _client(handler).generate_json("prompt")

    def test_blad_http_daje_llmerror(self):
        with pytest.raises(LlmError):
            _client(_generate_handler({}, status=500)).generate_json("prompt")

    def test_embed_obsluguje_nowy_ksztalt_odpowiedzi(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"embeddings": [[0.1, 0.2, 0.3]]})

        assert _client(handler).embed("tekst") == [0.1, 0.2, 0.3]

    def test_embed_obsluguje_stary_ksztalt_odpowiedzi(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"embedding": [0.4, 0.5]})

        assert _client(handler).embed("tekst") == [0.4, 0.5]

    def test_health_false_gdy_brak_serwera(self):
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("brak")

        assert _client(handler).health() is False


# --------------------------------------------------------------------------- #
# Weryfikacja cytatu — ochrona przed halucynacja
# --------------------------------------------------------------------------- #


class TestQuoteIsVerifiable:
    def test_cytat_obecny_w_materiale(self):
        assert quote_is_verifiable("w pełni bezpieczna", MATERIAL) is True

    def test_rozna_wielkosc_liter_jest_akceptowana(self):
        assert quote_is_verifiable("W PEŁNI BEZPIECZNA", MATERIAL) is True

    def test_zwiniete_biale_znaki_sa_akceptowane(self):
        assert quote_is_verifiable("w pełni\n  bezpieczna", MATERIAL) is True

    def test_zmyslony_cytat_jest_odrzucany(self):
        assert quote_is_verifiable("gwarantujemy zwrot kapitału", MATERIAL) is False

    def test_brak_cytatu(self):
        assert quote_is_verifiable(None, MATERIAL) is False

    def test_za_krotki_cytat_nic_nie_dowodzi(self):
        assert quote_is_verifiable("KNF", MATERIAL) is False


# --------------------------------------------------------------------------- #
# Prompt wsadowy nr 1
# --------------------------------------------------------------------------- #


class TestEvaluateBatch1:
    def test_zwraca_zawsze_cztery_reguly_w_stalej_kolejnosci(self):
        client = _client(_generate_handler({"results": []}))
        results = evaluate_batch_1(_doc(), client)
        assert [r.rule_id for r in results] == list(RULE_META)

    def test_poprawna_odpowiedz_mapuje_sie_na_ruleresult(self):
        payload = {
            "results": [
                {
                    "rule_id": "18",
                    "verdict": "fail",
                    "confidence": 0.9,
                    "summary": "Nadzór użyty jako gwarancja bezpieczeństwa.",
                    "quote": "w pełni bezpieczna — spełniamy rygorystyczne wymogi nadzorcze KNF",
                }
            ]
        }
        results = evaluate_batch_1(_doc(), _client(_generate_handler(payload)))
        r18 = next(r for r in results if r.rule_id == "18")
        assert r18.verdict is Verdict.FAIL
        assert r18.confidence == 0.9
        assert r18.severity == 5
        assert r18.evidence.kind is EvidenceKind.QUOTE
        assert r18.evidence.quote is not None
        assert "art. 44 ust. 8" in r18.legal_basis

    def test_zmyslony_cytat_obniza_confidence_i_oznacza_ustalenie(self):
        """Regula 18 twierdzi, ze cos w materiale JEST — jesli model nie
        potrafi tego wskazac, ustalenie zostaje, ale mocno odwazone."""
        payload = {
            "results": [
                {
                    "rule_id": "18",
                    "verdict": "fail",
                    "confidence": 1.0,
                    "summary": "Powołanie się na nadzór.",
                    "quote": "gwarantujemy zwrot kapitału przez KNF",
                }
            ]
        }
        results = evaluate_batch_1(_doc(), _client(_generate_handler(payload)))
        r18 = next(r for r in results if r.rule_id == "18")
        assert r18.verdict is Verdict.FAIL
        assert r18.confidence == pytest.approx(0.4)
        assert r18.evidence.quote is None
        assert "weryfikacji recznej" in r18.evidence.summary

    def test_fail_bez_cytatu_jest_ok_dla_reguly_o_braku(self):
        """Regula 2 (oznaczenie reklamy): `fail` znaczy, ze oznaczenia NIE MA,
        wiec nie ma czego cytowac i confidence nie jest obnizane."""
        payload = {
            "results": [
                {
                    "rule_id": "2",
                    "verdict": "fail",
                    "confidence": 0.95,
                    "summary": "Materiał nie jest oznaczony jako reklama.",
                    "quote": None,
                }
            ]
        }
        results = evaluate_batch_1(_doc(), _client(_generate_handler(payload)))
        r2 = next(r for r in results if r.rule_id == "2")
        assert r2.verdict is Verdict.FAIL
        assert r2.confidence == 0.95
        assert r2.evidence.kind is EvidenceKind.ABSENCE

    def test_awaria_modelu_daje_not_applicable_nie_fail(self):
        """Krytyczne: awaria Ollamy w trakcie demo nie moze wyprodukowac
        naruszen ani wywrocic potoku."""

        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("Ollama nie dziala")

        results = evaluate_batch_1(_doc(), _client(handler))
        assert len(results) == 4
        assert all(r.verdict is Verdict.NOT_APPLICABLE for r in results)
        assert all("niedostepny" in r.evidence.summary for r in results)

    def test_pominieta_regula_daje_not_applicable(self):
        payload = {"results": [{"rule_id": "1", "verdict": "pass", "confidence": 1.0}]}
        results = evaluate_batch_1(_doc(), _client(_generate_handler(payload)))
        r17 = next(r for r in results if r.rule_id == "17")
        assert r17.verdict is Verdict.NOT_APPLICABLE
        assert "pominal" in r17.evidence.summary

    def test_nieznany_werdykt_nie_wywraca_potoku(self):
        payload = {
            "results": [{"rule_id": "1", "verdict": "moze_byc", "confidence": 0.5}]
        }
        results = evaluate_batch_1(_doc(), _client(_generate_handler(payload)))
        r1 = next(r for r in results if r.rule_id == "1")
        assert r1.verdict is Verdict.NOT_APPLICABLE
        assert "nieznany werdykt" in r1.evidence.summary

    def test_confidence_poza_zakresem_jest_przycinane(self):
        payload = {
            "results": [{"rule_id": "1", "verdict": "fail", "confidence": 7.5}]
        }
        results = evaluate_batch_1(_doc(), _client(_generate_handler(payload)))
        r1 = next(r for r in results if r.rule_id == "1")
        assert r1.confidence == 1.0

    def test_confidence_nieliczbowe_nie_wywraca_potoku(self):
        payload = {
            "results": [{"rule_id": "1", "verdict": "fail", "confidence": "duza"}]
        }
        results = evaluate_batch_1(_doc(), _client(_generate_handler(payload)))
        r1 = next(r for r in results if r.rule_id == "1")
        assert 0.0 <= r1.confidence <= 1.0

    def test_brak_listy_results_daje_not_applicable(self):
        results = evaluate_batch_1(_doc(), _client(_generate_handler({"foo": "bar"})))
        assert all(r.verdict is Verdict.NOT_APPLICABLE for r in results)

    def test_pusty_material_nie_wola_modelu(self):
        def handler(request: httpx.Request) -> httpx.Response:
            raise AssertionError("Model nie powinien byc wolany dla pustego tekstu")

        results = evaluate_batch_1(_doc(text="   "), _client(handler))
        assert all(r.verdict is Verdict.NOT_APPLICABLE for r in results)

    def test_transkrypcja_wideo_trafia_do_promptu(self):
        """Reklama wideo musi byc oceniana tym samym promptem co tekstowa."""
        captured: dict[str, str] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["prompt"] = json.loads(request.content)["prompt"]
            return httpx.Response(200, json={"response": json.dumps({"results": []})})

        doc = AdDocument(
            id="v",
            source="tiktok",
            url="https://example.invalid/v",
            fetched_at=datetime(2026, 11, 21, tzinfo=timezone.utc),
            text="Opis pod filmem",
            transcript={  # type: ignore[arg-type]
                "engine": "faster-whisper-medium-int8",
                "lang": "pl",
                "text": "powiem wam jak zarobic osiemnascie procent",
                "segments": [],
            },
        )
        evaluate_batch_1(doc, _client(handler))
        assert "Opis pod filmem" in captured["prompt"]
        assert "osiemnascie procent" in captured["prompt"]

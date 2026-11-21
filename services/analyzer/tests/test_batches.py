"""Testy wsadow 2, 3, 4 i wspolnej logiki batching.py.

Wszystko na httpx.MockTransport — bez dzialajacej Ollamy.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import httpx
import pytest

from analyzer.contracts import AdDocument, EvidenceKind, Verdict
from analyzer.llm import OllamaClient
from analyzer.rules_llm import batch_2, batch_3, batch_4
from analyzer.rules_llm.batching import evaluate_batch

MATERIAL = (
    "Fundusz Alfa osiągnął w ostatnich 5 latach średnio 12% rocznie. "
    "Prognozujemy zysk 20% w przyszłym roku. Brak podatku Belki. "
    "Risk warning: capital at risk."
)

# (modul, funkcja, rule_id, cytat prawdziwy w MATERIAL)
BATCHES = [
    (batch_2, batch_2.evaluate_batch_2, "9", "Brak podatku Belki"),
    (batch_3, batch_3.evaluate_batch_3, "12a", "średnio 12% rocznie"),
    (batch_4, batch_4.evaluate_batch_4, "15", "Prognozujemy zysk 20%"),
]
IDS = ["batch_2", "batch_3", "batch_4"]


def _doc(text: str = MATERIAL) -> AdDocument:
    return AdDocument(
        id="test-id",
        source="web",
        url="https://example.invalid/x",
        fetched_at=datetime(2026, 11, 21, tzinfo=timezone.utc),
        text=text,
    )


def _client(handler) -> OllamaClient:
    return OllamaClient(
        client=httpx.Client(transport=httpx.MockTransport(handler), base_url="http://fake")
    )


def _ok(payload: dict):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"response": json.dumps(payload, ensure_ascii=False)}
        )

    return handler


def _by_id(results, rule_id):
    return next(r for r in results if r.rule_id == rule_id)


@pytest.mark.parametrize("mod,fn,rule_id,quote", BATCHES, ids=IDS)
class TestKazdyWsad:
    def test_kolejnosc_i_liczba_regul(self, mod, fn, rule_id, quote):
        results = fn(_doc(), _client(_ok({"results": []})))
        assert [r.rule_id for r in results] == list(mod.RULE_META)

    def test_poprawne_mapowanie(self, mod, fn, rule_id, quote):
        payload = {
            "results": [
                {
                    "rule_id": rule_id,
                    "verdict": "fail",
                    "confidence": 0.8,
                    "summary": "Naruszenie.",
                    "quote": quote,
                }
            ]
        }
        r = _by_id(fn(_doc(), _client(_ok(payload))), rule_id)
        name, severity, basis = mod.RULE_META[rule_id]
        assert r.verdict is Verdict.FAIL
        assert r.confidence == 0.8
        assert r.rule_name == name
        assert r.severity == severity
        assert r.legal_basis == basis
        assert r.evidence.kind is EvidenceKind.QUOTE
        assert r.evidence.quote == quote

    def test_awaria_modelu_daje_not_applicable_nie_fail(self, mod, fn, rule_id, quote):
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("Ollama nie dziala")

        results = fn(_doc(), _client(handler))
        assert len(results) == len(mod.RULE_META)
        assert all(r.verdict is Verdict.NOT_APPLICABLE for r in results)
        assert all("niedostepny" in r.evidence.summary for r in results)

    def test_pominieta_regula(self, mod, fn, rule_id, quote):
        results = fn(_doc(), _client(_ok({"results": []})))
        assert all(r.verdict is Verdict.NOT_APPLICABLE for r in results)
        assert all("pominal" in r.evidence.summary for r in results)

    def test_nieznany_werdykt(self, mod, fn, rule_id, quote):
        payload = {"results": [{"rule_id": rule_id, "verdict": "moze_byc"}]}
        r = _by_id(fn(_doc(), _client(_ok(payload))), rule_id)
        assert r.verdict is Verdict.NOT_APPLICABLE
        assert "nieznany werdykt" in r.evidence.summary

    def test_pusty_material_nie_wola_modelu(self, mod, fn, rule_id, quote):
        def handler(request: httpx.Request) -> httpx.Response:
            raise AssertionError("Model nie powinien byc wolany")

        results = fn(_doc(text="  "), _client(handler))
        assert all(r.verdict is Verdict.NOT_APPLICABLE for r in results)

    def test_prompt_zawiera_material_i_wszystkie_reguly(self, mod, fn, rule_id, quote):
        captured: dict[str, str] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["prompt"] = json.loads(request.content)["prompt"]
            return httpx.Response(200, json={"response": json.dumps({"results": []})})

        fn(_doc(), _client(handler))
        assert "Risk warning: capital at risk." in captured["prompt"]
        assert "{material}" not in captured["prompt"]
        for rid in mod.RULE_META:
            assert f'"rule_id": "{rid}"' in captured["prompt"] or f"Reguła {rid} " in captured["prompt"]


# Reguly, dla ktorych brak cytatu ma obnizac confidence (fail = cos JEST).
CITED = [
    # Regula 10 celowo POMINIETA: jest teraz hybrydowa i rozstrzygana
    # deterministycznie w lang_consistency.py, bo Bielik 4.5B konsekwentnie
    # uznawal angielskie ostrzezenie w polskiej reklamie za zgodne z przekazem.
    # Deterministyczny pomiar nie halucynuje cytatow, wiec zabezpieczenie
    # przed zmyslonym cytatem jej nie dotyczy. Pokrycie reguly 10 jest
    # w tests/test_lang_consistency.py.
    (batch_2.evaluate_batch_2, batch_2, r)
    for r in ("9", "11")
] + [
    (batch_3.evaluate_batch_3, batch_3, "12a"),
] + [(batch_4.evaluate_batch_4, batch_4, r) for r in ("15", "16")]


@pytest.mark.parametrize("fn,mod,rule_id", CITED, ids=[c[2] for c in CITED])
def test_zmyslony_cytat_obniza_confidence(fn, mod, rule_id):
    payload = {
        "results": [
            {
                "rule_id": rule_id,
                "verdict": "fail",
                "confidence": 1.0,
                "summary": "Cos jest.",
                "quote": "gwarantujemy zwrot kapitału przez KNF",
            }
        ]
    }
    r = _by_id(fn(_doc(), _client(_ok(payload))), rule_id)
    assert r.verdict is Verdict.FAIL
    assert r.confidence == pytest.approx(0.4)
    assert r.evidence.quote is None
    assert "weryfikacji recznej" in r.evidence.summary


class TestBatch3BrakCytatuNieKaraDlaAbsencji:
    def test_stale_fail_means_absence(self):
        assert batch_3.FAIL_MEANS_ABSENCE == {"12b", "14"}
        assert batch_2.FAIL_MEANS_ABSENCE == set()
        assert batch_4.FAIL_MEANS_ABSENCE == set()

    @pytest.mark.parametrize("rule_id", ["12b", "14"])
    def test_fail_bez_cytatu_nie_obniza_confidence(self, rule_id):
        payload = {
            "results": [
                {
                    "rule_id": rule_id,
                    "verdict": "fail",
                    "confidence": 0.9,
                    "summary": "Brak wymaganego ostrzeżenia.",
                    "quote": None,
                }
            ]
        }
        r = _by_id(batch_3.evaluate_batch_3(_doc(), _client(_ok(payload))), rule_id)
        assert r.verdict is Verdict.FAIL
        assert r.confidence == 0.9
        assert r.evidence.kind is EvidenceKind.ABSENCE
        assert "weryfikacji recznej" not in r.evidence.summary

    @pytest.mark.parametrize("rule_id", ["12b", "14"])
    def test_zmyslony_cytat_jest_odrzucony_ale_bez_kary(self, rule_id):
        payload = {
            "results": [
                {
                    "rule_id": rule_id,
                    "verdict": "fail",
                    "confidence": 0.9,
                    "summary": "Brak ostrzeżenia.",
                    "quote": "tego zdania nie ma w materiale",
                }
            ]
        }
        r = _by_id(batch_3.evaluate_batch_3(_doc(), _client(_ok(payload))), rule_id)
        assert r.confidence == 0.9
        assert r.evidence.quote is None
        assert r.evidence.kind is EvidenceKind.ABSENCE


def test_evaluate_batch_generyczny_respektuje_fail_means_absence():
    meta = {"X": ("Regula X", 2, "podstawa")}
    payload = {
        "results": [
            {"rule_id": "X", "verdict": "fail", "confidence": 1.0, "summary": "s"}
        ]
    }
    kwargs = dict(prompt_file="batch_2.txt", rule_meta=meta)
    kara = evaluate_batch(_doc(), _client(_ok(payload)), fail_means_absence=set(), **kwargs)
    bez = evaluate_batch(_doc(), _client(_ok(payload)), fail_means_absence={"X"}, **kwargs)
    assert kara[0].confidence == pytest.approx(0.4)
    assert bez[0].confidence == 1.0

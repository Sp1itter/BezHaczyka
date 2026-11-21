"""Testy bramki warunku wstepnego.

Regresja na realny blad znaleziony na ZYWYM modelu: Bielik 4.5B dawal `fail`
dla regul 12a, 12b i 14 na materiale z sama prognoza, bez zadnych wynikow
historycznych. Dwie proby doprecyzowania promptu nie pomogly, wiec warunek
rozstrzygamy deterministycznie w kodzie.
"""

from __future__ import annotations

from datetime import datetime, timezone

import httpx
import pytest

from analyzer.contracts import AdDocument, Verdict
from analyzer.llm import OllamaClient
from analyzer.rules_llm.batch_3 import evaluate_batch_3
from analyzer.rules_llm.batch_4 import evaluate_batch_4
from analyzer.rules_llm.preconditions import (
    mentions_forecast,
    mentions_forecast_or_tax,
    mentions_historical_performance,
    mentions_tax,
)

MATERIAL_PROGNOZA = (
    "Za rok zarobisz 20%! Nasza prognoza pokazuje dalsze wzrosty. "
    "Inwestowanie wiąże się z ryzykiem."
)
MATERIAL_HISTORYCZNY = (
    "Wyniki historyczne naszego funduszu: w 2024 roku stopa zwrotu wyniosła 12%."
)


def _doc(text: str) -> AdDocument:
    return AdDocument(
        id="t",
        source="web",
        url="https://example.invalid/x",
        fetched_at=datetime(2026, 11, 21, tzinfo=timezone.utc),
        text=text,
    )


def _client_that_must_not_be_called() -> OllamaClient:
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError(
            "Model NIE powinien byc wolany — warunek wstepny nie jest spelniony"
        )

    return OllamaClient(
        client=httpx.Client(transport=httpx.MockTransport(handler), base_url="http://fake")
    )


def _client_returning_fail(rule_ids: list[str]) -> OllamaClient:
    import json

    payload = {
        "results": [
            {
                "rule_id": rid,
                "verdict": "fail",
                "confidence": 0.9,
                "summary": "model twierdzi naruszenie",
                "quote": None,
            }
            for rid in rule_ids
        ]
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"response": json.dumps(payload)})

    return OllamaClient(
        client=httpx.Client(transport=httpx.MockTransport(handler), base_url="http://fake")
    )


class TestWynikiHistoryczne:
    @pytest.mark.parametrize(
        "tekst",
        [
            "Wyniki historyczne funduszu za ostatnie 5 lat",
            "w 2023 roku stopa zwrotu wyniosla 8%",
            "W ubieglym roku osiagnelismy 14%",
            "stopa zwrotu za 2024 r.",
            "od poczatku roku +9%",
            "w ostatnich 5 latach fundusz rosl",
            "wynik za 2022 byl dodatni",
            "kurs wzrosl o 12%",
            "YTD +4%",
        ],
    )
    def test_rozpoznaje_wyniki_historyczne(self, tekst: str) -> None:
        assert mentions_historical_performance(tekst)

    @pytest.mark.parametrize(
        "tekst",
        [
            "Za rok zarobisz 20%!",
            "Prognozujemy dalsze wzrosty",
            "Potencjalny zysk do 30%",
            "Zainwestuj dzis w akcje naszej spolki",
            "Oferujemy rachunek maklerski bez oplat",
        ],
    )
    def test_prognoza_nie_jest_wynikiem_historycznym(self, tekst: str) -> None:
        """To jest sedno naprawy: prognoza NIE uruchamia regul 12a/12b/14."""
        assert not mentions_historical_performance(tekst)


class TestBramkiWsadu3:
    def test_prognoza_daje_not_applicable_bez_wolania_modelu(self) -> None:
        """Regresja: zywy model dawal tu `fail` dla wszystkich trzech regul."""
        results = evaluate_batch_3(
            _doc(MATERIAL_PROGNOZA), _client_that_must_not_be_called()
        )
        assert len(results) == 3
        assert all(r.verdict is Verdict.NOT_APPLICABLE for r in results)
        assert all("wynikow historycznych" in r.evidence.summary for r in results)
        assert all("art. 44 ust. 4" in r.evidence.summary for r in results)

    def test_material_historyczny_przechodzi_bramke_do_modelu(self) -> None:
        results = evaluate_batch_3(
            _doc(MATERIAL_HISTORYCZNY),
            _client_returning_fail(["12a", "12b", "14"]),
        )
        assert [r.verdict for r in results] == [Verdict.FAIL] * 3

    def test_falszywy_alarm_nie_podnosi_score(self) -> None:
        """Przy zablokowanej bramce score musi byc 0.0 — brak podstaw to nie
        naruszenie."""
        from analyzer.scoring import risk_score

        results = evaluate_batch_3(
            _doc(MATERIAL_PROGNOZA), _client_that_must_not_be_called()
        )
        assert risk_score(results) == 0.0


class TestBramkiWsadu4:
    def test_brak_prognozy_i_podatkow_daje_not_applicable(self) -> None:
        results = evaluate_batch_4(
            _doc("Oferujemy rachunek maklerski bez oplat za prowadzenie."),
            _client_that_must_not_be_called(),
        )
        assert len(results) == 2
        assert all(r.verdict is Verdict.NOT_APPLICABLE for r in results)

    def test_sama_prognoza_przepuszcza_do_modelu(self) -> None:
        results = evaluate_batch_4(
            _doc(MATERIAL_PROGNOZA), _client_returning_fail(["15", "16"])
        )
        assert [r.verdict for r in results] == [Verdict.FAIL] * 2

    def test_sama_wzmianka_o_podatkach_przepuszcza_do_modelu(self) -> None:
        results = evaluate_batch_4(
            _doc("Zyski podlegaja opodatkowaniu podatkiem Belki."),
            _client_returning_fail(["15", "16"]),
        )
        assert [r.verdict for r in results] == [Verdict.FAIL] * 2

    @pytest.mark.parametrize(
        "tekst", ["prognoza zyskow", "szacujemy wzrost", "za rok", "potencjalny zysk"]
    )
    def test_rozpoznaje_prognoze(self, tekst: str) -> None:
        assert mentions_forecast(tekst)

    @pytest.mark.parametrize(
        "tekst", ["podatek Belki", "opodatkowanie zyskow", "ulga podatkowa", "PIT"]
    )
    def test_rozpoznaje_podatki(self, tekst: str) -> None:
        assert mentions_tax(tekst)

    def test_warunek_jest_alternatywa_nie_koniunkcja(self) -> None:
        """Material z prognoza ale bez podatkow MUSI przejsc — inaczej
        zgubilibysmy regule 15."""
        assert mentions_forecast_or_tax("prognoza zysku 20%")
        assert mentions_forecast_or_tax("podatek Belki wynosi 19%")
        assert not mentions_forecast_or_tax("rachunek maklerski bez oplat")

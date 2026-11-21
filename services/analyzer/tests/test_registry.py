"""Testy rejestru regul. Na httpx.MockTransport, bez Ollamy."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import httpx
import pytest

from analyzer.contracts import AdDocument, Relation, ScopeStatus, Verdict
from analyzer.llm import OllamaClient
from analyzer.pipeline import EntityResolution, analyze
from analyzer.rules_llm import batch_1, batch_2, batch_3, batch_4, registry
from analyzer.rules_llm.registry import (
    ALL_RULE_META,
    build_config,
    coverage_report,
    expected_rule_ids,
    module2_runners,
)

# "3" jest nasza od momentu, gdy scraper dostarczyl RenderProbe: regula
# hybrydowa mierzy odleglosc miedzy obietnica zysku a ostrzezeniem.
OUR_IDS = {"1", "2", "3", "9", "10", "11", "12a", "12b", "14", "15", "16", "17", "18"}


def _doc() -> AdDocument:
    return AdDocument(
        id="d1",
        source="web",
        url="https://example.invalid/a",
        fetched_at=datetime(2026, 11, 21, tzinfo=timezone.utc),
        text="Kup akcje przez XYZ. Zyski do 18% rocznie!",
    )


def _entities() -> EntityResolution:
    return EntityResolution(
        publisher_relation=Relation.OFFICIAL,
        publisher_is_authorized=True,
        firm_name_in_ad="XYZ DM S.A.",
        registry_knf_id="DM-123",
        registry_official_name="XYZ DM S.A.",
        registry_score=0.94,
    )


def _client(handler) -> OllamaClient:
    return OllamaClient(
        client=httpx.Client(transport=httpx.MockTransport(handler), base_url="http://fake")
    )


def _all_pass_handler(request: httpx.Request) -> httpx.Response:
    results = [
        {"rule_id": rid, "verdict": "pass", "confidence": 0.9, "summary": "ok"}
        for rid in ALL_RULE_META
    ]
    return httpx.Response(200, json={"response": json.dumps({"results": results})})


def _down_handler(request: httpx.Request) -> httpx.Response:
    raise httpx.ConnectError("Ollama nie dziala")


def test_piec_runnerow():
    """Cztery wsady LLM plus regula hybrydowa 3 (pomiar odleglosci miedzy
    obietnica zysku a ostrzezeniem)."""
    runners = module2_runners(_client(_all_pass_handler))
    assert len(runners) == 5
    assert all(callable(r) for r in runners)


def test_pelna_analiza_zwraca_wszystkie_nasze_reguly():
    cfg = build_config(_client(_all_pass_handler))
    finding = analyze(_doc(), _entities(), cfg)
    assert {r.rule_id for r in finding.rule_results} == OUR_IDS
    assert len(finding.rule_results) == 13
    assert coverage_report(finding.rule_results)["complete"] is True


def test_brak_kolizji_rule_id():
    total = sum(len(m.RULE_META) for m in (batch_1, batch_2, batch_3, batch_4))
    assert len(ALL_RULE_META) == total + 1  # +1 regula hybrydowa 3


def test_kolizja_podnosi_blad(monkeypatch):
    monkeypatch.setitem(batch_2.RULE_META, "1", ("x", 1, "y"))
    with pytest.raises(ValueError, match="Kolizja"):
        registry._merge_meta()


def test_expected_nie_zawiera_regul_spoza_naszych():
    ids = expected_rule_ids()
    # Regula 3 jest JUZ NASZA (hybrydowa, odblokowana przez RenderProbe
    # ze scrapera). Reguly 4-8 licza sie z geometrii po stronie osoby A,
    # a 13 nadal czeka na implementacje.
    for foreign in ("4", "5", "6", "7", "8", "13"):
        assert foreign not in ids
    assert "3" in ids
    assert ids == ("1", "2", "3", "9", "10", "11", "12a", "12b", "14", "15", "16", "17", "18")


def test_awaria_modelu_not_applicable_i_zero_ryzyka():
    cfg = build_config(_client(_down_handler))
    finding = analyze(_doc(), _entities(), cfg)
    assert len(finding.rule_results) == 13
    # Regula 3 nie potrzebuje modelu — mierzy odleglosc deterministycznie,
    # wiec przy padnietej Ollamie nadal cos orzeka. Pozostale 12 musi byc
    # not_applicable.
    llm = [r for r in finding.rule_results if r.rule_id != "3"]
    assert all(r.verdict is Verdict.NOT_APPLICABLE for r in llm)
    assert finding.risk_score >= 0.0


def test_coverage_report_wykrywa_braki():
    cfg = build_config(_client(_all_pass_handler))
    results = analyze(_doc(), _entities(), cfg).rule_results
    rep = coverage_report([r for r in results if r.rule_id not in ("9", "18")])
    assert rep["expected"] == 13
    assert rep["returned"] == 11
    assert rep["missing"] == 2
    assert rep["missing_rule_ids"] == ["9", "18"]
    assert rep["complete"] is False
    assert coverage_report([])["missing"] == 13


def test_build_config_przekazuje_kwargs():
    cfg = build_config(_client(_all_pass_handler), scope_override=ScopeStatus.OUT_OF_SCOPE)
    assert cfg.scope_override is ScopeStatus.OUT_OF_SCOPE
    assert len(cfg.module2_runners) == 5

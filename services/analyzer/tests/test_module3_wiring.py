"""Task 3b: Modul 2 dla kazdego materialu w zakresie + Modul 3 w potoku."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import httpx

from analyzer.contracts import AdDocument, Engine, Evidence, EvidenceKind, Relation, RuleResult, Verdict
from analyzer.llm import OllamaClient
from analyzer.module3 import advisory_signals, assess_shadow_advisory
from analyzer.pipeline import AnalyzerConfig, EntityResolution, analyze

DISCLAIMER = "Nasze wpisy nie stanowią porady inwestycyjnej ani rekomendacji. Dziś omawiamy rynek."
ADVICE = "Za opłatą wskażemy Ci obligacje i fundusze, które warto kupić w tym kwartale. Rekomendujemy akcje Beta."
VIRTUNE = "Virtune Solana ETP. Dostępny w XTB, BOŚ oraz Alior Banku. Inwestowanie wiąże się z ryzykiem."


def _doc(text: str, source: str = "web", **kw) -> AdDocument:
    return AdDocument(
        id="d1",
        source=source,
        url="https://example.invalid/a",
        fetched_at=datetime(2026, 11, 22, tzinfo=timezone.utc),
        text=text,
        **kw,
    )


def _fake_client(payload: dict, calls: list | None = None) -> OllamaClient:
    def handler(request):
        if calls is not None:
            calls.append(request)
        return httpx.Response(200, json={"response": json.dumps(payload, ensure_ascii=False)})

    return OllamaClient(
        client=httpx.Client(transport=httpx.MockTransport(handler), base_url="http://fake")
    )


def _runner(rule_id: str = "2"):
    def run(doc):
        return [
            RuleResult(
                rule_id=rule_id,
                rule_name="r",
                engine=Engine.LLM,
                verdict=Verdict.PASS,
                severity=3,
                legal_basis="art. 44",
                evidence=Evidence(kind=EvidenceKind.QUOTE, summary="x"),
            )
        ]

    return run


M3_FAIL = {"verdict": "fail", "confidence": 0.9, "summary": "rekomendacja", "quote": "Rekomendujemy akcje Beta"}


def test_disclaimer_nie_daje_sygnalu():
    assert advisory_signals(DISCLAIMER) == []


def test_pozytywny_tekst_daje_sygnal_i_fail():
    assert advisory_signals(ADVICE)
    calls: list = []
    res = assess_shadow_advisory(
        _doc(ADVICE), publisher_is_authorized=False, client=_fake_client(M3_FAIL, calls)
    )
    assert calls and res.rule_id == "M3" and res.verdict is Verdict.FAIL


def test_disclaimer_nie_wola_modelu():
    calls: list = []
    res = assess_shadow_advisory(
        _doc(DISCLAIMER), publisher_is_authorized=False, client=_fake_client(M3_FAIL, calls)
    )
    assert not calls and res.verdict is Verdict.NOT_APPLICABLE


def test_r2_reklama_trzeciej_strony_bez_zyskow_dostaje_modul2():
    f = analyze(
        _doc(VIRTUNE),
        EntityResolution(
            publisher_relation=Relation.THIRD_PARTY, mentions_authorized_firm=True
        ),
        AnalyzerConfig(module2_runners=[_runner()]),
    )
    assert f.routing.rule == "R2"
    assert 2 in f.modules
    assert any(r.rule_id == "2" for r in f.rule_results)


def test_poza_zakresem_bez_regul():
    f = analyze(
        _doc("Kredyt we frankach, unieważnienie umowy. Pomagamy frankowiczom.", source="youtube"),
        EntityResolution(),
        AnalyzerConfig(module2_runners=[_runner()]),
    )
    assert f.routing.scope_gate.value == "out_of_scope"
    assert f.rule_results == []
    assert f.routing.reason


def test_modul3_podpiety_w_potoku_i_ustawia_primary():
    calls: list = []
    f = analyze(
        _doc(ADVICE),
        EntityResolution(publisher_is_authorized=False),
        AnalyzerConfig(
            module2_runners=[_runner()], module3_client=_fake_client(M3_FAIL, calls)
        ),
    )
    m3 = [r for r in f.rule_results if r.rule_id == "M3"]
    assert calls and len(m3) == 1 and m3[0].verdict is Verdict.FAIL
    assert f.primary_module == 3
    assert f.risk_score >= 70


def test_modul3_pomijany_dla_zastrzezenia():
    calls: list = []
    f = analyze(
        _doc(DISCLAIMER),
        EntityResolution(publisher_is_authorized=False),
        AnalyzerConfig(module3_client=_fake_client(M3_FAIL, calls)),
    )
    assert not calls
    assert not any(r.verdict is Verdict.FAIL and r.rule_id == "M3" for r in f.rule_results)


def test_regula_2_guard_platformy_meta_ad_library():
    from analyzer.rules_llm.batch_1 import evaluate_batch_1

    payload = {
        "results": [
            {"rule_id": "1", "verdict": "pass", "confidence": 0.9, "summary": "ok", "quote": None},
            {"rule_id": "2", "verdict": "fail", "confidence": 0.9, "summary": "brak oznaczenia", "quote": None},
        ]
    }
    doc = _doc("Virtune Solana ETP dostępny w XTB.", source="facebook", is_paid_ad=True)
    res = evaluate_batch_1(doc, _fake_client(payload))
    r2 = next(r for r in res if r.rule_id == "2")
    assert r2.verdict is Verdict.PASS


def test_reanalyze_payload_jak_scraper():
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "tools" / "reanalyze.py"
    spec = importlib.util.spec_from_file_location("reanalyze", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    p = mod.build_payload({"case_id": "abc", "entity_resolution": {"publisher_relation": "third_party"}})
    assert set(p) == {"document_id", "enqueued_at", "entity_resolution", "det_results"}
    assert p["document_id"] == "abc" and p["det_results"] == []
    assert mod.QUEUE_NAME == "q:gpu" and mod.FUNC_NAME == "analyzer.worker.analyze_document"


# --- zbior deweloperski bramki (10 tekstow: 5 doradczych, 5 nie) ----------- #
DEV_ADVISORY = [
    "Zapisz się na nasz płatny kanał: w każdy poniedziałek podajemy 3 spółki do kupienia i cenę, przy której trzeba je sprzedać.",
    "Wypełnij ankietę, a nasz ekspert ułoży Ci portfel funduszy ETF dopasowany do Twojego wieku. Koszt 250 zł.",
    "Kupuj obligacje skarbowe 10-letnie, sprzedawaj akcje banków — to nasza strategia na jesień.",
    "Mamy dla Ciebie sygnały kupna na kontrakty terminowe. Wejście w pozycję długą na WIG20 zalecamy dziś.",
    "Jako doradca wskażemy Ci, w które fundusze zainwestować oszczędności i jaką alokację przyjąć.",
]
DEV_NOT = [
    "Prowadzimy kawiarnię w Gdańsku, zapraszamy na kawę.",
    "Webinar edukacyjny: czym jest obligacja i jak liczy się jej rentowność. Bez rekomendacji.",
    "Nie stanowimy rekomendacji ani porady inwestycyjnej. Inwestowanie wiąże się z ryzykiem.",
    "Oferujemy doradztwo podatkowe i księgowe dla firm. Umów konsultację.",
    "Fundusz Alfa osiągnął w 2025 roku wynik 8%. Dokument KID dostępny na stronie.",
]
# Z tej piatki do modelu docieraja tylko teksty z instrumentem (decyzje trafia model).
DEV_NOT_REACH_LLM = {1, 4}  # indeksy: edukacja o obligacji, wynik funduszu


import pytest


@pytest.mark.parametrize("text", DEV_ADVISORY)
def test_bramka_doradcze_docieraja_do_modelu(text):
    calls: list = []
    res = assess_shadow_advisory(
        _doc(text), publisher_is_authorized=False, client=_fake_client(M3_FAIL, calls)
    )
    assert calls, text


@pytest.mark.parametrize("i", range(len(DEV_NOT)))
def test_bramka_niedoradcze(i):
    calls: list = []
    assess_shadow_advisory(
        _doc(DEV_NOT[i]), publisher_is_authorized=False, client=_fake_client(M3_FAIL, calls)
    )
    assert bool(calls) == (i in DEV_NOT_REACH_LLM), DEV_NOT[i]


def test_brak_rekomendacji_to_negacja_bez_sygnalu():
    # Decyzja: "Brak rekomendacji" to zaprzeczenie (jak "nie stanowi rekomendacji"),
    # wiec nie jest sygnalem; bez wzmianki o instrumencie model nie jest wolany.
    assert advisory_signals("Brak rekomendacji? Jest.") == []

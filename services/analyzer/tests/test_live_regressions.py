"""Regresje z zywych danych (21.11) - falszywe alarmy zgloszone przez zespol.

Teksty czesciowo bez ogonkow: normalize() je i tak usuwa, a wzorce musza dzialac
tak samo z ogonkami i bez (warianty z ogonkami obok).
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from analyzer.contracts import (
    AdDocument,
    Engine,
    Evidence,
    EvidenceKind,
    RiskLevel,
    RuleResult,
    ScopeStatus,
    Verdict,
)
from analyzer.router import has_investment_recommendation, has_profit_claims
from analyzer.rules_hybrid import assess_rule_3
from analyzer.rules_llm.guards import apply_guards
from analyzer.scope_gate import classify_scope
from analyzer.scoring import HIGH_THRESHOLD, MEDIUM_THRESHOLD, risk_level, risk_score


# --- 1. profit regex -------------------------------------------------------- #

NOT_PROFIT = [
    "76% rachunkow inwestorow detalicznych traci pieniadze",
    "76% rachunków inwestorów detalicznych traci pieniądze",
    "Kody promocyjne Revolut - znizki do 90%",
    "Kody promocyjne Revolut - zniżki do 90%",
    "mBank przegral 99% spraw",
    "mBank przegrał 99% spraw",
    "Program Partnerski mBank: jak zaczac zarabiac",
    "Program Partnerski mBank: jak zacząć zarabiać",
]
PROFIT = [
    "zysk 12% rocznie",
    "stopa zwrotu 8%",
    "zarobilem 30% w miesiac",
    "oprocentowanie 7%",
    "nawet 15% zysku",
    # z holdout-2: procent ze znakiem i czasownik wzrostu
    "2023: +21%, 2024: +18% na funduszu akcji! W 2025 znow bedzie na plusie",
    "indeks WIG wzrosnie do konca 2027 roku o okolo 25%",
    "do 18% rocznie",
]


@pytest.mark.parametrize("text", NOT_PROFIT)
def test_nie_jest_obietnica_zysku(text):
    assert has_profit_claims(text) is False


@pytest.mark.parametrize("text", PROFIT)
def test_nadal_obietnica_zysku(text):
    assert has_profit_claims(text) is True


def test_regula_3_nie_traktuje_ostrzezenia_jako_obietnicy():
    doc = _doc("76% rachunkow inwestorow detalicznych traci pieniadze na CFD")
    assert assess_rule_3(doc).verdict is Verdict.NOT_APPLICABLE


# --- 2. negacja rekomendacji ------------------------------------------------ #

NOT_RECO = [
    "nie stanowi porady inwestycyjnej ani rekomendacji",
    "nasze wpisy nie sa rekomendacjami",
    "nasze wpisy nie są rekomendacjami",
    "materialy nie sa rekomendacja w rozumieniu przepisow",
    "żadna rekomendacja inwestycyjna",
]
RECO = [
    "rekomendujemy zakup akcji CD Projekt",
    "nasza rekomendacja: kupuj",
    "przygotujemy dla Ciebie indywidualna rekomendacje portfela",
    "doradzimy, w co zainwestowac",
]


@pytest.mark.parametrize("text", NOT_RECO)
def test_zastrzezenie_to_nie_rekomendacja(text):
    assert has_investment_recommendation(text) is False


@pytest.mark.parametrize("text", RECO)
def test_prawdziwa_rekomendacja(text):
    assert has_investment_recommendation(text) is True


# --- 3. brama zakresu ------------------------------------------------------- #

OUT_OF_SCOPE = [
    "Votum frankowicze: kredyt we frankach, uniewaznienie umowy kredytowej",
    "Kancelaria pomaga frankowiczom - unieważnienie umowy kredytu we frankach",
    "Kod promocyjny i kupon rabatowy - znizka 20% na zakupy",
    "KARTA WALUTOWA na wakacje - bez prowizji za przewalutowanie",
    "Karta kredytowa bonus 200 zl za pierwsza transakcje",
    "Telefon od osoby podajacej sie za przedstawiciela XTB - uwazaj na oszustow",
]
IN_SCOPE_INSTR = [
    "Kredyt we frankach a CFD na EUR/CHF",
    "Karta walutowa i konto maklerskie: kup akcje i ETF",
    "Oszustwo: ktos podaje sie za XTB i oferuje handel CFD z dzwignia",
    "Kod promocyjny do rachunku maklerskiego, bonus za obligacje",
]


@pytest.mark.parametrize("text", OUT_OF_SCOPE)
def test_poza_zakresem(text):
    s = classify_scope(text)
    assert s.status is ScopeStatus.OUT_OF_SCOPE
    assert s.reason


@pytest.mark.parametrize("text", IN_SCOPE_INSTR)
def test_sygnal_instrumentu_nie_wyklucza(text):
    assert classify_scope(text).status is not ScopeStatus.OUT_OF_SCOPE


def test_cfd_na_krypto_nadal_w_zakresie_a_spot_poza():
    assert classify_scope("CFD na bitcoina z dzwignia").status is ScopeStatus.IN_SCOPE
    assert classify_scope("kup bitcoina w naszym kantorze krypto").status is ScopeStatus.OUT_OF_SCOPE


# --- 4. regula 2: oznaczenie platformy -------------------------------------- #


def _res(rule_id, verdict, severity=3, confidence=0.9):
    return RuleResult(
        rule_id=rule_id, rule_name="r", engine=Engine.LLM, verdict=verdict,
        confidence=confidence, severity=severity, legal_basis="x",
        evidence=Evidence(kind=EvidenceKind.ABSENCE, summary="model"),
    )


@pytest.mark.parametrize(
    "text",
    ["Sponsorowane", "Materiał sponsorowany", "#reklama", "#ad", "Reklama", "współpraca reklamowa"],
)
def test_regula_2_oznaczenie_w_tekscie(text):
    out = apply_guards([_res("2", Verdict.FAIL)], f"Kup cos {text}")
    assert out[0].verdict is Verdict.PASS


def test_regula_2_metadane_platformy():
    out = apply_guards(
        [_res("2", Verdict.FAIL)], "Kup akcje teraz", doc_meta={"is_paid_ad": True}
    )
    assert out[0].verdict is Verdict.PASS
    assert "oznaczenie platformy" in out[0].evidence.summary


def test_regula_2_bez_metadanych_i_oznaczenia_zostaje_fail():
    out = apply_guards([_res("2", Verdict.FAIL)], "Kup akcje teraz", doc_meta={"source": "web"})
    assert out[0].verdict is Verdict.FAIL


# --- 5. regula 3 na dlugich tekstach ---------------------------------------- #


def _doc(text: str, source: str = "youtube") -> AdDocument:
    return AdDocument(
        id="t", source=source, url="https://example.invalid/a",
        fetched_at=datetime(2026, 11, 21, tzinfo=timezone.utc), text=text,
    )


def test_regula_3_dlugi_tekst_ostrzezenie_gdzies_indziej_lagodniej():
    text = "Zysk 12% rocznie z naszych strategii. " + ("opis filmu " * 60) + (
        "Inwestowanie wiaze sie z ryzykiem utraty kapitalu."
    )
    r = assess_rule_3(_doc(text))
    assert r.verdict is Verdict.FAIL
    assert r.confidence == 0.6
    assert r.severity == 3


def test_regula_3_brak_ostrzezenia_nadal_pelny_fail():
    r = assess_rule_3(_doc("Zysk 12% rocznie z naszych strategii."))
    assert r.verdict is Verdict.FAIL
    assert r.confidence == 1.0
    assert r.severity == 5


def test_regula_3_ostrzezenie_blisko_pass():
    r = assess_rule_3(_doc("Zysk 12% rocznie. Inwestowanie wiaze sie z ryzykiem utraty kapitalu."))
    assert r.verdict is Verdict.PASS


# --- 6. spojnosc score i poziomu -------------------------------------------- #


def test_poziom_high_ma_score_co_najmniej_high():
    results = [_res("3", Verdict.FAIL, severity=5, confidence=1.0)] + [
        _res(str(i), Verdict.PASS, severity=3) for i in range(8)
    ]
    score = risk_score(results)
    assert risk_level(score, results) is RiskLevel.HIGH
    assert score >= HIGH_THRESHOLD


def test_poziom_medium_ma_score_co_najmniej_medium():
    results = [_res("6", Verdict.FAIL, severity=4, confidence=1.0)] + [
        _res(str(i), Verdict.PASS, severity=3) for i in range(8)
    ]
    score = risk_score(results)
    assert risk_level(score, results) is RiskLevel.MEDIUM
    assert score >= MEDIUM_THRESHOLD


def test_niska_pewnosc_nie_podnosi_score():
    results = [_res("7", Verdict.FAIL, severity=5, confidence=0.6)] + [
        _res(str(i), Verdict.PASS, severity=3) for i in range(8)
    ]
    assert risk_score(results) < MEDIUM_THRESHOLD

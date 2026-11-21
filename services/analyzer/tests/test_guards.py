"""Testy straznikow werdyktow (guards.py), warunku historycznego i reguly 10.

Kazdy straznik w obie strony: odpala / nie odpala.
"""

from __future__ import annotations

import pytest

from analyzer.contracts import Engine, Evidence, EvidenceKind, RuleResult, Verdict
from analyzer.rules_llm.guards import apply_guards, historical_years_covered
from analyzer.rules_llm.lang_consistency import apply_rule_10_override
from analyzer.rules_llm.preconditions import mentions_historical_performance
from analyzer.router import normalize


def _res(rule_id: str, verdict: Verdict, quote: str | None = None) -> RuleResult:
    return RuleResult(
        rule_id=rule_id,
        rule_name="r",
        engine=Engine.LLM,
        verdict=verdict,
        confidence=0.9,
        severity=3,
        legal_basis="x",
        evidence=Evidence(
            kind=EvidenceKind.QUOTE if quote else EvidenceKind.ABSENCE,
            summary="model",
            quote=quote,
        ),
    )


def _run(rule_id: str, verdict: Verdict, text: str) -> RuleResult:
    return apply_guards([_res(rule_id, verdict)], text)[0]


# ---- warunek historyczny (m2-14) ---------------------------------------- #


@pytest.mark.parametrize(
    "text",
    [
        "Wyniki w pełnych latach kalendarzowych 2019–2023: 2019 +6%, 2020 +1%.",
        "Fundusz: 2022 −5%, 2023 +8%.",
        "Stopy zwrotu w pełnych latach kalendarzowych (źródło: TFI).",
        "Wyniki 2019-2023 są dostępne.",
    ],
)
def test_historyczne_nowe_wzorce_odpalaja(text):
    assert mentions_historical_performance(text)


@pytest.mark.parametrize(
    "text",
    [
        "Prognoza 2026-2030: spodziewamy się wzrostów.",
        "W 2027: +8% to nasz cel.",
        "Zarobisz 20% za rok.",
    ],
)
def test_historyczne_przyszle_lata_nie_odpalaja(text):
    assert not mentions_historical_performance(text)


# ---- regula 2 ------------------------------------------------------------ #


@pytest.mark.parametrize(
    "text,quote",
    [
        ("REKLAMA. Zapraszamy do funduszu.", "REKLAMA"),
        ("Zapraszamy #ad do funduszu", "#ad"),
        ("To materiał promocyjny funduszu", "materiał promocyjny"),
        ("Wpis sponsorowany przez TFI", "sponsorowany"),
        ("Współpraca płatna z marką", "Współpraca płatna"),
    ],
)
def test_regula_2_oznaczenie_daje_pass_z_cytatem(text, quote):
    r = _run("2", Verdict.FAIL, text)
    assert r.verdict is Verdict.PASS
    assert r.evidence.quote == quote
    assert quote in text
    assert "rozstrzygniete w kodzie" in r.evidence.summary


def test_regula_2_bez_oznaczenia_zostaje_werdykt_modelu():
    r = _run("2", Verdict.FAIL, "Zapraszamy do funduszu, zarabiaj z nami.")
    assert r.verdict is Verdict.FAIL
    assert r.engine is Engine.LLM


def test_regula_2_nie_rusza_not_applicable():
    assert _run("2", Verdict.NOT_APPLICABLE, "REKLAMA. x").verdict is Verdict.NOT_APPLICABLE


# ---- regula 10 ------------------------------------------------------------ #

META10 = {"10": ("Spojnosc", 3, "art")}


def test_regula_10_bez_ryzyka_wymusza_na():
    out = apply_rule_10_override(
        [_res("10", Verdict.PASS)], "Zarobisz nawet 20% w skali roku. Zapisz sie.", META10
    )
    assert out[0].verdict is Verdict.NOT_APPLICABLE
    assert "regula 3" in out[0].evidence.summary


def test_regula_10_z_ryzykiem_dalej_oceniana():
    text = (
        "Zapraszamy do funduszu, ktory jest dla was i dla nas. "
        "Risk warning: investing involves risk and you may lose your capital."
    )
    out = apply_rule_10_override([_res("10", Verdict.PASS)], text, META10)
    assert out[0].verdict is Verdict.FAIL


# ---- regula 12a ------------------------------------------------------------ #


def test_12a_jeden_rok_pass_zamieniony_na_fail():
    r = _run("12a", Verdict.PASS, "Fundusz zyskał w 2021 roku aż 41%!")
    assert r.verdict is Verdict.FAIL
    assert "wykryto lat: 1" in r.evidence.summary


@pytest.mark.parametrize(
    "text",
    [
        "Wyniki 2019–2023: 2019 +6%, 2023 +8%.",
        "Stopa zwrotu w ostatnich 5 latach: 40%.",
        "Wyniki za 2019, 2020, 2021, 2022 i 2023.",
        "Fundusz działa od 2015 roku, wynik 70%.",
    ],
)
def test_12a_pelny_okres_zostaje_pass(text):
    assert _run("12a", Verdict.PASS, text).verdict is Verdict.PASS


def test_12a_nie_zamienia_fail_na_pass():
    assert _run("12a", Verdict.FAIL, "Wyniki 2019–2023").verdict is Verdict.FAIL


def test_historical_years_covered():
    assert historical_years_covered(normalize("2019-2022")) == (False, 2)
    assert historical_years_covered(normalize("2019-2023"))[0] is True


# ---- regula 12b ------------------------------------------------------------ #


def test_12b_pass_bez_walut_i_oplat_to_fail():
    r = _run("12b", Verdict.PASS, "Stopy zwrotu 2019 +5%. Wyniki historyczne nie gwarantuja.")
    assert r.verdict is Verdict.FAIL
    assert r.evidence.kind is EvidenceKind.ABSENCE


def test_12b_tylko_waluty_bez_oplat_to_fail():
    r = _run("12b", Verdict.PASS, "Zmiany kursów walut mogą wpływać na wynik.")
    assert r.verdict is Verdict.FAIL


def test_12b_waluty_i_oplaty_zostaje_pass():
    text = "Wynik pomniejszony o opłaty, a zmiany kursów walut mogą wpływać na wartość."
    assert _run("12b", Verdict.PASS, text).verdict is Verdict.PASS


# ---- regula 16 ------------------------------------------------------------- #


def test_16_belka_bez_zastrzezenia_to_fail():
    r = _run("16", Verdict.PASS, "Skorzystaj z braku podatku Belki na IKE.")
    assert r.verdict is Verdict.FAIL


@pytest.mark.parametrize(
    "text",
    [
        "Brak podatku Belki na IKE; traktowanie zależy od indywidualnej sytuacji klienta.",
        "Zwolnienie z podatku może ulec zmianie.",
        "Brak podatku, ale zmiany przepisów są możliwe.",
    ],
)
def test_16_z_zastrzezeniem_zostaje_pass(text):
    assert _run("16", Verdict.PASS, text).verdict is Verdict.PASS


# ---- regula 17 -------------------------------------------------------------- #


def test_17_aprobata_knf_to_fail_z_cytatem():
    text = (
        "REKLAMA. Fundusz Pi — produkt zatwierdzony przez KNF! "
        "Komisja Nadzoru Finansowego sprawdziła i pozytywnie oceniła nasz fundusz."
    )
    r = _run("17", Verdict.PASS, text)
    assert r.verdict is Verdict.FAIL
    assert r.evidence.quote and r.evidence.quote in text


@pytest.mark.parametrize(
    "text",
    [
        "Podlegamy nadzorowi KNF.",
        "Posiadamy zezwolenie KNF na prowadzenie działalności.",
        "Prospekt zatwierdzony przez KNF jest dostępny na stronie.",
        "Fundusz jest sprawdzony przez naszych analityków. Podlegamy nadzorowi KNF.",
    ],
)
def test_17_prawdziwa_informacja_nie_odpala(text):
    assert _run("17", Verdict.PASS, text).verdict is Verdict.PASS


def test_17_nie_zamienia_na_pass_i_nie_rusza_na():
    assert _run("17", Verdict.NOT_APPLICABLE, "zatwierdzony przez KNF").verdict is Verdict.NOT_APPLICABLE


# ---- regula 14 ------------------------------------------------------------- #


def test_14_wyniki_bez_zastrzezenia_to_fail():
    text = "W latach 2019-2023 fundusz zarobil srednio 9% rocznie. Dolacz juz dzis!"
    assert _run("14", Verdict.PASS, text).verdict is Verdict.FAIL


@pytest.mark.parametrize("text", [
    "Wyniki historyczne nie stanowią wiarygodnego wskaźnika przyszłych wyników.",
    "Przeszłe wyniki nie gwarantują osiągnięcia podobnych w przyszłości.",
    "Historyczne stopy zwrotu nie są gwarancją przyszłych zysków.",
    "Dotychczasowe wyniki nie są wskaźnikiem przyszłych rezultatów.",
])
def test_14_z_zastrzezeniem_zostaje_pass(text):
    assert _run("14", Verdict.PASS, text).verdict is Verdict.PASS


def test_14_fail_modelu_nie_jest_zmieniany():
    text = "Wyniki historyczne nie stanowią wiarygodnego wskaźnika przyszłych wyników."
    assert _run("14", Verdict.FAIL, text).verdict is Verdict.FAIL


# ---- reguly 17 i 18: warunek wstepny "odwolanie do organu nadzoru" -------- #
# Regresja z prawdziwego korpusu FB: Bielik dal fail 18 ("powoluje sie na
# nadzor KNF") dla reklamy apartamentu i ETP, w ktorych nie ma slowa o nadzorze.


@pytest.mark.parametrize("rule_id", ["17", "18"])
@pytest.mark.parametrize("text", [
    "To Twoj czas, zeby zainwestowac i zaczac odpoczywac nad Baltykiem.",
    "Virtune Staked Solana ETP jest notowany na GPW. Kapital narazony na ryzyko.",
])
def test_bez_odwolania_do_nadzoru_17_i_18_daja_pass(rule_id, text):
    """Brak odwolania do KNF SPELNIA art. 44 ust. 8 -> PASS (scoring liczy ocenione)."""
    for v in (Verdict.FAIL, Verdict.PASS):
        r = _run(rule_id, v, text)
        assert r.verdict is Verdict.PASS
        assert r.confidence == 1.0
        assert "nie sugeruje jego aprobaty" in r.evidence.summary


def test_bez_odwolania_do_nadzoru_not_applicable_zostaje():
    assert _run("17", Verdict.NOT_APPLICABLE, "Zwykla reklama.").verdict is Verdict.NOT_APPLICABLE


# ---- straznik 17: zaprzeczenie nie jest aprobata ------------------------- #


@pytest.mark.parametrize("text", [
    "KNF nie ocenia ani nie zatwierdza produktu.",
    "Produkt nie zostal zatwierdzony przez KNF.",
    "Fundusz bez zatwierdzenia KNF jest oferowany inaczej, a KNF nie zatwierdza produktow.",
])
def test_17_zaprzeczenie_nie_odpala(text):
    assert _run("17", Verdict.PASS, text).verdict is Verdict.PASS


@pytest.mark.parametrize("text", [
    "Produkt zatwierdzony przez KNF.",
    "Fundusz zaakceptowany przez KNF, wiec jest pewny.",
])
def test_17_aprobata_nadal_fail(text):
    assert _run("17", Verdict.PASS, text).verdict is Verdict.FAIL


# ---- regula 2: ogolne oznaczenia reklamy --------------------------------- #


@pytest.mark.parametrize("text", [
    "KOMUNIKAT MARKETINGOWY. Fundusz Gamma.",
    "Materialy reklamowe funduszu.",
    "Tresc sponsorowana: nowy ETF.",
    "Sponsorem odcinka jest Delta.",
    "Partner materialu: Delta. Zainwestuj.",
    "Super oferta #reklama",
    "#wspolpracaplatna z Delta",
    "Wpis oparty o wspolprace platna.",
])
def test_2_ogolne_oznaczenia_reklamy_daja_pass(text):
    assert _run("2", Verdict.FAIL, text).verdict is Verdict.PASS


@pytest.mark.parametrize("text", [
    "Moje ETF-y na emeryture #wspolpraca. Link w bio, aplikacja naszego partnera.",
    "Zainwestuj dzis w fundusz.",
])
def test_2_sam_wspolpraca_i_brak_oznaczenia_zostaja_werdyktem_modelu(text):
    assert _run("2", Verdict.FAIL, text).verdict is Verdict.FAIL


@pytest.mark.parametrize("text", [
    "Inwestycja w pelni bezpieczna - spelniamy rygorystyczne wymogi KNF.",
    "Jestesmy pod nadzorem Komisji Nadzoru Finansowego.",
    "Fundusz nadzorowany przez regulatora, wiec Twoje pieniadze sa bezpieczne.",
])
def test_z_odwolaniem_do_nadzoru_18_zostaje_werdyktem_modelu(text):
    assert _run("18", Verdict.FAIL, text).verdict is Verdict.FAIL

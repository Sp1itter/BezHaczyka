"""Fix round 1 dla regresji z zywych danych (przeglad Task 3a)."""

from __future__ import annotations

import pytest

from analyzer.contracts import ScopeStatus
from analyzer.router import has_profit_claims
from analyzer.scope_gate import classify_scope


@pytest.mark.parametrize(
    "text",
    [
        "Zainwestuj w zloto z kuponem rabatowym",
        "Zainwestuj w złoto z kuponem rabatowym",
        "Kod promocyjny do XTB",
        "Kupon rabatowy Trading 212",
    ],
)
def test_inwestowanie_i_brokerzy_nie_wypadaja_z_zakresu(text):
    assert classify_scope(text).status is not ScopeStatus.OUT_OF_SCOPE


def test_lokata_i_kod_promocyjny_poza_zakresem():
    assert classify_scope("Lokata 5% i kod promocyjny w banku").status is ScopeStatus.OUT_OF_SCOPE


def test_jedna_znizka_nie_wyklucza():
    assert classify_scope("zniżka na prowizje, handluj akcjami").status is not ScopeStatus.OUT_OF_SCOPE
    late = ("opis dlugiego filmu o inwestowaniu " * 15) + "znizka na prowizje"
    assert classify_scope(late).status is not ScopeStatus.OUT_OF_SCOPE


@pytest.mark.parametrize("text", ["12% w rok", "Do 18% w rok na obligacjach", "8% w skali roku"])
def test_procent_z_okresem_to_obietnica(text):
    assert has_profit_claims(text) is True


def test_przegral_w_rok_nadal_nie_obietnica():
    assert has_profit_claims("mBank przegral 99% spraw w rok") is False


def test_myslnik_slowny_nie_jest_znakiem_procentu():
    assert has_profit_claims("Revolut - 90% klientow zadowolonych") is False
    assert has_profit_claims("wynik -11,8% w 2022") is True


# --- zywy stos 22.11 02:25: gra "Hero Wars" dostala HIGH przez "+50% ALLY SPEED" ---
HERO_WARS = (
    "Hero Wars - 43 BILLION Archdemon Damage! Wodryn Event. Boss, we choose:\n\n"
    "HASTE EMBLEM\n\nIts effect gives:\n\n+50% ALLY SPEED\n\nbut also:\n\n+20% ENEMY SPEED"
)


def test_procent_ze_znakiem_w_grze_to_nie_zysk():
    assert not has_profit_claims(HERO_WARS)


def test_gra_bez_sygnalu_finansowego_poza_zakresem():
    assert classify_scope(HERO_WARS).status is ScopeStatus.OUT_OF_SCOPE


@pytest.mark.parametrize(
    "text",
    [
        "Mój portfel +21% w tym roku",
        "Akcje CD Projekt -11,8% od szczytu, ale ja dokupuję",
        "ETF na S&P 500: +25% YTD",
    ],
)
def test_procent_ze_znakiem_z_kontekstem_finansowym_to_zysk(text):
    assert has_profit_claims(text)


# --- zywy stos 22.11 03:00: rozrywka ze sponsorem cashback i promocje bankowe jako HIGH ---
@pytest.mark.parametrize(
    "text",
    [
        "Wariograf: Bad Boy o Miłosnych Zdradach Labrygi! Sponsor odcinka: Kupujesz jak zawsze, "
        "zyskujesz WIĘCEJ! Patron medialny: Super Express",
        "Najlepszy Bank - Jak Szybko Zarobić 430zł na Konto w Banku. Darmowe konto osobiste, "
        "promocje bankowe krok po kroku.",
        "Warunki i nagrody w programie poleceń PolecamBank mBank. Poleć znajomym konto i odbierz nagrodę.",
        "Jak otrzymać 100 zł od aplikacji Revolut – poradnik krok po kroku, załóż konto i zamów kartę.",
    ],
)
def test_rozrywka_i_promocje_bankowe_poza_zakresem(text):
    assert classify_scope(text).status is ScopeStatus.OUT_OF_SCOPE


@pytest.mark.parametrize(
    "text",
    [
        "Odbierz darmową akcję o wartości nawet do 100 PLN! Prowadzę Cię krok po kroku przez konto w XTB.",
        "Załóż konto maklerskie i zyskaj 8% rocznie na obligacjach",
        "Interactive Brokers: TLT PUT SELL na 1 dzień, premia z opcji",
    ],
)
def test_promocje_brokerskie_zostaja_w_zakresie(text):
    assert classify_scope(text).status is not ScopeStatus.OUT_OF_SCOPE


# --- test 20 min (22.11): fałszywe wysokie ryzyka spoza instrumentów finansowych ---
@pytest.mark.parametrize(
    "text",
    [
        "Apartamenty inwestycyjne przy plaży to pewny zysk. Harmony Resort w Kołobrzegu. "
        "Regulamin strony Assethome - Premium Real Estate",
        "Jak mieć dochód pasywny Inwestując w garaże? #inwestowanie #garaże #dochód",
    ],
)
def test_nieruchomosci_i_garaze_poza_zakresem(text):
    assert classify_scope(text).status is ScopeStatus.OUT_OF_SCOPE


def test_skrot_eth_tylko_jako_cale_slowo():
    # "assethome" zawiera "eth", ale to nie Ethereum
    assert classify_scope("Kupuj ETH i BTC na giełdzie kryptowalut").underlying == "crypto"
    assert classify_scope("Assethome - apartamenty nad morzem").underlying != "crypto"


def test_reklama_vinted_bez_sygnalu_finansowego_poza_zakresem():
    text = ("Zarabiaj na Vinted już dziś – zrób zdjęcie, dodaj ogłoszenie, powtórz. "
            "Więcej miejsca, więcej gotówki. Dużo miejsca, brak opłat. vinted.pl")
    assert classify_scope(text).status is ScopeStatus.OUT_OF_SCOPE

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

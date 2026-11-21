"""Testy bramy zakresu.

Najwazniejszy test w calym serwisie: CFD na kryptoaktywo MUSI zostac w zakresie.
Pierwotny design mial slownikowy filtr wykluczajacy slowa "krypto"/"bitcoin",
co wycielo by najagresywniej reklamowane produkty detaliczne pod nadzorem KNF.
"""

from analyzer.scope_gate import classify_scope
from analyzer.contracts import ScopeStatus


class TestCfdNaKryptoZostajeWZakresie:
    """Regresja na blad domenowy — art. 2 ust. 1 pkt 2 lit. h ustawy o obrocie."""

    def test_cfd_na_bitcoina_jest_w_zakresie(self):
        scope = classify_scope("Handluj CFD na Bitcoina z dzwignia 1:2 juz dzis!")
        assert scope.status is ScopeStatus.IN_SCOPE
        assert scope.instrument_wrapper == "cfd"
        assert scope.underlying == "crypto"
        assert "crypto_derivative" in scope.tags
        assert "lit. h" in (scope.legal_basis or "")

    def test_cfd_z_dzwignia_dostaje_tag_leveraged(self):
        scope = classify_scope("Kontrakty na różnicę na ETH, dźwignia 1:100")
        assert scope.status is ScopeStatus.IN_SCOPE
        assert "leveraged" in scope.tags

    def test_polskie_ogonki_sa_normalizowane(self):
        """'Kontrakt na Różnicę' musi trafic w klucz 'kontrakt na roznice'."""
        scope = classify_scope("Oferujemy Kontrakt na Różnicę na indeks WIG20")
        assert scope.status is ScopeStatus.IN_SCOPE
        assert scope.instrument_wrapper == "cfd"

    def test_etn_na_ethereum_jest_w_zakresie(self):
        scope = classify_scope("ETN na Ethereum dostepny na GPW")
        assert scope.status is ScopeStatus.IN_SCOPE
        assert scope.instrument_wrapper == "etn"

    def test_fundusz_z_ekspozycja_na_krypto_jest_w_zakresie(self):
        scope = classify_scope(
            "Fundusz inwestycyjny z ekspozycja na kryptoaktywa — tytul uczestnictwa"
        )
        assert scope.status is ScopeStatus.IN_SCOPE
        assert scope.underlying == "crypto"


class TestPozaZakresemTylkoBezOpakowania:
    def test_zakup_spot_bitcoina_jest_poza_zakresem(self):
        scope = classify_scope(
            "Kup bitcoina w naszym kantorze krypto i trzymaj we wlasnym portfelu"
        )
        assert scope.status is ScopeStatus.OUT_OF_SCOPE
        assert scope.reason == "spot_crypto_mica"

    def test_staking_jest_poza_zakresem(self):
        scope = classify_scope("Stakuj swoje tokeny i zarabiaj — gielda krypto")
        assert scope.status is ScopeStatus.OUT_OF_SCOPE
        assert scope.reason == "spot_crypto_mica"

    def test_nieruchomosc_jest_poza_zakresem(self):
        scope = classify_scope("Zainwestuj w apartament w Zakopanem")
        assert scope.status is ScopeStatus.OUT_OF_SCOPE
        assert scope.reason == "not_financial_instrument"


class TestNiepewneIdaDoTriage:
    def test_nierozpoznany_material_nie_jest_kasowany(self):
        """`uncertain`, nie `out_of_scope` — nadzorca musi to zobaczyc."""
        scope = classify_scope("Najlepsza okazja tego roku, nie przegap!")
        assert scope.status is ScopeStatus.UNCERTAIN
        assert scope.reason is not None


class TestZwykleInstrumenty:
    def test_akcje_sa_w_zakresie(self):
        scope = classify_scope("Kup akcje spolki technologicznej przez nasz rachunek")
        assert scope.status is ScopeStatus.IN_SCOPE
        assert scope.instrument_wrapper == "akcje"

    def test_akcje_spolki_kryptominingowej_sa_w_zakresie(self):
        """Opakowanie (akcje) decyduje, nie aktywo bazowe (krypto)."""
        scope = classify_scope("Akcje spolki zajmujacej sie kopaniem krypto")
        assert scope.status is ScopeStatus.IN_SCOPE
        assert scope.instrument_wrapper == "akcje"
        assert "crypto_derivative" in scope.tags

    def test_obligacje_sa_w_zakresie(self):
        scope = classify_scope("Obligacje korporacyjne z kuponem 8%")
        assert scope.status is ScopeStatus.IN_SCOPE
        assert scope.instrument_wrapper == "obligacje"

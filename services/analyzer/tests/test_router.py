"""Testy routera — par. 6.5 design doca. Pierwszenstwo R3 > R2 > R1."""

from analyzer.contracts import Relation, ScopeStatus
from analyzer.router import RoutingInput, has_profit_claims, route


def _inp(**kwargs) -> RoutingInput:
    defaults = dict(
        scope_status=ScopeStatus.IN_SCOPE,
        text="Zwykly material reklamowy",
        publisher_relation=Relation.UNKNOWN,
        publisher_is_authorized=False,
        mentions_authorized_firm=False,
    )
    defaults.update(kwargs)
    return RoutingInput(**defaults)  # type: ignore[arg-type]


class TestR1WlasnyMaterialFirmy:
    def test_oficjalny_kanal_idzie_do_modulu_2(self):
        d = route(
            _inp(
                publisher_relation=Relation.OFFICIAL,
                publisher_is_authorized=True,
                firm_name_in_ad="XYZ DM S.A.",
            )
        )
        assert d.modules == [2]
        assert d.primary_module == 2
        assert d.routing.rule == "R1"
        assert "XYZ DM S.A." in d.routing.reason


class TestR2PodmiotTrzeci:
    def test_finfluencer_idzie_do_modulu_1(self):
        d = route(
            _inp(
                publisher_relation=Relation.THIRD_PARTY,
                mentions_authorized_firm=True,
                publisher_name="@finfluencer_pl",
                firm_name_in_ad="XYZ DM S.A.",
            )
        )
        assert d.primary_module == 1
        assert d.routing.rule == "R2"

    def test_finfluencer_z_obietnica_zysku_dostaje_tez_modul_2(self):
        """Reklama podmiotu trzeciego obiecujaca zyski uruchamia wymog
        informacji o ryzyku — wiec oceniamy ja TEZ regulami Modulu 2."""
        d = route(
            _inp(
                text="Zarobisz 18% rocznie dzieki XYZ!",
                publisher_relation=Relation.THIRD_PARTY,
                mentions_authorized_firm=True,
            )
        )
        assert d.modules == [1, 2]
        assert d.primary_module == 1
        assert "Modulu 2" in d.routing.reason


class TestR3DoradztwoBezZezwolenia:
    def test_nieautoryzowany_z_rekomendacja_idzie_do_modulu_3(self):
        d = route(
            _inp(
                text="Nasz family office — rekomendujemy akcje i sygnaly kupna",
                publisher_is_authorized=False,
                publisher_name="Kowalski Wealth",
            )
        )
        assert d.primary_module == 3
        assert d.routing.rule == "R3"
        assert "art. 76" in d.routing.reason

    def test_sama_oferta_bez_rekomendacji_nie_odpala_r3(self):
        """'family office' bez rekomendacji nie jest jeszcze doradztwem
        inwestycyjnym w rozumieniu art. 76 — to chroni przed fala false positives."""
        d = route(
            _inp(
                text="Jestesmy family office z 20-letnim doswiadczeniem",
                publisher_is_authorized=False,
            )
        )
        assert d.primary_module != 3

    def test_r3_ma_pierwszenstwo_nad_r2(self):
        """Nieautoryzowany podmiot dajacy rekomendacje I wymieniajacy
        autoryzowana firme -> prymarnie Modul 3, bo brak zezwolenia jest
        naruszeniem powazniejszym niz brak ujawnienia wspolpracy."""
        d = route(
            _inp(
                text="Rekomendujemy akcje — sygnaly kupna od nas",
                publisher_relation=Relation.THIRD_PARTY,
                publisher_is_authorized=False,
                mentions_authorized_firm=True,
            )
        )
        assert d.primary_module == 3
        assert d.routing.rule == "R3"


class TestR4Triage:
    def test_nieustalony_podmiot_nadal_ocenia_modul_2(self):
        """Poprawka po integracji ze scraperem.

        Wczesniej R4 dawalo modules=[], czyli ZERO ocenionych regul. Na realnym
        dokumencie z Meta Ad Library (bez dopasowanego rejestru KNF) oznaczalo
        to, ze material nie byl oceniany w ogole, a razem z nim przepadaly
        wyniki regul DET policzone juz przez scraper.

        Wymogi art. 44 rozporzadzenia del. 2017/565 dotycza MATERIALU, nie
        statusu publikujacego, wiec Modul 2 jest ocena bazowa. `status: triage`
        nadal sygnalizuje, ze podmiot wymaga ustalenia przez czlowieka.
        """
        d = route(_inp(text="Losowy tekst bez sygnalow"))
        assert d.modules == [2]
        assert d.primary_module == 2
        assert d.routing.rule == "R4"
        assert "Modul 2" in d.routing.reason
        assert "rejestru KNF" in d.routing.reason

    def test_poza_zakresem_nie_jest_kasowany(self):
        """Dokument poza zakresem zachowujemy z powodem — nadzorca musi
        moc zweryfikowac, czego narzedzie nie ocenialo."""
        d = route(_inp(scope_status=ScopeStatus.OUT_OF_SCOPE))
        assert d.modules == []
        assert d.routing.scope_gate is ScopeStatus.OUT_OF_SCOPE
        assert "poza zakresem" in d.routing.reason.lower()


class TestHasProfitClaims:
    def test_wykrywa_obietnice_zysku(self):
        assert has_profit_claims("Zarobisz na tym krocie") is True
        assert has_profit_claims("Stopa zwrotu 12% rocznie") is True

    def test_nie_wykrywa_tam_gdzie_nie_ma(self):
        assert has_profit_claims("Informacja o naszej siedzibie") is False

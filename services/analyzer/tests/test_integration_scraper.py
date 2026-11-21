"""Testy integracji ze scraperem (PR #2, FacebookAdsSource osoby A).

Dzialaja na PRAWDZIWYCH fixtures ze scrapera, nie na atrapach:
  fixtures/contract-examples/facebook_ad_document.json
  fixtures/contract-examples/rule_result_facebook.json

Kazdy test tutaj odpowiada realnemu bledowi znalezionemu przy spinaniu obu
serwisow albo pilnuje granicy, ktora musi pozostac spojna. Zaden z tych bledow
nie byl widoczny w testach jednostkowych zadnego z serwisow osobno.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from analyzer.contracts import AdDocument, RuleResult, ScopeStatus, Verdict
from analyzer.pipeline import AnalyzerConfig, EntityResolution, analyze
from analyzer.scoring import coverage, risk_score

REPO_ROOT = Path(__file__).resolve().parents[3]
EXAMPLES = REPO_ROOT / "fixtures" / "contract-examples"
SCRAPER_CONTRACTS = REPO_ROOT / "services" / "scraper" / "contracts.py"

FB_DOC = EXAMPLES / "facebook_ad_document.json"
FB_RULES = EXAMPLES / "rule_result_facebook.json"

pytestmark = pytest.mark.skipif(
    not FB_DOC.exists(), reason="brak fixtures ze scrapera (PR #2 niezmergowany)"
)


def _doc() -> AdDocument:
    return AdDocument.model_validate(json.loads(FB_DOC.read_text(encoding="utf-8")))


def _det() -> list[RuleResult]:
    raw = json.loads(FB_RULES.read_text(encoding="utf-8"))
    return [RuleResult.model_validate(r) for r in raw]


# --------------------------------------------------------------------------- #
# Granica kontraktu — duplikat u osoby A nie moze sie rozjechac z naszym
# --------------------------------------------------------------------------- #


class TestGranicyKontraktu:
    """Interfejs i modele sa ZDUPLIKOWANE miedzy serwisami (zadnego
    services/common/, bo wymusiloby context: . w docker-compose). Te testy
    sa mechanizmem, ktory chroni duplikaty przed cichym rozjechaniem sie."""

    def test_dokument_ze_scrapera_waliduje_sie_naszym_modelem(self) -> None:
        doc = _doc()
        assert doc.source == "facebook"
        assert doc.text

    def test_wyniki_det_ze_scrapera_waliduja_sie_naszym_modelem(self) -> None:
        det = _det()
        assert {r.rule_id for r in det} == {"4", "5", "6", "7", "8"}

    def test_brak_pol_ignorowanych_po_cichu(self) -> None:
        """Walidacja pydantica domyslnie IGNORUJE nadmiarowe pola, wiec samo
        `model_validate` nie dowodzi zgodnosci. Porownujemy zbiory kluczy."""
        data = json.loads(FB_DOC.read_text(encoding="utf-8"))
        assert set(data) == set(AdDocument.model_fields), (
            "Ksztalt AdDocument rozjechal sie miedzy scraperem a analyzerem"
        )

    @pytest.mark.skipif(
        not SCRAPER_CONTRACTS.exists(), reason="brak services/scraper/contracts.py"
    )
    def test_modele_obu_serwisow_maja_identyczne_pola(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "scraper_contracts_under_test", SCRAPER_CONTRACTS
        )
        assert spec is not None and spec.loader is not None
        theirs = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = theirs
        spec.loader.exec_module(theirs)

        import analyzer.contracts as ours

        for nazwa in ("AdDocument", "RuleResult", "TextNode", "Evidence", "Scope"):
            a = getattr(ours, nazwa)
            b = getattr(theirs, nazwa)
            assert set(a.model_fields) == set(b.model_fields), (
                f"{nazwa}: pola rozjechaly sie miedzy serwisami"
            )


# --------------------------------------------------------------------------- #
# Brama zakresu na realnej reklamie
# --------------------------------------------------------------------------- #


class TestBramyZakresuNaRealnejReklamie:
    def test_etp_jest_rozpoznawany_a_nie_akcje_z_porownania(self) -> None:
        """Regresja: reklama Virtune Staked Solana ETP mowi "inwestowanie
        w Solane w podobny sposob jak zakup akcji". Bez wzorca na ETP
        wykrywalismy opakowanie "akcje" na podstawie PORÓWNANIA, a nie
        faktycznego instrumentu — wlasciwa decyzja z niewlasciwego powodu."""
        doc = _doc()
        analyze(doc, EntityResolution(), AnalyzerConfig())
        assert doc.scope.status is ScopeStatus.IN_SCOPE
        assert doc.scope.instrument_wrapper == "etp"
        assert doc.scope.legal_basis

    def test_krypto_etp_nie_wypada_jako_krypto(self) -> None:
        """Kryterium jest instrumentowe: ETP na kryptoaktywo to papier
        wartosciowy, wiec ZOSTAJE w zakresie."""
        doc = _doc()
        analyze(doc, EntityResolution(), AnalyzerConfig())
        assert doc.scope.status is ScopeStatus.IN_SCOPE


# --------------------------------------------------------------------------- #
# Przeplyw wynikow DET ze scrapera
# --------------------------------------------------------------------------- #


class TestPrzeplywuDetResults:
    def test_wyniki_det_trafiaja_do_findingu(self) -> None:
        f = analyze(_doc(), EntityResolution(), AnalyzerConfig(), det_results=_det())
        assert [r.rule_id for r in f.rule_results] == ["4", "5", "6", "7", "8"]

    def test_regula_7_lapie_ostrzezenie_za_progiem_zobacz_wiecej(self) -> None:
        """Heurystyka feedu osoby A: ostrzezenie dalej niz 125 znakow jest
        schowane za "Zobacz wiecej"."""
        f = analyze(_doc(), EntityResolution(), AnalyzerConfig(), det_results=_det())
        r7 = next(r for r in f.rule_results if r.rule_id == "7")
        assert r7.verdict is Verdict.FAIL
        assert r7.confidence < 1.0, "heurystyka feedu ma obnizona pewnosc"

    def test_typografia_meta_nie_podnosi_score(self) -> None:
        """R4, R5 i R8 sa not_applicable dla zrodla facebook (tekst sklada
        Meta, nie reklamodawca) i NIE moga wchodzic do mianownika scoringu."""
        f = analyze(_doc(), EntityResolution(), AnalyzerConfig(), det_results=_det())
        na = [r for r in f.rule_results if r.verdict is Verdict.NOT_APPLICABLE]
        assert {r.rule_id for r in na} == {"4", "5", "8"}
        assert coverage(f.rule_results) == pytest.approx(0.4)
        # 5 regul, ocenialne tylko 6 i 7; fail tylko 7
        assert f.risk_score == risk_score(f.rule_results)
        assert 0.0 < f.risk_score < 100.0

    def test_dokument_poza_zakresem_nie_dostaje_regul_det(self) -> None:
        """Material poza zakresem nie jest oceniany — takze wynikami DET,
        ktore scraper juz policzyl."""
        doc = _doc()
        doc.text = "Kup bitcoina w naszym kantorze krypto i trzymaj we wlasnym portfelu"
        doc.transcript = None
        f = analyze(doc, EntityResolution(), AnalyzerConfig(), det_results=_det())
        assert f.routing.scope_gate is ScopeStatus.OUT_OF_SCOPE
        assert f.rule_results == []
        assert f.risk_score == 0.0

    def test_brak_wynikow_det_nie_wywraca_potoku(self) -> None:
        f = analyze(_doc(), EntityResolution(), AnalyzerConfig(), det_results=None)
        assert f.rule_results == []
        assert f.risk_score == 0.0


# --------------------------------------------------------------------------- #
# Regula R4 — nieustalony podmiot
# --------------------------------------------------------------------------- #


class TestRegulyR4:
    """Regresja na najpowazniejszy blad integracyjny.

    Scraper oddaje dokument z `publisher.is_official_firm_channel = false`
    i bez dopasowania do rejestru KNF, bo rejestr jest po stronie resolvera.
    Przy pierwotnym R4 (modules=[]) oznaczalo to, ze KAZDA swiezo zescrapowana
    reklama trafiala do triage z ZEREM ocenionych regul — razem z gotowymi
    wynikami DET, za ktore scraper juz zaplacil renderem.
    """

    def test_nieustalony_podmiot_nadal_ocenia_modul_2(self) -> None:
        f = analyze(_doc(), EntityResolution(), AnalyzerConfig(), det_results=_det())
        assert f.routing.rule == "R4"
        assert f.modules == [2]
        assert f.primary_module == 2
        assert f.rule_results, "material w zakresie MUSI zostac oceniony"

    def test_status_triage_sygnalizuje_brak_podmiotu(self) -> None:
        f = analyze(_doc(), EntityResolution(), AnalyzerConfig(), det_results=_det())
        assert f.status == "triage"
        assert "rejestru KNF" in f.routing.reason
        assert "Modul 2" in f.routing.reason

    def test_powod_routingu_jest_czytelny_dla_nadzorcy(self) -> None:
        f = analyze(_doc(), EntityResolution(), AnalyzerConfig(), det_results=_det())
        assert len(f.routing.reason) > 60
        assert f.routing.reason[0].isupper()


# --------------------------------------------------------------------------- #
# Warstwa wektorowa liczona przez analyzer
# --------------------------------------------------------------------------- #


class TestWarstwyWektorowej:
    def test_analyzer_dolicza_simhash_ktorego_scraper_nie_ustawia(self) -> None:
        """Handoff osoby A: simhash, embedding, transcript i scope zostaja
        null — liczy je analyzer (par. 6.5)."""
        doc = _doc()
        assert doc.simhash is None, "fixture ma miec pusty simhash"
        analyze(doc, EntityResolution(), AnalyzerConfig())
        assert doc.simhash and len(doc.simhash) == 16

    def test_embedding_bez_klienta_zostaje_pusty_i_nie_wywraca(self) -> None:
        doc = _doc()
        analyze(doc, EntityResolution(), AnalyzerConfig(embed_client=None))
        assert doc.embedding is None


# --------------------------------------------------------------------------- #
# Worker: det_results z zadania kolejki
# --------------------------------------------------------------------------- #


class TestWorkeraZDetResults:
    def _api(self, doc: AdDocument):
        wyslane: list = []

        class FakeApi:
            def get_document(self, document_id: str) -> AdDocument:
                return doc

            def post_finding(self, finding) -> None:
                wyslane.append(finding)

        return FakeApi(), wyslane

    def test_det_results_z_payloadu_trafiaja_do_findingu(self) -> None:
        from analyzer.worker import handle_job

        doc = _doc()
        api, wyslane = self._api(doc)
        payload = {
            "document_id": doc.id,
            "det_results": json.loads(FB_RULES.read_text(encoding="utf-8")),
        }
        finding = handle_job(payload, api=api)  # type: ignore[arg-type]
        assert finding is not None
        assert [r.rule_id for r in finding.rule_results] == ["4", "5", "6", "7", "8"]
        assert wyslane and wyslane[0] is finding

    def test_niepoprawny_wynik_det_jest_pomijany_a_nie_fatalny(self) -> None:
        """Lepiej ocenic dokument niepelnym zestawem regul (coverage to pokaze)
        niz nie ocenic go wcale."""
        from analyzer.worker import handle_job

        doc = _doc()
        api, _ = self._api(doc)
        poprawne = json.loads(FB_RULES.read_text(encoding="utf-8"))
        payload = {
            "document_id": doc.id,
            "det_results": [poprawne[0], {"rule_id": "X", "smieci": True}],
        }
        finding = handle_job(payload, api=api)  # type: ignore[arg-type]
        assert finding is not None
        assert [r.rule_id for r in finding.rule_results] == ["4"]

    def test_brak_det_results_w_payloadzie_jest_dozwolony(self) -> None:
        from analyzer.worker import handle_job

        doc = _doc()
        api, _ = self._api(doc)
        finding = handle_job({"document_id": doc.id}, api=api)  # type: ignore[arg-type]
        assert finding is not None
        assert finding.rule_results == []

    def test_det_results_nie_bedace_lista_sa_ignorowane(self) -> None:
        from analyzer.worker import handle_job

        doc = _doc()
        api, _ = self._api(doc)
        finding = handle_job(
            {"document_id": doc.id, "det_results": "nie lista"},  # type: ignore[arg-type]
            api=api,  # type: ignore[arg-type]
        )
        assert finding is not None
        assert finding.rule_results == []

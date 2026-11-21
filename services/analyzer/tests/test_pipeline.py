"""Testy potoku analizy i warstwy wektorowej."""

from __future__ import annotations

from datetime import datetime, timezone

import httpx
import pytest

from analyzer.contracts import (
    AdDocument,
    Engine,
    Evidence,
    EvidenceKind,
    RiskLevel,
    RuleResult,
    Relation,
    ScopeStatus,
    Verdict,
)
from analyzer.embeddings import (
    classify_similarity,
    cosine,
    embed_document_text,
    hamming_distance,
    is_near_duplicate_simhash,
    knn_score,
    normalize,
    simhash,
    simhash_hex,
    tokenize,
)
from analyzer.llm import OllamaClient
from analyzer.pipeline import AnalyzerConfig, EntityResolution, analyze


def _doc(text: str, doc_id: str = "d1") -> AdDocument:
    return AdDocument(
        id=doc_id,
        source="web",
        url="https://example.invalid/a",
        fetched_at=datetime(2026, 11, 21, tzinfo=timezone.utc),
        text=text,
    )


def _runner(results: list[RuleResult]):
    def run(doc: AdDocument) -> list[RuleResult]:
        return results

    return run


def _rule(rule_id: str, verdict: Verdict, severity: int = 3) -> RuleResult:
    return RuleResult(
        rule_id=rule_id,
        rule_name=f"regula {rule_id}",
        engine=Engine.LLM,
        verdict=verdict,
        severity=severity,
        legal_basis="art. 44",
        evidence=Evidence(kind=EvidenceKind.QUOTE, summary="x"),
    )


# --------------------------------------------------------------------------- #
# Potok
# --------------------------------------------------------------------------- #


class TestAnalyze:
    def test_material_firmy_idzie_do_modulu_2_i_jest_oceniany(self):
        doc = _doc("Kup akcje przez XYZ. Zyski do 18% rocznie!")
        entities = EntityResolution(
            publisher_relation=Relation.OFFICIAL,
            publisher_is_authorized=True,
            firm_name_in_ad="XYZ DM S.A.",
            registry_knf_id="DM-123",
            registry_official_name="XYZ DM S.A.",
            registry_score=0.94,
        )
        config = AnalyzerConfig(
            module2_runners=(_runner([_rule("18", Verdict.FAIL, severity=5)]),)
        )
        finding = analyze(doc, entities, config)

        assert finding.modules == [2]
        assert finding.primary_module == 2
        assert finding.routing.rule == "R1"
        assert finding.risk_score == 100.0
        assert finding.risk_level is RiskLevel.HIGH
        assert finding.entities.investment_firm.registry_match is not None
        assert finding.entities.investment_firm.registry_match.knf_id == "DM-123"
        assert finding.status == "new"

    def test_cfd_na_krypto_nie_wypada_z_zakresu(self):
        """Regresja na blad domenowy — caly potok, nie tylko brama."""
        doc = _doc("Handluj CFD na Bitcoina, dzwignia 1:2. Zyski do 30%!")
        finding = analyze(doc)
        assert finding.routing.scope_gate is ScopeStatus.IN_SCOPE

    def test_zakup_spot_krypto_nie_jest_oceniany_ale_zachowany(self):
        doc = _doc("Kup bitcoina w naszym kantorze krypto, wlasny portfel")
        config = AnalyzerConfig(
            module2_runners=(_runner([_rule("1", Verdict.FAIL)]),)
        )
        finding = analyze(doc, None, config)

        assert finding.routing.scope_gate is ScopeStatus.OUT_OF_SCOPE
        assert finding.modules == []
        assert finding.rule_results == []  # regul NIE uruchomiono
        assert finding.risk_score == 0.0
        assert "poza zakresem" in finding.routing.reason.lower()

    def test_finfluencer_z_zyskiem_dostaje_dwa_moduly_i_jest_oceniany(self):
        doc = _doc("Zarobisz 18% rocznie z XYZ! Link w bio.")
        entities = EntityResolution(
            publisher_relation=Relation.THIRD_PARTY,
            mentions_authorized_firm=True,
            publisher_name="@finfluencer_pl",
            firm_name_in_ad="XYZ DM S.A.",
            affiliate_link="https://example.invalid/?ref=x",
        )
        config = AnalyzerConfig(
            module2_runners=(_runner([_rule("2", Verdict.FAIL)]),)
        )
        finding = analyze(doc, entities, config)

        assert finding.modules == [1, 2]
        assert finding.primary_module == 1
        assert finding.rule_results, "Modul 2 w modules -> reguly MUSZA sie wykonac"
        assert finding.entities.advertiser.affiliate_link is not None

    def test_triage_dostaje_status_triage(self):
        finding = analyze(_doc("Akcje spolki technologicznej"))
        assert finding.routing.rule == "R4"
        assert finding.status == "triage"

    def test_awaria_runnera_nie_wywraca_potoku(self):
        """Krytyczne: padnieta regula nie moze zabic calej analizy na demo."""

        def broken(doc: AdDocument) -> list[RuleResult]:
            raise RuntimeError("Ollama padla w pol requestu")

        doc = _doc("Kup akcje przez XYZ. Zyski 18%!")
        entities = EntityResolution(
            publisher_relation=Relation.OFFICIAL, publisher_is_authorized=True
        )
        config = AnalyzerConfig(
            module2_runners=(broken, _runner([_rule("1", Verdict.PASS)]))
        )
        finding = analyze(doc, entities, config)

        assert len(finding.rule_results) == 2
        crashed = finding.rule_results[0]
        assert crashed.verdict is Verdict.NOT_APPLICABLE
        assert "zglosil blad" in crashed.evidence.summary
        # Awaria nie podniosla score'u
        assert finding.risk_score == 0.0

    def test_transkrypcja_wplywa_na_brame_zakresu(self):
        """Instrument moze byc wymieniony tylko w narracji wideo."""
        doc = AdDocument(
            id="v1",
            source="tiktok",
            url="https://example.invalid/v",
            fetched_at=datetime(2026, 11, 21, tzinfo=timezone.utc),
            text="Link w bio!",
            transcript={  # type: ignore[arg-type]
                "engine": "faster-whisper",
                "lang": "pl",
                "text": "handluj kontraktami na roznice z dzwignia",
                "segments": [],
            },
        )
        finding = analyze(doc)
        assert finding.routing.scope_gate is ScopeStatus.IN_SCOPE

    def test_brak_regul_daje_poprawny_finding(self):
        """Faza, w ktorej reguly jeszcze nie istnieja, tez musi dzialac."""
        finding = analyze(_doc("Kup akcje przez XYZ"))
        assert finding.rule_results == []
        assert finding.risk_score == 0.0
        assert finding.id
        assert finding.document_id == "d1"


# --------------------------------------------------------------------------- #
# Warstwa wektorowa
# --------------------------------------------------------------------------- #


class TestNormalizacjaITokeny:
    def test_ogonki_i_interpunkcja_sa_usuwane(self):
        assert normalize("Zyski do 18%, już dziś!") == "zyski do 18 juz dzis"

    def test_tokeny_pomijaja_krotkie_slowa(self):
        assert "do" not in tokenize("Zyski do 18% rocznie")
        assert "zyski" in tokenize("Zyski do 18% rocznie")


class TestSimhash:
    def test_ten_sam_tekst_ma_ten_sam_hash(self):
        assert simhash("Zyski do 18% rocznie") == simhash("Zyski do 18% rocznie")

    def test_rozna_wielkosc_liter_nie_zmienia_hasha(self):
        assert simhash("ZYSKI DO 18%") == simhash("zyski do 18%")

    def test_literowka_daje_maly_dystans(self):
        a = "Inwestuj w akcje spolki technologicznej z naszym domem maklerskim"
        b = "Inwestuj w akcje spolki technologicznej z naszym domem maklerskim!"
        assert hamming_distance(simhash(a), simhash(b)) <= 6

    def test_rozne_reklamy_daja_duzy_dystans(self):
        a = "Inwestuj w akcje spolki technologicznej przez rachunek maklerski"
        b = "Kup apartament w Zakopanem i wynajmuj go turystom przez caly rok"
        assert hamming_distance(simhash(a), simhash(b)) > 6

    def test_hex_ma_stala_dlugosc(self):
        assert len(simhash_hex("cokolwiek")) == 16

    def test_pusty_tekst_nie_wywraca(self):
        assert simhash("") == 0

    def test_is_near_duplicate(self):
        assert is_near_duplicate_simhash("Zyski 18% rocznie z nami", "Zyski 18% rocznie z nami")


class TestCosine:
    def test_identyczne_wektory(self):
        assert cosine([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == pytest.approx(1.0)

    def test_przeciwne_wektory(self):
        assert cosine([1.0, 0.0], [-1.0, 0.0]) == pytest.approx(-1.0)

    def test_prostopadle_wektory(self):
        assert cosine([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)

    def test_rozne_dlugosci_nie_rzucaja(self):
        assert cosine([1.0], [1.0, 2.0]) == 0.0

    def test_wektor_zerowy_nie_dzieli_przez_zero(self):
        assert cosine([0.0, 0.0], [1.0, 2.0]) == 0.0

    def test_pusty_wektor(self):
        assert cosine([], [1.0]) == 0.0


class TestClassifySimilarity:
    def test_duplikat_po_simhashu(self):
        assert classify_similarity(0.1, simhash_dist=2) == "duplicate"

    def test_duplikat_po_cosine(self):
        assert classify_similarity(0.97) == "duplicate"

    def test_wariant_kampanii(self):
        assert classify_similarity(0.90) == "same_campaign"

    def test_rozne_materialy(self):
        assert classify_similarity(0.40) == "unrelated"


class TestKnnScore:
    def test_za_maly_zbior_daje_none(self):
        assert knn_score([1.0, 0.0], [([1.0, 0.0], True)], k=5) is None

    def test_sasiedzi_naruszajacy_daja_wysoki_score(self):
        labelled = [([1.0, 0.0], True)] * 5
        assert knn_score([1.0, 0.0], labelled, k=5) == pytest.approx(1.0)

    def test_sasiedzi_czysci_daja_zero(self):
        labelled = [([1.0, 0.0], False)] * 5
        assert knn_score([1.0, 0.0], labelled, k=5) == pytest.approx(0.0)

    def test_pusty_wektor_daje_none(self):
        assert knn_score([], [([1.0], True)] * 5, k=5) is None


class TestEmbedDocumentText:
    def test_zwraca_embedding_z_wymiarem(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"embeddings": [[0.1, 0.2, 0.3]]})

        client = OllamaClient(
            client=httpx.Client(
                transport=httpx.MockTransport(handler), base_url="http://fake"
            )
        )
        emb = embed_document_text("jakis tekst", client)
        assert emb is not None
        assert emb.dim == 3
        assert emb.model == "bge-m3"

    def test_niedostepny_model_daje_none_nie_wyjatek(self):
        """Brak embeddingu to degradacja (dedup na simhashu), nie awaria."""

        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("brak Ollamy")

        client = OllamaClient(
            client=httpx.Client(
                transport=httpx.MockTransport(handler), base_url="http://fake"
            )
        )
        assert embed_document_text("tekst", client) is None

    def test_pusty_tekst_nie_wola_modelu(self):
        def handler(request: httpx.Request) -> httpx.Response:
            raise AssertionError("nie powinno byc wywolania")

        client = OllamaClient(
            client=httpx.Client(
                transport=httpx.MockTransport(handler), base_url="http://fake"
            )
        )
        assert embed_document_text("   ", client) is None

"""Potok analizy: AdDocument -> Finding.

To serce serwisu. Sklada w jedna calosc etapy z par. 6.5 design doca:

    ① transkrypcja         (stt — gdy sa media i brak transkryptu)
    ② embedding + simhash  (musi widziec transkrypt)
    ③ brama zakresu        (scope_gate)
    ④ resolver podmiotow   (dane od osoby A, wstrzykiwane jako EntityResolution)
    ⑤ router               (router)
    ⑥ ewaluacja regul      (rejestr regul: DET od A + LLM nasze)
    ⑦ scoring              (scoring)

KOLEJNOSC NIE JEST DOWOLNA. Transkrypcja idzie PIERWSZA, przed brama zakresu
i przed routerem, i NIE MOZE byc uzalezniona od modulu. To problem jajka i kury:
modul wyznacza router, router czyta sygnaly z tekstu, a w reklamie wideo te
sygnaly moga istniec WYLACZNIE w narracji. Gdybysmy transkrybowali tylko to,
co trafilo do Modulu 1, reklama finfluencera obiecujaca zyski glosem nie mialaby
w tekscie zadnego sygnalu, wiec router dalby R4 i nigdy nie dowiedzielibysmy sie,
ze nalezalo ja przetranskrybowac.
    ⑥ Finding              (gotowy JSON do POST /findings)

Reguly sa WSTRZYKIWANE, nie importowane na sztywno — dzieki temu potok
testuje sie bez Ollamy i bez RenderProbe, a dodanie reguly 19 nie wymaga
ruszania tego pliku.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Sequence

from analyzer.contracts import (
    AdDocument,
    AdvertiserRef,
    Entities,
    Finding,
    InvestmentFirmRef,
    RegistryMatch,
    Relation,
    RuleResult,
    Transcript,
    ScopeStatus,
    Verdict,
)
from analyzer.det_placeholders import missing_det_placeholders
from analyzer.router import RoutingInput, route
from analyzer.scope_gate import classify_scope
from analyzer.scoring import risk_level, risk_score

# Regula = cokolwiek, co ma `.rule_id` i `.evaluate(doc)`. Nie importujemy
# Protocol z rules_llm.base, zeby potok nie zalezal od warstwy LLM.
RuleLike = object
RuleRunner = Callable[[AdDocument], list[RuleResult]]

log = logging.getLogger(__name__)


@dataclass
class EntityResolution:
    """Ustalenia resolvera podmiotow — produkuje je osoba A.

    Potok ich nie wylicza; przyjmuje gotowe. Dzieki temu nie dubluje sie
    logika fuzzy matchingu, a my nie czekamy na rejestr KNF.
    """

    publisher_relation: Relation = Relation.UNKNOWN
    publisher_is_authorized: bool = False
    mentions_authorized_firm: bool = False
    publisher_name: str | None = None
    firm_name_in_ad: str | None = None
    registry_knf_id: str | None = None
    registry_official_name: str | None = None
    registry_score: float = 0.0
    disclosure_found: bool = False
    affiliate_link: str | None = None

    def to_entities(self) -> Entities:
        match = None
        if self.registry_knf_id or self.registry_official_name:
            match = RegistryMatch(
                knf_id=self.registry_knf_id,
                official_name=self.registry_official_name,
                score=self.registry_score,
            )
        return Entities(
            investment_firm=InvestmentFirmRef(
                name_in_ad=self.firm_name_in_ad,
                registry_match=match,
                is_authorized=self.publisher_is_authorized,
            ),
            advertiser=AdvertiserRef(
                name=self.publisher_name,
                relation_to_firm=self.publisher_relation,
                disclosure_found=self.disclosure_found,
                affiliate_link=self.affiliate_link,
            ),
        )


@dataclass
class AnalyzerConfig:
    """Co potok ma uruchomic. Puste listy = nic nie liczymy, co jest poprawne
    w fazie, w ktorej reguly jeszcze nie istnieja."""

    # Runnery regul Modulu 2 (18 regul). Kazdy zwraca liste RuleResult.
    module2_runners: Sequence[RuleRunner] = field(default_factory=tuple)
    # Czy nadpisac wynik bramy zakresu (gdy LLM rozstrzygnal `uncertain`).
    scope_override: ScopeStatus | None = None
    # Klient do policzenia embeddingu, gdy dokument go nie ma. None = pomijamy.
    # Brak embeddingu to degradacja (dedup na samym simhashu), nie awaria.
    embed_client: object | None = None
    # Producent transkryptu dla reklam z mediami. Wstrzykiwany, bo transkrypt
    # moze pochodzic albo z naszego faster-whisper (analyzer.stt), albo
    # od osoby A ze scrapera — potok nie musi wiedzieć skad.
    # None = nie transkrybujemy (transcript zostaje None, reguly degraduja sie
    # do not_applicable, nic sie nie wywraca).
    transcriber: Callable[[AdDocument], Transcript | None] | None = None


def analyze(
    doc: AdDocument,
    entities: EntityResolution | None = None,
    config: AnalyzerConfig | None = None,
    det_results: list[RuleResult] | None = None,
) -> Finding:
    """Przepusc dokument przez caly potok i zwroc gotowy Finding.

    Nie rzuca wyjatkami na brakujace dane. Dokument bez tekstu, bez
    RenderProbe albo poza zakresem daje poprawny Finding z uzasadnieniem —
    nadzorca musi widziec, czego narzedzie nie ocenialo.
    """
    entities = entities or EntityResolution()
    config = config or AnalyzerConfig()

    # --- ① transkrypcja -------------------------------------------------- #
    # MUSI byc przed brama zakresu, embeddingiem i routerem: instrument,
    # obietnica zysku albo rekomendacja moga wystapic tylko w narracji wideo.
    _ensure_transcript(doc, config)

    # --- ② reprezentacja wektorowa -------------------------------------- #
    # Scraper oddaje dokument z `simhash` i `embedding` ustawionymi na null —
    # liczy je analyzer (par. 6.5 i 6.7 design doca). Specyfikacja wymaga
    # reprezentacji wektorowej wprost, wiec to nie jest opcjonalne.
    _ensure_vector_representation(doc, config)

    # --- ① brama zakresu ------------------------------------------------ #
    # Liczymy na tekscie WRAZ z transkrypcja: reklama wideo moze wymieniac
    # instrument tylko w narracji.
    scope = classify_scope(doc.analyzable_text)
    if config.scope_override is not None:
        scope.status = config.scope_override
    doc.scope = scope

    # --- ③ router ------------------------------------------------------- #
    decision = route(
        RoutingInput(
            scope_status=scope.status,
            text=doc.analyzable_text,
            publisher_relation=entities.publisher_relation,
            publisher_is_authorized=entities.publisher_is_authorized,
            mentions_authorized_firm=entities.mentions_authorized_firm,
            firm_name_in_ad=entities.firm_name_in_ad,
            publisher_name=entities.publisher_name,
        )
    )

    # --- ④ ewaluacja regul --------------------------------------------- #
    results: list[RuleResult] = []
    if 2 in decision.modules:
        # Reguly DET (4, 5, 6, 7, 8) liczy SCRAPER z geometrii renderu i oddaje
        # je gotowe w zadaniu kolejki — analyzer nie ma RenderProbe w swojej
        # domenie i nie powtarza tych pomiarow. Doklejamy je do wynikow regul
        # LLM, zeby scoring widzial pelny obraz.
        if det_results:
            results.extend(det_results)
        # Brakujace reguly 4-8 -> wypelniacze not_applicable (widoczne w coverage).
        results.extend(missing_det_placeholders(doc, det_results))
        for runner in config.module2_runners:
            try:
                results.extend(runner(doc))
            except Exception as exc:  # noqa: BLE001
                # Padnieta regula nie moze wywrocic calego potoku w trakcie
                # demo. Logujemy przez evidence innych regul i idziemy dalej.
                results.append(_crashed_rule_result(runner, exc))

    # --- ⑤ scoring ------------------------------------------------------ #
    score = risk_score(results)

    return Finding(
        id=str(uuid.uuid4()),
        document_id=doc.id,
        primary_module=decision.primary_module,
        modules=decision.modules,
        routing=decision.routing,
        risk_score=score,
        # Poziom liczymy z DWOCH sygnalow: proporcji naruszonych wymogow (score)
        # oraz wagi najciezszego potwierdzonego naruszenia (results). Patrz
        # scoring.risk_level — bez tego drugiego sygnalu powazne naruszenie
        # rozcienczalo sie liczba regul, ktore material spelnia.
        risk_level=risk_level(score, results),
        rule_results=results,
        entities=entities.to_entities(),
        status="triage" if decision.routing.rule == "R4" else "new",
        created_at=datetime.now(timezone.utc),
    )


AUDIO_KINDS = ("video", "audio")


def _ensure_transcript(doc: AdDocument, config: AnalyzerConfig) -> None:
    """Dolicz transkrypt, gdy reklama ma media i jeszcze go nie ma.

    Warunek jest MEDIALNY, nie modulowy — patrz docstring modulu.

    Awaria transkrypcji NIE jest awaria analizy: transcript zostaje None,
    reguly oparte na osi czasu zwracaja not_applicable z powodem, a `coverage`
    pokazuje nadzorcy, ze material oceniono niepelnym zestawem. Lepiej ocenic
    reklame z samego opisu niz nie ocenic jej wcale.
    """
    if doc.transcript is not None or config.transcriber is None:
        return
    if not any(m.kind in AUDIO_KINDS for m in doc.media):
        return

    try:
        doc.transcript = config.transcriber(doc)
    except Exception as exc:  # noqa: BLE001
        log.warning(
            "Transkrypcja dokumentu %s nieudana (%s: %s) — analizuje bez niej",
            doc.id,
            type(exc).__name__,
            exc,
        )


def _ensure_vector_representation(doc: AdDocument, config: AnalyzerConfig) -> None:
    """Dolicz `simhash` i `embedding`, jesli dokument ich nie ma.

    `simhash` liczymy ZAWSZE — to czysta funkcja, bez modelu i bez kosztu.
    `embedding` tylko gdy podano klienta; jego brak degraduje dedup do samego
    simhasha, ale nie jest awaria i nie blokuje oceny regul.
    """
    from analyzer.embeddings import embed_document_text, simhash_hex

    text = doc.analyzable_text
    if not text.strip():
        return

    if not doc.simhash:
        doc.simhash = simhash_hex(text)

    if doc.embedding is None and config.embed_client is not None:
        doc.embedding = embed_document_text(text, config.embed_client)  # type: ignore[arg-type]


def _crashed_rule_result(runner: RuleRunner, exc: Exception) -> RuleResult:
    """Awaria runnera regul -> not_applicable z powodem, nigdy fail."""
    from analyzer.contracts import Engine, Evidence, EvidenceKind

    name = getattr(runner, "__name__", runner.__class__.__name__)
    return RuleResult(
        rule_id="?",
        rule_name=f"awaria runnera {name}",
        engine=Engine.LLM,
        verdict=Verdict.NOT_APPLICABLE,
        confidence=1.0,
        severity=1,
        legal_basis="",
        evidence=Evidence(
            kind=EvidenceKind.ABSENCE,
            summary=f"Runner regul zglosil blad: {type(exc).__name__}: {exc}",
        ),
    )

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
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
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
from analyzer.completeness import is_partial
from analyzer.det_placeholders import missing_det_placeholders
from analyzer.rules_det_fallback import det_fallback_results
from analyzer.router import RoutingInput, route
from analyzer.scope_gate import NO_SIGNAL_REASON, classify_scope
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
    # Wymieniona firma jest w rejestrze KNF. Nie podano -> wnioskujemy z registry_knf_id.
    firm_is_authorized: bool = False
    # Aktywnosc zezwolenia dopasowanej firmy (None: brak danych); false = cofniete.
    firm_license_active: bool | None = None
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
                is_authorized=self.firm_is_authorized
                or (bool(self.registry_knf_id) and self.firm_license_active is not False),
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
    # Klient LLM dla Modulu 3 (shadow advisory) — ten sam, ktory obsluguje wsady
    # Modulu 2. None = Modul 3 nie jest wolany (testy bez Ollamy); produkcyjny
    # build_config/default_config zawsze go ustawia.
    module3_client: object | None = None


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
    # Wideo/audio bez transkryptu (awaria STT): brak sygnalu w samym tytule nie
    # dowodzi braku sygnalu w narracji, wiec nie wykluczamy - zostaje do oceny.
    # Tylko przy bardzo krotkim tekscie (sam tytul): reklama z pelnym tekstem kreacji
    # bez zadnego sygnalu finansowego (np. "Zarabiaj na Vinted") jest poza zakresem.
    if (
        scope.status is ScopeStatus.OUT_OF_SCOPE
        and scope.reason == NO_SIGNAL_REASON
        and doc.transcript is None
        and len(doc.analyzable_text.strip()) < 120
        and any(m.kind in AUDIO_KINDS for m in doc.media)
    ):
        scope.status = ScopeStatus.UNCERTAIN
        scope.reason = "brak transkryptu wideo - nie mozna wykluczyc sygnalu w narracji"
    doc.scope = scope

    # ---③ router ------------------------------------------------------- #
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

    if scope.status is ScopeStatus.OUT_OF_SCOPE and scope.reason:
        # powod wykluczenia widoczny w routing (UI/API czyta routing, nie doc.scope)
        decision.routing.reason = f"{decision.routing.reason} Powod: {scope.reason}."

    # --- ④ ewaluacja regul --------------------------------------------- #
    results: list[RuleResult] = []
    # Modul 2 (art. 44) to ocena bazowa KAZDEGO materialu w zakresie, niezaleznie
    # od trasy R1-R4: trasa rozstrzyga o przypisaniu do Modulu 1/3, nie o tym,
    # czy ostrzezenie o ryzyku ma byc czytelne. Poza zakresem nie oceniamy.
    in_scope = scope.status is not ScopeStatus.OUT_OF_SCOPE
    if in_scope:
        # Reguly DET (4, 5, 6, 7, 8) liczy SCRAPER z geometrii renderu i oddaje
        # je gotowe w zadaniu kolejki — analyzer nie ma RenderProbe w swojej
        # domenie i nie powtarza tych pomiarow. Doklejamy je do wynikow regul
        # LLM, zeby scoring widzial pelny obraz.
        if det_results:
            results.extend(det_results)
        # Reguly 4-8 bez wyniku scrapera: liczymy z render_probe (fallback),
        # a gdy go brak — wypelniacze not_applicable (widoczne w coverage).
        fallback = det_fallback_results(doc, det_results)
        results.extend(fallback)
        results.extend(missing_det_placeholders(doc, [*(det_results or []), *fallback]))
        # Modul 3 biegnie w tej samej puli watkow co runnery Modulu 2.
        extra: list[RuleRunner] = []
        if 3 in decision.modules and config.module3_client is not None:
            extra.append(_module3_runner(entities, config.module3_client))
        results.extend(_run_module2(doc, config, extra))

    # --- straz niekompletnego materialu -------------------------------- #
    if is_partial(doc):
        results = [guard_partial_result(r) for r in results]

    # --- ⑤ scoring ------------------------------------------------------ #
    score = risk_score(results)

    primary_module = decision.primary_module
    if any(r.rule_id == "M3" and r.verdict is Verdict.FAIL for r in results):
        primary_module = 3

    return Finding(
        id=str(uuid.uuid4()),
        document_id=doc.id,
        primary_module=primary_module,
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


def _run_one(runner: RuleRunner, doc: AdDocument) -> list[RuleResult]:
    try:
        return list(runner(doc))
    except Exception as exc:  # noqa: BLE001
        # Padnieta regula nie moze wywrocic calego potoku w trakcie
        # demo. Logujemy przez evidence innych regul i idziemy dalej.
        return [_crashed_rule_result(runner, exc)]


def _module3_runner(entities: EntityResolution, client: object) -> RuleRunner:
    """Runner Modulu 3 w ksztalcie RuleRunner (doc -> [RuleResult])."""
    from analyzer.module3 import assess_shadow_advisory

    def run_module3(doc: AdDocument) -> list[RuleResult]:
        return [
            assess_shadow_advisory(
                doc,
                publisher_is_authorized=entities.publisher_is_authorized,
                client=client,  # type: ignore[arg-type]
            )
        ]

    return run_module3


def _run_module2(
    doc: AdDocument, config: AnalyzerConfig, extra: Sequence[RuleRunner] = ()
) -> list[RuleResult]:
    """Uruchom runnery Modulu 2 rownolegle; wyniki w kolejnosci runnerow.

    Wspolbieznosc: env LLM_BATCH_CONCURRENCY (domyslnie 4; 1 = sekwencyjnie).
    Kolejnosc wyniku jest identyczna jak w wersji sekwencyjnej, bo zbieramy
    po indeksie runnera, nie po czasie zakonczenia.
    """
    runners = [*config.module2_runners, *extra]
    try:
        conc = int(os.getenv("LLM_BATCH_CONCURRENCY", "4"))
    except ValueError:
        conc = 4
    workers = min(conc, len(runners))
    if workers <= 1:
        return [r for runner in runners for r in _run_one(runner, doc)]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_run_one, runner, doc) for runner in runners]
        return [r for f in futures for r in f.result()]


AUDIO_KINDS = ("video", "audio")

# Reguly, w ktorych FAIL znaczy "czegos BRAKUJE" w materiale. Przy czesciowej
# transkrypcji (klipy napisow <= 2 x 30 s) brak w klipie nie dowodzi braku w
# filmie, wiec taki FAIL degradujemy do not_applicable. Reguly "obecnosci"
# (material cos zawiera: 17, 18 ...) zostaja bez zmian.
ABSENCE_FAIL_RULES: dict[str, str] = {
    "1": "identyfikacji firmy",  # batch_1 FAIL_MEANS_ABSENCE
    "2": "oznaczenia reklamy",  # batch_1 FAIL_MEANS_ABSENCE
    "3": "ostrzezenia o ryzyku",  # regula hybrydowa: fail = brak/oddalenie ostrzezenia
    # 11, 12a, 15, 16: wyzwalacz (porownanie, wyniki, prognoza, podatki) jest
    # w materiale, ale fail orzeka o BRAKU zrodla / okresu / ostrzezenia /
    # zastrzezenia - ktore moze byc w niewidzianej czesci filmu. To, ze batch_2
    # i batch_4 maja pusty FAIL_MEANS_ABSENCE, dotyczy weryfikacji cytatu
    # (cytuja wyzwalacz), nie semantyki werdyktu.
    "11": "zrodla i zalozen porownania",
    "12a": "okresu referencyjnego i zrodla wynikow",
    "12b": "ostrzezenia o walucie i oplatach",  # batch_3 FAIL_MEANS_ABSENCE
    "14": "ostrzezenia przy wynikach historycznych",  # batch_3 FAIL_MEANS_ABSENCE
    "15": "ostrzezenia przy prognozie",
    "16": "zastrzezenia o indywidualnej sytuacji podatkowej",
}
# Swiadomie NIE na liscie: 10 (fail = ostrzezenie JEST, ale w innym jezyku),
# 9 (ostrzezenie jest, ale niezrozumiale), 13, 17, 18 (material cos zawiera
# lub eksponuje), DET 4-8 (pomiar renderu, nie tekstu).
_PARTIAL_SUMMARY_MAX = 200


def guard_partial_result(r: RuleResult) -> RuleResult:
    """FAIL reguly typu "brak" przy czesciowym materiale -> NOT_APPLICABLE."""
    from analyzer.contracts import Evidence, EvidenceKind

    if r.verdict is not Verdict.FAIL or r.rule_id not in ABSENCE_FAIL_RULES:
        return r
    old = r.evidence.summary or ""
    if len(old) > _PARTIAL_SUMMARY_MAX:
        old = old[:_PARTIAL_SUMMARY_MAX].rstrip() + "..."
    return r.model_copy(
        update={
            "verdict": Verdict.NOT_APPLICABLE,
            "confidence": 1.0,
            "evidence": Evidence(
                kind=EvidenceKind.ABSENCE,
                summary=(
                    "Material znany tylko we fragmentach (czesciowa transkrypcja) — "
                    f"braku {ABSENCE_FAIL_RULES[r.rule_id]} nie da sie stwierdzic. "
                    f"Pierwotne ustalenie modelu: {old}"
                ),
            ),
        }
    )


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

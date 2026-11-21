"""Kontrakty danych InvestWatch — ZAMROZONE. KOPIA serwisu scraper.

Zrodlo prawdy: docs/superpowers/specs/2026-11-21-investwatch-design.md par. 6.
Plik jest DOSLOWNA kopia services/analyzer/analyzer/contracts.py (bez
services/common/ — patrz par. 5). Przed rozjechaniem sie kopii chroni
tests/test_contracts.py, ktory waliduje te modele przeciw
fixtures/contract-examples/*.json — tak samo jak test w analyzerze.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

# --------------------------------------------------------------------------- #
# Slowniki wartosci
# --------------------------------------------------------------------------- #


class Engine(str, Enum):
    """Jakiego rodzaju dowodu wymaga regula."""

    DET = "DET"  # deterministyczny, z geometrii renderu (osoba A)
    LLM = "LLM"  # semantyczny, Bielik (osoba B)
    HYBRID = "HYBRID"  # jedno i drugie (reguly 3 i 13)


class Verdict(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    NOT_APPLICABLE = "not_applicable"


class EvidenceKind(str, Enum):
    MEASUREMENT = "measurement"  # liczba (reguly DET)
    QUOTE = "quote"  # doslowny cytat z materialu (reguly LLM)
    ABSENCE = "absence"  # czegos wymaganego brakuje


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ScopeStatus(str, Enum):
    IN_SCOPE = "in_scope"
    OUT_OF_SCOPE = "out_of_scope"
    UNCERTAIN = "uncertain"


class Relation(str, Enum):
    """Relacja reklamujacego do firmy inwestycyjnej."""

    OFFICIAL = "official"  # oficjalny kanal firmy
    THIRD_PARTY = "third_party"  # podmiot trzeci / finfluencer
    UNKNOWN = "unknown"


BackgroundConfidence = Literal["resolved", "assumed_canvas", "unknown"]
BehindInteraction = Literal["details", "accordion", "modal", "link", "hidden"]
ViewportName = Literal["desktop", "tablet", "mobile"]


# --------------------------------------------------------------------------- #
# RenderProbe — produkuje osoba A, konsumuja reguly DET i HYBRID
# --------------------------------------------------------------------------- #


class BBox(BaseModel):
    x: float
    y: float
    w: float
    h: float


class TextNode(BaseModel):
    """Jeden widoczny wezel tekstowy wraz z geometria renderu.

    Uwaga dla osoby A: `background_effective` to tlo WYZNACZONE przez wejscie
    w gore drzewa i kompozycje alfa, a nie `getComputedStyle().backgroundColor`
    samego wezla — ten prawie zawsze zwraca rgba(0, 0, 0, 0).
    """

    text: str
    font_px: float
    font_weight: int = 400
    color: str
    background_effective: str | None = None
    background_source: str | None = None
    background_confidence: BackgroundConfidence = "unknown"
    contrast_ratio: float | None = None
    bbox: BBox
    visible: bool = True
    clipped: bool = False
    behind_interaction: BehindInteraction | None = None
    collapsed_evidence: str | None = None
    dom_path: str = ""
    in_footer: bool = False


class ViewportProbe(BaseModel):
    dominant_font_px: float
    page_height_px: float
    nodes: list[TextNode] = Field(default_factory=list)


class RenderProbe(BaseModel):
    viewports: dict[str, ViewportProbe] = Field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Brama zakresu (par. 6.6)
# --------------------------------------------------------------------------- #


class Scope(BaseModel):
    """Czy material podlega naszym 18 regulom (rezim MiFID II).

    Kryterium jest INSTRUMENTOWE, nie aktywowe: decyduje opakowanie
    (CFD, ETN, fundusz, akcje...), a nie to, co jest aktywem bazowym.
    CFD na kryptoaktywo JEST instrumentem finansowym — art. 2 ust. 1 pkt 2
    lit. h ustawy o obrocie instrumentami finansowymi.
    """

    status: ScopeStatus = ScopeStatus.UNCERTAIN
    instrument_wrapper: str | None = None
    underlying: str | None = None
    legal_basis: str | None = None
    tags: list[str] = Field(default_factory=list)
    reason: str | None = None


# --------------------------------------------------------------------------- #
# Transkrypcja (speech-to-text)
# --------------------------------------------------------------------------- #


class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str

    @property
    def duration(self) -> float:
        return max(self.end - self.start, 1e-6)

    @property
    def chars_per_second(self) -> float:
        """Tempo mowy. Disclaimer czytany 2x szybciej niz reszta narracji
        to mierzalny sygnal ukrywania ryzyka."""
        return len(self.text) / self.duration


class Transcript(BaseModel):
    engine: str
    lang: str = "pl"
    text: str
    segments: list[TranscriptSegment] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# AdDocument — produkuje osoba A, konsumuje analyzer
# --------------------------------------------------------------------------- #


class Publisher(BaseModel):
    handle: str | None = None
    display_name: str | None = None
    profile_url: str | None = None
    is_official_firm_channel: bool = False


class MediaItem(BaseModel):
    kind: Literal["video", "audio", "image"]
    path: str
    duration_s: float | None = None


class Embedding(BaseModel):
    model: str = "bge-m3"
    dim: int = 1024
    vector: list[float] = Field(default_factory=list)


class AdDocument(BaseModel):
    id: str
    source: str
    url: str
    fetched_at: datetime
    publisher: Publisher = Field(default_factory=Publisher)
    lang: str = "pl"
    title: str | None = None
    text: str = ""
    html_path: str | None = None
    screenshots: dict[str, str] = Field(default_factory=dict)
    media: list[MediaItem] = Field(default_factory=list)
    transcript: Transcript | None = None
    render_probe: RenderProbe | None = None
    embedding: Embedding | None = None
    simhash: str | None = None
    scope: Scope = Field(default_factory=Scope)

    @property
    def analyzable_text(self) -> str:
        """Tekst do regul semantycznych: tresc widoczna + transkrypcja wideo.

        Dzieki temu reklama wideo przechodzi przez DOKLADNIE ten sam silnik
        regul co reklama tekstowa.
        """
        parts = [self.text]
        if self.transcript is not None:
            parts.append(self.transcript.text)
        return "\n\n".join(p for p in parts if p)


# --------------------------------------------------------------------------- #
# RuleResult — wspolny format wyniku dla regul DET, LLM i HYBRID
# --------------------------------------------------------------------------- #


class Evidence(BaseModel):
    """Dowod, na ktorym opiera sie werdykt reguly.

    Dla regul LLM `summary` MUSI zawierac doslowny cytat z materialu,
    nigdy parafraze — nadzorca musi moc zweryfikowac ustalenie.
    """

    kind: EvidenceKind
    summary: str
    measured: dict[str, float] | None = None
    quote: str | None = None
    viewport: ViewportName | None = None
    screenshot_crop: str | None = None
    transcript_ts: float | None = None


class RuleResult(BaseModel):
    rule_id: str
    rule_name: str
    engine: Engine
    verdict: Verdict
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    severity: int = Field(ge=1, le=5, default=3)
    legal_basis: str = ""
    evidence: Evidence


# --------------------------------------------------------------------------- #
# Finding — ujednolicony obiekt wyjsciowy wszystkich trzech modulow
# --------------------------------------------------------------------------- #


class RegistryMatch(BaseModel):
    knf_id: str | None = None
    official_name: str | None = None
    score: float = 0.0


class InvestmentFirmRef(BaseModel):
    name_in_ad: str | None = None
    registry_match: RegistryMatch | None = None
    is_authorized: bool = False


class AdvertiserRef(BaseModel):
    name: str | None = None
    relation_to_firm: Relation = Relation.UNKNOWN
    disclosure_found: bool = False
    affiliate_link: str | None = None


class Entities(BaseModel):
    investment_firm: InvestmentFirmRef = Field(default_factory=InvestmentFirmRef)
    advertiser: AdvertiserRef = Field(default_factory=AdvertiserRef)


class Routing(BaseModel):
    """Dlaczego dokument trafil do danego modulu.

    `reason` jest zdaniem po polsku i JEST POKAZYWANE w dashboardzie —
    nadzorca musi moc zakwestionowac decyzje routera.
    """

    rule: Literal["R1", "R2", "R3", "R4"]
    reason: str
    scope_gate: ScopeStatus


class Finding(BaseModel):
    id: str
    document_id: str
    primary_module: int | None = None
    modules: list[int] = Field(default_factory=list)
    routing: Routing
    risk_score: float = 0.0
    risk_level: RiskLevel = RiskLevel.LOW
    rule_results: list[RuleResult] = Field(default_factory=list)
    entities: Entities = Field(default_factory=Entities)
    knn_score: float | None = None
    status: Literal["new", "in_review", "confirmed", "dismissed", "triage"] = "new"
    created_at: datetime

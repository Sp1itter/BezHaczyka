"""Generator przykladow kontraktow do fixtures/contract-examples/.

Przyklady sa generowane Z MODELI, wiec sa poprawne z konstrukcji. Osoba A i C
pracuja na nich, dopoki serwisy nie sa gotowe — to one odblokowuja prace
rownolegla, zanim analyzer cokolwiek zwroci.

Uruchomienie (z services/analyzer):
    python tools/gen_contract_examples.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analyzer.contracts import (  # noqa: E402
    AdDocument,
    AdvertiserRef,
    BBox,
    Embedding,
    Engine,
    Entities,
    Evidence,
    EvidenceKind,
    Finding,
    InvestmentFirmRef,
    MediaItem,
    Publisher,
    RegistryMatch,
    Relation,
    RenderProbe,
    RiskLevel,
    Routing,
    RuleResult,
    Scope,
    ScopeStatus,
    TextNode,
    Transcript,
    TranscriptSegment,
    Verdict,
    ViewportProbe,
)

OUT = Path(__file__).resolve().parents[3] / "fixtures" / "contract-examples"

NOW = datetime(2026, 11, 21, 14, 3, 0, tzinfo=timezone.utc)

# --------------------------------------------------------------------------- #
# RenderProbe: reklama z ostrzezeniem 7 px schowanym w <details> w stopce
# --------------------------------------------------------------------------- #

PROFIT_NODE = TextNode(
    text="Zyski do 18% rocznie!",
    font_px=34.0,
    font_weight=700,
    color="#111111",
    background_effective="#ffffff",
    background_source="ancestor:main>section",
    background_confidence="resolved",
    contrast_ratio=18.9,
    bbox=BBox(x=24, y=310, w=342, h=44),
    dom_path="main>section:nth-of-type(1)>h2",
)

RISK_NODE = TextNode(
    text="Inwestowanie wiąże się z ryzykiem utraty kapitału.",
    font_px=7.0,
    font_weight=400,
    color="#c9c9c9",
    background_effective="#ffffff",
    background_source="ancestor:body",
    background_confidence="resolved",
    contrast_ratio=1.9,
    bbox=BBox(x=24, y=4080, w=342, h=9),
    behind_interaction="details",
    collapsed_evidence="details[not(@open)]",
    dom_path="footer>details>p",
    in_footer=True,
)

RENDER_PROBE = RenderProbe(
    viewports={
        "mobile": ViewportProbe(
            dominant_font_px=16.0,
            page_height_px=4210.0,
            nodes=[PROFIT_NODE, RISK_NODE],
        )
    }
)

# --------------------------------------------------------------------------- #
# AdDocument
# --------------------------------------------------------------------------- #

AD_DOCUMENT = AdDocument(
    id="11111111-1111-4111-8111-111111111111",
    source="instagram",
    url="https://example.invalid/promo/cfd-btc",
    fetched_at=NOW,
    publisher=Publisher(
        handle="@finfluencer_pl",
        display_name="Jan Inwestor",
        profile_url="https://example.invalid/@finfluencer_pl",
        is_official_firm_channel=False,
    ),
    lang="pl",
    title="Zyski do 18% rocznie!",
    text=(
        "Zyski do 18% rocznie! Handluj CFD na Bitcoina z dźwignią 1:2 "
        "u naszego partnera XYZ Dom Maklerski. Zarejestruj rachunek przez "
        "mój link. Inwestowanie wiąże się z ryzykiem utraty kapitału."
    ),
    html_path="s3://raw/11111111.html",
    screenshots={
        "desktop": "s3://shots/11111111-1920.png",
        "mobile": "s3://shots/11111111-390.png",
    },
    media=[MediaItem(kind="video", path="s3://media/11111111.mp4", duration_s=34.2)],
    transcript=Transcript(
        engine="faster-whisper-medium-int8",
        lang="pl",
        text=(
            "Cześć, dziś pokażę wam jak zarobić osiemnaście procent rocznie. "
            "Inwestowanie wiąże się z ryzykiem."
        ),
        segments=[
            TranscriptSegment(
                start=4.2, end=8.1, text="jak zarobić osiemnaście procent rocznie"
            ),
            TranscriptSegment(
                start=33.8, end=34.2, text="inwestowanie wiąże się z ryzykiem"
            ),
        ],
    ),
    render_probe=RENDER_PROBE,
    embedding=Embedding(model="bge-m3", dim=1024, vector=[0.0123, -0.0456, 0.0789]),
    simhash="a3f1c09e5b7d2401",
    scope=Scope(
        status=ScopeStatus.IN_SCOPE,
        instrument_wrapper="cfd",
        underlying="crypto",
        legal_basis="art. 2 ust. 1 pkt 2 lit. h ustawy o obrocie",
        tags=["crypto_derivative", "leveraged"],
    ),
)

# --------------------------------------------------------------------------- #
# RuleResult: regula 4 (rozmiar czcionki ryzyka) — DET, z dowodem liczbowym
# --------------------------------------------------------------------------- #

RULE_RESULT = RuleResult(
    rule_id="4",
    rule_name="Rozmiar czcionki ryzyka",
    engine=Engine.DET,
    verdict=Verdict.FAIL,
    confidence=1.0,
    severity=4,
    legal_basis="art. 44 ust. 2 lit. c rozporządzenia del. 2017/565",
    evidence=Evidence(
        kind=EvidenceKind.MEASUREMENT,
        summary=(
            "Ostrzeżenie o ryzyku ma 7.0 px przy dominującej czcionce 16.0 px (44%)."
        ),
        measured={"risk_font_px": 7.0, "dominant_font_px": 16.0, "ratio": 0.44},
        viewport="mobile",
        screenshot_crop="s3://crops/11111111-rule4.png",
    ),
)

RULE_RESULT_LLM = RuleResult(
    rule_id="18",
    rule_name="Nadzór jako argument bezpieczeństwa",
    engine=Engine.LLM,
    verdict=Verdict.FAIL,
    confidence=0.88,
    severity=5,
    legal_basis="art. 44 ust. 8 rozporządzenia del. 2017/565",
    evidence=Evidence(
        kind=EvidenceKind.QUOTE,
        summary=(
            "Materiał powołuje się na nadzór KNF jako argument bezpieczeństwa "
            "inwestycji."
        ),
        quote="Nasza inwestycja jest w pełni bezpieczna — spełniamy rygorystyczne wymogi KNF",
    ),
)

RULE_RESULT_NA = RuleResult(
    rule_id="5",
    rule_name="Ekspozycja i kontrast ryzyka",
    engine=Engine.DET,
    verdict=Verdict.NOT_APPLICABLE,
    confidence=1.0,
    severity=4,
    legal_basis="art. 44 ust. 2 lit. c i e rozporządzenia del. 2017/565",
    evidence=Evidence(
        kind=EvidenceKind.ABSENCE,
        summary=(
            "Nie dało się zmierzyć kontrastu — tło graficzne "
            "(background_confidence=unknown). Wymaga oceny ręcznej."
        ),
        viewport="mobile",
    ),
)

# --------------------------------------------------------------------------- #
# Finding
# --------------------------------------------------------------------------- #

FINDING = Finding(
    id="22222222-2222-4222-8222-222222222222",
    document_id=AD_DOCUMENT.id,
    primary_module=1,
    modules=[1, 2],
    routing=Routing(
        rule="R2",
        reason=(
            "@finfluencer_pl nie jest oficjalnym kanałem XYZ Dom Maklerski, "
            "a materiał reklamuje tę firmę lub jej produkty — reklama przez "
            "podmiot trzeci. Materiał zawiera twierdzenia o zyskach, więc "
            "dodatkowo oceniany regułami Modułu 2."
        ),
        scope_gate=ScopeStatus.IN_SCOPE,
    ),
    risk_score=78.5,
    risk_level=RiskLevel.HIGH,
    rule_results=[RULE_RESULT, RULE_RESULT_LLM, RULE_RESULT_NA],
    entities=Entities(
        investment_firm=InvestmentFirmRef(
            name_in_ad="XYZ Dom Maklerski",
            registry_match=RegistryMatch(
                knf_id="DM-123", official_name="XYZ DM S.A.", score=0.94
            ),
            is_authorized=True,
        ),
        advertiser=AdvertiserRef(
            name="@finfluencer_pl",
            relation_to_firm=Relation.THIRD_PARTY,
            disclosure_found=False,
            affiliate_link="https://example.invalid/?ref=finflu123",
        ),
    ),
    knn_score=0.81,
    status="new",
    created_at=NOW,
)


EXAMPLES = {
    "ad_document.json": AD_DOCUMENT,
    "render_probe.json": RENDER_PROBE,
    "rule_result.json": RULE_RESULT,
    "finding.json": FINDING,
    "scope.json": AD_DOCUMENT.scope,
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, model in EXAMPLES.items():
        path = OUT / name
        path.write_text(
            json.dumps(
                model.model_dump(mode="json"),
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"zapisano {path.relative_to(OUT.parents[1])}")


if __name__ == "__main__":
    main()

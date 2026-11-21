"""Reguly hybrydowe — semantyka plus pomiar fizyczny.

Regula 3 (art. 44 ust. 2 lit. b rozporzadzenia del. 2017/565) wymaga, zeby
informacji o potencjalnych zyskach TOWARZYSZYLA BEZPOSREDNIO informacja
o istotnym ryzyku. Slowo "bezposrednio" jest tu kluczowe: ostrzezenie
wepchniete 4000 pikseli nizej, w stopce, formalnie istnieje, ale nie towarzyszy
niczemu.

To jest dokladnie pierwsze pytanie mentorow UKNF: czy reklama jest rzetelna.
I jest to pytanie MIERZALNE — dlatego regula laczy wykrycie semantyczne
(gdzie pada obietnica zysku, gdzie ostrzezenie) z pomiarem fizycznym
(ile pikseli, znakow albo sekund miedzy nimi).

Trzy osie pomiaru, zaleznie od tego, co mamy:
  - GEOMETRIA  — odleglosc pionowa bboxow w RenderProbe (najmocniejszy dowod),
  - TEKST      — odleglosc w znakach, gdy brak RenderProbe,
  - CZAS       — sekundy w transkrypcji, dla reklam wideo.

Pomiar jest deterministyczny, wiec demo zachowuje sie tak samo za kazdym razem.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from analyzer.config_loader import get_threshold
from analyzer.contracts import (
    AdDocument,
    Engine,
    Evidence,
    EvidenceKind,
    RuleResult,
    TextNode,
    Verdict,
    ViewportProbe,
)
from analyzer.router import PROFIT_CLAIM_PATTERNS, mask_non_claims, normalize
from analyzer.rules_llm import preconditions
from analyzer.rules_llm.lang_consistency import EN_RISK_PATTERNS, PL_RISK_PATTERNS

RULE_3_META = (
    "Informacja o ryzyku",
    5,
    "art. 44 ust. 2 lit. b rozporządzenia del. 2017/565",
)

RULE_13_META = (
    "Dominacja wyników historycznych",
    3,
    "art. 44 ust. 4 lit. a rozporządzenia del. 2017/565",
)

RISK_PATTERNS = PL_RISK_PATTERNS + EN_RISK_PATTERNS

# Progi domyslne; nadpisywalne w analyzer/config/thresholds.yaml.
DEFAULT_MAX_DISTANCE_PX = 600.0  # mniej wiecej jeden ekran telefonu
DEFAULT_MAX_OFFSET_CHARS = 300
DEFAULT_MAX_GAP_SECONDS = 5.0

# Kolejnosc preferencji viewportow: mobile jest najbardziej restrykcyjny,
# bo to na telefonie ostrzezenie najlatwiej wypchnac poza ekran.
VIEWPORT_ORDER = ("mobile", "tablet", "desktop")


@dataclass(frozen=True)
class Proximity:
    """Wynik pomiaru odleglosci miedzy obietnica zysku a ostrzezeniem."""

    axis: str  # "geometria" | "tekst" | "czas"
    distance: float
    unit: str  # "px" | "znakow" | "s"
    threshold: float
    profit_quote: str
    risk_quote: str | None
    viewport: str | None = None
    # Dowod proporcjonalnosci (tylko os geometrii): rozmiary czcionek pary.
    profit_font_px: float | None = None
    risk_font_px: float | None = None

    @property
    def within(self) -> bool:
        return self.distance <= self.threshold


def _norm_for(text: str, patterns: tuple[str, ...]) -> str:
    """normalize(); dla wzorcow obietnicy zysku dodatkowo bez zaprzeczen/oplat."""
    norm = normalize(text)
    return mask_non_claims(norm) if patterns is PROFIT_CLAIM_PATTERNS else norm


def _matches(text: str, patterns: tuple[str, ...]) -> bool:
    norm = _norm_for(text, patterns)
    return any(re.search(p, norm) for p in patterns)


def _first_match_offset(text: str, patterns: tuple[str, ...]) -> int | None:
    norm = _norm_for(text, patterns)
    offsets = [m.start() for p in patterns if (m := re.search(p, norm))]
    return min(offsets) if offsets else None


def _pick_viewport(doc: AdDocument) -> tuple[str, ViewportProbe] | None:
    if doc.render_probe is None:
        return None
    for name in VIEWPORT_ORDER:
        vp = doc.render_probe.viewports.get(name)
        if vp is not None and vp.nodes:
            return name, vp
    for name, vp in doc.render_probe.viewports.items():
        if vp.nodes:
            return name, vp
    return None


def _center_y(node: TextNode) -> float:
    return node.bbox.y + node.bbox.h / 2.0


def measure_geometry(doc: AdDocument) -> Proximity | None:
    """Odleglosc pionowa miedzy najblizsza para: obietnica zysku / ostrzezenie.

    Najmocniejszy dowod, bo mowi o tym, co odbiorca FAKTYCZNIE widzi na ekranie,
    a nie o tym, co jest w kodzie strony.
    """
    picked = _pick_viewport(doc)
    if picked is None:
        return None
    viewport, vp = picked

    profit_nodes = [n for n in vp.nodes if n.visible and _matches(n.text, PROFIT_CLAIM_PATTERNS)]
    if not profit_nodes:
        return None

    threshold = float(get_threshold("rules.rule_3.max_distance_px", DEFAULT_MAX_DISTANCE_PX))
    risk_nodes = [n for n in vp.nodes if n.visible and _matches(n.text, RISK_PATTERNS)]

    if not risk_nodes:
        # Obietnica zysku jest, ostrzezenia nie ma w ogole. To nie jest "daleko",
        # to jest "brak" — i tak tez musi zostac opisane.
        return Proximity(
            axis="geometria",
            distance=float("inf"),
            unit="px",
            threshold=threshold,
            profit_quote=profit_nodes[0].text,
            risk_quote=None,
            viewport=viewport,
            profit_font_px=profit_nodes[0].font_px,
        )

    best: tuple[float, TextNode, TextNode] | None = None
    for p in profit_nodes:
        for r in risk_nodes:
            d = abs(_center_y(r) - _center_y(p))
            if best is None or d < best[0]:
                best = (d, p, r)
    assert best is not None

    distance, profit, risk = best
    return Proximity(
        axis="geometria",
        distance=distance,
        unit="px",
        threshold=threshold,
        profit_quote=profit.text,
        risk_quote=risk.text,
        viewport=viewport,
        profit_font_px=profit.font_px,
        risk_font_px=risk.font_px,
    )


def measure_text(doc: AdDocument) -> Proximity | None:
    """Odleglosc w znakach — gdy nie ma RenderProbe (np. import, API)."""
    text = doc.analyzable_text
    p_off = _first_match_offset(text, PROFIT_CLAIM_PATTERNS)
    if p_off is None:
        return None

    threshold = float(get_threshold("rules.rule_3.max_offset_chars", DEFAULT_MAX_OFFSET_CHARS))
    r_off = _first_match_offset(text, RISK_PATTERNS)

    def _fragment(off: int) -> str:
        return text[max(0, off - 20) : off + 90].strip()

    if r_off is None:
        return Proximity(
            axis="tekst",
            distance=float("inf"),
            unit="znakow",
            threshold=threshold,
            profit_quote=_fragment(p_off),
            risk_quote=None,
        )

    return Proximity(
        axis="tekst",
        distance=float(abs(r_off - p_off)),
        unit="znakow",
        threshold=threshold,
        profit_quote=_fragment(p_off),
        risk_quote=_fragment(r_off),
    )


def measure_timeline(doc: AdDocument) -> Proximity | None:
    """Odstep w sekundach dla reklamy wideo.

    Obietnica zysku w sekundzie 5 i ostrzezenie w 33.8 na 34.2 sekundy
    materialu to nie jest "towarzyszenie bezposrednie" — nawet jesli oba
    zdania w transkrypcji sa.
    """
    if doc.transcript is None or not doc.transcript.segments:
        return None

    profit_seg = next(
        (s for s in doc.transcript.segments if _matches(s.text, PROFIT_CLAIM_PATTERNS)), None
    )
    if profit_seg is None:
        return None

    threshold = float(get_threshold("rules.rule_3.max_gap_seconds", DEFAULT_MAX_GAP_SECONDS))
    risk_seg = next(
        (s for s in doc.transcript.segments if _matches(s.text, RISK_PATTERNS)), None
    )

    if risk_seg is None:
        return Proximity(
            axis="czas",
            distance=float("inf"),
            unit="s",
            threshold=threshold,
            profit_quote=profit_seg.text,
            risk_quote=None,
        )

    return Proximity(
        axis="czas",
        distance=abs(risk_seg.start - profit_seg.start),
        unit="s",
        threshold=threshold,
        profit_quote=profit_seg.text,
        risk_quote=risk_seg.text,
    )


def measure_proximity(doc: AdDocument) -> Proximity | None:
    """Najmocniejszy dostepny pomiar. None = brak obietnicy zysku."""
    for measure in (measure_geometry, measure_timeline, measure_text):
        result = measure(doc)
        if result is not None:
            return result
    return None


def assess_rule_3(doc: AdDocument) -> RuleResult:
    """Oceń regule 3: czy ostrzezenie o ryzyku towarzyszy obietnicy zysku."""
    name, severity, basis = RULE_3_META

    def _result(verdict: Verdict, evidence: Evidence, confidence: float = 1.0) -> RuleResult:
        return RuleResult(
            rule_id="3",
            rule_name=name,
            engine=Engine.HYBRID,
            verdict=verdict,
            confidence=confidence,
            severity=severity,
            legal_basis=basis,
            evidence=evidence,
        )

    prox = measure_proximity(doc)

    if prox is None:
        # Regula 3 jest warunkowa: bez twierdzen o zyskach nie ma czego
        # obudowywac ostrzezeniem.
        return _result(
            Verdict.NOT_APPLICABLE,
            Evidence(
                kind=EvidenceKind.ABSENCE,
                summary=(
                    "Material nie zawiera twierdzen o potencjalnych zyskach, "
                    "wiec wymog bezposredniego towarzyszenia informacji o ryzyku "
                    "nie ma zastosowania."
                ),
            ),
        )

    if prox.risk_quote is None:
        return _result(
            Verdict.FAIL,
            Evidence(
                kind=EvidenceKind.ABSENCE,
                summary=(
                    f"Material zawiera twierdzenie o zyskach, ale NIE ZAWIERA "
                    f"zadnej informacji o ryzyku (pomiar na osi: {prox.axis})."
                ),
                quote=prox.profit_quote[:300],
                viewport=prox.viewport,  # type: ignore[arg-type]
            ),
        )

    measured = {
        "odleglosc": round(prox.distance, 1),
        "prog": prox.threshold,
    }
    font_note = ""
    if prox.profit_font_px and prox.risk_font_px is not None:
        ratio = prox.risk_font_px / prox.profit_font_px
        measured["font_zysku_px"] = prox.profit_font_px
        measured["font_ryzyka_px"] = prox.risk_font_px
        measured["proporcja_font_ryzyko_do_zysku"] = round(ratio, 2)
        ratio_pl = f"{ratio:.2f}".replace(".", ",")
        font_note = (
            f" Czcionka ostrzezenia: {prox.risk_font_px:g} px wobec "
            f"{prox.profit_font_px:g} px obietnicy zysku ({ratio_pl})."
        )

    if prox.within:
        return _result(
            Verdict.PASS,
            Evidence(
                kind=EvidenceKind.MEASUREMENT,
                summary=(
                    f"Ostrzezenie o ryzyku towarzyszy twierdzeniu o zyskach: "
                    f"{prox.distance:.0f} {prox.unit} odstepu przy progu "
                    f"{prox.threshold:.0f} (os: {prox.axis})." + font_note
                ),
                measured=measured,
                quote=prox.risk_quote[:300],
                viewport=prox.viewport,  # type: ignore[arg-type]
            ),
        )

    return _result(
        Verdict.FAIL,
        Evidence(
            kind=EvidenceKind.MEASUREMENT,
            summary=(
                f"Ostrzezenie o ryzyku NIE towarzyszy bezposrednio twierdzeniu "
                f"o zyskach: {prox.distance:.0f} {prox.unit} odstepu przy progu "
                f"{prox.threshold:.0f} (os: {prox.axis}). Twierdzenie o zysku: "
                f"\"{prox.profit_quote[:80]}\"." + font_note
            ),
            measured=measured,
            quote=prox.risk_quote[:300],
            viewport=prox.viewport,  # type: ignore[arg-type]
        ),
    )


def rule_3_runner(doc: AdDocument) -> list[RuleResult]:
    """Runner zgodny z AnalyzerConfig.module2_runners."""
    return [assess_rule_3(doc)]


DEFAULT_DOMINANCE_RATIO = 1.0


def assess_rule_13(doc: AdDocument) -> RuleResult:
    """Oceń regule 13: czy wyniki historyczne sa najbardziej wyeksponowanym elementem.

    Miara ekspozycji to rozmiar czcionki wezla (przy remisie liczy sie
    wyzsze polozenie). Brak pomiaru renderu to NOT_APPLICABLE, nigdy fail.
    """
    name, severity, basis = RULE_13_META

    def _result(verdict: Verdict, evidence: Evidence, confidence: float) -> RuleResult:
        return RuleResult(
            rule_id="13",
            rule_name=name,
            engine=Engine.HYBRID,
            verdict=verdict,
            confidence=confidence,
            severity=severity,
            legal_basis=basis,
            evidence=evidence,
        )

    def _na(reason: str) -> RuleResult:
        return _result(
            Verdict.NOT_APPLICABLE,
            Evidence(kind=EvidenceKind.ABSENCE, summary=reason),
            1.0,
        )

    if not preconditions.mentions_historical_performance(doc.analyzable_text):
        return _na(preconditions.HISTORICAL_REASON)

    picked = _pick_viewport(doc)
    if picked is None:
        return _na(
            "brak pomiaru renderu (RenderProbe) — dominacji wizualnej nie da sie "
            "ocenic bez geometrii"
        )
    viewport, vp = picked

    visible = [n for n in vp.nodes if n.visible]
    hist_nodes = [n for n in visible if _matches(n.text, preconditions.HISTORICAL_PATTERNS)]
    if not hist_nodes:
        return _na(
            "Wyniki historyczne wystepuja w tekscie, ale zaden widoczny element "
            "strony ich nie zawiera — dominacji wizualnej nie da sie ocenic."
        )

    # Najwieksza czcionka; remis rozstrzyga wyzsze polozenie (mniejsze y).
    hist = min(hist_nodes, key=lambda n: (-n.font_px, n.bbox.y))
    others = [n for n in visible if not any(n is h for h in hist_nodes)]
    ratio_threshold = float(
        get_threshold("rules.rule_13.dominance_ratio", DEFAULT_DOMINANCE_RATIO)
    )

    if not others:
        # Jeden widoczny wezel to niepelny pomiar, nie dowod dominacji.
        return _na(
            "Brak innych widocznych elementow do porownania — dominacji "
            "wizualnej nie da sie ocenic."
        )

    max_other = max(n.font_px for n in others)
    top_ties = [n for n in others if n.font_px == max_other]
    ratio = hist.font_px / max_other if max_other else float("inf")
    higher_than_ties = hist.bbox.y <= min(n.bbox.y for n in top_ties)
    dominates = hist.font_px >= max_other * ratio_threshold and (
        hist.font_px > max_other or higher_than_ties
    )

    measured = {
        "font_wyniku_hist_px": hist.font_px,
        "max_font_innych_px": max_other,
        "dominant_font_px": vp.dominant_font_px,
        "prog": ratio_threshold,
        "stosunek": round(ratio, 2),
    }
    if dominates:
        summary = (
            f"Wyniki historyczne sa najbardziej wyeksponowanym elementem: "
            f"{hist.font_px:g} px przy {max_other:g} px najwiekszej innej czcionki "
            f"(viewport {viewport})."
        )
    else:
        summary = (
            f"Wyniki historyczne nie dominuja: {hist.font_px:g} px wobec "
            f"{max_other:g} px najwiekszej innej czcionki (viewport {viewport})."
        )
    return _result(
        Verdict.FAIL if dominates else Verdict.PASS,
        Evidence(
            kind=EvidenceKind.MEASUREMENT,
            summary=summary,
            measured=measured,
            quote=hist.text[:300],
            viewport=viewport,  # type: ignore[arg-type]
        ),
        0.9,
    )


def rule_13_runner(doc: AdDocument) -> list[RuleResult]:
    """Runner zgodny z AnalyzerConfig.module2_runners."""
    return [assess_rule_13(doc)]

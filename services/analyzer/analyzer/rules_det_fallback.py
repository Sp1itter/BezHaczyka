"""Reguly DET 4-8 liczone w analyzerze, gdy scraper ich nie dostarczyl.

Scraper Facebooka liczy 4-8 sam (z nadpisaniami typografii Meta) i przekazuje
w `det_results` — jego wynik ma ZAWSZE pierwszenstwo. Dla pozostalych zrodel
(web, YouTube z renderem...) liczymy te reguly tu, wprost z `doc.render_probe`,
wg design doca par. 7 i par. 6.2.1.

Zasada: brak danych -> not_applicable z powodem, nigdy fail. Falszywy alarm to
najgorszy blad narzedzia nadzorczego.

Wezly ryzyka = widoczne wezly pasujace do RISK_PATTERNS (te same co regula 3).
Brak takiego wezla -> NA: BRAK ostrzezenia ocenia regula 3, nie reguly 4-8.
"""

from __future__ import annotations

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
from analyzer.det_placeholders import DET_RULES
from analyzer.rules_hybrid import RISK_PATTERNS, _matches

DEFAULT_MIN_RATIO = 0.9
DEFAULT_MIN_CONTRAST = 4.5
DEFAULT_FOOTER_FRACTION = 0.85
DEFAULT_MIN_MOBILE_FONT_PX = 9.0
HIDDEN_PATH_MARKERS = ("footer", "legal", "disclaimer")

REASON_NO_RISK = "brak informacji o ryzyku w renderze; jej brak ocenia regula 3"

_Hit = tuple[str, ViewportProbe, TextNode]  # (nazwa viewportu, viewport, wezel)


def _result(rule_id: str, verdict: Verdict, evidence: Evidence) -> RuleResult:
    name, severity, basis = DET_RULES[rule_id]
    return RuleResult(
        rule_id=rule_id,
        rule_name=name,
        engine=Engine.DET,
        verdict=verdict,
        confidence=1.0,
        severity=severity,
        legal_basis=basis,
        evidence=evidence,
    )


def _na(rule_id: str, reason: str) -> RuleResult:
    return _result(
        rule_id, Verdict.NOT_APPLICABLE, Evidence(kind=EvidenceKind.ABSENCE, summary=reason)
    )


def _risk_hits(
    doc: AdDocument, visible_only: bool = True, include_unseen: bool = False
) -> list[_Hit]:
    """Wezly ryzyka.

    include_unseen=True dolacza wezly niewidoczne BEZ behind_interaction (ukryte lub
    przyciete bez mechanizmu "kliknij"). Semantyka jak w probe.js: visible=false +
    behind_interaction="hidden" to display:none itp. (regula 7), a wezel schowany za
    "Zobacz wiecej" ma behind_interaction i ocenia go TYLKO regula 7 — nie dublujemy kary.
    """
    out: list[_Hit] = []
    if doc.render_probe is None:
        return out
    for name, vp in doc.render_probe.viewports.items():
        for n in vp.nodes:
            if visible_only and not n.visible:
                if not (include_unseen and n.behind_interaction is None):
                    continue
            if _matches(n.text, RISK_PATTERNS):
                out.append((name, vp, n))
    return out


def _evidence(summary: str, hit: _Hit, measured: dict[str, float]) -> Evidence:
    name, _vp, node = hit
    return Evidence(
        kind=EvidenceKind.MEASUREMENT,
        summary=summary,
        measured=measured,
        quote=node.text[:500],
        viewport=name if name in ("desktop", "tablet", "mobile") else None,  # type: ignore[arg-type]
    )


def _dominant_font_px(vp: ViewportProbe) -> float:
    """Przewazajaca czcionka materialu BEZ informacji o ryzyku.

    probe.js wybiera rozmiar z najwieksza laczna liczba znakow widocznych wezlow,
    ale liczy w tym samo ostrzezenie. Dlugie, drobne zastrzezenie (8 px, 200
    znakow) staje sie wtedy "przewazajaca czcionka" i regula 4 nigdy go nie
    zlapie - to falszywy negatyw na najczestszym triku. Kryterium UKNF porownuje
    ostrzezenie z przewazajaca czcionka MATERIALU, wiec liczymy ja z wezlow
    nie-ryzyka; wartosc z probe tylko gdy innych wezlow brak.
    """
    chars: dict[float, int] = {}
    for n in vp.nodes:
        if n.visible and n.font_px > 0 and not _matches(n.text, RISK_PATTERNS):
            chars[n.font_px] = chars.get(n.font_px, 0) + len(n.text)
    if chars:
        return max(chars, key=lambda px: (chars[px], px))
    return vp.dominant_font_px if vp.dominant_font_px > 0 else 0.0


def _rule_4(doc: AdDocument) -> RuleResult:
    hits = [h for h in _risk_hits(doc) if _dominant_font_px(h[1]) > 0]
    if not hits:
        return _na("4", REASON_NO_RISK)
    min_ratio = float(get_threshold("rules.rule_4.min_ratio", DEFAULT_MIN_RATIO))
    worst = min(hits, key=lambda h: h[2].font_px / _dominant_font_px(h[1]))
    ratio = worst[2].font_px / _dominant_font_px(worst[1])
    summary = (
        f"Czcionka ostrzezenia {worst[2].font_px:g} px to {ratio:.2f} czcionki dominujacej "
        f"({_dominant_font_px(worst[1]):g} px); prog {min_ratio:g}."
    )
    return _result(
        "4",
        Verdict.FAIL if ratio < min_ratio else Verdict.PASS,
        _evidence(
            summary,
            worst,
            {
                "risk_font_px": worst[2].font_px,
                "dominant_font_px": _dominant_font_px(worst[1]),
                "ratio": round(ratio, 3),
            },
        ),
    )


def _rule_5(doc: AdDocument) -> RuleResult:
    hits = _risk_hits(doc)
    if not hits:
        return _na("5", REASON_NO_RISK)
    # Tlo nieznane albo brak kontrastu -> wezel nieoceniany (par. 6.2.1), nigdy fail.
    measurable = [
        h
        for h in hits
        if h[2].background_confidence != "unknown" and h[2].contrast_ratio is not None
    ]
    if not measurable:
        return _na(
            "5",
            "Tlo ostrzezenia nieznane (background_confidence=unknown) — kontrastu nie da sie zmierzyc",
        )
    min_contrast = float(get_threshold("rules.rule_5.min_contrast", DEFAULT_MIN_CONTRAST))
    worst = min(measurable, key=lambda h: float(h[2].contrast_ratio or 0.0))
    ratio = float(worst[2].contrast_ratio or 0.0)
    summary = f"Kontrast ostrzezenia {ratio:.2f}:1 (WCAG); prog {min_contrast:g}:1."
    return _result(
        "5",
        Verdict.FAIL if ratio < min_contrast else Verdict.PASS,
        _evidence(summary, worst, {"contrast_ratio": ratio}),
    )


def _rule_6(doc: AdDocument) -> RuleResult:
    hits = [h for h in _risk_hits(doc, include_unseen=True) if h[1].page_height_px > 0]
    if not hits:
        return _na("6", REASON_NO_RISK)
    fraction = float(get_threshold("rules.rule_6.footer_position_fraction", DEFAULT_FOOTER_FRACTION))

    def hidden_path(n: TextNode) -> bool:
        return n.in_footer or any(m in n.dom_path.lower() for m in HIDDEN_PATH_MARKERS)

    def share(h: _Hit) -> float:
        return h[2].bbox.y / h[1].page_height_px

    # Najpierw wezel ukryty (visible=false bez interakcji), potem w stopce/legal,
    # w przeciwnym razie ten polozony najnizej.
    unseen = next((h for h in hits if not h[2].visible), None)
    worst = (
        unseen
        or next((h for h in hits if hidden_path(h[2])), None)
        or max(hits, key=share)
    )
    y_share = share(worst)
    in_hidden = hidden_path(worst[2])
    if unseen is not None:
        return _result(
            "6",
            Verdict.FAIL,
            _evidence(
                f"Ostrzezenie ukryte (niewidoczne w renderze, viewport {worst[0]})"
                + (", w stopce / sekcji prawnej" if in_hidden else "")
                + ".",
                worst,
                {"y_share_of_page": round(y_share, 3), "hidden": 1.0,
                 "in_footer": 1.0 if in_hidden else 0.0},
            ),
        )
    summary = (
        f"Ostrzezenie zaczyna sie na {y_share:.0%} wysokosci strony"
        + (", w stopce / sekcji prawnej" if in_hidden else "")
        + f"; prog {fraction:.0%}."
    )
    return _result(
        "6",
        Verdict.FAIL if (in_hidden or y_share > fraction) else Verdict.PASS,
        _evidence(
            summary,
            worst,
            {"y_share_of_page": round(y_share, 3), "in_footer": 1.0 if in_hidden else 0.0},
        ),
    )


def _rule_7(doc: AdDocument) -> RuleResult:
    # Wezel schowany za interakcja bywa niewidoczny (visible=False) — to wlasnie
    # on jest dowodem, wiec tu nie filtrujemy po `visible`.
    hits = _risk_hits(doc, visible_only=False)
    if not hits:
        return _na("7", REASON_NO_RISK)
    behind = [h for h in hits if h[2].behind_interaction is not None]
    if behind:
        h = behind[0]
        return _result(
            "7",
            Verdict.FAIL,
            _evidence(
                f"Ostrzezenie dostepne dopiero po interakcji ({h[2].behind_interaction}: "
                f"{h[2].collapsed_evidence}).",
                h,
                {"behind_interaction": 1.0},
            ),
        )
    return _result(
        "7",
        Verdict.PASS,
        _evidence("Ostrzezenie widoczne bez klikania.", hits[0], {"behind_interaction": 0.0}),
    )


def _rule_8(doc: AdDocument) -> RuleResult:
    all_hits = _risk_hits(doc, include_unseen=True)
    hits = [h for h in all_hits if h[2].visible]
    if not all_hits:
        return _na("8", REASON_NO_RISK)
    min_font = float(get_threshold("rules.rule_8.min_mobile_font_px", DEFAULT_MIN_MOBILE_FONT_PX))
    clipped = next((h for h in hits if h[2].clipped), None)
    if clipped is not None:
        return _result(
            "8",
            Verdict.FAIL,
            _evidence(
                f"Ostrzezenie obciete (clipped) w viewporcie {clipped[0]}.",
                clipped,
                {"clipped": 1.0, "font_px": clipped[2].font_px},
            ),
        )
    # Ostrzezenie niewidoczne na mobile (bez interakcji): ukryte/przyciete przy zmianie ukladu.
    unseen = next((h for h in all_hits if h[0] == "mobile" and not h[2].visible), None)
    if unseen is not None:
        return _result(
            "8",
            Verdict.FAIL,
            _evidence(
                "Ostrzezenie niewidoczne/przyciete na mobile.",
                unseen,
                {"visible": 0.0, "clipped": 1.0 if unseen[2].clipped else 0.0,
                 "font_px": unseen[2].font_px},
            ),
        )
    mobile = [h for h in hits if h[0] == "mobile"]
    if not mobile:
        return _na("8", "Brak pomiaru viewportu mobile — responsywnosci nie da sie ocenic")
    small = min(mobile, key=lambda h: h[2].font_px)
    return _result(
        "8",
        Verdict.FAIL if small[2].font_px < min_font else Verdict.PASS,
        _evidence(
            f"Czcionka ostrzezenia na mobile {small[2].font_px:g} px; prog {min_font:g} px.",
            small,
            {"font_px": small[2].font_px, "clipped": 0.0},
        ),
    )


_RULES = {"4": _rule_4, "5": _rule_5, "6": _rule_6, "7": _rule_7, "8": _rule_8}


def det_fallback_results(
    doc: AdDocument, det_results: list[RuleResult] | None
) -> list[RuleResult]:
    """Reguly 4-8 policzone z doc.render_probe dla tych, ktorych nie ma w det_results.

    Bez render_probe zwraca [] — wtedy zostaja wypelniacze z det_placeholders.
    """
    if doc.render_probe is None:
        return []
    # Facebook: typografie w Ad Library sklada Meta, nie reklamodawca (nadpisania
    # w services/scraper/sources/facebook_rules.py). Ogolny pomiar dalby tam falszywe
    # alarmy, wiec zrodlo ma wlasnosc regul 4-8; bez jego wyniku zostaje placeholder.
    if doc.source == "facebook":
        return []
    present = {r.rule_id for r in (det_results or [])}
    return [fn(doc) for rid, fn in _RULES.items() if rid not in present]

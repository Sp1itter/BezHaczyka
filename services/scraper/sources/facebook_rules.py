"""RuleResult regul DET 4–8 dla zrodla `facebook` (design doc par. 6.3, par. 7).

`rules_det/` (osoba A) jeszcze nie istnieje. Ten modul to WARSTWA ZRODLA
FACEBOOK, ktora rules_det ma wolac zamiast ogolnych regul, gdy
`doc.source == "facebook"` — bo w Meta Ad Library czesc regul mierzy
interfejs platformy, a nie decyzje reklamodawcy. Progi z par. 7.

  R4 rozmiar czcionki   -> not_applicable  (typografia platformy)
  R5 kontrast           -> not_applicable  (typografia platformy; tekst na grafice i tak `unknown`)
  R6 ukrywanie          -> DET na wezlach z ostrzezeniem w kreacji (stopka / legal / dol kreacji)
  R7 za 1 kliknieciem   -> DET `behind_interaction`, a dla feedu HYBRID: ostrzezenie za
                           progiem „Zobacz wiecej" (risk_offset_chars > 125), confidence 0.6
  R8 RWD                -> not_applicable  (typografia platformy)

Gdy w tresci nie ma zadnego ostrzezenia o ryzyku, R6 i R7 sa `not_applicable`:
BRAK ostrzezenia ocenia regula 3 (HYBRID, analyzer), a nie reguly polozenia.
`not_applicable` nie wchodzi do mianownika scoringu (par. 9).
"""

from __future__ import annotations

from contracts import AdDocument, Engine, Evidence, EvidenceKind, RuleResult, TextNode, Verdict
from sources.facebook import (
    _RISK_RE,
    PLATFORM_TYPOGRAPHY_REASON,
    feed_fold_evidence,
    platform_rule_override,
)

_BASIS = "rozporządzenia del. 2017/565"
RULES: dict[str, tuple[str, int, str]] = {
    # rule_id: (nazwa z par. 7, severity, podstawa prawna)
    "4": ("Rozmiar czcionki ryzyka", 4, f"art. 44 ust. 2 lit. c {_BASIS}"),
    "5": ("Ekspozycja i kontrast", 3, f"art. 44 ust. 2 lit. c, e {_BASIS}"),
    "6": ("Zakrywanie / ukrywanie", 4, f"art. 44 ust. 2 lit. e {_BASIS}"),
    "7": ("Dostępność za 1 kliknięciem", 4, f"art. 44 ust. 2 lit. b, e {_BASIS}"),
    "8": ("Responsywność", 2, f"art. 44 ust. 2 lit. g {_BASIS}"),
}
HIDDEN_PATH_MARKERS = ("footer", "legal", "disclaimer")
BOTTOM_SHARE = 0.85
FEED_FOLD_CONFIDENCE = 0.6  # heurystyka feedu, nie pomiar — ostrozniejsza waga w scoringu


def _result(rule_id: str, verdict: Verdict, evidence: Evidence,
            engine: Engine = Engine.DET, confidence: float = 1.0) -> RuleResult:
    name, severity, basis = RULES[rule_id]
    return RuleResult(rule_id=rule_id, rule_name=name, engine=engine, verdict=verdict,
                      confidence=confidence, severity=severity, legal_basis=basis, evidence=evidence)


def _risk_nodes(doc: AdDocument, viewport: str = "desktop") -> list[TextNode]:
    if not doc.render_probe or viewport not in doc.render_probe.viewports:
        return []
    return [n for n in doc.render_probe.viewports[viewport].nodes if _RISK_RE.search(n.text)]


def _platform(rule_id: str, doc: AdDocument) -> RuleResult:
    verdict, reason = platform_rule_override(rule_id, doc.source)  # type: ignore[misc]
    dominant = None
    if doc.render_probe and "desktop" in doc.render_probe.viewports:
        dominant = doc.render_probe.viewports["desktop"].dominant_font_px
    return _result(rule_id, Verdict(verdict), Evidence(
        kind=EvidenceKind.MEASUREMENT,
        summary=f"{reason}: tekst w DOM Ad Library składa Meta, nie reklamodawca — reguła nie mierzy "
                "decyzji reklamodawcy. Tekst wtopiony w grafikę/wideo wymaga oceny ręcznej.",
        measured={"dominant_font_px": dominant} if dominant is not None else None,
        viewport="desktop" if dominant is not None else None,
        screenshot_crop=doc.screenshots.get("desktop"),
    ))


def _rule6(doc: AdDocument) -> RuleResult:
    nodes = _risk_nodes(doc)
    if not nodes:
        return _result("6", Verdict.NOT_APPLICABLE, Evidence(
            kind=EvidenceKind.ABSENCE,
            summary="Brak ostrzeżenia o ryzyku w kreacji (DOM) — nie ma czego ukrywać; brak ostrzeżenia ocenia reguła 3.",
        ))
    all_nodes = doc.render_probe.viewports["desktop"].nodes  # type: ignore[union-attr]
    top = min(n.bbox.y for n in all_nodes)
    bottom = max(n.bbox.y + n.bbox.h for n in all_nodes)
    height = max(bottom - top, 1.0)
    worst = max(nodes, key=lambda n: n.bbox.y)
    share = (worst.bbox.y - top) / height
    hidden_path = worst.in_footer or any(m in worst.dom_path.lower() for m in HIDDEN_PATH_MARKERS)
    failed = hidden_path or share > BOTTOM_SHARE
    sentence = feed_fold_evidence(worst.text)
    quote = (sentence.quote if sentence else worst.text)[:500]  # doslowne zdanie z ostrzezeniem
    return _result("6", Verdict.FAIL if failed else Verdict.PASS, Evidence(
        kind=EvidenceKind.MEASUREMENT,
        summary=(f"Ostrzeżenie „{quote[:160]}” zaczyna się na {share:.0%} wysokości kreacji"
                 + (", w stopce / sekcji prawnej" if hidden_path else "") + "."),
        measured={"y_share_of_creative": round(share, 3), "in_footer": 1.0 if worst.in_footer else 0.0},
        quote=quote,
        viewport="desktop",
        screenshot_crop=doc.screenshots.get("desktop"),
    ))


def _rule7(doc: AdDocument) -> RuleResult:
    nodes = _risk_nodes(doc)
    behind = [n for n in nodes if n.behind_interaction is not None]
    if behind:
        n = behind[0]
        return _result("7", Verdict.FAIL, Evidence(
            kind=EvidenceKind.MEASUREMENT,
            summary=f"Ostrzeżenie dostępne dopiero po interakcji ({n.behind_interaction}: {n.collapsed_evidence}).",
            quote=n.text[:500], viewport="desktop", screenshot_crop=doc.screenshots.get("desktop"),
        ))
    fold = feed_fold_evidence(doc.text)
    if fold is None:
        return _result("7", Verdict.NOT_APPLICABLE, Evidence(
            kind=EvidenceKind.ABSENCE,
            summary="Brak ostrzeżenia o ryzyku w treści — dostępności nie da się ocenić; brak ocenia reguła 3.",
        ))
    if fold.beyond_fold:
        return _result("7", Verdict.FAIL, Evidence(
            kind=EvidenceKind.MEASUREMENT,
            summary=(f"Ostrzeżenie zaczyna się na znaku {fold.risk_offset_chars} treści głównej — za progiem "
                     f"{fold.fold_chars} znaków, po którym feed Meta ucina tekst przyciskiem „Zobacz więcej”. "
                     "Prawdopodobnie ukryte za kliknięciem (heurystyka feedu, nie pomiar Ad Library)."),
            measured=fold.measured(), quote=fold.quote,
        ), engine=Engine.HYBRID, confidence=FEED_FOLD_CONFIDENCE)
    return _result("7", Verdict.PASS, Evidence(
        kind=EvidenceKind.MEASUREMENT,
        summary=f"Ostrzeżenie w pierwszych {fold.fold_chars} znakach treści głównej — widoczne bez rozwijania.",
        measured=fold.measured(), quote=fold.quote,
    ), engine=Engine.HYBRID, confidence=FEED_FOLD_CONFIDENCE)


def facebook_det_results(doc: AdDocument) -> list[RuleResult]:
    """RuleResult dla regul 4–8 dokumentu z FacebookAdsSource (w kolejnosci 4, 5, 6, 7, 8)."""
    if doc.source != "facebook":
        raise ValueError(f"facebook_det_results tylko dla source=facebook, jest {doc.source!r}")
    return [_platform("4", doc), _platform("5", doc), _rule6(doc), _rule7(doc), _platform("8", doc)]


__all__ = ["PLATFORM_TYPOGRAPHY_REASON", "RULES", "facebook_det_results"]

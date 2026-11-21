"""Reguly DET 4-8 dla dowolnego zrodla (design doc par. 7, par. 6.2.1).

Licza sie wylacznie z `AdDocument.render_probe`. Kazda regula ocenia WEZLY
Z OSTRZEZENIEM O RYZYKU (fraza ostrzegawcza, nie samo slowo „ryzyko").
Brak ostrzezenia = `not_applicable`: brak ocenia regula 3 (HYBRID, analyzer),
a nie reguly polozenia i wygladu. Brak RenderProbe = `not_applicable` z powodem.

Progi z par. 7 (stale ponizej):
  R4  risk_font_px / dominant_font_px < 0.9              -> fail
  R5  contrast_ratio < 4.5; tlo `unknown` -> not_applicable, nigdy fail
  R6  stopka / legal / disclaimer w dom_path albo y > 85% strony -> fail
  R7  behind_interaction != null                          -> fail
  R8  clipped na ktorymkolwiek viewporcie albo font < 9 px na mobile -> fail
"""

from __future__ import annotations

from contracts import AdDocument, Engine, RuleResult, TextNode, ViewportProbe
from rules_det.base import RuleBase
from sources.facebook import _RISK_RE as RISK_RE  # jedna definicja frazy ostrzegawczej w serwisie
from sources.facebook_rules import RULES

FONT_RATIO_MIN = 0.9
CONTRAST_MIN = 4.5
BOTTOM_SHARE = 0.85
MOBILE_FONT_MIN_PX = 9.0
HIDDEN_PATH_MARKERS = ("footer", "legal", "disclaimer")
VIEWPORT_ORDER = ("mobile", "tablet", "desktop")  # mobile najpierw: najdotkliwszy przypadek
SCREENSHOT_KEY = {"desktop": "desktop", "mobile": "mobile"}  # tablet: brak zrzutu w kontrakcie


def risk_nodes(vp: ViewportProbe) -> list[TextNode]:
    return [n for n in vp.nodes if RISK_RE.search(n.text)]


def _viewports(doc: AdDocument) -> list[tuple[str, ViewportProbe]]:
    if doc.render_probe is None:
        return []
    vps = doc.render_probe.viewports
    return [(name, vps[name]) for name in VIEWPORT_ORDER if name in vps]


def _short(text: str, limit: int = 300) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


class _DetRule(RuleBase):
    engine = Engine.DET

    def __init__(self) -> None:
        name, severity, basis = RULES[self.rule_id]
        self.rule_name, self.severity, self.legal_basis = name, severity, basis

    def _crop(self, doc: AdDocument, viewport: str) -> str | None:
        key = SCREENSHOT_KEY.get(viewport)
        return doc.screenshots.get(key) if key else None

    def _precheck(self, doc: AdDocument) -> RuleResult | list[tuple[str, ViewportProbe, list[TextNode]]]:
        vps = _viewports(doc)
        if not vps:
            return self.not_applicable("Brak RenderProbe — geometrii renderu nie zmierzono.")
        with_risk = [(name, vp, risk_nodes(vp)) for name, vp in vps]
        if not any(nodes for _, _, nodes in with_risk):
            return self.not_applicable(
                "Brak ostrzeżenia o ryzyku w treści — wygląd i położenie nie mają czego dotyczyć; brak ocenia reguła 3."
            )
        return with_risk


class Rule4FontSize(_DetRule):
    rule_id = "4"

    def evaluate(self, doc: AdDocument) -> RuleResult:
        pre = self._precheck(doc)
        if isinstance(pre, RuleResult):
            return pre
        worst = None  # (ratio, viewport, node, dominant)
        for name, vp, nodes in pre:
            if vp.dominant_font_px <= 0:
                continue
            for n in nodes:
                ratio = n.font_px / vp.dominant_font_px
                if worst is None or ratio < worst[0]:
                    worst = (ratio, name, n, vp.dominant_font_px)
        if worst is None:
            return self.not_applicable("Nie wyznaczono dominującej czcionki strony.")
        ratio, name, node, dominant = worst
        measured = {"risk_font_px": node.font_px, "dominant_font_px": dominant, "ratio": round(ratio, 3)}
        summary = (f"Ostrzeżenie o ryzyku ma {node.font_px:g} px przy dominującej czcionce {dominant:g} px "
                   f"({ratio:.0%}, viewport {name}).")
        kw = {"viewport": name, "screenshot_crop": self._crop(doc, name)}
        if ratio < FONT_RATIO_MIN:
            return self.failed(summary, quote=_short(node.text), measured=measured, **kw)
        return self.passed(summary, quote=_short(node.text), measured=measured, **kw)


class Rule5Contrast(_DetRule):
    rule_id = "5"

    def evaluate(self, doc: AdDocument) -> RuleResult:
        pre = self._precheck(doc)
        if isinstance(pre, RuleResult):
            return pre
        measured_nodes = [
            (name, n) for name, _, nodes in pre for n in nodes
            if n.visible and n.background_confidence != "unknown" and n.contrast_ratio is not None
        ]
        if not measured_nodes:
            return self.not_applicable(
                "Tło ostrzeżenia jest graficzne albo nie dało się go wyznaczyć — kontrast wymaga oceny ręcznej."
            )
        name, node = min(measured_nodes, key=lambda x: x[1].contrast_ratio)
        measured = {"contrast_ratio": node.contrast_ratio, "threshold": CONTRAST_MIN}
        summary = (f"Kontrast ostrzeżenia {node.contrast_ratio:g}:1 ({node.color} na {node.background_effective}, "
                   f"viewport {name}); wymagane co najmniej {CONTRAST_MIN:g}:1.")
        kw = {"viewport": name, "screenshot_crop": self._crop(doc, name)}
        if node.contrast_ratio < CONTRAST_MIN:
            return self.failed(summary, quote=_short(node.text), measured=measured, **kw)
        return self.passed(summary, quote=_short(node.text), measured=measured, **kw)


class Rule6Hidden(_DetRule):
    rule_id = "6"

    def evaluate(self, doc: AdDocument) -> RuleResult:
        pre = self._precheck(doc)
        if isinstance(pre, RuleResult):
            return pre
        for name, vp, nodes in pre:
            height = max(vp.page_height_px, 1.0)
            for n in nodes:
                share = n.bbox.y / height
                path_hit = n.in_footer or any(m in n.dom_path.lower() for m in HIDDEN_PATH_MARKERS)
                if path_hit or share > BOTTOM_SHARE:
                    where = "w stopce / sekcji prawnej" if path_hit else f"na {share:.0%} wysokości strony"
                    return self.failed(
                        f"Ostrzeżenie o ryzyku umieszczone {where} (viewport {name}, {n.dom_path}).",
                        quote=_short(n.text),
                        measured={"y_share": round(share, 3), "in_footer": 1.0 if n.in_footer else 0.0},
                        viewport=name, screenshot_crop=self._crop(doc, name),
                    )
        name, vp, nodes = next(p for p in pre if p[2])
        n = nodes[0]
        share = n.bbox.y / max(vp.page_height_px, 1.0)
        return self.passed(
            f"Ostrzeżenie o ryzyku w treści głównej, na {share:.0%} wysokości strony (viewport {name}).",
            quote=_short(n.text), measured={"y_share": round(share, 3), "in_footer": 0.0}, viewport=name,
        )


class Rule7OneClick(_DetRule):
    rule_id = "7"

    def evaluate(self, doc: AdDocument) -> RuleResult:
        pre = self._precheck(doc)
        if isinstance(pre, RuleResult):
            return pre
        for name, _, nodes in pre:
            for n in nodes:
                if n.behind_interaction is not None:
                    return self.failed(
                        f"Ostrzeżenie widoczne dopiero po interakcji: {n.behind_interaction} "
                        f"({n.collapsed_evidence}, viewport {name}).",
                        quote=_short(n.text), viewport=name, screenshot_crop=self._crop(doc, name),
                    )
        name, _, nodes = next(p for p in pre if p[2])
        return self.passed(
            f"Ostrzeżenie widoczne bez rozwijania i klikania (viewport {name}).",
            quote=_short(nodes[0].text), viewport=name,
        )


class Rule8Responsive(_DetRule):
    rule_id = "8"

    def evaluate(self, doc: AdDocument) -> RuleResult:
        pre = self._precheck(doc)
        if isinstance(pre, RuleResult):
            return pre
        names = [name for name, _, _ in pre]
        if "mobile" not in names:
            return self.not_applicable("Brak pomiaru na viewporcie mobilnym (390 px).")
        for name, _, nodes in pre:
            for n in nodes:
                if n.clipped:
                    return self.failed(
                        f"Ostrzeżenie ucięte na viewporcie {name}.",
                        quote=_short(n.text), measured={"clipped": 1.0},
                        viewport=name, screenshot_crop=self._crop(doc, name),
                    )
        mobile_nodes = next(nodes for name, _, nodes in pre if name == "mobile")
        small = [n for n in mobile_nodes if n.font_px < MOBILE_FONT_MIN_PX]
        if small:
            n = min(small, key=lambda x: x.font_px)
            return self.failed(
                f"Na telefonie ostrzeżenie ma {n.font_px:g} px, poniżej progu czytelności {MOBILE_FONT_MIN_PX:g} px.",
                quote=_short(n.text), measured={"mobile_font_px": n.font_px, "threshold": MOBILE_FONT_MIN_PX},
                viewport="mobile", screenshot_crop=self._crop(doc, "mobile"),
            )
        return self.passed(
            f"Ostrzeżenie nieucięte na {len(names)} viewportach i czytelne na telefonie.",
            quote=_short((mobile_nodes or [n for _, _, ns in pre for n in ns])[0].text),
            measured={"viewports": float(len(names))},
        )


DET_RULES: list[_DetRule] = [Rule4FontSize(), Rule5Contrast(), Rule6Hidden(), Rule7OneClick(), Rule8Responsive()]

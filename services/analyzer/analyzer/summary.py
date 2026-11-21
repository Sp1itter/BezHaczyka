"""Podsumowanie findingu dla nadzorcy: 2-3 zdania po polsku, dlaczego taka ocena.

Zrodla: `llm` (Bielik, gdy sa naruszenia i model odpowiada sensownie) albo
`template` (deterministyczny szablon). Szablon jest ZAWSZE dostepny: brak
naruszen nie wola modelu (oszczednosc GPU), a awaria lub zly wynik modelu
nigdy nie zostawia findingu bez podsumowania.
"""

from __future__ import annotations

import logging
import re

from analyzer.contracts import AdDocument, Finding, Relation, RiskLevel, RuleResult, Verdict
from analyzer.llm import LlmError, OllamaClient, load_prompt

log = logging.getLogger(__name__)

PROMPT_FILE = "summary.txt"
MAX_LEN = 700  # dluzsza odpowiedz modelu odrzucamy
QUOTE_LEN = 120  # dlugosc cytatu w szablonie i w prompcie

_LEVEL_PL = {RiskLevel.HIGH: "wysokie", RiskLevel.MEDIUM: "średnie", RiskLevel.LOW: "niskie"}
_RELATION_PL = {
    Relation.OFFICIAL: "oficjalny kanał firmy",
    Relation.THIRD_PARTY: "podmiot trzeci",
    Relation.UNKNOWN: "relacja nieustalona",
}


def _short(text: str | None, limit: int = QUOTE_LEN) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _score(finding: Finding) -> str:
    return f"{round(finding.risk_score)}"


def _failed(finding: Finding) -> list[RuleResult]:
    return [r for r in finding.rule_results if r.verdict is Verdict.FAIL]


def _proof(rule: RuleResult) -> str:
    ev = rule.evidence
    return _short(ev.quote or ev.summary)


def _firm(finding: Finding) -> str:
    firm = finding.entities.investment_firm
    name = firm.name_in_ad
    if firm.registry_match and firm.registry_match.official_name:
        name = firm.registry_match.official_name
    if not name:
        return "nie ustalono"
    return f"{name} ({'autoryzowana przez KNF' if firm.is_authorized else 'brak autoryzacji KNF'})"


def _advertiser(finding: Finding, doc: AdDocument | None) -> str:
    name = finding.entities.advertiser.name
    if not name and doc is not None:
        name = doc.publisher.display_name or doc.publisher.handle
    return name or "nie ustalono"


def _tail(finding: Finding, doc: AdDocument | None) -> str:
    relation = _RELATION_PL[finding.entities.advertiser.relation_to_firm]
    return f"Podmiot: {_firm(finding)}. Publikujący: {_advertiser(finding, doc)} ({relation})."


def _template(finding: Finding, doc: AdDocument | None) -> str:
    level = _LEVEL_PL.get(finding.risk_level, "niskie")
    fails = _failed(finding)
    if not fails:
        evaluated = sum(1 for r in finding.rule_results if r.verdict is Verdict.PASS)
        skipped = sum(1 for r in finding.rule_results if r.verdict is Verdict.NOT_APPLICABLE)
        return (
            f"Nie stwierdzono naruszeń (ryzyko {level}, wynik {_score(finding)}). "
            f"Oceniono {evaluated} reguł; {skipped} nie miało zastosowania lub wymaga "
            f"weryfikacji. {_tail(finding, doc)}"
        )
    items = "; ".join(f"reguła {r.rule_id} ({r.rule_name}) — „{_proof(r)}”" for r in fails)
    return (
        f"Ryzyko {level} (wynik {_score(finding)}). Naruszenia: {items}. "
        f"{_tail(finding, doc)}"
    )


def _prompt(finding: Finding, doc: AdDocument | None, fails: list[RuleResult]) -> str:
    adv = finding.entities.advertiser
    violations = "\n".join(
        f"- reguła {r.rule_id} ({r.rule_name}); podstawa prawna: "
        f"{r.legal_basis or 'brak'}; dowód: {_proof(r)}"
        for r in fails
    )
    values = {
        "risk_level": _LEVEL_PL.get(finding.risk_level, "niskie"),
        "risk_score": _score(finding),
        "modules": ", ".join(str(m) for m in finding.modules) or "brak",
        "routing_reason": finding.routing.reason,
        "firm": _firm(finding),
        "advertiser": _advertiser(finding, doc),
        "relation": _RELATION_PL[adv.relation_to_firm],
        "disclosure": "tak" if adv.disclosure_found else "nie",
        "violations": violations,
    }
    # Jeden przebieg: dowody moga zawierac "{...}" i nie wolno ich podstawiac ponownie.
    return re.sub(
        r"\{(\w+)\}", lambda m: values.get(m.group(1), m.group(0)), load_prompt(PROMPT_FILE)
    )


def _mentions_rule(text: str, rule_id: str) -> bool:
    """Czy tekst odwoluje sie do reguly (numer jako samodzielny token, nie czesc liczby)."""
    pattern = r"(?<![\w.,%])" + re.escape(rule_id) + r"(?![\w%]|[.,]\d)"
    return re.search(pattern, text) is not None


def _accept(data: object, fails: list[RuleResult]) -> str | None:
    """Odpowiedz modelu po straznikach; None = odrzucona."""
    if not isinstance(data, dict):
        return None
    text = str(data.get("summary") or "").strip()
    if not text or len(text) > MAX_LEN:
        return None
    if not any(_mentions_rule(text, r.rule_id) for r in fails):
        return None
    return text


def build_summary(
    finding: Finding,
    doc: AdDocument | None,
    client: OllamaClient | None = None,
    use_llm: bool = True,
) -> tuple[str, str]:
    """Zwroc (tekst, engine), engine in {"llm", "template"}. Nigdy nie rzuca LlmError."""
    fails = _failed(finding)
    if fails and use_llm:
        try:
            client = client or OllamaClient()
            data = client.generate_json(_prompt(finding, doc, fails))
            text = _accept(data, fails)
            if text:
                return text, "llm"
            log.warning("Podsumowanie %s: odpowiedz modelu odrzucona", finding.id)
        except LlmError as exc:
            log.warning("Podsumowanie %s: model niedostepny: %s", finding.id, exc)
    return _template(finding, doc), "template"

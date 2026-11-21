"""Podsumowanie findingu dla nadzorcy: 2-3 zdania po polsku, dlaczego taka ocena.

Zrodla: `llm` (Bielik, gdy sa naruszenia i model odpowiada sensownie) albo
`template` (deterministyczny szablon). Szablon jest ZAWSZE dostepny: brak
naruszen nie wola modelu (oszczednosc GPU), a awaria lub zly wynik modelu
nigdy nie zostawia findingu bez podsumowania.
"""

from __future__ import annotations

import logging
import re
import unicodedata

from analyzer.contracts import AdDocument, Finding, Relation, RiskLevel, RuleResult, Verdict
from analyzer.llm import LlmError, OllamaClient, load_prompt

log = logging.getLogger(__name__)

PROMPT_FILE = "summary.txt"
MAX_LEN = 450  # jeden limit: w prompcie i w straznika (dluzsza odpowiedz odrzucamy)
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


def _authorization(finding: Finding) -> str:
    firm = finding.entities.investment_firm
    if not (firm.name_in_ad or (firm.registry_match and firm.registry_match.official_name)):
        return "nie ustalono"
    return "autoryzowana przez KNF" if firm.is_authorized else "brak autoryzacji KNF"


def _data_values(finding: Finding, doc: AdDocument | None, fails: list[RuleResult]) -> dict:
    adv = finding.entities.advertiser
    firm = finding.entities.investment_firm
    name = firm.name_in_ad
    if firm.registry_match and firm.registry_match.official_name:
        name = firm.registry_match.official_name
    violations = "\n".join(
        f"- reguła {r.rule_id} ({r.rule_name}); podstawa prawna: "
        f"{r.legal_basis or 'brak'}; dowód: {_proof(r)}"
        for r in fails
    )
    return {
        "risk_level": _LEVEL_PL.get(finding.risk_level, "niskie"),
        "risk_score": _score(finding),
        "modules": ", ".join(str(m) for m in finding.modules) or "brak",
        "routing_reason": finding.routing.reason,
        "firm": name or "nie ustalono",
        "authorization": _authorization(finding),
        "advertiser": _advertiser(finding, doc),
        "relation": _RELATION_PL[adv.relation_to_firm],
        "disclosure": "tak" if adv.disclosure_found else "nie",
        "violations": violations,
    }


def _prompt(values: dict) -> str:
    values = {**values, "max_len": str(MAX_LEN)}
    # Jeden przebieg: dowody moga zawierac "{...}" i nie wolno ich podstawiac ponownie.
    return re.sub(
        r"\{(\w+)\}", lambda m: values.get(m.group(1), m.group(0)), load_prompt(PROMPT_FILE)
    )


def _fold(text: str) -> str:
    """Casefold bez diakrytykow (l z kreska tez), do porownan podciagow."""
    text = text.casefold().replace("ł", "l")
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c))


def _mentions_rule(text: str, rule_id: str) -> bool:
    """Czy tekst odwoluje sie do reguly (numer jako samodzielny token, nie czesc liczby)."""
    pattern = r"(?<![\w.,%])" + re.escape(rule_id) + r"(?![\w%]|[.,]\d)"
    return re.search(pattern, text) is not None


# Tokeny twierdzen prawnych/oskarzen: wolno ich uzyc tylko, gdy wystepuja w danych
# podanych modelowi (np. w podstawie prawnej reguly). Inaczej model je zmyslil.
CLAIM_TOKENS = (
    "art.", "ustaw", "rozporzadz", "dyrektyw", "zezwol", "autoryz", "licencj", "doradztw",
    "nielegaln", "oszust", "piramid", "gwarantow", "kara", "sankcj", "prokurat",
    "modul", "rejestr",  # numery modulow i rejestr KNF: tylko jesli wynikaja z naruszonych regul
)

# Sprzecznosci z naruszona regula: wzorce (na tekscie bez diakrytykow), ktore NIE moga
# wystapic, gdy regula jest naruszona (np. regula 3 lamie sie brakiem informacji o
# ryzyku, wiec streszczenie nie moze twierdzic, ze ta informacja jest).
CONTRADICTIONS: dict[str, tuple[str, ...]] = {
    "1": (r"(podaje|zawiera|wskazuje) (pelna |oficjaln\w* )?nazw\w* firm",),
    "2": (r"(jest|zostal\w*) oznaczon\w* jako reklam",),
    "3": (
        r"zawiera (informacj|ostrzezen)\w* o ryzyk",
        r"informacj\w* o ryzyku (jest|sa|zostal)",
    ),
}

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-ZĄĆĘŁŃÓŚŹŻ„\"(])")


def _sentences(text: str) -> int:
    return len(_SENTENCE_SPLIT.split(text.strip()))


def check_llm_reply(data: object, fails: list[RuleResult], data_block: str):
    """Straznik odpowiedzi modelu: (tekst, None) gdy przyjeta, (None, powod) gdy odrzucona."""
    if not isinstance(data, dict):
        return None, "ksztalt"
    text = str(data.get("summary") or "").strip()
    if not text:
        return None, "pusta"
    if len(text) > MAX_LEN:
        return None, "za_dluga"
    if _sentences(text) > 3:
        return None, "za_duzo_zdan"
    if not any(_mentions_rule(text, r.rule_id) for r in fails):
        return None, "brak_numeru_reguly"
    folded, source = _fold(text), _fold(data_block)
    for token in CLAIM_TOKENS:
        if token in folded and token not in source:
            return None, f"twierdzenie:{token}"
    for r in fails:
        for pattern in CONTRADICTIONS.get(r.rule_id, ()):
            if re.search(pattern, folded):
                return None, f"sprzecznosc:{r.rule_id}"
    return text, None


def explain_summary(
    finding: Finding,
    doc: AdDocument | None,
    client: OllamaClient | None = None,
    use_llm: bool = True,
) -> tuple[str, str, str | None]:
    """(tekst, engine, powod_odrzucenia_LLM albo None). Nigdy nie rzuca LlmError."""
    fails = _failed(finding)
    reason = None
    if fails and use_llm:
        values = _data_values(finding, doc, fails)
        # Zrodlo tokenow twierdzen: tylko naruszone reguly i pole Autoryzacja (routing moze
        # wspominac o doradztwie, ale to nie jest podstawa naruszenia).
        data_block = values["violations"] + "\n" + values["authorization"]
        try:
            client = client or OllamaClient()
            text, reason = check_llm_reply(
                client.generate_json(_prompt(values)), fails, data_block
            )
            if text:
                return text, "llm", None
            log.warning("Podsumowanie %s: odpowiedz modelu odrzucona (%s)", finding.id, reason)
        except LlmError as exc:
            reason = "llm_error"
            log.warning("Podsumowanie %s: model niedostepny: %s", finding.id, exc)
    return _template(finding, doc), "template", reason


def build_summary(
    finding: Finding,
    doc: AdDocument | None,
    client: OllamaClient | None = None,
    use_llm: bool = True,
) -> tuple[str, str]:
    """Zwroc (tekst, engine), engine in {"llm", "template"}."""
    text, engine, _ = explain_summary(finding, doc, client, use_llm)
    return text, engine

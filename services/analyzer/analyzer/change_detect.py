"""Detektor zmian — z porownania dwoch przebiegow robi zdarzenie nadzorcze.

Nadzorce nie interesuje, ze reklama istnieje, tylko ze reklamodawca usunal
ostrzezenie o ryzyku, podmienil tresc albo wycofal material. Pojedynczy przebieg
scrapera tego nie widzi. Modul to czyste funkcje: bez bazy, bez modelu, bez sieci.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from analyzer.contracts import (
    AdDocument,
    ChangeEvent,
    ChangeKind,
    ChangeSimilarity,
    Finding,
    RiskLevel,
    RuleDiff,
    RuleResult,
    Verdict,
)
from analyzer.embeddings import (
    SAME_CAMPAIGN_COSINE,
    cosine,
    hamming_distance,
    simhash,
)

# Reguly mowiace o ostrzezeniu o ryzyku (3, 6, 14). Tylko ich zmiana pass<->fail
# jest "usunieciem/dodaniem ostrzezenia".
RISK_WARNING_RULES: frozenset[str] = frozenset({"3", "6", "14"})

_RISK_ORDER = {RiskLevel.LOW: 0, RiskLevel.MEDIUM: 1, RiskLevel.HIGH: 2}


def diff_rule_results(
    previous: list[RuleResult], current: list[RuleResult]
) -> list[RuleDiff]:
    """Reguly, ktorych werdykt sie zmienil, posortowane po rule_id.

    Regula obecna tylko w jednym przebiegu nie jest roznica werdyktu - pomijana.
    Przejscie not_applicable -> fail NIE jest usunieciem ostrzezenia: znaczy tylko,
    ze tym razem dalo sie regule ocenic. Rozroznia to wywolujacy po from_verdict.
    """
    prev = {r.rule_id: r.verdict for r in previous}
    out: list[RuleDiff] = []
    for r in current:
        if r.rule_id in prev and prev[r.rule_id] != r.verdict:
            out.append(
                RuleDiff(
                    rule_id=r.rule_id,
                    from_verdict=prev[r.rule_id],
                    to_verdict=r.verdict,
                )
            )
    return sorted(out, key=lambda d: d.rule_id)


# --------------------------------------------------------------------------- #
# Pomocnicze
# --------------------------------------------------------------------------- #


def _simhash_int(doc: AdDocument) -> int:
    """Simhash z dokumentu; gdy brak lub uszkodzony - doliczany z tekstu."""
    if doc.simhash:
        try:
            return int(doc.simhash, 16)
        except ValueError:
            pass
    return simhash(doc.analyzable_text)


def _have_embeddings(a: AdDocument, b: AdDocument) -> bool:
    return a.embedding is not None and b.embedding is not None


def _cosine(a: AdDocument, b: AdDocument) -> float:
    """Brak embeddingu to degradacja do 0.0 (zostaje simhash), nie blad."""
    if a.embedding is None or b.embedding is None:
        return 0.0
    return cosine(a.embedding.vector, b.embedding.vector)


def _basis(rule_ids: list[str], *results: list[RuleResult]) -> str:
    """Podstawy prawne wskazanych regul, bez powtorzen, w kolejnosci regul."""
    bases: list[str] = []
    for rid in rule_ids:
        for lst in results:
            found = next(
                (r.legal_basis for r in lst if r.rule_id == rid and r.legal_basis), ""
            )
            if found:
                if found not in bases:
                    bases.append(found)
                break
    return "; ".join(bases)


def _rule_phrase(rule_ids: list[str], basis: str) -> str:
    label = ("regula " if len(rule_ids) == 1 else "reguly ") + ", ".join(rule_ids)
    return f"({label}, {basis})" if basis else f"({label})"


def _new_event(
    kind: ChangeKind,
    previous: Finding,
    current: Finding | None,
    summary: str,
    rule_diff: list[RuleDiff] | None = None,
    similarity: ChangeSimilarity | None = None,
) -> ChangeEvent:
    return ChangeEvent(
        id=str(uuid.uuid4()),
        document_id=(current or previous).document_id,
        kind=kind,
        detected_at=datetime.now(timezone.utc),
        previous_finding_id=previous.id,
        current_finding_id=current.id if current else None,
        rule_diff=rule_diff or [],
        similarity=similarity or ChangeSimilarity(),
        risk_level_from=previous.risk_level,
        risk_level_to=current.risk_level if current else None,
        summary=summary,
    )


def _transitions(
    diff: list[RuleDiff], src: Verdict, dst: Verdict
) -> list[str]:
    """Id regul z RISK_WARNING_RULES, ktore przeszly dokladnie src -> dst."""
    return [
        d.rule_id
        for d in diff
        if d.rule_id in RISK_WARNING_RULES
        and d.from_verdict is src
        and d.to_verdict is dst
    ]


# --------------------------------------------------------------------------- #
# Klasyfikacja
# --------------------------------------------------------------------------- #


def detect_change(
    previous: Finding,
    current: Finding,
    *,
    previous_doc: AdDocument,
    current_doc: AdDocument,
) -> ChangeEvent | None:
    """Klasyfikuje zmiane miedzy dwoma przebiegami; None gdy nic do zglaszania.

    Pierwszenstwo: usuniecie ostrzezenia, eskalacja ryzyka, dodanie ostrzezenia,
    brak zmiany (identyczny simhash), nowy wariant kampanii, tresc zmieniona.
    Nigdy nie rzuca z powodu braku embeddingu ani simhasha - degraduje.
    """
    diff = diff_rule_results(previous.rule_results, current.rule_results)
    distance = hamming_distance(_simhash_int(previous_doc), _simhash_int(current_doc))
    cos = _cosine(previous_doc, current_doc)
    similarity = ChangeSimilarity(
        simhash_distance=distance,
        cosine=round(cos, 4) if _have_embeddings(previous_doc, current_doc) else None,
    )

    def event(kind: ChangeKind, summary: str) -> ChangeEvent:
        return _new_event(kind, previous, current, summary, diff, similarity)

    removed = _transitions(diff, Verdict.PASS, Verdict.FAIL)
    if removed:
        basis = _basis(removed, current.rule_results, previous.rule_results)
        return event(
            ChangeKind.OSTRZEZENIE_USUNIETE,
            "Ostrzezenie o ryzyku zostalo usuniete z tresci glownej reklamy "
            f"{_rule_phrase(removed, basis)}.",
        )

    if _RISK_ORDER[current.risk_level] > _RISK_ORDER[previous.risk_level]:
        return event(
            ChangeKind.ESKALACJA_RYZYKA,
            "Poziom ryzyka reklamy wzrosl z "
            f"'{previous.risk_level.value}' do '{current.risk_level.value}'.",
        )

    added = _transitions(diff, Verdict.FAIL, Verdict.PASS)
    if added:
        basis = _basis(added, current.rule_results, previous.rule_results)
        return event(
            ChangeKind.OSTRZEZENIE_DODANE,
            "Ostrzezenie o ryzyku zostalo dodane do reklamy "
            f"{_rule_phrase(added, basis)}.",
        )

    if distance == 0:
        return None

    if cos >= SAME_CAMPAIGN_COSINE:
        return event(
            ChangeKind.NOWY_WARIANT_KAMPANII,
            "Wykryto przeredagowany wariant tej samej kampanii reklamowej.",
        )

    return event(
        ChangeKind.TRESC_ZMIENIONA,
        "Tresc reklamy zostala istotnie zmieniona w stosunku do poprzedniej wersji.",
    )


def detect_disappeared(previous: Finding, *, previous_doc: AdDocument) -> ChangeEvent:
    """Zdarzenie dla materialu, ktorego pobranie zwrocilo 404."""
    return _new_event(
        ChangeKind.REKLAMA_ZNIKNELA,
        previous,
        None,
        "Reklama zostala wycofana ze zrodla i nie jest juz dostepna "
        "(widziano ja jeszcze w poprzednim przebiegu).",
    )

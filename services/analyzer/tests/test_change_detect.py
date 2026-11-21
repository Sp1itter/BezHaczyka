"""Testy detektora zmian: diff regul i klasyfikacja zdarzen."""

from __future__ import annotations

from datetime import datetime, timezone

from analyzer.change_detect import (
    RISK_WARNING_RULES,
    detect_change,
    detect_disappeared,
    diff_rule_results,
)
from analyzer.contracts import (
    AdDocument,
    ChangeKind,
    Embedding,
    Evidence,
    EvidenceKind,
    Engine,
    Finding,
    RiskLevel,
    Routing,
    RuleDiff,
    RuleResult,
    ScopeStatus,
    Verdict,
)
from analyzer.embeddings import simhash_hex

_BASIS = {"3": "art. 44 ust. 2 lit. a", "6": "art. 44 ust. 2 lit. e", "14": "art. 44 ust. 2 lit. h"}


def _r(rule_id: str, verdict: Verdict) -> RuleResult:
    return RuleResult(
        rule_id=rule_id,
        rule_name=f"Regula {rule_id}",
        engine=Engine.LLM,
        verdict=verdict,
        legal_basis=_BASIS.get(rule_id, "art. 1"),
        evidence=Evidence(kind=EvidenceKind.ABSENCE, summary="x"),
    )


def _finding(
    fid: str,
    results: list[RuleResult],
    risk: RiskLevel = RiskLevel.LOW,
) -> Finding:
    return Finding(
        id=fid,
        document_id="doc-1",
        routing=Routing(rule="R1", reason="powod", scope_gate=ScopeStatus.IN_SCOPE),
        risk_level=risk,
        rule_results=results,
        created_at=datetime(2026, 11, 22, tzinfo=timezone.utc),
    )


def _doc(text: str, vector: list[float] | None = None, with_hash: bool = True) -> AdDocument:
    return AdDocument(
        id="doc-1",
        source="test",
        url="http://localhost/x",
        fetched_at=datetime(2026, 11, 22, tzinfo=timezone.utc),
        text=text,
        simhash=simhash_hex(text) if with_hash else None,
        embedding=Embedding(dim=len(vector), vector=vector) if vector else None,
    )


# --------------------------------------------------------------------------- #
# Zadanie 5: diff regul
# --------------------------------------------------------------------------- #


def test_identyczne_wyniki_daja_pusty_diff():
    rs = [_r("1", Verdict.PASS), _r("6", Verdict.FAIL)]
    assert diff_rule_results(rs, list(rs)) == []


def test_zmiana_werdyktu_jest_wykrywana():
    d = diff_rule_results([_r("6", Verdict.PASS)], [_r("6", Verdict.FAIL)])
    assert d == [RuleDiff(rule_id="6", from_verdict=Verdict.PASS, to_verdict=Verdict.FAIL)]


def test_przejscie_z_not_applicable_nie_jest_usunieciem_ostrzezenia():
    # Review Focus 5: not_applicable -> fail znaczy "dalo sie ocenic",
    # NIE "reklamodawca usunal ostrzezenie". Pomylenie da falszywy alarm.
    d = diff_rule_results([_r("6", Verdict.NOT_APPLICABLE)], [_r("6", Verdict.FAIL)])
    assert d[0].from_verdict is Verdict.NOT_APPLICABLE


def test_regula_tylko_w_jednym_przebiegu_jest_pomijana():
    d = diff_rule_results(
        [_r("1", Verdict.PASS)], [_r("2", Verdict.FAIL), _r("1", Verdict.PASS)]
    )
    assert d == []


def test_diff_jest_posortowany_po_rule_id():
    prev = [_r("9", Verdict.PASS), _r("10", Verdict.PASS), _r("2", Verdict.PASS)]
    cur = [_r("9", Verdict.FAIL), _r("10", Verdict.FAIL), _r("2", Verdict.FAIL)]
    assert [d.rule_id for d in diff_rule_results(prev, cur)] == sorted(["9", "10", "2"])


# --------------------------------------------------------------------------- #
# Zadanie 6: klasyfikacja
# --------------------------------------------------------------------------- #

_TEKST = "Inwestuj w obligacje i zarabiaj stabilnie, bez zadnego ryzyka dla Ciebie"
_V1 = [1.0, 0.0, 0.0, 0.0]


def test_usuniecie_ostrzezenia_ma_pierwszenstwo_nad_eskalacja():
    prev = _finding("p", [_r("6", Verdict.PASS)], RiskLevel.LOW)
    cur = _finding("c", [_r("6", Verdict.FAIL)], RiskLevel.HIGH)
    ev = detect_change(prev, cur, previous_doc=_doc(_TEKST), current_doc=_doc(_TEKST + " 2"))
    assert ev is not None and ev.kind is ChangeKind.OSTRZEZENIE_USUNIETE
    assert ev.risk_level_from is RiskLevel.LOW and ev.risk_level_to is RiskLevel.HIGH


def test_usuniecie_ostrzezenia_nazywa_regule_i_podstawe_prawna():
    prev = _finding("p", [_r("6", Verdict.PASS)])
    cur = _finding("c", [_r("6", Verdict.FAIL)])
    ev = detect_change(prev, cur, previous_doc=_doc(_TEKST), current_doc=_doc("zupelnie inny"))
    assert ev is not None
    assert "regula 6" in ev.summary and "art. 44 ust. 2 lit. e" in ev.summary
    assert ev.previous_finding_id == "p" and ev.current_finding_id == "c"


def test_eskalacja_ryzyka_bez_zmiany_ostrzezen():
    prev = _finding("p", [_r("1", Verdict.PASS)], RiskLevel.LOW)
    cur = _finding("c", [_r("1", Verdict.PASS)], RiskLevel.MEDIUM)
    ev = detect_change(prev, cur, previous_doc=_doc(_TEKST), current_doc=_doc(_TEKST))
    assert ev is not None and ev.kind is ChangeKind.ESKALACJA_RYZYKA


def test_dodanie_ostrzezenia():
    prev = _finding("p", [_r("6", Verdict.FAIL)])
    cur = _finding("c", [_r("6", Verdict.PASS)])
    ev = detect_change(prev, cur, previous_doc=_doc(_TEKST), current_doc=_doc("inna tresc"))
    assert ev is not None and ev.kind is ChangeKind.OSTRZEZENIE_DODANE


def test_identyczny_simhash_nie_daje_zdarzenia():
    prev = _finding("p", [_r("1", Verdict.PASS)])
    cur = _finding("c", [_r("1", Verdict.PASS)])
    assert detect_change(prev, cur, previous_doc=_doc(_TEKST), current_doc=_doc(_TEKST)) is None


def test_przeredagowany_wariant_daje_nowy_wariant_kampanii():
    prev = _finding("p", [_r("1", Verdict.PASS)])
    cur = _finding("c", [_r("1", Verdict.PASS)])
    a = _doc(_TEKST, _V1)
    b = _doc("Zupelnie inne slowa na ten sam temat obligacji", [0.95, 0.1, 0.0, 0.0])
    ev = detect_change(prev, cur, previous_doc=a, current_doc=b)
    assert ev is not None and ev.kind is ChangeKind.NOWY_WARIANT_KAMPANII
    assert ev.similarity.cosine is not None and ev.similarity.cosine >= 0.88


def test_istotna_zmiana_tresci_daje_tresc_zmieniona():
    prev = _finding("p", [_r("1", Verdict.PASS)])
    cur = _finding("c", [_r("1", Verdict.PASS)])
    a = _doc(_TEKST, _V1)
    b = _doc("Kup kryptowaluty, nowa oferta tylko dzis", [0.0, 1.0, 0.0, 0.0])
    ev = detect_change(prev, cur, previous_doc=a, current_doc=b)
    assert ev is not None and ev.kind is ChangeKind.TRESC_ZMIENIONA


def test_brak_embeddingu_degraduje_do_simhasha_bez_wyjatku():
    prev = _finding("p", [_r("1", Verdict.PASS)])
    cur = _finding("c", [_r("1", Verdict.PASS)])
    ev = detect_change(
        prev, cur, previous_doc=_doc(_TEKST, with_hash=False), current_doc=_doc("inna tresc reklamy")
    )
    assert ev is not None and ev.kind is ChangeKind.TRESC_ZMIENIONA
    assert ev.similarity.cosine is None
    same = detect_change(
        prev, cur, previous_doc=_doc(_TEKST, with_hash=False), current_doc=_doc(_TEKST)
    )
    assert same is None


def test_detect_disappeared_daje_reklama_zniknela():
    prev = _finding("p", [_r("1", Verdict.PASS)], RiskLevel.MEDIUM)
    ev = detect_disappeared(prev, previous_doc=_doc(_TEKST))
    assert ev.kind is ChangeKind.REKLAMA_ZNIKNELA
    assert ev.previous_finding_id == "p" and ev.current_finding_id is None
    assert ev.risk_level_from is RiskLevel.MEDIUM and ev.risk_level_to is None


def test_summary_jest_zdaniem_po_polsku():
    prev = _finding("p", [_r("6", Verdict.PASS)])
    cur = _finding("c", [_r("6", Verdict.FAIL)], RiskLevel.HIGH)
    events = [
        detect_change(prev, cur, previous_doc=_doc(_TEKST), current_doc=_doc("x y z")),
        detect_disappeared(prev, previous_doc=_doc(_TEKST)),
    ]
    for ev in events:
        assert ev is not None
        assert ev.summary[0].isupper() and ev.summary.endswith(".")
        assert len(ev.summary.split()) >= 5
        assert "_" not in ev.summary and "Traceback" not in ev.summary


def test_zmiana_regul_spoza_RISK_WARNING_RULES_nie_daje_usuniecia_ostrzezenia():
    assert "1" not in RISK_WARNING_RULES
    prev = _finding("p", [_r("1", Verdict.PASS)])
    cur = _finding("c", [_r("1", Verdict.FAIL)])
    ev = detect_change(prev, cur, previous_doc=_doc(_TEKST), current_doc=_doc("inna tresc reklamy"))
    assert ev is not None and ev.kind is not ChangeKind.OSTRZEZENIE_USUNIETE


def test_not_applicable_na_fail_nie_daje_usuniecia_ostrzezenia():
    # Review Focus 5 na poziomie klasyfikacji: falszywy alarm nadzorczy.
    prev = _finding("p", [_r("6", Verdict.NOT_APPLICABLE)])
    cur = _finding("c", [_r("6", Verdict.FAIL)])
    ev = detect_change(prev, cur, previous_doc=_doc(_TEKST), current_doc=_doc("inna tresc reklamy"))
    assert ev is None or ev.kind is not ChangeKind.OSTRZEZENIE_USUNIETE

"""Testy scoringu — par. 9 design doca."""

from analyzer.contracts import (
    Engine,
    Evidence,
    EvidenceKind,
    RiskLevel,
    RuleResult,
    Verdict,
)
from analyzer.scoring import (
    MEDIUM_THRESHOLD,
    coverage,
    failed_rules,
    is_flagged,
    max_breach_severity,
    risk_level,
    risk_score,
)


def _rule(
    rule_id: str,
    verdict: Verdict,
    severity: int = 3,
    confidence: float = 1.0,
) -> RuleResult:
    return RuleResult(
        rule_id=rule_id,
        rule_name=f"regula {rule_id}",
        engine=Engine.LLM,
        verdict=verdict,
        confidence=confidence,
        severity=severity,
        legal_basis="art. 44 rozp. 2017/565",
        evidence=Evidence(kind=EvidenceKind.QUOTE, summary="test"),
    )


class TestRiskScore:
    def test_pusta_lista_daje_zero(self):
        assert risk_score([]) == 0.0

    def test_wszystko_zdane_daje_zero(self):
        results = [_rule("1", Verdict.PASS), _rule("2", Verdict.PASS)]
        assert risk_score(results) == 0.0

    def test_wszystko_zlamane_daje_sto(self):
        results = [_rule("1", Verdict.FAIL), _rule("2", Verdict.FAIL)]
        assert risk_score(results) == 100.0

    def test_wazenie_po_severity(self):
        """Zlamana regula o severity 4 przy zdanej o severity 1 => 80%."""
        results = [
            _rule("1", Verdict.FAIL, severity=4),
            _rule("2", Verdict.PASS, severity=1),
        ]
        assert risk_score(results) == 80.0

    def test_confidence_obniza_wklad(self):
        results = [_rule("1", Verdict.FAIL, severity=2, confidence=0.5)]
        assert risk_score(results) == 50.0


class TestNotApplicableNieWchodziDoMianownika:
    """Kluczowa decyzja z par. 9: reklama milczaca o podatkach nie moze
    dostawac sztucznie niskiego score'u tylko dlatego, ze o czyms nie wspomniala."""

    def test_not_applicable_jest_pomijane(self):
        results = [
            _rule("1", Verdict.FAIL, severity=3),
            _rule("16", Verdict.NOT_APPLICABLE, severity=3),
        ]
        # 3 / 3 = 100%, a nie 3 / 6 = 50%
        assert risk_score(results) == 100.0

    def test_same_not_applicable_daje_zero_nie_dzielenie_przez_zero(self):
        results = [
            _rule("16", Verdict.NOT_APPLICABLE),
            _rule("12a", Verdict.NOT_APPLICABLE),
        ]
        assert risk_score(results) == 0.0


class TestRiskLevel:
    def test_progi(self):
        assert risk_level(85.0) is RiskLevel.HIGH
        assert risk_level(70.0) is RiskLevel.HIGH
        assert risk_level(55.0) is RiskLevel.MEDIUM
        assert risk_level(40.0) is RiskLevel.MEDIUM
        assert risk_level(10.0) is RiskLevel.LOW


class TestIsFlagged:
    def test_suwak_thresholdu_zmienia_flage(self):
        """Ta sama funkcja musi byc zaimplementowana w JS po stronie frontu,
        zeby panel kalibracji dzialal bez requestu do modelu."""
        assert is_flagged(60.0, threshold=50.0) is True
        assert is_flagged(60.0, threshold=70.0) is False

    def test_rowny_progowi_jest_oflagowany(self):
        assert is_flagged(50.0, threshold=50.0) is True


class TestFailedRules:
    def test_sortowanie_od_najciezszej(self):
        results = [
            _rule("a", Verdict.FAIL, severity=2),
            _rule("b", Verdict.FAIL, severity=5),
            _rule("c", Verdict.PASS, severity=5),
        ]
        out = failed_rules(results)
        assert [r.rule_id for r in out] == ["b", "a"]


class TestCoverage:
    def test_pokrycie_pokazuje_ile_dalo_sie_ocenic(self):
        results = [
            _rule("1", Verdict.FAIL),
            _rule("2", Verdict.PASS),
            _rule("3", Verdict.NOT_APPLICABLE),
            _rule("4", Verdict.NOT_APPLICABLE),
        ]
        assert coverage(results) == 0.5

    def test_pusta_lista(self):
        assert coverage([]) == 0.0


class TestEskalacjiPoNajciezszymNaruszeniu:
    """Regresja na wade wzoru znaleziona na zbiorze zlotym.

    `risk_score` jest proporcjonalny, wiec to samo naruszenie o wadze 5 dawalo
    45 punktow przy dwoch zdanych regulach i tylko 17 przy osmiu — im wiecej
    wymogow reklama spelniala, tym taniej wychodzilo jej powazne naruszenie.
    Nadzorca nie mysli "narusza jeden z dziewieciu wymogow", tylko "narusza
    art. 44 ust. 8", dlatego poziom bierze TEZ wage najciezszego naruszenia.
    """

    def test_ciezkie_naruszenie_eskaluje_mimo_niskiego_score(self):
        results = [_rule("18", Verdict.FAIL, severity=5)] + [
            _rule(str(i), Verdict.PASS, severity=3) for i in range(8)
        ]
        score = risk_score(results)
        assert score < MEDIUM_THRESHOLD, "score ma byc niski — o to w tym tescie chodzi"
        assert risk_level(score, results) is RiskLevel.HIGH

    def test_naruszenie_wagi_4_eskaluje_do_medium(self):
        results = [_rule("14", Verdict.FAIL, severity=4)] + [
            _rule(str(i), Verdict.PASS, severity=3) for i in range(8)
        ]
        assert risk_level(risk_score(results), results) is RiskLevel.MEDIUM

    def test_heurystyka_o_niskiej_pewnosci_nie_eskaluje(self):
        """Regula 7 na feedzie Facebooka ma confidence 0.6 — heurystyka nie moze
        sama podnosic materialu do poziomu wysokiego."""
        results = [_rule("7", Verdict.FAIL, severity=5, confidence=0.6)] + [
            _rule(str(i), Verdict.PASS, severity=3) for i in range(8)
        ]
        assert risk_level(risk_score(results), results) is RiskLevel.LOW

    def test_eskalacja_nigdy_nie_obniza_poziomu(self):
        """Wysoki score zostaje wysoki, nawet gdy najciezsze naruszenie jest lekkie."""
        results = [_rule("16", Verdict.FAIL, severity=2)]
        assert risk_score(results) == 100.0
        assert risk_level(risk_score(results), results) is RiskLevel.HIGH

    def test_bez_results_zachowanie_jak_wczesniej(self):
        assert risk_level(10.0) is RiskLevel.LOW
        assert risk_level(85.0) is RiskLevel.HIGH

    def test_brak_naruszen_nie_eskaluje(self):
        results = [_rule("1", Verdict.PASS, severity=5)]
        assert risk_level(risk_score(results), results) is RiskLevel.LOW


class TestMaxBreachSeverity:
    def test_bierze_najciezsze_pewne_naruszenie(self):
        results = [
            _rule("a", Verdict.FAIL, severity=3),
            _rule("b", Verdict.FAIL, severity=5),
            _rule("c", Verdict.PASS, severity=5),
        ]
        assert max_breach_severity(results) == 5

    def test_pomija_naruszenia_o_niskiej_pewnosci(self):
        results = [_rule("a", Verdict.FAIL, severity=5, confidence=0.4)]
        assert max_breach_severity(results) == 0

    def test_pusta_lista(self):
        assert max_breach_severity([]) == 0

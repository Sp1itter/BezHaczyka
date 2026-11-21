"""Test kontraktowy — pilnuje, zeby kopie kontraktow sie nie rozjechaly.

Interfejs `Rule` i modele kontraktow sa ZDUPLIKOWANE miedzy serwisami
(scraper osoby A i analyzer osoby B), bo wspolny modul wymusilby `context: .`
w docker-compose. Ten test jest mechanizmem, ktory chroni duplikaty:
oba serwisy walidują te same pliki z fixtures/contract-examples/.

Jesli osoba A zmieni kształt RuleResult u siebie, ten test padnie od razu,
a nie dopiero przy integracji o 19:00.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from analyzer.contracts import (
    AdDocument,
    Finding,
    RenderProbe,
    RuleResult,
    Scope,
    ScopeStatus,
    Verdict,
)
from analyzer.rules_llm.base import Rule, RuleBase

FIXTURES = Path(__file__).resolve().parents[3] / "fixtures" / "contract-examples"

MODELS = {
    "ad_document.json": AdDocument,
    "render_probe.json": RenderProbe,
    "rule_result.json": RuleResult,
    "finding.json": Finding,
    "scope.json": Scope,
}


@pytest.mark.parametrize("filename,model", MODELS.items())
def test_przyklad_waliduje_sie_przeciw_modelowi(filename: str, model: type) -> None:
    path = FIXTURES / filename
    assert path.exists(), (
        f"Brak {path}. Wygeneruj: python tools/gen_contract_examples.py"
    )
    data = json.loads(path.read_text(encoding="utf-8"))
    model.model_validate(data)


def test_rule_result_ma_dowod_dla_kazdego_werdyktu() -> None:
    """Kazdy RuleResult musi miec evidence — nadzorca nie przyjmie werdyktu
    bez uzasadnienia. To nie jest opcjonalne pole."""
    data = json.loads((FIXTURES / "rule_result.json").read_text(encoding="utf-8"))
    rr = RuleResult.model_validate(data)
    assert rr.evidence.summary
    assert rr.evidence.measured is not None, (
        "Regula DET musi podac pomiar, nie tylko opis"
    )


def test_finding_moze_nalezec_do_wielu_modulow() -> None:
    """Regresja: dawny kontrakt mial `module: int` i to uniemozliwialo
    reklame finfluencera obiecujaca zyski (Modul 1 + Modul 2 naraz)."""
    data = json.loads((FIXTURES / "finding.json").read_text(encoding="utf-8"))
    f = Finding.model_validate(data)
    assert len(f.modules) > 1
    assert f.primary_module in f.modules
    assert f.routing.reason, "routing.reason jest pokazywane w UI, nie moze byc puste"


def test_cfd_na_krypto_jest_w_zakresie_w_przykladzie() -> None:
    """Przyklad kontraktu utrwala poprawna interpretacje zakresu."""
    data = json.loads((FIXTURES / "scope.json").read_text(encoding="utf-8"))
    s = Scope.model_validate(data)
    assert s.status is ScopeStatus.IN_SCOPE
    assert s.instrument_wrapper == "cfd"
    assert s.underlying == "crypto"
    assert "crypto_derivative" in s.tags


def test_analyzable_text_zawiera_transkrypcje() -> None:
    """Reklama wideo musi przechodzic przez TEN SAM silnik regul co tekstowa."""
    data = json.loads((FIXTURES / "ad_document.json").read_text(encoding="utf-8"))
    doc = AdDocument.model_validate(data)
    assert doc.transcript is not None
    assert doc.transcript.text in doc.analyzable_text
    assert doc.text in doc.analyzable_text


def test_tempo_segmentu_transkryptu_jest_liczone() -> None:
    """Disclaimer czytany szybciej niz reszta narracji to mierzalny sygnal."""
    data = json.loads((FIXTURES / "ad_document.json").read_text(encoding="utf-8"))
    doc = AdDocument.model_validate(data)
    assert doc.transcript is not None
    risk_seg = doc.transcript.segments[-1]
    profit_seg = doc.transcript.segments[0]
    assert risk_seg.chars_per_second > profit_seg.chars_per_second, (
        "W przykladzie ostrzezenie jest czytane szybciej — to ma byc wykrywalne"
    )


class TestInterfejsRule:
    def test_rulebase_spelnia_protokol(self) -> None:
        class DummyRule(RuleBase):
            rule_id = "test"
            rule_name = "regula testowa"
            legal_basis = "brak"

            def evaluate(self, doc: AdDocument) -> RuleResult:
                return self.passed("ok", quote="cytat")

        assert isinstance(DummyRule(), Rule)

    def test_not_applicable_nigdy_nie_jest_failem(self) -> None:
        """Krytyczne dla reguly 5: brak danych != naruszenie."""

        class DummyRule(RuleBase):
            rule_id = "5"
            rule_name = "kontrast"
            legal_basis = "art. 44 ust. 2 lit. c i e"

            def evaluate(self, doc: AdDocument) -> RuleResult:
                return self.not_applicable("tlo graficzne, nie da sie zmierzyc")

        result = DummyRule().evaluate(None)  # type: ignore[arg-type]
        assert result.verdict is Verdict.NOT_APPLICABLE
        assert result.verdict is not Verdict.FAIL
        assert "tlo graficzne" in result.evidence.summary

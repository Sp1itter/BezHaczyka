"""Test kontraktowy kopii kontraktow scrapera — lustro testu w analyzerze.

Oba serwisy waliduja TE SAME pliki z fixtures/contract-examples/. Jesli kopie
sie rozjada, padnie test po tej stronie, ktora odbiegla od przykladow.
"""

from __future__ import annotations

import json

import pytest

from contracts import AdDocument, Finding, RenderProbe, RuleResult, Scope
from tests.conftest import REPO_ROOT

EXAMPLES = REPO_ROOT / "fixtures" / "contract-examples"
MODELS = {
    "ad_document.json": AdDocument,
    "render_probe.json": RenderProbe,
    "rule_result.json": RuleResult,
    "finding.json": Finding,
    "scope.json": Scope,
}


@pytest.mark.parametrize("filename,model", MODELS.items())
def test_example_validates(filename, model):
    data = json.loads((EXAMPLES / filename).read_text(encoding="utf-8"))
    model.model_validate(data)


def test_contract_copy_matches_analyzer():
    """Cialo pliku (bez naglowka) musi byc identyczne z kopia analyzera."""
    ours = (REPO_ROOT / "services" / "scraper" / "contracts.py").read_text(encoding="utf-8")
    theirs_path = REPO_ROOT / "services" / "analyzer" / "analyzer" / "contracts.py"
    if not theirs_path.exists():
        pytest.skip("brak kopii analyzera w tym checkoutcie")
    theirs = theirs_path.read_text(encoding="utf-8")
    body = lambda s: s.split("from __future__ import annotations", 1)[1]
    assert body(ours) == body(theirs)


def test_facebook_golden_examples():
    """Artefakty handoffu z prawdziwego nagrania (tools/gen_facebook_examples.py)."""
    doc_path = EXAMPLES / "facebook_ad_document.json"
    rr_path = EXAMPLES / "rule_result_facebook.json"
    if not doc_path.exists():
        pytest.skip("brak facebook_ad_document.json — uruchom tools/gen_facebook_examples.py")
    doc = AdDocument.model_validate(json.loads(doc_path.read_text(encoding="utf-8")))
    assert doc.source == "facebook" and "/ads/library/?id=" in doc.url
    assert set(doc.screenshots) == {"desktop", "mobile"}  # par. 6.1: bez tabletu
    results = [RuleResult.model_validate(r) for r in json.loads(rr_path.read_text(encoding="utf-8"))]
    assert [r.rule_id for r in results] == ["4", "5", "6", "7", "8"]
    for r in results:
        if r.rule_id in {"4", "5", "8"}:
            assert r.verdict.value == "not_applicable"

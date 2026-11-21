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

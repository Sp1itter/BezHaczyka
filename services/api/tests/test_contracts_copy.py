"""Kopia kontraktow api musi byc identyczna z kopia analyzera (bez services/common/)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from api import contracts as ours

REPO = Path(__file__).resolve().parents[3]
ANALYZER = REPO / "services" / "analyzer" / "analyzer" / "contracts.py"
MODELS = ("AdDocument", "Finding", "RuleResult", "RenderProbe", "Scope", "ChangeEvent")


def _load_analyzer():
    spec = importlib.util.spec_from_file_location("analyzer_contracts_copy", ANALYZER)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod  # pydantic rozwiazuje adnotacje przez sys.modules
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.skipif(not ANALYZER.exists(), reason="brak kopii analyzera w checkoutcie")
@pytest.mark.parametrize("name", MODELS)
def test_schema_identical_with_analyzer(name: str) -> None:
    theirs = _load_analyzer()
    assert getattr(ours, name).model_json_schema() == getattr(theirs, name).model_json_schema()


@pytest.mark.parametrize(
    "fixture,model",
    [("finding.json", "Finding"), ("ad_document.json", "AdDocument"),
     ("facebook_ad_document.json", "AdDocument")],
)
def test_fixtures_validate(fixture: str, model: str) -> None:
    data = json.loads((REPO / "fixtures" / "contract-examples" / fixture).read_text(encoding="utf-8"))
    getattr(ours, model).model_validate(data)

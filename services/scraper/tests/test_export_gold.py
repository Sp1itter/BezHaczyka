"""Eksport pelnych AdDocument dla analyzera i casedb (tools/export_gold_documents.py)."""

from __future__ import annotations

import json
import re

from contracts import AdDocument, RuleResult
from tests.conftest import FIXTURES, REPO_ROOT
from tools.export_gold_documents import export


def test_export_writes_documents_det_and_list(tmp_path, chromium_available):
    ids = export(FIXTURES / "facebook", tmp_path)
    assert sorted(ids) == ["1234567890123456", "2345678901234567"]
    for ad_id in ids:
        doc = AdDocument.model_validate(json.loads((tmp_path / f"{ad_id}.json").read_text(encoding="utf-8")))
        assert doc.render_probe is not None
        assert set(doc.render_probe.viewports) == {"desktop", "tablet", "mobile"}
        assert set(doc.screenshots) == {"desktop", "mobile"}
        det = [RuleResult.model_validate(r)
               for r in json.loads((tmp_path / f"{ad_id}.det.json").read_text(encoding="utf-8"))]
        assert [r.rule_id for r in det] == ["4", "5", "6", "7", "8"]
    all_docs = json.loads((tmp_path / "facebook_all.json").read_text(encoding="utf-8"))
    assert isinstance(all_docs, list) and len(all_docs) == 2


def test_exported_files_are_sanitized(tmp_path, chromium_available):
    export(FIXTURES / "facebook", tmp_path)
    for path in tmp_path.glob("*.json"):
        hosts = set(re.findall(r"(?i)https?://([A-Za-z0-9_.\-]+)", path.read_text(encoding="utf-8")))
        assert hosts <= {"example.invalid"}, (path.name, hosts)


def test_committed_gold_documents_are_complete():
    """Wyeksportowany korpus w repo: 8 reklam, kazda z RenderProbe i det_results."""
    out = REPO_ROOT / "fixtures" / "gold" / "documents"
    docs = sorted(p for p in out.glob("*.json") if not p.name.endswith(".det.json") and p.name != "facebook_all.json")
    assert len(docs) == 8
    for p in docs:
        doc = AdDocument.model_validate(json.loads(p.read_text(encoding="utf-8")))
        assert doc.render_probe is not None and len(doc.render_probe.viewports) == 3
        assert (out / f"{p.stem}.det.json").is_file()

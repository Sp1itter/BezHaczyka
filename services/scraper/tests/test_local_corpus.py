"""Korpus demo: kazda strona daje dokladnie werdykty ze swojego .labels.json."""

from __future__ import annotations

import json

import pytest

from contracts import AdDocument
from rules_det import evaluate_det
from sources import Source
from sources.local_corpus import LocalCorpusSource
from storage import LocalBlobStore
from tests.conftest import REPO_ROOT

CORPUS = REPO_ROOT / "fixtures" / "demo-ads"
PAGES = sorted(p.stem for p in CORPUS.glob("demo-*.html"))


@pytest.fixture(scope="module")
def results(tmp_path_factory, chromium_available) -> dict[str, tuple[AdDocument, dict[str, str]]]:
    src = LocalCorpusSource(corpus_dir=CORPUS, store=LocalBlobStore(tmp_path_factory.mktemp("blobs")))
    out = {}
    for url in src.discover():
        doc = src.fetch(url)
        out[src._page_name(url)[:-5]] = (doc, {r.rule_id: r.verdict.value for r in evaluate_det(doc)})
    return out


def test_corpus_has_pages_with_labels():
    assert len(PAGES) >= 3
    for stem in PAGES:
        assert (CORPUS / f"{stem}.labels.json").is_file(), stem


def test_source_protocol_and_discover_urls():
    src = LocalCorpusSource(corpus_dir=CORPUS)
    assert isinstance(src, Source)
    assert all(u.startswith("file:///") for u in src.discover())
    served = LocalCorpusSource(corpus_dir=CORPUS, base_url="http://nginx")
    assert served.discover("demo-001") == ["http://nginx/demo-001.html"]


@pytest.mark.parametrize("stem", PAGES)
def test_page_verdicts_match_labels(results, stem):
    labels = json.loads((CORPUS / f"{stem}.labels.json").read_text(encoding="utf-8"))["rule_labels"]
    _, verdicts = results[stem]
    assert {k: verdicts[k] for k in labels} == labels


@pytest.mark.parametrize("stem", PAGES)
def test_documents_follow_contract(results, stem):
    doc, _ = results[stem]
    AdDocument.model_validate(doc.model_dump(mode="json"))
    assert doc.source == "web"
    assert set(doc.render_probe.viewports) == {"desktop", "tablet", "mobile"}
    assert doc.screenshots == {"desktop": f"s3://shots/{doc.id}-1920.png", "mobile": f"s3://shots/{doc.id}-390.png"}
    assert doc.text and doc.title


def test_document_id_independent_of_url():
    a = LocalCorpusSource(corpus_dir=CORPUS)
    b = LocalCorpusSource(corpus_dir=CORPUS, base_url="http://nginx")
    assert a._page_name(a.discover("demo-001")[0]) == b._page_name(b.discover("demo-001")[0])

"""Kontrakt przekazania scraper -> API -> analyzer (docs/INTEGRACJA.md)."""

from __future__ import annotations

import json
import urllib.error
from datetime import UTC, datetime

import pytest

from contracts import AdDocument, RuleResult
from jobs import (
    ANALYSIS_QUEUE,
    ANALYZE_FUNC,
    ApiError,
    build_analysis_payload,
    det_results_for,
    hand_off,
    post_document,
)
from tests.conftest import REPO_ROOT

GOLDEN = REPO_ROOT / "fixtures" / "contract-examples" / "facebook_ad_document.json"


@pytest.fixture
def doc() -> AdDocument:
    return AdDocument.model_validate(json.loads(GOLDEN.read_text(encoding="utf-8")))


class FakeQueue:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def enqueue(self, func, *args, **kwargs):
        self.calls.append((func, args, kwargs))


class FakeResponse:
    def __init__(self, status: int, body: bytes) -> None:
        self.status, self._body = status, body

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_names_match_analyzer_worker():
    # analyzer/worker.py: QUEUE_NAME = "q:gpu", def analyze_document(payload)
    assert ANALYSIS_QUEUE == "q:gpu"
    assert ANALYZE_FUNC == "analyzer.worker.analyze_document"


def test_payload_shape_matches_integracja():
    now = datetime(2026, 11, 21, 18, 0, tzinfo=UTC)
    assert build_analysis_payload("abc", [], now) == {
        "document_id": "abc",
        "enqueued_at": "2026-11-21T18:00:00Z",
        "det_results": [],
    }


def test_facebook_det_results_are_valid_rule_results(doc):
    det = det_results_for(doc)
    assert [r["rule_id"] for r in det] == ["4", "5", "6", "7", "8"]
    for r in det:
        RuleResult.model_validate(r)


def test_post_document_sends_full_document_and_returns_api_id(doc):
    seen = {}

    def opener(req, timeout):
        seen["url"], seen["method"] = req.full_url, req.get_method()
        seen["body"] = json.loads(req.data)
        return FakeResponse(201, json.dumps({"id": "api-id-1"}).encode())

    assert post_document(doc, base_url="http://api.test:8000", opener=opener) == "api-id-1"
    assert seen["url"] == "http://api.test:8000/documents" and seen["method"] == "POST"
    AdDocument.model_validate(seen["body"])


def test_post_document_falls_back_to_document_id(doc):
    assert post_document(doc, base_url="http://x.test", opener=lambda r, timeout: FakeResponse(200, b"")) == doc.id


def test_post_document_raises_when_api_down(doc):
    def opener(req, timeout):
        raise urllib.error.URLError("connection refused")

    with pytest.raises(ApiError):
        post_document(doc, base_url="http://x.test", opener=opener)


def test_post_document_raises_on_bad_status(doc):
    with pytest.raises(ApiError):
        post_document(doc, base_url="http://x.test", opener=lambda r, timeout: FakeResponse(500, b""))


def test_hand_off_posts_then_enqueues_minimal_payload(doc):
    queue = FakeQueue()
    payload = hand_off(doc, queue, poster=lambda d: d.id)
    assert len(queue.calls) == 1
    func, args, _kwargs = queue.calls[0]
    assert func == ANALYZE_FUNC
    assert args == (payload,)
    assert set(payload) == {"document_id", "enqueued_at", "det_results"}
    assert payload["document_id"] == doc.id
    assert len(payload["det_results"]) == 5


def test_hand_off_does_not_enqueue_when_api_fails(doc):
    queue = FakeQueue()

    def poster(d):
        raise ApiError("down")

    with pytest.raises(ApiError):
        hand_off(doc, queue, poster=poster)
    assert queue.calls == []

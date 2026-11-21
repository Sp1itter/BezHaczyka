"""Produkcyjne punkty wejscia musza dostac PELNY potok, nie pusty AnalyzerConfig.

Regresja: worker RQ wolal analyze(..., config=None), a pipeline podstawial
AnalyzerConfig() bez runnerow - zadanie ze scrapera dostawalo same placeholdery.
"""

from __future__ import annotations

import pytest

from analyzer import worker
from analyzer.rules_llm import registry


@pytest.mark.real_default_config
def test_default_config_ma_wszystkie_runnery_modulu_2(monkeypatch):
    monkeypatch.setenv("STT_ENABLED", "0")
    registry.default_config.cache_clear()
    cfg = registry.default_config()
    assert len(cfg.module2_runners) == len(registry.module2_runners(None))
    assert cfg.embed_client is not None
    assert cfg.transcriber is None


@pytest.mark.real_default_config
def test_default_config_wpina_whisper_gdy_wlaczony(monkeypatch):
    monkeypatch.setenv("STT_ENABLED", "1")
    registry.default_config.cache_clear()
    cfg = registry.default_config()
    assert callable(cfg.transcriber)
    registry.default_config.cache_clear()


class _FakeApi:
    def post_document(self, doc):  # dokument z payloadu zapisujemy przed analiza
        pass


@pytest.mark.real_default_config
def test_worker_bez_configu_uzywa_pelnego_potoku(monkeypatch):
    seen = {}

    def fake_analyze(doc, entities, config, det_results=None):
        seen["config"] = config
        raise RuntimeError("stop")

    monkeypatch.setenv("STT_ENABLED", "0")
    registry.default_config.cache_clear()
    monkeypatch.setattr(worker, "analyze", fake_analyze)
    payload = {"id": "x", "url": "https://example.invalid/a", "text": "t",
               "fetched_at": "2026-11-21T00:00:00Z", "source": "web"}
    try:
        worker.handle_job(payload, api=_FakeApi())  # type: ignore[arg-type]
    except RuntimeError:
        pass
    assert seen["config"] is not None
    assert len(seen["config"].module2_runners) > 0
    registry.default_config.cache_clear()

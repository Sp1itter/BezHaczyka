"""Wspolne fixtury testow analyzera."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _offline_default_config(request, monkeypatch):
    """Testy nigdy nie wolaja zywej Ollamy przez registry.default_config.

    Worker bez jawnego configu buduje pelny potok produkcyjny (LLM + Whisper).
    W testach podmieniamy go na pusty AnalyzerConfig, chyba ze test jest
    oznaczony `real_default_config` (test samej fabryki).
    """
    # Podsumowanie findingu tez nie wola Ollamy (szablon); testy summary podstawiaja atrape.
    monkeypatch.setenv("SUMMARY_LLM", "0")
    if request.node.get_closest_marker("real_default_config"):
        yield
        return
    from analyzer.pipeline import AnalyzerConfig
    from analyzer.rules_llm import registry

    monkeypatch.setattr(registry, "default_config", lambda: AnalyzerConfig())
    yield


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "real_default_config: uzyj prawdziwej fabryki default_config"
    )

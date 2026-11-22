"""Worker czeka na modele, zanim zacznie analizowac (kontenery z autoskalera przy pierwszym starcie)."""

from __future__ import annotations

from analyzer.worker import wait_for_models


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def sleep(self, s):
        self.t += s


def test_czeka_az_modele_sie_pojawia(monkeypatch):
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama:11434")
    answers = [[], ["bge-m3:latest"], ["bge-m3:latest", "SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0"]]
    clock = Clock()
    assert wait_for_models(fetch_tags=lambda: answers.pop(0), sleep=clock.sleep, clock=clock) is True
    assert clock.t == 20


def test_ollama_niedostepna_konczy_po_limicie(monkeypatch):
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama:11434")
    monkeypatch.setenv("ANALYZER_MODEL_WAIT_S", "30")
    clock = Clock()

    def boom():
        raise ConnectionError("nie wstala")

    assert wait_for_models(fetch_tags=boom, sleep=clock.sleep, clock=clock) is False
    assert clock.t >= 30


def test_pusty_adres_wylacza_czekanie(monkeypatch):
    monkeypatch.setenv("OLLAMA_BASE_URL", "")
    assert wait_for_models(fetch_tags=lambda: [], sleep=lambda s: None) is False

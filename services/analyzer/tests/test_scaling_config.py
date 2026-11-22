"""Testy konfiguracji skalowania i jej niezmiennikow."""

import pytest

from analyzer.scaling import (
    DEFAULT_SCALING_CONFIG,
    ScalingConfigError,
    load_scaling_config,
)


def _zapisz(tmp_path, tresc):
    p = tmp_path / "scaling.yaml"
    p.write_text(tresc, encoding="utf-8")
    return p


def test_domyslny_plik_sie_wczytuje():
    cfg = load_scaling_config()
    assert cfg.executor == "compose"
    assert cfg.hard_max_total == 16
    assert cfg.queues["q:gpu"].max_workers == 4


def test_plik_yaml_zgodny_z_domyslna_konfiguracja():
    assert load_scaling_config() == DEFAULT_SCALING_CONFIG


def test_brak_pliku_daje_domyslna_konfiguracje_bez_wyjatku(tmp_path):
    assert load_scaling_config(tmp_path / "nie-ma.yaml") == DEFAULT_SCALING_CONFIG


def test_uszkodzony_yaml_daje_domyslna_konfiguracje(tmp_path):
    p = _zapisz(tmp_path, "scaling: [to nie slownik")
    assert load_scaling_config(p) == DEFAULT_SCALING_CONFIG


def test_wiecej_workerow_gpu_niz_endpointow_jest_odrzucane(tmp_path):
    # Review Focus 1: puste workery GPU nie daja przepustowosci,
    # bo caly czas analizy to model (zmierzone: 100% czasu).
    p = _zapisz(
        tmp_path,
        "scaling:\n"
        "  executor: dry-run\n"
        "  hard_max_total: 6\n"
        "  queues:\n"
        "    'q:gpu': {min: 1, max: 8, scale_up_backlog: 3, scale_down_idle_s: 600}\n"
        "  ollama_endpoints: ['http://127.0.0.1:11434']\n",
    )
    with pytest.raises(ScalingConfigError, match="OLLAMA_NUM_PARALLEL"):
        load_scaling_config(p)


def test_min_wieksze_od_max_jest_odrzucane(tmp_path):
    p = _zapisz(
        tmp_path,
        "scaling:\n"
        "  queues:\n"
        "    'q:ingest': {min: 3, max: 2, scale_up_backlog: 10, scale_down_idle_s: 300}\n",
    )
    with pytest.raises(ScalingConfigError, match="min"):
        load_scaling_config(p)


def test_hard_max_total_mniejszy_od_sumy_min_jest_odrzucany(tmp_path):
    p = _zapisz(
        tmp_path,
        "scaling:\n"
        "  hard_max_total: 2\n"
        "  queues:\n"
        "    'q:ingest': {min: 1, max: 4, scale_up_backlog: 10, scale_down_idle_s: 300}\n"
        "    'q:render': {min: 1, max: 2, scale_up_backlog: 5, scale_down_idle_s: 300}\n"
        "    'q:gpu': {min: 1, max: 1, scale_up_backlog: 3, scale_down_idle_s: 600}\n",
    )
    with pytest.raises(ScalingConfigError, match="hard_max_total"):
        load_scaling_config(p)


def test_nieznany_executor_jest_odrzucany(tmp_path):
    p = _zapisz(tmp_path, "scaling:\n  executor: kubernetes\n")
    with pytest.raises(ScalingConfigError, match="executor"):
        load_scaling_config(p)

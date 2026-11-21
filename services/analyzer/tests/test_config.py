"""Testy loadera progow (analyzer/config_loader.py) i zgodnosci YAML-a z kodem."""

from __future__ import annotations

from analyzer import embeddings, scoring
from analyzer.config_loader import (
    DEFAULT_THRESHOLDS,
    DEFAULT_THRESHOLDS_PATH,
    get_threshold,
    load_thresholds,
)


def test_poprawny_plik_jest_wczytywany(tmp_path):
    cfg = tmp_path / "progi.yaml"
    cfg.write_text(
        "scoring:\n  flag_threshold: 61.0\n  high_threshold: 80.0\n",
        encoding="utf-8",
    )

    result = load_thresholds(cfg)

    assert result["scoring"]["flag_threshold"] == 61.0
    assert result["scoring"]["high_threshold"] == 80.0


def test_brakujacy_plik_zwraca_wartosci_domyslne(tmp_path):
    result = load_thresholds(tmp_path / "nie_ma_tego.yaml")

    assert result == DEFAULT_THRESHOLDS


def test_uszkodzony_yaml_zwraca_wartosci_domyslne(tmp_path):
    cfg = tmp_path / "zepsuty.yaml"
    cfg.write_text("scoring: [niedomkniete, \n  : : :", encoding="utf-8")

    result = load_thresholds(cfg)

    assert result == DEFAULT_THRESHOLDS


def test_plik_nie_bedacy_slownikiem_zwraca_wartosci_domyslne(tmp_path):
    cfg = tmp_path / "lista.yaml"
    cfg.write_text("- 1\n- 2\n- 3\n", encoding="utf-8")

    assert load_thresholds(cfg) == DEFAULT_THRESHOLDS


def test_pusty_plik_zwraca_wartosci_domyslne(tmp_path):
    cfg = tmp_path / "pusty.yaml"
    cfg.write_text("", encoding="utf-8")

    assert load_thresholds(cfg) == DEFAULT_THRESHOLDS


def test_brakujace_klucze_uzupelniane_domyslnymi(tmp_path):
    cfg = tmp_path / "czesciowy.yaml"
    cfg.write_text("scoring:\n  flag_threshold: 55.0\n", encoding="utf-8")

    result = load_thresholds(cfg)

    assert result["scoring"]["flag_threshold"] == 55.0
    # Pozostale klucze pochodza z wartosci domyslnych.
    assert result["scoring"]["high_threshold"] == DEFAULT_THRESHOLDS["scoring"]["high_threshold"]
    assert result["dedup"] == DEFAULT_THRESHOLDS["dedup"]


def test_odczyt_po_sciezce_z_kropkami():
    assert get_threshold("scoring.flag_threshold", -1) == 50.0
    assert get_threshold("rules.rule_5.min_contrast", -1) == 4.5


def test_wartosc_domyslna_dla_brakujacego_klucza():
    assert get_threshold("nie.ma.takiego.klucza", 123) == 123
    assert get_threshold("scoring.nieistniejacy", "fallback") == "fallback"


def test_wartosc_domyslna_gdy_sciezka_wchodzi_w_liscia():
    # `scoring.flag_threshold` jest liczba, wiec dalsza kropka nie ma czego odczytac.
    assert get_threshold("scoring.flag_threshold.dalej", "fallback") == "fallback"


def test_get_threshold_domyslnie_none():
    assert get_threshold("nie.ma.takiego.klucza") is None


def test_domyslny_plik_jest_zgodny_z_fallbackiem():
    # Plik w repo musi dawac te same wartosci liczbowe co fallback w kodzie.
    # Plik moze miec dodatkowe pola opisowe (legal_basis), dlatego porownujemy
    # wartosci liscie po liscie, a nie cale slowniki.
    assert DEFAULT_THRESHOLDS_PATH.exists()
    def _lisc(node, prefix=""):
        if isinstance(node, dict):
            for key, val in node.items():
                yield from _lisc(val, f"{prefix}{key}.")
        else:
            yield prefix.rstrip("."), node

    for path, value in _lisc(DEFAULT_THRESHOLDS):
        assert get_threshold(path) == value, path


def test_progi_scoringu_zgodne_z_scoring_py():
    assert get_threshold("scoring.flag_threshold") == scoring.DEFAULT_FLAG_THRESHOLD
    assert get_threshold("scoring.high_threshold") == scoring.HIGH_THRESHOLD
    assert get_threshold("scoring.medium_threshold") == scoring.MEDIUM_THRESHOLD


def test_progi_deduplikacji_zgodne_z_embeddings_py():
    assert get_threshold("dedup.near_duplicate_cosine") == embeddings.NEAR_DUPLICATE_COSINE
    assert get_threshold("dedup.same_campaign_cosine") == embeddings.SAME_CAMPAIGN_COSINE
    assert get_threshold("dedup.simhash_max_distance") == embeddings.SIMHASH_MAX_DISTANCE

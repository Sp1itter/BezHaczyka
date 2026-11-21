"""Testy metryk kalibracji (tools/evaluate.py) — par. 9 design doca."""

import json
import random

import pytest

from analyzer.scoring import DEFAULT_FLAG_THRESHOLD
from tools import evaluate
from tools.evaluate import (
    DEFAULT_GOLD_PATH,
    best_threshold,
    build_report,
    confusion_matrix,
    load_gold,
    metrics,
    threshold_sweep,
)


class TestPustyZbior:
    def test_metryki_zerowe_bez_wyjatku(self):
        m = metrics([], [], 50.0)
        assert m["precision"] == 0.0
        assert m["recall"] == 0.0
        assert m["f1"] == 0.0
        assert m["accuracy"] == 0.0
        assert m["tp"] == m["fp"] == m["fn"] == m["tn"] == 0

    def test_najlepszy_prog_to_domyslny(self):
        assert best_threshold([], []) == DEFAULT_FLAG_THRESHOLD

    def test_raport_mowi_o_braku_wynikow(self):
        lines = build_report([])
        assert any("Zbior zloty: 0" in line for line in lines)


class TestWszystkoNaruszenia:
    def test_kazdy_material_zlapany(self):
        m = metrics([80.0, 90.0], [True, True], 50.0)
        assert m["tp"] == 2
        assert m["fp"] == m["fn"] == m["tn"] == 0
        assert m["precision"] == 1.0
        assert m["recall"] == 1.0
        assert m["accuracy"] == 1.0


class TestNicNieNaruszaNic:
    def test_wszystko_to_falszywe_alarmy(self):
        m = metrics([80.0, 90.0], [False, False], 50.0)
        assert m["fp"] == 2
        assert m["tn"] == 0
        assert m["precision"] == 0.0
        # brak pozytywow w zbiorze -> recall 0.0, nie wyjatek
        assert m["recall"] == 0.0
        assert m["f1"] == 0.0


class TestIdealnyKlasyfikator:
    def test_precision_i_recall_rowne_jeden(self):
        scores = [10.0, 20.0, 80.0, 90.0]
        labels = [False, False, True, True]
        m = metrics(scores, labels, 50.0)
        assert m["precision"] == 1.0
        assert m["recall"] == 1.0
        assert m["f1"] == 1.0
        assert m["accuracy"] == 1.0


class TestKlasyfikatorLosowy:
    def test_precision_bliski_udzialowi_naruszen(self):
        # wyniki i etykiety niezalezne -> precision ~ udzial naruszen (0.5)
        rng = random.Random(42)
        n = 5000
        scores = [rng.uniform(0.0, 100.0) for _ in range(n)]
        labels = [rng.random() < 0.5 for _ in range(n)]
        m = metrics(scores, labels, 50.0)
        assert m["precision"] == pytest.approx(0.5, abs=0.05)
        assert m["recall"] == pytest.approx(0.5, abs=0.05)


class TestDzieleniePrzezZero:
    def test_prog_zero_flaguje_wszystko(self):
        scores = [0.0, 50.0, 100.0]
        labels = [False, True, False]
        m = metrics(scores, labels, 0.0)
        assert m["tp"] == 1
        assert m["fp"] == 2
        assert m["fn"] == 0
        assert m["recall"] == 1.0
        assert m["precision"] == pytest.approx(1 / 3)

    def test_prog_100_bez_flag_nie_rzuca(self):
        # nic nie przekracza progu 100 -> tp+fp == 0 -> precision 0.0
        m = metrics([10.0, 20.0], [True, False], 100.0)
        assert m["precision"] == 0.0
        assert m["recall"] == 0.0
        assert m["f1"] == 0.0
        assert m["fn"] == 1
        assert m["tn"] == 1


class TestMacierzPomylek:
    def test_cztery_kwadranty(self):
        scores = [90.0, 90.0, 10.0, 10.0]
        labels = [True, False, True, False]
        assert confusion_matrix(scores, labels, 50.0) == {"tp": 1, "fp": 1, "fn": 1, "tn": 1}

    def test_rozna_dlugosc_list_to_blad_wywolujacego(self):
        with pytest.raises(ValueError):
            confusion_matrix([1.0, 2.0], [True], 50.0)


class TestPrzemiatanieProgow:
    def test_zwraca_21_punktow(self):
        rows = threshold_sweep([10.0, 90.0], [False, True])
        assert len(rows) == 21
        assert rows[0]["threshold"] == 0.0
        assert rows[-1]["threshold"] == 100.0

    def test_wszystkie_wiersze_maja_metryki(self):
        for row in threshold_sweep([10.0, 90.0], [False, True]):
            for key in ("tp", "fp", "fn", "tn", "precision", "recall", "f1", "accuracy"):
                assert key in row

    def test_niepoprawny_krok(self):
        with pytest.raises(ValueError):
            threshold_sweep([1.0], [True], step=0)


class TestBestThreshold:
    def test_znane_optimum(self):
        # negatyw przy 45, pozytyw przy 50 -> jedyny prog z siatki idealnie rozdzielajacy to 50
        assert best_threshold([45.0, 50.0], [False, True]) == 50.0

    def test_optimum_przy_perfekcyjnym_rozdzieleniu(self):
        scores = [10.0, 20.0, 40.0, 80.0]
        labels = [False, False, True, True]
        best = best_threshold(scores, labels)
        assert 20.0 < best <= 40.0
        assert metrics(scores, labels, best)["f1"] == 1.0

    def test_remis_wybiera_prog_blizszy_domyslnemu(self):
        # F1=1.0 dla progow 25..60 -> najblizszy 50
        assert best_threshold([10.0, 20.0, 60.0, 80.0], [False, False, True, True]) == 50.0


class TestLoadGold:
    def test_brakujacy_plik(self, tmp_path, capsys):
        items = load_gold(tmp_path / "nie-ma.json")
        assert items == []
        assert "OSTRZEZENIE" in capsys.readouterr().err

    def test_uszkodzony_json(self, tmp_path, capsys):
        path = tmp_path / "labels.json"
        path.write_text("{nie jest json", encoding="utf-8")
        assert load_gold(path) == []
        assert "OSTRZEZENIE" in capsys.readouterr().err

    def test_poprawna_pozycja_i_pominiete_zle(self, tmp_path, capsys):
        path = tmp_path / "labels.json"
        payload = {
            "version": 1,
            "items": [
                {
                    "id": "a",
                    "source": "x.html",
                    "is_violation": True,
                    "note": "n",
                    "rule_labels": {"4": "fail"},
                    "score": 77,
                },
                {"id": "b", "is_violation": "tak"},  # zly typ is_violation
                {"id": "c", "is_violation": False},  # bez score i rule_labels
            ],
        }
        path.write_text(json.dumps(payload), encoding="utf-8")
        items = load_gold(path)
        assert [i.id for i in items] == ["a", "c"]
        assert items[0].score == 77.0
        assert items[0].rule_labels == {"4": "fail"}
        assert items[1].score is None
        assert items[1].rule_labels == {}
        assert "pozycja #1" in capsys.readouterr().err

    def test_brak_listy_items(self, tmp_path, capsys):
        path = tmp_path / "labels.json"
        path.write_text(json.dumps({"version": 1}), encoding="utf-8")
        assert load_gold(path) == []
        assert "items" in capsys.readouterr().err

    def test_prawdziwy_zbior_w_repo_sie_laduje(self):
        assert DEFAULT_GOLD_PATH.exists()
        items = load_gold()
        assert len(items) >= 8
        assert len({i.id for i in items}) == len(items)


class TestRaport:
    def test_bez_score_raport_ostrzega(self):
        items = [evaluate.GoldItem(id="a", source="", is_violation=True)]
        lines = build_report(items)
        assert any("Brak pozycji z polem score" in line for line in lines)

    def test_z_score_raport_ma_tabele_i_rekomendacje(self):
        items = [
            evaluate.GoldItem(id="a", source="", is_violation=True, score=80.0),
            evaluate.GoldItem(id="b", source="", is_violation=False, score=10.0),
        ]
        text = "\n".join(build_report(items))
        assert "Przemiatanie progow" in text
        assert "Macierz pomylek dla progu domyslnego" in text
        assert "Rekomendowany prog (max F1)" in text

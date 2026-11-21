"""Testy narzedzia ewaluacji regul (bez Ollamy): metryki oraz walidacja zbioru."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import eval_rules as ev  # noqa: E402


def _row(rule, exp, got, pending=False):
    return ev.Row("c", rule, exp, got, "s", None, pending)


def test_metryki_macierz_pomylek():
    rows = [
        _row("3", "fail", "fail"),  # TP
        _row("3", "fail", "pass"),  # FN
        _row("3", "pass", "fail"),  # FP
        _row("3", "pass", "not_applicable"),  # TN, ale nie dokladne trafienie
        _row("3", "not_applicable", "not_applicable"),  # TN
    ]
    st = ev.compute_metrics(rows)["3"]
    assert (st.tp, st.fp, st.fn, st.tn) == (1, 1, 1, 2)
    assert st.n == 5
    assert st.accuracy == pytest.approx(2 / 5)
    assert len(st.mismatches) == 3


def test_pending_nie_wchodzi_do_macierzy():
    rows = [_row("4", "fail", "not_applicable", pending=True), _row("4", "pass", "pass")]
    st = ev.compute_metrics(rows)["4"]
    assert st.pending == 1 and st.n == 1 and st.accuracy == 1.0


def test_kolejnosc_regul_numeryczna():
    rows = [_row(r, "pass", "pass") for r in ("12b", "2", "12a", "10", "1")]
    assert list(ev.compute_metrics(rows)) == ["1", "2", "10", "12a", "12b"]


def test_tabela_zawiera_reguly():
    out = ev.format_table(ev.compute_metrics([_row("1", "fail", "fail")]))
    assert "regula" in out and "razem" in out


def test_wszystkie_przypadki_laduja_sie_i_sa_poprawne():
    cases = ev.load_cases()
    assert 24 <= len(cases) <= 40
    valid = ev.valid_rule_ids()
    for c in cases:
        assert c.expected, c.id
        assert set(c.expected) <= valid, c.id
        assert c.doc.source == "synthetic"
        assert c.doc.text.strip()


def test_pokrycie_regul_fail_i_pass_lub_na():
    cases = ev.load_cases()
    for rule in ("1", "2", "3", "9", "10", "11", "12a", "12b", "13", "14", "15", "16", "17", "18"):
        verdicts = {c.expected[rule] for c in cases if rule in c.expected}
        assert "fail" in verdicts, f"brak przypadku fail dla reguly {rule}"
        assert verdicts & {"pass", "not_applicable"}, f"brak przypadku pass/NA dla reguly {rule}"


def test_przypadki_nie_podszywaja_sie_pod_realne_firmy():
    for c in ev.load_cases():
        assert "example.invalid" in c.doc.url


def test_walidacja_odrzuca_nieznana_regule(tmp_path):
    import json

    good = json.loads(ev.DEFAULT_CASES_PATH.read_text(encoding="utf-8"))
    good["cases"][0]["expected"] = {"99": "fail"}
    p = tmp_path / "c.json"
    p.write_text(json.dumps(good), encoding="utf-8")
    with pytest.raises(ValueError):
        ev.load_cases(p)


def test_offline_uruchamia_potok_bez_modelu(tmp_path):
    out = tmp_path / "r.json"
    assert ev.main(["--offline", "--out", str(out)]) == 0
    assert out.exists()

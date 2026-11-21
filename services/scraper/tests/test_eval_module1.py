"""Porownanie wynikow resolvera z etykietami (tools/eval_module1.py) - bez bazy."""

from __future__ import annotations

from tools.eval_module1 import DEFAULT_CASES, compare_case, evaluate, firm_correct, load_cases


def _res(rel="official", disc=False, name="XTB S.A."):
    return {"publisher_relation": rel, "disclosure_found": disc, "registry_official_name": name}


def _lab(rel="official", disc=False, firm="XTB S.A."):
    return {"relation": rel, "disclosure": disc, "firm": firm}


def test_firm_correct_case_insensitive_and_null():
    assert firm_correct("XTB S.A.", "xtb s.a.") is True
    assert firm_correct("XTB S.A.", None) is False
    assert firm_correct(None, "XTB S.A.") is None


def test_compare_case_reports_each_field():
    errs = compare_case("c1", _lab("official", True), _res("third_party", False, "Inna"))
    assert {e["field"] for e in errs} == {"relation", "disclosure", "firm"}
    assert compare_case("c2", _lab(), _res()) == []


def test_evaluate_metrics():
    pairs = [
        ("a", _lab("official", True), _res("official", True)),      # tp
        ("b", _lab("third_party", True), _res("third_party", False, "Inna")),  # fn, firma zle
        ("c", _lab("unknown", False, None), _res("third_party", True)),  # fp, relation zle
        ("d", _lab("official", False), _res("official", False)),
    ]
    r = evaluate(pairs)
    assert r["n"] == 4
    assert r["relation_accuracy"] == 0.75
    assert r["disclosure_precision"] == 0.5 and r["disclosure_recall"] == 0.5
    assert r["firm_evaluated"] == 3 and r["firm_accuracy"] == round(2 / 3, 4)
    assert {(e["case_id"], e["field"]) for e in r["errors"]} == {
        ("b", "disclosure"), ("b", "firm"), ("c", "relation"), ("c", "disclosure")}


def test_evaluate_empty_and_no_positive_class():
    r = evaluate([("x", _lab("unknown", False, None), _res("unknown", False, None))])
    assert r["disclosure_precision"] is None and r["disclosure_recall"] is None
    assert r["firm_accuracy"] is None


def test_labels_file_is_well_formed():
    cases = load_cases(DEFAULT_CASES)
    assert len(cases) == 40
    assert sum(c["source"] == "facebook" for c in cases) >= 12
    assert sum(c["source"] == "youtube" for c in cases) >= 12
    for c in cases:
        assert c["labels"]["relation"] in {"official", "third_party", "unknown"}
        assert c["labels"]["note"]

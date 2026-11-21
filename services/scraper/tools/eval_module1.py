"""Ewaluacja Modulu 1: resolver vs etykiety z fixtures/module1-labels/cases.jsonl.

    python tools/eval_module1.py --db postgresql://... [--cases plik.jsonl] [--out wynik.json]

Metryki: accuracy `relation`, precision/recall `disclosure` (klasa true),
accuracy `firm` (tylko gdy etykieta `firm` != null) oraz lista pomylek.
Funkcje porownania sa czyste (bez bazy) - patrz tests/test_eval_module1.py.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

DEFAULT_CASES = Path(__file__).resolve().parents[3] / "fixtures" / "module1-labels" / "cases.jsonl"


def load_cases(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _norm(value: str | None) -> str:
    return (value or "").strip().casefold()


def firm_correct(label_firm: str | None, got_name: str | None) -> bool | None:
    """None gdy etykieta firmy jest pusta (nie oceniamy), inaczej zgodnosc nazw (bez wielkosci liter)."""
    if label_firm is None:
        return None
    return _norm(label_firm) == _norm(got_name)


def compare_case(case_id: str, labels: dict, result: dict) -> list[dict]:
    """Pomylki dla jednego przypadku: lista {case_id, field, expected, got}."""
    errors = []
    pairs = [
        ("relation", labels.get("relation"), result.get("publisher_relation")),
        ("disclosure", bool(labels.get("disclosure")), bool(result.get("disclosure_found"))),
    ]
    if firm_correct(labels.get("firm"), result.get("registry_official_name")) is False:
        pairs.append(("firm", labels.get("firm"), result.get("registry_official_name")))
    for field, expected, got in pairs:
        if expected != got:
            errors.append({"case_id": case_id, "field": field, "expected": expected, "got": got})
    return errors


def _ratio(num: int, den: int) -> float | None:
    return round(num / den, 4) if den else None


def evaluate(pairs: list[tuple[str, dict, dict]]) -> dict:
    """pairs: (case_id, labels, wynik resolvera) -> raport z metrykami i pomylkami."""
    rel_ok = tp = fp = fn = firm_ok = firm_n = 0
    errors: list[dict] = []
    for case_id, labels, result in pairs:
        errors += compare_case(case_id, labels, result)
        rel_ok += labels.get("relation") == result.get("publisher_relation")
        exp, got = bool(labels.get("disclosure")), bool(result.get("disclosure_found"))
        tp += exp and got
        fp += (not exp) and got
        fn += exp and (not got)
        ok = firm_correct(labels.get("firm"), result.get("registry_official_name"))
        if ok is not None:
            firm_n += 1
            firm_ok += ok
    return {
        "n": len(pairs),
        "relation_accuracy": _ratio(rel_ok, len(pairs)),
        "disclosure_precision": _ratio(tp, tp + fp),
        "disclosure_recall": _ratio(tp, tp + fn),
        "disclosure_counts": {"tp": tp, "fp": fp, "fn": fn},
        "firm_accuracy": _ratio(firm_ok, firm_n),
        "firm_evaluated": firm_n,
        "errors": errors,
    }


def run(cases: list[dict], conn) -> dict:
    from contracts import AdDocument
    from resolver import Registry, resolve

    registry = Registry.from_db(conn, force=True)
    pairs = [(c["case_id"], c["labels"], resolve(AdDocument.model_validate(c["doc"]), registry))
             for c in cases]
    return evaluate(pairs)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", default=os.environ.get("DATABASE_URL"), help="URL Postgresa (domyslnie DATABASE_URL)")
    ap.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    ap.add_argument("--out", type=Path, help="zapis raportu JSON")
    args = ap.parse_args(argv)
    if not args.db:
        ap.error("brak --db i DATABASE_URL")
    import psycopg
    import psycopg.rows

    with psycopg.connect(args.db, row_factory=psycopg.rows.dict_row) as conn:
        report = run(load_cases(args.cases), conn)
    text = json.dumps(report, ensure_ascii=False, indent=2)
    print(text)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

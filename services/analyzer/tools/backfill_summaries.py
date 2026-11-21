"""Uzupelnia podsumowania AI dla findingow, ktore ich jeszcze nie maja.

    python tools/backfill_summaries.py --db URL [--llm] [--limit N]

Bez --llm uzywa wylacznie szablonu. Uruchamiac z services/analyzer.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analyzer.contracts import AdDocument, Finding  # noqa: E402
from analyzer.db_store import _normalize_doc  # noqa: E402
from analyzer.summary import build_summary  # noqa: E402

log = logging.getLogger("backfill_summaries")

_FINDING_KEYS = (
    "id", "document_id", "primary_module", "modules", "routing", "risk_score",
    "risk_level", "rule_results", "entities", "knn_score", "status", "created_at",
)


def _finding_of(row: dict) -> Finding:
    raw = {k: row[k] for k in _FINDING_KEYS if k in row and row[k] is not None}
    raw["id"], raw["document_id"] = str(row["id"]), str(row["document_id"])
    return Finding.model_validate(raw)


def _doc_of(row: dict) -> AdDocument | None:
    snap = row.get("document_snapshot")
    if not snap:
        return None
    try:
        return AdDocument.model_validate(_normalize_doc(snap))
    except ValueError:  # ValidationError dziedziczy po ValueError
        return None


def backfill(conn, *, use_llm: bool, limit: int | None = None, client=None) -> dict:
    """Policz i zapisz podsumowania; zwraca liczniki {total, llm, template, errors}."""
    sql = "SELECT * FROM findings WHERE summary IS NULL ORDER BY created_at DESC"
    params: tuple = ()
    if limit:
        sql += " LIMIT %s"
        params = (limit,)
    rows = conn.execute(sql, params).fetchall()
    stats = {"total": len(rows), "llm": 0, "template": 0, "errors": 0}
    for row in rows:
        try:
            text, engine = build_summary(
                _finding_of(row), _doc_of(row), client=client, use_llm=use_llm
            )
            conn.execute(
                "UPDATE findings SET summary = %s, summary_engine = %s WHERE id = %s",
                (text, engine, row["id"]),
            )
            conn.commit()
            stats[engine] += 1
        except Exception as exc:  # jeden zly rekord nie zatrzymuje reszty
            conn.rollback()
            stats["errors"] += 1
            log.error("Finding %s pominiety: %s", row.get("id"), exc)
    return stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True, help="URL bazy Postgres (casedb)")
    parser.add_argument("--llm", action="store_true", help="uzyj Bielika (domyslnie sam szablon)")
    parser.add_argument("--limit", type=int, default=None, help="maksymalna liczba findingow")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO)

    from casedb import db

    with db.connect(args.db) as conn:
        stats = backfill(conn, use_llm=args.llm, limit=args.limit)
    print(
        f"Findingow: {stats['total']}, llm: {stats['llm']}, "
        f"szablon: {stats['template']}, bledy: {stats['errors']}"
    )
    return 1 if stats["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())

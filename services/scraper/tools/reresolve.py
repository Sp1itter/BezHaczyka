"""Ponowne rozwiazanie istniejacych przypadkow: cases.raw -> resolve() -> cases.entity_resolution.

    python tools/reresolve.py --db postgresql://... [--source youtube] [--dry-run]

Wypisuje podsumowanie zmian relacji i ujawnien (np. third_party -> official).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def summarize(changes: list[tuple[dict | None, dict]]) -> dict:
    """Podsumowanie par (stary wynik, nowy wynik)."""
    rel = Counter()
    disc = Counter()
    for old, new in changes:
        old = old or {}
        if old.get("publisher_relation") != new.get("publisher_relation"):
            rel[f"{old.get('publisher_relation')} -> {new.get('publisher_relation')}"] += 1
        o, n = bool(old.get("disclosure_found")), bool(new.get("disclosure_found"))
        if o != n:
            disc[f"{str(o).lower()} -> {str(n).lower()}"] += 1
    return {
        "cases": len(changes),
        "relation_changes": dict(rel),
        "disclosure_changes": dict(disc),
        "disclosure_found_after": sum(bool(n.get("disclosure_found")) for _, n in changes),
        "affiliate_without_disclosure_after": sum(bool(n.get("affiliate_without_disclosure")) for _, n in changes),
    }


def run(conn, *, source: str | None = None, dry_run: bool = False, registry=None) -> dict:
    from contracts import AdDocument
    from psycopg.types.json import Jsonb
    from resolver import Registry, resolve

    registry = registry or Registry.from_db(conn, force=True)
    sql = "SELECT case_id, raw, entity_resolution FROM cases WHERE raw IS NOT NULL"
    params: tuple = ()
    if source:
        sql += " AND source = %s"
        params = (source,)
    rows = conn.execute(sql + " ORDER BY case_id", params).fetchall()
    changes = []
    skipped = 0
    with conn.transaction():
        for r in rows:
            try:
                with conn.transaction():  # SAVEPOINT: blad jednego przypadku nie psuje reszty
                    new = resolve(AdDocument.model_validate(r["raw"]), registry)
                    if not dry_run:
                        merged = {**(r["entity_resolution"] or {}), **new}
                        conn.execute("UPDATE cases SET entity_resolution = %s WHERE case_id = %s",
                                     (Jsonb(merged), r["case_id"]))
            except Exception:  # noqa: BLE001 - zly przypadek jest liczony i pomijany
                skipped += 1
                continue
            changes.append((r["entity_resolution"], new))
    out = summarize(changes)
    out["skipped_invalid"] = skipped
    out["dry_run"] = dry_run
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", default=os.environ.get("DATABASE_URL"), help="URL Postgresa (domyslnie DATABASE_URL)")
    ap.add_argument("--source", help="tylko przypadki z tego zrodla (np. youtube)")
    ap.add_argument("--dry-run", action="store_true", help="policz i wypisz, bez zapisu")
    args = ap.parse_args(argv)
    if not args.db:
        ap.error("brak --db i DATABASE_URL")
    import psycopg
    import psycopg.rows

    with psycopg.connect(args.db, row_factory=psycopg.rows.dict_row) as conn:
        summary = run(conn, source=args.source, dry_run=args.dry_run)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

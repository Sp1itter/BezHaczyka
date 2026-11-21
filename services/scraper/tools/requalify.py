"""Jednorazowa ponowna kwalifikacja filmow YouTube odrzuconych tylko przez brak napisow.

    python tools/requalify.py [--dry-run] [--limit N]

Filmy `skipped` bez napisow (cases.raw.transcript = null) przechodza przez nowa regule
z sources/youtube.py: jezyk tytulu/opisu + wzmianka o firmie z rejestru KNF. Zakwalifikowane
dostaja status `new`, dowody (cases.extra.meta.requalified) i trafiaja do q:gpu jak swiezy
fetch. Potrzebne, bo record_document przy `unchanged` nie zmienia statusu, wiec sam recheck
by ich nie odzyskal. Idempotentne: drugi przebieg nie ma juz czego zmieniac.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def candidates(conn, limit: int | None) -> list[dict]:
    sql = ("SELECT case_id, raw, entity_resolution FROM cases"
           " WHERE source = 'youtube' AND status = 'skipped' AND gone_at IS NULL"
           " AND (raw->'transcript' IS NULL OR raw->'transcript' = 'null'::jsonb)"
           " ORDER BY last_seen_at DESC")
    if limit:
        sql += f" LIMIT {int(limit)}"
    return conn.execute(sql).fetchall()


def requalify(raw: dict, dictionary: list[dict], language: str = "pl") -> list[dict]:
    """Dowody (wzmianki o firmach) albo [] - ta sama regula co YouTubeSource bez napisow."""
    from sources.youtube import is_language, mentions

    title, text = raw.get("title") or "", raw.get("text") or ""
    body = text.removeprefix(title).lstrip("\n")  # text = tytul + opis + komentarze autora
    if not is_language(title + "\n" + body, language):
        return []
    return mentions(title, "title", dictionary) + mentions(body, "description", dictionary)


def run(conn, redis, *, dry_run: bool = False, limit: int | None = None, enqueue=None) -> dict:
    from contracts import AdDocument
    from psycopg.types.json import Jsonb as PgJsonb

    from jobs import _enqueue_analysis, _rows
    from resolver import Registry
    from sources.youtube import dictionary_from_registry

    registry = Registry.from_db(conn)
    dictionary = dictionary_from_registry([r for r in _rows(registry) if r.get("source", "curated") == "curated"])
    enqueue = enqueue or _enqueue_analysis
    rows = candidates(conn, limit)
    picked = []
    for row in rows:
        found = requalify(row["raw"], dictionary)
        if not found:
            continue
        picked.append(str(row["case_id"]))
        if dry_run:
            continue
        conn.execute(
            "UPDATE cases SET status = 'new', updated_at = now(),"
            " extra = jsonb_set(extra, '{meta}', COALESCE(extra->'meta', '{}'::jsonb) || %s)"
            " WHERE case_id = %s AND status = 'skipped'",
            (PgJsonb({"requalified": {"basis": found[0]["basis"], "evidence": found}}), row["case_id"]),
        )
        conn.commit()
        enqueue(redis, AdDocument.model_validate(row["raw"]), str(row["case_id"]), row["entity_resolution"] or {})
    return {"candidates": len(rows), "requalified": len(picked), "dry_run": dry_run, "case_ids": picked[:20]}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--limit", type=int)
    args = p.parse_args(argv)

    from casedb import db

    import jobs

    with db.connect() as conn:
        print(json.dumps(run(conn, jobs._redis(), dry_run=args.dry_run, limit=args.limit), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

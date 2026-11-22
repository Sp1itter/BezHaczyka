"""Usuwa duplikaty findingow: jeden finding na document_id.

Dla kazdego document_id z >1 findingiem:
  * zostaje NAJNOWSZA ANALIZA (najpozniejszy created_at),
  * pola pracy analityka (status, assignee, assigned_by, assigned_at, review_*)
    kopiujemy z wiersza, w ktorym analityk ostatnio cos zmienil
    (max z reviewed_at / assigned_at / ostatniego zdarzenia finding_events),
  * finding_events usuwanych wierszy przepinamy na wiersz zachowany
    (historia pracy nie ginie),
  * pozostale wiersze usuwamy.

Zasada: praca analityka wazniejsza niz brak duplikatow - gdy nie ma sladu pracy
(status 'new', brak przypisania, oceny i zdarzen), zostaje po prostu najnowszy wiersz.

DOMYSLNIE DRY-RUN (tylko liczby). `--apply` wykonuje zmiany w JEDNEJ transakcji.

Uzycie (z /app, DATABASE_URL w srodowisku):

    python tools/dedupe_findings.py
    python tools/dedupe_findings.py --apply
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# `python tools/<skrypt>.py` ma w sys.path tylko katalog tools/, a nie /app.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ANALYST_FIELDS = (
    "status", "assignee", "assigned_by", "assigned_at",
    "review_verdict", "review_label", "review_note", "reviewed_by", "reviewed_at",
)
_MIN = datetime.min.replace(tzinfo=timezone.utc)


def _aware(dt):
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def has_work(row: dict, last_event) -> bool:
    return bool(
        (row.get("status") or "new") != "new"
        or row.get("assignee")
        or row.get("review_verdict")
        or row.get("review_label")
        or row.get("review_note")
        or last_event
    )


def work_time(row: dict, last_event):
    stamps = [_aware(row.get("reviewed_at")), _aware(row.get("assigned_at")), _aware(last_event)]
    stamps = [s for s in stamps if s is not None]
    return max(stamps) if stamps else _MIN


def plan(rows: list[dict], last_events: dict) -> list[dict]:
    """Plan dla grup duplikatow (czysta funkcja, bez bazy).

    rows: findingi (id, document_id, created_at, pola analityka);
    last_events: {finding_id: czas ostatniego zdarzenia}.
    Zwraca liste {document_id, keep, copy_from, copy (dict pol lub None), delete[]}.
    """
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        groups[str(r["document_id"])].append(r)
    out = []
    for doc_id, grp in groups.items():
        if len(grp) < 2:
            continue
        grp = sorted(grp, key=lambda r: (_aware(r["created_at"]) or _MIN, str(r["id"])))
        keep = grp[-1]
        worked = [r for r in grp if has_work(r, last_events.get(str(r["id"])))]
        source = max(worked, key=lambda r: work_time(r, last_events.get(str(r["id"])))) if worked else None
        copy = None
        if source is not None and source is not keep:
            copy = {f: source.get(f) for f in ANALYST_FIELDS}
        out.append({
            "document_id": doc_id,
            "keep": str(keep["id"]),
            "copy_from": str(source["id"]) if source is not None else None,
            "copy": copy,
            "delete": [str(r["id"]) for r in grp if r is not keep],
        })
    return out


def load(conn) -> tuple[list[dict], dict]:
    rows = conn.execute(
        "SELECT id, document_id, status, created_at, assignee, assigned_by, assigned_at,"
        " review_verdict, review_label, review_note, reviewed_by, reviewed_at FROM findings"
        " WHERE document_id IN (SELECT document_id FROM findings GROUP BY document_id"
        " HAVING count(*) > 1)"
    ).fetchall()
    ev = conn.execute(
        "SELECT finding_id, max(at) AS last_at FROM finding_events GROUP BY finding_id"
    ).fetchall()
    return list(rows), {str(e["finding_id"]): e["last_at"] for e in ev}


def apply_plan(conn, actions: list[dict]) -> dict:
    moved = 0
    with conn.transaction():
        for a in actions:
            if a["copy"]:
                sets = ", ".join(f"{f} = %s" for f in ANALYST_FIELDS)
                conn.execute(
                    f"UPDATE findings SET {sets} WHERE id = %s",
                    [a["copy"][f] for f in ANALYST_FIELDS] + [a["keep"]],
                )
            if a["delete"]:
                cur = conn.execute(
                    "UPDATE finding_events SET finding_id = %s WHERE finding_id = ANY(%s::uuid[])",
                    (a["keep"], a["delete"]),
                )
                moved += cur.rowcount or 0
                conn.execute("DELETE FROM findings WHERE id = ANY(%s::uuid[])", (a["delete"],))
    return {"events_moved": moved}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--apply", action="store_true", help="wykonaj zmiany (domyslnie dry-run)")
    args = ap.parse_args(argv)

    from analyzer.casedb_bridge import connect

    with connect() as conn:
        total = conn.execute("SELECT count(*) AS n FROM findings").fetchone()["n"]
        rows, last_events = load(conn)
        actions = plan(rows, last_events)
        to_delete = sum(len(a["delete"]) for a in actions)
        copies = sum(1 for a in actions if a["copy"])
        print(f"Findingow: {total}; dokumentow z duplikatami: {len(actions)}; "
              f"wierszy do usuniecia: {to_delete}; z kopiowaniem pracy analityka: {copies}")
        if not args.apply:
            for a in actions[:10]:
                print(f"  {a['document_id']}: zostaje {a['keep']}, usun {len(a['delete'])}"
                      + (f", praca z {a['copy_from']}" if a["copy"] else ""))
            print("DRY-RUN: nic nie zmieniono. Dodaj --apply.")
            return 0
        res = apply_plan(conn, actions)
        after = conn.execute("SELECT count(*) AS n FROM findings").fetchone()["n"]
        print(f"Usunieto: {to_delete}; zdarzen przepietych: {res['events_moved']}; "
              f"findingow teraz: {after}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

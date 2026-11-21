"""CLI: python -m casedb <komenda>. Szczegoly: python -m casedb -h"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from casedb import db, export, ingest, store


def _load(path: str) -> list:
    data = json.loads(sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8"))
    return data if isinstance(data, list) else [data]


def _write(data, output: str | None) -> None:
    text = json.dumps(data, ensure_ascii=False, indent=2)
    if output:
        Path(output).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text + "\n")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="casedb", description="Wspolna baza przypadkow InvestWatch")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("migrate", help="utworz/aktualizuj schemat")

    pi = sub.add_parser("ingest", help="wczytaj wynik scrapera (plik JSON lub - dla stdin)")
    pi.add_argument("source", choices=["youtube", "facebook", "www"])
    pi.add_argument("files", nargs="+")

    pe = sub.add_parser("export", help="eksport przypadkow do JSON")
    pe.add_argument("--case-id", action="append", default=[])
    pe.add_argument("--status")
    pe.add_argument("--source", choices=["youtube", "facebook", "www"])
    pe.add_argument("--limit", type=int)
    pe.add_argument("--claim", metavar="WORKER",
                    help="zarezerwuj przypadki 'new' (status -> queued) i wyeksportuj")
    pe.add_argument("--raw", action="store_true", help="dolacz surowy wynik scrapera")
    pe.add_argument("-o", "--output")

    pc = sub.add_parser("add-column", help="dodaj kolumne, np. add-column cases risk_score 'double precision'")
    pc.add_argument("table", choices=store.TABLES)
    pc.add_argument("name")
    pc.add_argument("type")

    pa = sub.add_parser("ai-result", help="zapisz wynik modelu z pliku JSON")
    pa.add_argument("case_id")
    pa.add_argument("--task", required=True)
    pa.add_argument("--model", required=True)
    pa.add_argument("--version", default="")
    pa.add_argument("--endpoint")
    pa.add_argument("--label")
    pa.add_argument("--score", type=float)
    pa.add_argument("file")

    ps = sub.add_parser("status", help="ustaw status przypadku")
    ps.add_argument("case_id")
    ps.add_argument("status", choices=store.STATUSES)
    ps.add_argument("--error")

    args = p.parse_args(argv)
    with db.connect() as conn:
        if args.cmd == "migrate":
            applied = db.migrate(conn)
            print("zastosowano: " + (", ".join(applied) or "nic (schemat aktualny)"), file=sys.stderr)
        elif args.cmd == "ingest":
            ids = []
            for f in args.files:
                for item in _load(f):
                    case = (ingest.from_youtube(item) if args.source == "youtube"
                            else ingest.from_ad_document(item, args.source))
                    ids.append(store.save_case(conn, case))
            conn.commit()
            print(f"zapisano {len(ids)} przypadkow", file=sys.stderr)
            _write(ids, None)
        elif args.cmd == "export":
            if args.claim:
                ids = store.claim(conn, args.claim, args.limit or 10, source=args.source)
                conn.commit()
            elif args.case_id:
                ids = args.case_id
            else:
                ids = export.find_case_ids(conn, status=args.status, source=args.source,
                                           limit=args.limit)
            _write(export.export_cases(conn, ids, include_raw=args.raw), args.output)
        elif args.cmd == "add-column":
            store.add_column(conn, args.table, args.name, args.type)
            conn.commit()
        elif args.cmd == "ai-result":
            result = json.loads(Path(args.file).read_text(encoding="utf-8"))
            store.save_ai_result(conn, args.case_id, args.task, args.model, result,
                                 version=args.version, endpoint=args.endpoint,
                                 label=args.label, score=args.score)
            conn.commit()
        elif args.cmd == "status":
            store.set_status(conn, args.case_id, args.status, args.error)
            conn.commit()
    return 0

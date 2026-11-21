"""Zasila baze przykladami kontraktowymi, zeby dashboard mial co pokazac bez scrapera i Bielika.

    python -m api.seed                       # do bazy z DATABASE_URL (domyslnie SQLite dev)
    python -m api.seed --dir ../../fixtures/contract-examples

Wczytuje wszystkie *document*.json jako AdDocument i finding*.json jako Finding.
To sa prawdziwe obiekty kontraktowe z fixtures/, nie wymyslone dane demo.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from api.contracts import AdDocument, Finding
from api.store import open_store

_PARENTS = Path(__file__).resolve().parents
DEFAULT_DIR = (_PARENTS[3] if len(_PARENTS) > 3 else _PARENTS[-1]) / "fixtures" / "contract-examples"


def seed(store, directory: Path) -> tuple[int, int]:
    docs = findings = 0
    for p in sorted(directory.glob("*document*.json")):
        store.upsert_document(AdDocument.model_validate(json.loads(p.read_text(encoding="utf-8"))))
        docs += 1
    for p in sorted(directory.glob("finding*.json")):
        f = Finding.model_validate(json.loads(p.read_text(encoding="utf-8")))
        if store.document_exists(f.document_id):
            store.upsert_finding(f)
            findings += 1
        else:
            print(f"pomijam {p.name}: brak dokumentu {f.document_id}")
    return docs, findings


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dir", type=Path, default=DEFAULT_DIR)
    args = ap.parse_args()
    store = open_store(os.getenv("DATABASE_URL"))
    docs, findings = seed(store, args.dir)
    print(f"Zaladowano: {docs} dokumentow, {findings} findingow ({store.dialect})")


if __name__ == "__main__":
    main()

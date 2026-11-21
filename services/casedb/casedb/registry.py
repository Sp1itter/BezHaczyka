"""Wczytywanie rejestru podmiotow nadzorowanych KNF z CSV."""

from __future__ import annotations

import csv
from importlib import resources
from pathlib import Path

LIST_FIELDS = ("aliases", "domains", "handles")
FIELDS = ("knf_id", "name", "type", "country", "register", "aliases", "domains", "handles",
          "source_url")


def packaged_registry_path() -> Path:
    return Path(str(resources.files("casedb") / "data" / "knf_registry.csv"))


def _split(value: str | None) -> list[str]:
    return [p.strip() for p in (value or "").split(";") if p.strip()]


def read_registry_csv(path: str | Path) -> list[dict]:
    """Czyta CSV (UTF-8); pola aliases/domains/handles rozdzielone ';' -> listy."""
    rows = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            if not (r.get("knf_id") or "").strip() or not (r.get("name") or "").strip():
                continue
            row = {k: (r.get(k) or "").strip() or None for k in FIELDS}
            for k in LIST_FIELDS:
                row[k] = _split(r.get(k))
            rows.append(row)
    return rows

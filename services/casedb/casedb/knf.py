"""Snapshot rejestru KNF (firmy inwestycyjne i agenci) w tabeli knf_entities.

Definicje (Zalacznik do Tematu 1, wyzwanie KNF):
- firma inwestycyjna: dom maklerski, bank prowadzacy dzialalnosc maklerska, zagraniczna firma
  inwestycyjna prowadzaca dzialalnosc maklerska w RP, zagraniczna osoba prawna spoza UE
  prowadzaca dzialalnosc maklerska w RP;
- zagraniczna firma inwestycyjna: podmiot z innego panstwa UE/EOG prowadzacy dzialalnosc
  maklerska na podstawie zezwolenia tamtejszego nadzoru (takze zagraniczna instytucja kredytowa).
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

import psycopg
from psycopg.types.json import Jsonb

DEFAULT_SNAPSHOT = Path(__file__).resolve().parent / "data" / "knf_snapshot.jsonl"

# wykaz -> (kategoria, czy podmiot ma obecnie prawo dzialac)
REGISTERS = {
    "banki_maklerskie": ("firma_inwestycyjna", True),
    "domy_maklerskie": ("firma_inwestycyjna", True),
    "dm_ue_bez_oddzialu": ("firma_inwestycyjna", True),
    "dm_ue_oddzial": ("firma_inwestycyjna", True),
    "zfi_oddzialy": ("zagraniczna_firma_inwestycyjna", True),
    "zfi_bez_oddzialu": ("zagraniczna_firma_inwestycyjna", True),
    "agenci_osoby_fizyczne": ("agent", True),
    "agenci_osoby_prawne": ("agent", True),
    "cofniete_zezwolenia": ("firma_inwestycyjna", False),
    "dane_historyczne": ("firma_inwestycyjna", False),
}
_LEGAL_TAIL = re.compile(
    r"( (s a|sa|sp z o o|sp k|spolka akcyjna|spolka z ograniczona odpowiedzialnoscia|ag|se|plc|ltd"
    r"|limited|gmbh|n v|nv|b v|bv|inc|llc|ab|oy|as|a s|s r l|srl|s l|sl|s p a|spa|sas|kft|ad|d d|d o o))+$"
)


def name_key(name: str) -> str:
    """Klucz porownan: male litery, bez diakrytykow, interpunkcji i koncowych form prawnych."""
    text = unicodedata.normalize("NFKD", name.casefold().replace("ł", "l"))
    text = "".join(c for c in text if not unicodedata.combining(c))
    return _LEGAL_TAIL.sub("", re.sub(r"[^a-z0-9]+", " ", text).strip())


def read_snapshot(path: Path | str = DEFAULT_SNAPSHOT) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_snapshot(conn: psycopg.Connection, rows: list[dict]) -> int:
    """Zastepuje zawartosc knf_entities podanym snapshotem (jedna transakcja)."""
    unknown = {r["register"] for r in rows} - REGISTERS.keys()
    if unknown:
        raise ValueError(f"nieznane wykazy: {sorted(unknown)}")
    with conn.transaction():
        conn.execute("DELETE FROM knf_entities")
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO knf_entities (register, category, active, name, name_key, former_names,"
                " former_keys, fields, source_url, fetched_at)"
                " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                [
                    (r["register"], *REGISTERS[r["register"]], r["name"], name_key(r["name"]),
                     r.get("former_names", []), [name_key(n) for n in r.get("former_names", [])],
                     Jsonb(r.get("fields", {})), r["source_url"], r["fetched_at"])
                    for r in rows
                ],
            )
    return len(rows)


def lookup(conn: psycopg.Connection, name: str) -> list[dict]:
    """Wpisy KNF pasujace do nazwy (biezacej lub dawnej) po normalizacji."""
    key = name_key(name)
    if not key:
        return []
    return conn.execute(
        "SELECT register, category, active, name, former_names, fields, source_url, fetched_at"
        " FROM knf_entities WHERE name_key = %s OR %s = ANY(former_keys)"
        " ORDER BY active DESC, register, name",
        (key, key),
    ).fetchall()

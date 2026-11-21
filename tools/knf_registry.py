"""Aktualizacja rejestru KNF (services/casedb/casedb/data/knf_registry.csv) z oficjalnych wykazow.

Pobiera cztery wykazy z Zalacznika 1 (adresy w kolumnie `source_url` istniejacego CSV, strony
z paginacja `?page=N`), wyciaga nazwy podmiotow i DOPISUJE nowe do CSV. Istniejace wiersze
(w tym recznie dopisane aliasy, domeny i handle) pozostaja nietkniete; nowy podmiot dostaje
`knf_id` wygenerowany z nazwy (np. DM-NOWY-DOM-MAKLERSKI) i puste aliasy/domeny/handle
do recznego uzupelnienia.

    python tools/knf_registry.py --dry-run        # tylko pokaz, co zostaloby dopisane
    python tools/knf_registry.py                  # dopisz do pakietowego CSV
    python -m pytest services/scraper/tests/test_knf_registry.py   # test parsera

Parser jest odporny na ksztalt strony: bierze wiersze tabeli (pierwsza sensowna komorka to
nazwa), a gdy tabeli brak - linki w elementach listy. Szablon strony KNF moze sie zmienic,
dlatego wynik zawsze warto przejrzec (`--dry-run`) przed zapisem.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import time
import unicodedata
from html.parser import HTMLParser
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV = ROOT / "services" / "casedb" / "casedb" / "data" / "knf_registry.csv"
FIELDS = ["knf_id", "name", "type", "country", "register", "aliases", "domains", "handles", "source_url"]
ID_PREFIX = {
    "domy_maklerskie": "DM",
    "banki_maklerskie": "BM",
    "oddzialy_zagraniczne": "ZFI",
    "notyfikowane_bez_oddzialu": "ZFI",
}
TIMEOUT_S = 30.0
MAX_PAGES = 200
NAV_WORDS = {"nastepna", "poprzednia", "pierwsza", "ostatnia", "dalej", "wstecz", "next", "previous",
             "wiecej", "wyszukaj", "szukaj", "drukuj", "strona glowna", "mapa strony", "kontakt"}
LEGAL_TAIL = re.compile(r"( (s a|sa|sp z o o|spolka akcyjna|ag|se|plc|ltd|limited|gmbh|n v|nv|b v|bv|inc|llc|ab|oy))+$")


def fold(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.casefold().replace("ł", "l"))
    return "".join(c for c in text if not unicodedata.combining(c))


def name_key(name: str) -> str:
    """Klucz porownan nazw: bez diakrytykow, interpunkcji i koncowych form prawnych."""
    return LEGAL_TAIL.sub("", re.sub(r"[^a-z0-9]+", " ", fold(name)).strip())


class _Extractor(HTMLParser):
    """Wiersze tabel (teksty komorek) oraz linki z elementow listy."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[list[str]] = []
        self.links: list[str] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None
        self._is_th = False
        self._li = 0
        self._a: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag == "tr":
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell, self._is_th = [], tag == "th"
        elif tag == "li":
            self._li += 1
        elif tag == "a" and self._li:
            self._a = []

    def handle_endtag(self, tag: str) -> None:
        if tag in ("td", "th") and self._cell is not None and self._row is not None:
            if not self._is_th:
                self._row.append(" ".join("".join(self._cell).split()))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if any(self._row):
                self.rows.append(self._row)
            self._row = None
        elif tag == "li":
            self._li = max(0, self._li - 1)
        elif tag == "a" and self._a is not None:
            self.links.append(" ".join("".join(self._a).split()))
            self._a = None

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)
        if self._a is not None:
            self._a.append(data)


def _plausible(name: str) -> bool:
    key = fold(name).strip()
    return (len(name) >= 3 and re.search(r"[^\W\d_]", name) is not None and key not in NAV_WORDS
            and not re.fullmatch(r"[\d\s.,/-]+", name))


def parse_entities(html: str) -> list[str]:
    """Nazwy podmiotow ze strony wykazu: z tabeli (pierwsza sensowna komorka wiersza), a gdy jej brak - z linkow listy."""
    parser = _Extractor()
    parser.feed(html)
    names: list[str] = []
    for row in parser.rows:
        name = next((c for c in row if _plausible(c)), None)
        if name:
            names.append(name)
    if not names:
        names = [link for link in parser.links if _plausible(link)]
    return list(dict.fromkeys(names))


def fetch_register(client: httpx.Client, url: str, *, max_pages: int = MAX_PAGES, delay_s: float = 0.0) -> list[str]:
    """Nazwy ze wszystkich stron wykazu (`?page=N`), az strona nie wniesie nic nowego albo zwroci blad."""
    found: dict[str, None] = {}
    for page in range(1, max_pages + 1):
        response = client.get(url, params={"page": page})
        if response.status_code >= 400:
            break
        fresh = [n for n in parse_entities(response.text) if n not in found]
        if not fresh:
            break
        found.update(dict.fromkeys(fresh))
        if delay_s:
            time.sleep(delay_s)
    return list(found)


def make_id(prefix: str, name: str, taken: set[str]) -> str:
    """knf_id z nazwy: PREFIKS-SLUG (do 28 znakow), z licznikiem przy kolizji."""
    slug = re.sub(r"[^A-Z0-9]+", "-", name_key(name).upper()).strip("-")[:28].strip("-") or "PODMIOT"
    candidate, n = f"{prefix}-{slug}", 2
    while candidate in taken:
        candidate, n = f"{prefix}-{slug}-{n}", n + 1
    return candidate


def merge(rows: list[dict], fetched: dict[str, list[str]]) -> list[dict]:
    """Dopisuje podmioty, ktorych jeszcze nie ma (po nazwie lub aliasie); zwraca liste NOWYCH wierszy."""
    known = {name_key(v) for r in rows for v in [r["name"], *r["aliases"].split(";")] if v.strip()}
    template: dict[str, dict] = {}
    for r in rows:
        template.setdefault(r["source_url"], r)
    taken = {r["knf_id"] for r in rows}
    added: list[dict] = []
    for url, names in fetched.items():
        ref = template.get(url)
        if ref is None:
            continue
        prefix = ID_PREFIX.get(ref["register"], ref["knf_id"].split("-")[0])
        for name in names:
            key = name_key(name)
            if not key or key in known:
                continue
            known.add(key)
            knf_id = make_id(prefix, name, taken)
            taken.add(knf_id)
            added.append({**dict.fromkeys(FIELDS, ""), "knf_id": knf_id, "name": name, "type": ref["type"],
                          "country": ref["country"], "register": ref["register"], "source_url": url})
    return added


def read_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [{k: (r.get(k) or "") for k in FIELDS} for r in csv.DictReader(f)]


def write_csv(path: Path, rows: list[dict]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Uzupelnij rejestr KNF o nowe podmioty z wykazow Zalacznika 1")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--max-pages", type=int, default=MAX_PAGES)
    parser.add_argument("--delay", type=float, default=1.0, help="przerwa miedzy stronami (s)")
    parser.add_argument("--dry-run", action="store_true", help="nie zapisuj, tylko wypisz nowe podmioty")
    args = parser.parse_args(argv)

    rows = read_csv(args.csv)
    urls = list(dict.fromkeys(r["source_url"] for r in rows if r["source_url"]))
    fetched: dict[str, list[str]] = {}
    with httpx.Client(timeout=TIMEOUT_S, follow_redirects=True, headers={"User-Agent": "InvestWatch-registry/1.0"}) as client:
        for url in urls:
            try:
                fetched[url] = fetch_register(client, url, max_pages=args.max_pages, delay_s=args.delay)
            except httpx.HTTPError as exc:
                print(f"BLAD {url}: {exc}", file=sys.stderr)
                return 1
            print(f"{url}: {len(fetched[url])} podmiotow", file=sys.stderr)
    added = merge(rows, fetched)
    for r in added:
        print(f"+ {r['knf_id']}\t{r['name']}")
    if added and not args.dry_run:
        write_csv(args.csv, rows + added)
    print(f"{'do dopisania' if args.dry_run else 'dopisano'}: {len(added)}; razem: {len(rows) + (0 if args.dry_run else len(added))}",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

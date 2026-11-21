"""Snapshot wykazow KNF: firmy inwestycyjne i agenci firm inwestycyjnych.

Pobiera wszystkie podstrony (z paginacja `?page=N`) z
https://www.knf.gov.pl/podmioty/Podmioty_rynku_kapitalowego/Firmy_inwestycyjne_i_Agenci_firm_inwestycyjnych
i zapisuje JSONL: jeden wiersz = jeden podmiot z jednego wykazu. Tylko biblioteka standardowa.

    python tools/knf_snapshot.py                       # -> services/casedb/casedb/data/knf_snapshot.jsonl
    python tools/knf_snapshot.py --raw-dir snap/html   # dodatkowo surowe HTML stron
    python -m casedb load-knf                          # zaladuj snapshot do Postgresa (knf_entities)

Pola wiersza: register, name, name_label, former_names, fields (wszystkie pary etykieta ->
wartosc z karty podmiotu; tekst przekreslony na stronie ma prefiks "[skreślone] "),
source_url, page, fetched_at.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "services" / "casedb" / "casedb" / "data" / "knf_snapshot.jsonl"
BASE = "https://www.knf.gov.pl/podmioty/Podmioty_rynku_kapitalowego/Firmy_inwestycyjne_i_Agenci_firm_inwestycyjnych"
# podstrona KNF -> nazwa wykazu w snapshocie
REGISTERS = {
    "Banki_prowadzace_dzialalnosc_maklerska": "banki_maklerskie",
    "domy_maklerskie": "domy_maklerskie",
    "notyfikowane_firmy_inwestycyjne_oddzialy": "zfi_oddzialy",
    "notyfikowane_zagraniczne_firmy_inwestycyjne": "zfi_bez_oddzialu",
    "notyfikacje_domow_maklerskich_bez_otwierania_oddzialow": "dm_ue_bez_oddzialu",
    "notyfikacje_domow_maklerskich_przez_oddzial": "dm_ue_oddzial",
    "agenci_firm_inwestycyjnych_osoby_fizyczne": "agenci_osoby_fizyczne",
    "agenci_firm_inwestycyjnych_osoby_prawne": "agenci_osoby_prawne",
    "rejestr_firm_inwestycyjnych_ktorym_cofnieto_zezwolenie_na_dzialalnosc_maklerska": "cofniete_zezwolenia",
    "firmy_inwestycyjne_dane_historyczne": "dane_historyczne",
}
MAX_PAGES = 200
UA = "INWESTWATCH-snapshot/1.0"
STRIKE_TAGS = ("strike", "s", "del")


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


class CardParser(HTMLParser):
    """Karty podmiotow: <table> z wierszami <th>etykieta</th><td>wartosc</td>.

    Wartosc to lista linii (<br>, <li>); tekst w <strike> zbierany osobno (dawne dane).
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.cards: list[list[tuple[str, list[str], list[str]]]] = []
        self._card: list | None = None
        self._th: list[str] | None = None
        self._label = ""
        self._td = False
        self._lines: list[str] = []
        self._struck: list[str] = []
        self._buf: list[str] = []
        self._strike = 0

    def _flush(self) -> None:
        text = clean("".join(self._buf))
        if text:
            (self._struck if self._strike else self._lines).append(text)
        self._buf = []

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._card = []
        elif tag == "th" and self._card is not None:
            self._th = []
        elif tag == "td" and self._card is not None:
            self._td, self._lines, self._struck, self._buf = True, [], [], []
        elif self._td and tag in ("br", "li", "p", "div"):
            self._flush()
        elif self._td and tag in STRIKE_TAGS:
            self._flush()
            self._strike += 1

    def handle_endtag(self, tag):
        if tag == "th" and self._th is not None:
            self._label = clean("".join(self._th))
            self._th = None
        elif self._td and tag in STRIKE_TAGS:
            self._flush()
            self._strike = max(0, self._strike - 1)
        elif self._td and tag in ("li", "p", "div"):
            self._flush()
        elif tag == "td" and self._td:
            self._flush()
            self._card.append((self._label, self._lines, self._struck))
            self._td = False
        elif tag == "table" and self._card is not None:
            if self._card:
                self.cards.append(self._card)
            self._card = None

    def handle_data(self, data):
        if self._th is not None:
            self._th.append(data)
        elif self._td:
            self._buf.append(data)


def parse_cards(html: str) -> list[dict]:
    """Pierwszy wiersz karty to nazwa podmiotu; kolejne linie/przekreslenia nazwy = dawne nazwy."""
    p = CardParser()
    p.feed(html)
    out = []
    for card in p.cards:
        fields: dict[str, str] = {}
        name, former, name_label = None, [], ""
        for label, lines, struck in card:
            if not label:
                continue
            if name is None:
                name = lines[0] if lines else (struck[0] if struck else "")
                former, name_label = lines[1:] + struck, label
                continue
            fields[label] = "\n".join(lines + [f"[skreślone] {s}" for s in struck])
        if name:
            out.append({"name": name, "name_label": name_label, "former_names": former, "fields": fields})
    return out


def parse_revoked(html: str) -> list[dict]:
    """Strona 'cofnieto zezwolenie' to proza: <strong>1. NAZWA</strong> + akapit z opisem."""
    out = []
    pattern = r"<strong>\s*\d+\.\s*(.*?)</strong>(.*?)(?=<strong>\s*\d+\.|</div>)"
    for m in re.finditer(pattern, html, re.S):
        body = m.group(2)
        fields = {"Opis": clean(re.sub(r"<[^>]+>", " ", body))}
        links = sorted(set(re.findall(r'href="([^"]*komunikat[^"]*)"', body)))
        if links:
            fields["Link do komunikatu"] = "\n".join(link.replace("&amp;", "&") for link in links)
        name = clean(re.sub(r"<[^>]+>", "", m.group(1)))
        out.append({"name": name, "name_label": "Nazwa", "former_names": [], "fields": fields})
    return out


def last_page(html: str) -> int:
    return max((int(n) for n in re.findall(r"[?&]page=(\d+)", html)), default=1)


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8")
        except (urllib.error.URLError, TimeoutError):
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError("unreachable")


def snapshot(raw_dir: Path | None = None, delay: float = 0.3) -> list[dict]:
    fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rows: list[dict] = []
    for slug, register in REGISTERS.items():
        url = f"{BASE}/{slug}"
        html = fetch(url)
        pages = min(last_page(html), MAX_PAGES)
        seen: set[str] = set()
        for page in range(1, pages + 1):
            page_url = url if page == 1 else f"{url}?page={page}"
            if page > 1:
                time.sleep(delay)
                html = fetch(page_url)
            if raw_dir:
                raw_dir.mkdir(parents=True, exist_ok=True)
                (raw_dir / f"{register}_{page:03d}.html").write_text(html, encoding="utf-8")
            items = parse_revoked(html) if register == "cofniete_zezwolenia" else parse_cards(html)
            for it in items:
                key = json.dumps(it, sort_keys=True, ensure_ascii=False)
                if key not in seen:
                    seen.add(key)
                    rows.append({"register": register, **it, "source_url": page_url,
                                 "page": page, "fetched_at": fetched_at})
        print(f"{register}: {len(seen)} wpisow, {pages} stron", file=sys.stderr)
    return rows


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--raw-dir", type=Path, help="zapisz tez surowe HTML stron")
    ap.add_argument("--delay", type=float, default=0.3, help="przerwa miedzy stronami [s]")
    args = ap.parse_args(argv)
    rows = snapshot(args.raw_dir, args.delay)
    if not rows:
        print("Pusty snapshot - zmienil sie szablon strony KNF?", file=sys.stderr)
        return 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Zapisano {len(rows)} wierszy -> {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

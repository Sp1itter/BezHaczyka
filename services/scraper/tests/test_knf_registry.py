"""Test tools/knf_registry.py na recznie napisanym HTML-u (siec do knf.gov.pl nie jest potrzebna)."""

from __future__ import annotations

import importlib.util

import httpx
import pytest

from tests.conftest import REPO_ROOT

spec = importlib.util.spec_from_file_location("knf_registry", REPO_ROOT / "tools" / "knf_registry.py")
knf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(knf)

URL = "https://lista.example/domy_maklerskie"
TABLE_P1 = """<html><body><nav><a href="/">Strona glowna</a></nav>
<table><tr><th>Lp.</th><th>Nazwa</th></tr>
<tr><td>1.</td><td> XTB  S.A. </td><td>Warszawa</td></tr>
<tr><td>2.</td><td>Nowy Dom Maklerski S.A.</td><td>Krakow</td></tr>
<tr><td>3</td><td>Zażółć Securities Sp. z o.o.</td></tr></table>
<a href="?page=2">Następna</a></body></html>"""
TABLE_P2 = "<table><tr><td>4.</td><td>Trzeci Broker S.A.</td></tr><tr><td>1.</td><td>XTB S.A.</td></tr></table>"
LIST_HTML = """<main><ul><li><a href="/a">Alfa Brokers S.A.</a></li><li><a href="#">Dalej</a></li>
<li><a href="/b">Beta Securities</a></li><li><a href="/1">12</a></li></ul></main>"""

ROWS = [
    {"knf_id": "DM-XTB", "name": "XTB S.A.", "type": "dom maklerski", "country": "PL", "register": "domy_maklerskie",
     "aliases": "XTB;X-Trade Brokers", "domains": "xtb.com", "handles": "", "source_url": URL},
    {"knf_id": "DM-ZZ", "name": "Zolty Dom", "type": "dom maklerski", "country": "PL", "register": "domy_maklerskie",
     "aliases": "Zazolc Securities", "domains": "", "handles": "", "source_url": URL},
]


def test_parse_table_skips_header_numbers_and_nav():
    assert knf.parse_entities(TABLE_P1) == ["XTB S.A.", "Nowy Dom Maklerski S.A.", "Zażółć Securities Sp. z o.o."]


def test_parse_list_fallback_filters_noise():
    assert knf.parse_entities(LIST_HTML) == ["Alfa Brokers S.A.", "Beta Securities"]


def test_parse_empty():
    assert knf.parse_entities("<html><body>brak</body></html>") == []


def test_fetch_register_paginates_until_nothing_new():
    pages = {"1": TABLE_P1, "2": TABLE_P2, "3": TABLE_P2}
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        page = request.url.params["page"]
        calls.append(page)
        return httpx.Response(200, text=pages[page])

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        names = knf.fetch_register(client, URL)
    assert names == ["XTB S.A.", "Nowy Dom Maklerski S.A.", "Zażółć Securities Sp. z o.o.", "Trzeci Broker S.A."]
    assert calls == ["1", "2", "3"]


def test_fetch_register_stops_on_http_error():
    with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(404))) as client:
        assert knf.fetch_register(client, URL) == []


def test_merge_adds_only_new_and_keeps_existing():
    names = knf.parse_entities(TABLE_P1) + ["Nowy Dom Maklerski S.A."]
    added = knf.merge(ROWS, {URL: names})
    # XTB (nazwa) i Zażółć Securities (alias bez form prawnych i diakrytykow) juz sa
    assert [r["name"] for r in added] == ["Nowy Dom Maklerski S.A."]
    new = added[0]
    assert new["knf_id"] == "DM-NOWY-DOM-MAKLERSKI" and new["register"] == "domy_maklerskie"
    assert new["type"] == "dom maklerski" and new["aliases"] == new["domains"] == new["handles"] == ""
    assert knf.merge(ROWS + added, {URL: names}) == []  # idempotentne


def test_make_id_collisions_and_prefix():
    taken = {"ZFI-ACME"}
    assert knf.make_id("ZFI", "Acme Ltd", taken) == "ZFI-ACME-2"
    assert knf.make_id("BM", "", set()) == "BM-PODMIOT"


def test_csv_roundtrip_preserves_manual_columns(tmp_path):
    path = tmp_path / "r.csv"
    knf.write_csv(path, ROWS)
    rows = knf.read_csv(path)
    assert rows == ROWS


@pytest.mark.skipif(not knf.DEFAULT_CSV.exists(), reason="brak pakietowego CSV")
def test_real_csv_has_four_sources():
    urls = {r["source_url"] for r in knf.read_csv(knf.DEFAULT_CSV)}
    assert len(urls) == 4

import importlib.util
from pathlib import Path

from casedb import knf

REPO = Path(__file__).resolve().parents[3]
_spec = importlib.util.spec_from_file_location("knf_snapshot", REPO / "tools" / "knf_snapshot.py")
snap = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(snap)

CARDS = """
<div id="entityTable">
<table><tbody>
<tr><th>Nazwa</th><td><span>CERES DOM INWESTYCYJNY S.A.<br /><strike>EFIX DOM MAKLERSKI S.A.</strike></span></td></tr>
<tr><th>Dane Teleadresowe</th><td><ul><li><span>Plac Bankowy 1</span></li><li><span>00-139 Warszawa</span></li></ul></td></tr>
<tr><th>Zakres działalności</th><td><span>1, 4, 5</span></td></tr>
</tbody></table>
<table><tbody>
<tr><th>Nazwa podmiotu</th><td><span>3D Global Financial Services Ltd</span></td></tr>
<tr><th>Adres siedziby</th><td><span>4102 Limassol<br /><strike>P.O.BOX 53720</strike></span></td></tr>
</tbody></table>
</div>
<a href="?page=2">2</a><a href="?page=7">7</a>
"""
REVOKED = """<div><p><strong>1. ATHENA INVESTMENTS Dom Maklerski SA</strong></p>
<p><a href="https://www.knf.gov.pl/komunikacja/komunikaty?articleId=82764&amp;p_id=18">komunikat</a></p>
<p><strong>2. VENTUS ASSET MANAGEMENT S.A.</strong></p><p>cofnela zezwolenie</p></div>"""


def test_parse_cards():
    a, b = snap.parse_cards(CARDS)
    assert a["name"] == "CERES DOM INWESTYCYJNY S.A."
    assert a["former_names"] == ["EFIX DOM MAKLERSKI S.A."]
    assert a["fields"]["Dane Teleadresowe"] == "Plac Bankowy 1\n00-139 Warszawa"
    assert b["name_label"] == "Nazwa podmiotu"
    assert b["fields"]["Adres siedziby"] == "4102 Limassol\n[skreślone] P.O.BOX 53720"
    assert snap.last_page(CARDS) == 7


def test_parse_revoked():
    a, b = snap.parse_revoked(REVOKED)
    assert a["name"] == "ATHENA INVESTMENTS Dom Maklerski SA"
    assert "articleId=82764&p_id=18" in a["fields"]["Link do komunikatu"]
    assert b["name"] == "VENTUS ASSET MANAGEMENT S.A."


def test_name_key():
    assert knf.name_key("XTB S.A.") == knf.name_key("xtb sa") == "xtb"
    assert knf.name_key("Dom Maklerski Banku Ochrony Środowiska S.A.") == "dom maklerski banku ochrony srodowiska"


def test_snapshot_file_is_loadable():
    rows = knf.read_snapshot()
    assert len(rows) > 500
    assert {r["register"] for r in rows} == set(knf.REGISTERS)


def test_load_and_lookup(conn):
    rows = [
        {"register": "domy_maklerskie", "name": "CERES DOM INWESTYCYJNY S.A.",
         "former_names": ["EFIX DOM MAKLERSKI S.A."], "fields": {"Zakres działalności": "1, 4"},
         "source_url": "https://www.knf.gov.pl/x", "fetched_at": "2026-11-21T19:00:00+00:00"},
        {"register": "cofniete_zezwolenia", "name": "VENTUS ASSET MANAGEMENT S.A.", "fields": {},
         "source_url": "https://www.knf.gov.pl/y", "fetched_at": "2026-11-21T19:00:00+00:00"},
    ]
    assert knf.load_snapshot(conn, rows) == 2
    assert knf.load_snapshot(conn, rows) == 2  # ponowne ladowanie zastepuje, nie dubluje
    hit = knf.lookup(conn, "Efix Dom Maklerski SA")
    assert [h["name"] for h in hit] == ["CERES DOM INWESTYCYJNY S.A."]
    assert hit[0]["active"] and hit[0]["category"] == "firma_inwestycyjna"
    assert knf.lookup(conn, "Ventus Asset Management")[0]["active"] is False
    assert knf.lookup(conn, "Nieznany Broker Ltd") == []


# ---- synchronizacja snapshotu do authorized_entities -------------------------
def _snap(register, name, fields=None, former=None):
    return {"register": register, "name": name, "former_names": former or [], "fields": fields or {},
            "source_url": "https://knf.test/x", "fetched_at": "2026-11-21T10:00:00+00:00"}


def test_sync_registry_from_knf(conn):
    from casedb import store

    store.load_registry(conn, [{"knf_id": "DM-XTB", "name": "XTB S.A.", "aliases": [], "domains": ["xtb.com"],
                                "handles": []}])
    knf.load_snapshot(conn, [
        _snap("domy_maklerskie", "XTB Spółka Akcyjna"),  # pokrywa sie z curated
        _snap("zfi_bez_oddzialu", "Foreign Broker Ltd", {"Państwo macierzyste": "Cypr"}, ["Old Broker Ltd"]),
        _snap("dm_ue_oddzial", "Branch Invest AG",
              {"Nazwa kraju, w którym działalność domu maklerskiego została notyfikowana": "Niemcy"}),
        _snap("domy_maklerskie", "Polski Dom Maklerski S.A."),
        _snap("cofniete_zezwolenia", "Upadly Dom SA"),
        _snap("agenci_osoby_fizyczne", "Jan Kowalski"),
    ])
    n = store.sync_registry_from_knf(conn)
    assert n == 4
    assert store.sync_registry_from_knf(conn) == 4  # idempotentne
    by = {e["name"]: e for e in store.registry_entries(conn)}
    assert len(by) == 5 and "Jan Kowalski" not in by
    xtb = by["XTB S.A."]
    assert xtb["source"] == "curated" and xtb["domains"] == ["xtb.com"] and xtb["active"]
    fb = by["Foreign Broker Ltd"]
    assert (fb["source"], fb["country"], fb["aliases"], fb["active"]) == ("knf", "Cypr", ["Old Broker Ltd"], True)
    assert fb["knf_id"].startswith("KNF-zfi_bez_oddzialu-") and len(fb["knf_id"]) == len("KNF-zfi_bez_oddzialu-") + 10
    assert by["Branch Invest AG"]["country"] == "Niemcy"
    assert by["Polski Dom Maklerski S.A."]["country"] == "PL"
    assert by["Upadly Dom SA"]["active"] is False
    assert store.knf_agent_keys(conn) == {"jan kowalski"}

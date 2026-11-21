# compliance:allow-file - testowe adresy w danych wejsciowych (ruch sieciowy zamockowany)
"""Testy resolvera podmiotow (bez bazy: rejestr z listy wierszy)."""

from __future__ import annotations

import pytest
from contracts import AdDocument, Publisher, Transcript
from resolver import Registry, has_disclosure, resolve, with_official_flag

ROWS = [
    {"knf_id": "DM-XTB", "name": "XTB S.A.", "aliases": ["X-Trade Brokers", "XT"], "domains": ["xtb.com", "xtb.pl"],
     "handles": ["@xtb_official"]},
    {"knf_id": "DM-NOBLE", "name": "Noble Securities S.A.", "aliases": [], "domains": ["noblesecurities.pl"], "handles": []},
    {"knf_id": "DM-BOS", "name": "Dom Maklerski Banku Ochrony Środowiska S.A.", "aliases": ["DM BOŚ"], "domains": ["bossa.pl"],
     "handles": []},
]


@pytest.fixture(scope="module")
def reg() -> Registry:
    return Registry.from_rows(ROWS)


def doc(text: str, **pub) -> AdDocument:
    return AdDocument(id="1", source="www", url="https://blog.example/a", fetched_at="2026-11-21T10:00:00Z",
                      publisher=Publisher(**pub), text=text)


def test_name_mention_third_party(reg):
    r = resolve(doc("Zaloz konto w XTB i zarabiaj.", handle="blog.example", display_name="Blog"), reg)
    assert (r["publisher_relation"], r["registry_knf_id"], r["firm_name_in_ad"]) == ("third_party", "DM-XTB", "XTB")
    assert r["mentions_authorized_firm"] and r["firm_is_authorized"] and not r["publisher_is_authorized"]
    assert r["registry_official_name"] == "XTB S.A." and 0 < r["registry_score"] <= 1


def test_no_substring_and_no_short_alias(reg):
    r = resolve(doc("Mamy xtbx i prace xt oraz textbook."), reg)
    assert r["publisher_relation"] == "unknown" and r["registry_knf_id"] is None and r["registry_score"] == 0.0


def test_diacritics_and_case_insensitive(reg):
    r = resolve(doc("polecam dm boś, swietna oferta"), reg)
    assert r["registry_knf_id"] == "DM-BOS"


def test_domain_beats_name(reg):
    r = resolve(doc("Noble Securities jest ok, ale link: https://www.xtb.com/pl?ref=abc."), reg)
    assert r["registry_knf_id"] == "DM-XTB" and r["registry_score"] == 1.0
    assert r["affiliate_link"] == "https://www.xtb.com/pl?ref=abc"


def test_fuzzy_match(reg):
    r = resolve(doc("Oferta Noble Securites dla Ciebie"), reg)
    assert r["registry_knf_id"] == "DM-NOBLE" and 0.9 <= r["registry_score"] < 1


def test_official_by_domain_handle_and_name(reg):
    text = "XTB: nowa oferta"
    assert resolve(doc(text, profile_url="https://xtb.com", handle="xtb.com"), reg)["publisher_relation"] == "official"
    assert resolve(doc(text, handle="@XTB_Official"), reg)["publisher_relation"] == "official"
    r = resolve(doc(text, display_name="XTB"), reg)
    assert r["publisher_relation"] == "official" and r["publisher_is_authorized"]


def test_publisher_authorized_but_other_firm(reg):
    r = resolve(doc("Polecam XTB", display_name="Noble Securities"), reg)
    assert r["publisher_relation"] == "third_party" and r["publisher_is_authorized"]


def test_unknown_without_mention(reg):
    r = resolve(doc("Czym jest ETF? Poradnik."), reg)
    assert r["publisher_relation"] == "unknown" and not r["mentions_authorized_firm"]
    assert r["affiliate_link"] is None


def test_transcript_is_searched(reg):
    d = doc("Nowy odcinek", display_name="Kanal")
    d.transcript = Transcript(engine="yt", lang="pl", text="dzis o rachunku w XTB", segments=[])
    assert resolve(d, reg)["registry_knf_id"] == "DM-XTB"


@pytest.mark.parametrize("text,expected", [
    ("to jest #reklama", True), ("#Współpraca z marką", True), ("#ad", True), ("Materiał sponsorowany", True),
    ("wspolpraca reklamowa", True), ("partnerem odcinka jest X", True), ("lokowanie produktu", True),
    ("nagroda: head", False), ("#adventure", False), ("zwykly tekst", False),
])
def test_disclosure(text, expected):
    assert has_disclosure(text) is expected


def test_affiliate_variants(reg):
    for link in ("https://xtb.com/go?utm_campaign=x", "https://xtb.pl/ref/jan", "https://xtb.com/?coupon=A1"):
        assert resolve(doc(f"XTB tutaj {link} reszta"), reg)["affiliate_link"] == link
    assert resolve(doc("XTB https://xtb.com/oferta i https://inna.pl/?ref=1"), reg)["affiliate_link"] is None


def test_official_flag_copy(reg):
    d = doc("XTB", display_name="XTB")
    out = with_official_flag(d, resolve(d, reg))
    assert out.publisher.is_official_firm_channel and not d.publisher.is_official_firm_channel


def test_registry_cache(monkeypatch):
    from casedb import store
    calls = []
    monkeypatch.setattr(store, "registry_entries", lambda conn: calls.append(1) or ROWS)
    monkeypatch.setattr(store, "knf_agent_keys", lambda conn: set())
    Registry.clear_cache()
    a, b = Registry.from_db(object()), Registry.from_db(object())
    assert a is b and len(calls) == 1
    Registry.from_db(object(), force=True)
    assert len(calls) == 2
    Registry.clear_cache()


def test_official_channel_without_name_in_text_is_official():
    from datetime import UTC, datetime

    from contracts import AdDocument, Publisher
    from resolver import Registry, resolve

    reg = Registry.from_rows([{"knf_id": "DM-XTB", "name": "XTB S.A.", "aliases": ["XTB"],
                               "domains": ["xtb.com"], "handles": []}])
    doc = AdDocument(id="1", source="www", url="https://www.xtb.com/pl/blog/a",
                     fetched_at=datetime.now(UTC), text="Rynek akcji w tym tygodniu.",
                     publisher=Publisher(handle="www.xtb.com", display_name="Blog",
                                         profile_url="https://www.xtb.com"))
    r = resolve(doc, reg)
    assert r["publisher_relation"] == "official"
    assert r["publisher_is_authorized"] and r["registry_knf_id"] == "DM-XTB"
    assert r["firm_name_in_ad"] is None


# ---- pelny rejestr KNF: wpisy source='knf' -----------------------------------
KNF_ROWS = [
    {"knf_id": "KNF-zfi_bez_oddzialu-aaaaaaaaaa", "name": "Zagraniczny Broker Capital Markets", "aliases": [],
     "domains": [], "handles": [], "source": "knf", "active": True},
    {"knf_id": "KNF-cofniete_zezwolenia-bbbbbbbbbb", "name": "Upadly Dom Inwestycyjny", "aliases": [],
     "domains": [], "handles": [], "source": "knf", "active": False},
    {"knf_id": "KNF-zfi_oddzialy-cccccccccc", "name": "Ab Xy", "aliases": [], "domains": [], "handles": [],
     "source": "knf", "active": True},
    {"knf_id": "KNF-zfi_oddzialy-dddddddddd", "name": "Zeta", "aliases": [], "domains": [], "handles": [],
     "source": "knf", "active": True},
]


def test_knf_exact_only_no_fuzzy():
    reg = Registry.from_rows(KNF_ROWS)
    exact = resolve(doc("Polecam Zagraniczny Broker Capital Markets dla kazdego."), reg)
    assert exact["registry_knf_id"] == "KNF-zfi_bez_oddzialu-aaaaaaaaaa" and exact["firm_is_authorized"]
    typo = resolve(doc("Polecam Zagraniczny Broker Capitall Markets dla kazdego."), reg)
    assert typo["registry_knf_id"] is None


def test_knf_short_name_skipped():
    reg = Registry.from_rows(KNF_ROWS)
    assert {f.name for f in reg.firms} == {"Zagraniczny Broker Capital Markets", "Upadly Dom Inwestycyjny", "Ab Xy"}
    r = resolve(doc("Zeta to grecka litera."), reg)
    assert r["registry_knf_id"] is None


def test_inactive_firm_is_not_authorized():
    reg = Registry.from_rows(KNF_ROWS)
    r = resolve(doc("Upadly Dom Inwestycyjny obiecuje zyski."), reg)
    assert r["mentions_authorized_firm"] and r["firm_license_active"] is False
    assert r["firm_is_authorized"] is False
    assert resolve(doc("Nic o firmach."), reg)["firm_license_active"] is None


def test_agent_publisher_is_authorized():
    reg = Registry.from_rows(ROWS, agent_keys={"jan agent"})
    r = resolve(doc("Zaloz konto w XTB.", handle="jan", display_name="Jan Agent"), reg)
    assert r["publisher_relation"] == "third_party" and r["publisher_is_authorized"]
    other = resolve(doc("Zaloz konto w XTB.", handle="x", display_name="Ktos Inny"), reg)
    assert not other["publisher_is_authorized"]

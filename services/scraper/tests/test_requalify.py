"""tools/requalify.py: filmy bez napisow odzyskane regula wzmianki o firmie."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import requalify  # noqa: E402

from tests.test_youtube import PL  # noqa: E402

DICTIONARY = [{"id": "F1", "group": "F1", "type": "organization", "value": "Firma Przykład", "aliases": []}]


def test_requalify_firm_mention_in_description():
    raw = {"title": "Oferta", "text": "Oferta\n\n" + PL * 2 + " Dzisiaj o tym, co robi Firma Przykład."}
    found = requalify.requalify(raw, DICTIONARY)
    assert [f["target"] for f in found] == ["Firma Przykład"] and found[0]["field"] == "description"


def test_requalify_rejects_without_firm_or_wrong_language():
    assert requalify.requalify({"title": "Oferta", "text": "Oferta\n\n" + PL * 3}, DICTIONARY) == []
    english = "This video explains the investment offer of Firma Przykład and account registration in detail. " * 3
    assert requalify.requalify({"title": "Offer", "text": "Offer\n\n" + english}, DICTIONARY) == []


class FakeConn:
    def __init__(self, rows):
        self.rows, self.updates = rows, []

    def execute(self, sql, params=None):
        if sql.lstrip().startswith("UPDATE"):
            self.updates.append(params)
        return self

    def fetchall(self):
        return self.rows

    def commit(self):
        pass


def test_run_updates_and_enqueues_only_qualified(monkeypatch):
    import resolver

    rows = [{"knf_id": "F1", "name": "Firma Przykład", "aliases": [], "domains": []}]
    monkeypatch.setattr(resolver.Registry, "from_db", classmethod(lambda cls, conn: cls.from_rows(rows)))
    doc = {"id": "00000000-0000-0000-0000-000000000001", "source": "youtube",
           "url": "https://www.youtube.com/watch?v=aaaaaaaaaaa", "fetched_at": "2026-11-21T00:00:00Z",
           "publisher": {}, "lang": "pl", "title": "Oferta", "media": [], "screenshots": {}}
    good = {"case_id": "c1", "raw": {**doc, "text": "Oferta\n\n" + PL * 2 + " Dzisiaj o Firma Przykład."},
            "entity_resolution": {}}
    bad = {"case_id": "c2", "raw": {**doc, "text": "Oferta\n\n" + PL * 3}, "entity_resolution": {}}
    conn, sent = FakeConn([good, bad]), []
    out = requalify.run(conn, None, enqueue=lambda r, d, cid, res: sent.append(cid))
    assert out["requalified"] == 1 and sent == ["c1"] and len(conn.updates) == 1
    dry = requalify.run(FakeConn([good]), None, dry_run=True, enqueue=lambda *a: sent.append("x"))
    assert dry["requalified"] == 1 and sent == ["c1"]

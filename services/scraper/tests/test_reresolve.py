"""Testy czystej czesci tools/reresolve.py (podsumowanie zmian)."""

from __future__ import annotations

from tools.reresolve import summarize


def test_summarize_counts_changes():
    changes = [
        ({"publisher_relation": "third_party", "disclosure_found": False},
         {"publisher_relation": "official", "disclosure_found": True, "affiliate_without_disclosure": False}),
        ({"publisher_relation": "third_party", "disclosure_found": False},
         {"publisher_relation": "third_party", "disclosure_found": False, "affiliate_without_disclosure": True}),
        (None, {"publisher_relation": "unknown", "disclosure_found": False}),
    ]
    s = summarize(changes)
    assert s["cases"] == 3
    assert s["relation_changes"] == {"third_party -> official": 1, "None -> unknown": 1}
    assert s["disclosure_changes"] == {"false -> true": 1}
    assert s["disclosure_found_after"] == 1 and s["affiliate_without_disclosure_after"] == 1


class _Cur:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class _FakeConn:
    def __init__(self, rows):
        self.rows, self.updates = rows, []

    def execute(self, sql, params=()):
        if sql.startswith("UPDATE"):
            if params[1] == "bad-update":
                raise RuntimeError("update failed")
            self.updates.append(params[1])
            return _Cur([])
        return _Cur(self.rows)

    def transaction(self):
        from contextlib import nullcontext
        return nullcontext()


def test_run_skips_bad_cases_and_continues():
    from resolver import Registry
    from tools.reresolve import run

    good = {"id": "1", "source": "www", "url": "https://blog.example.invalid/a",
            "fetched_at": "2026-11-21T10:00:00Z", "publisher": {"handle": "x", "display_name": "X"},
            "text": "Zaloz konto w XTB"}
    rows = [
        {"case_id": "ok", "raw": good, "entity_resolution": {"publisher_relation": "unknown"}},
        {"case_id": "bad-doc", "raw": {"zly": 1}, "entity_resolution": None},
        {"case_id": "bad-update", "raw": good, "entity_resolution": None},
        {"case_id": "ok2", "raw": good, "entity_resolution": None},
    ]
    reg = Registry.from_rows([{"knf_id": "DM-XTB", "name": "XTB S.A.", "aliases": [], "domains": [], "handles": []}])
    conn = _FakeConn(rows)
    out = run(conn, registry=reg)
    assert out["skipped_invalid"] == 2 and out["cases"] == 2
    assert conn.updates == ["ok", "ok2"]

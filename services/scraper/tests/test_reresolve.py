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

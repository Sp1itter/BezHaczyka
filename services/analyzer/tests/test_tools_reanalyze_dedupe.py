"""Testy narzedzi tools/reanalyze.py (skipped) i tools/dedupe_findings.py (plan)."""

from __future__ import annotations

import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, TOOLS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _Cur:
    def __init__(self, sink):
        self.sink = sink

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params):
        self.sink.append((sql, params))

    def fetchall(self):
        return []


class _Conn:
    def __init__(self):
        self.calls = []

    def cursor(self):
        return _Cur(self.calls)


def test_reanalyze_domyslnie_pomija_skipped():
    mod = _load("reanalyze")
    conn = _Conn()
    mod.select_cases(conn, "youtube", None, 40)
    _, params = conn.calls[0]
    assert "skipped" in params[-2] and "processing" in params[-2] and "queued" in params[-2]


def test_reanalyze_include_skipped_wlacza_skipped():
    mod = _load("reanalyze")
    conn = _Conn()
    mod.select_cases(conn, None, None, None, include_skipped=True)
    _, params = conn.calls[0]
    assert params[0] == ["processing", "queued"]


def test_reanalyze_flaga_cli(monkeypatch):
    mod = _load("reanalyze")
    seen = {}
    monkeypatch.setattr(mod, "select_cases", lambda *a, **k: seen.setdefault("a", a) and [])
    import analyzer.casedb_bridge as bridge

    class _C:
        def __enter__(self):
            return object()

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(bridge, "connect", lambda: _C())
    assert mod.main(["--include-skipped"]) == 0
    assert seen["a"][-1] is True
    seen.clear()
    assert mod.main([]) == 0
    assert seen["a"][-1] is False


T0 = datetime(2026, 11, 22, 1, 0, tzinfo=timezone.utc)


def _row(i, doc, minutes, **kw):
    base = dict(id=i, document_id=doc, created_at=T0 + timedelta(minutes=minutes), status="new",
                assignee=None, assigned_by=None, assigned_at=None, review_verdict=None,
                review_label=None, review_note=None, reviewed_by=None, reviewed_at=None)
    base.update(kw)
    return base


def test_dedupe_zostaje_najnowsza_analiza_i_kopiuje_prace_analityka():
    d = _load("dedupe_findings")
    rows = [
        _row("old", "D1", 0, status="triage", assignee="ola", assigned_by="human",
             assigned_at=T0, review_verdict="confirmed", review_label="TP",
             reviewed_at=T0 + timedelta(minutes=5)),
        _row("new", "D1", 100),
        _row("solo", "D2", 10),
    ]
    acts = d.plan(rows, {})
    assert len(acts) == 1  # D2 nie ma duplikatu
    a = acts[0]
    assert a["keep"] == "new" and a["delete"] == ["old"] and a["copy_from"] == "old"
    assert a["copy"]["status"] == "triage" and a["copy"]["assignee"] == "ola"
    assert a["copy"]["review_verdict"] == "confirmed"


def test_dedupe_bez_pracy_zostaje_najnowszy_bez_kopiowania():
    d = _load("dedupe_findings")
    acts = d.plan([_row("a", "D", 0), _row("b", "D", 5), _row("c", "D", 9)], {})
    assert acts[0]["keep"] == "c" and sorted(acts[0]["delete"]) == ["a", "b"]
    assert acts[0]["copy"] is None and acts[0]["copy_from"] is None


def test_dedupe_praca_z_najpozniej_zmienionego_wiersza():
    d = _load("dedupe_findings")
    rows = [
        _row("a", "D", 0, assignee="ola", assigned_at=T0 + timedelta(minutes=1)),
        _row("b", "D", 5, assignee="ewa", assigned_at=T0 + timedelta(minutes=50)),
        _row("c", "D", 9),
    ]
    a = d.plan(rows, {})[0]
    assert a["copy_from"] == "b" and a["copy"]["assignee"] == "ewa"


def test_dedupe_zdarzenia_liczone_jako_praca():
    d = _load("dedupe_findings")
    rows = [_row("a", "D", 0), _row("b", "D", 5)]
    a = d.plan(rows, {"a": T0 + timedelta(minutes=2)})[0]
    assert a["copy_from"] == "a"  # a ma zdarzenia -> praca; zdarzenia przepnie apply_plan
    assert a["delete"] == ["a"]


def test_dedupe_praca_na_zachowanym_wierszu_nie_jest_kopiowana():
    d = _load("dedupe_findings")
    rows = [_row("a", "D", 0), _row("b", "D", 5, assignee="ola", assigned_at=T0)]
    a = d.plan(rows, {})[0]
    assert a["keep"] == "b" and a["copy"] is None and a["copy_from"] == "b"


def test_narzedzia_dodaja_katalog_aplikacji_do_sys_path():
    """`python tools/x.py` w obrazie (/app/tools) musi widziec pakiet analyzer."""
    import sys

    root = str(TOOLS.parent)
    for name in ("reanalyze", "dedupe_findings"):
        while root in sys.path:
            sys.path.remove(root)
        _load(name)
        assert root in sys.path

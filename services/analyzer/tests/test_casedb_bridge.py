"""Testy mostu do casedb na fake'owym polaczeniu (rejestruje SQL i parametry)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import httpx
import pytest

from analyzer import casedb_bridge
from analyzer.llm import OllamaClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import casedb_batch  # noqa: E402

FIX = Path(__file__).resolve().parents[3] / "fixtures" / "casedb-examples"


class _Cur:
    def __init__(self, rows):
        self.rows = rows

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def __iter__(self):
        return iter(self.rows)


class FakeConn:
    def __init__(self, ids=("c1",)):
        self.log: list[tuple[str, tuple]] = []
        self.ids = list(ids)
        self.commits = 0
        self.rollbacks = 0

    def execute(self, sql, params=()):
        s = " ".join(sql.split())
        self.log.append((s, tuple(params)))
        if s.startswith("UPDATE cases SET status = 'queued'"):
            return _Cur([{"case_id": i} for i in self.ids])
        if s.startswith("SELECT * FROM cases"):
            return _Cur([{"case_id": params[0], "source": "youtube", "url": "u",
                          "status": "processing", "title": "T", "lang": "pl",
                          "extra": {}, "raw": {}}])
        return _Cur([])

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def statuses(self):
        return [p[0] for s, p in self.log if s.startswith("UPDATE cases SET status = %s")]


def _ai(case):
    return {"task": "investwatch", "model": "m", "version": "v", "label": "low", "score": 0.1,
            "result": {"k": 1}}


@pytest.fixture(autouse=True)
def _no_psycopg(monkeypatch):
    monkeypatch.setattr(casedb_bridge, "_jsonb", lambda v: ("JSONB", v))


def test_claim_sql_i_parametry():
    c = FakeConn()
    assert casedb_bridge.claim(c, 5, source="youtube") == ["c1"]
    s, p = c.log[0]
    assert "FOR UPDATE SKIP LOCKED" in s and "attempts = attempts + 1" in s
    assert p == ("analyzer", ["new"], "youtube", "youtube", 5)


def test_kolejnosc_statusow_i_upsert():
    c = FakeConn()
    res = casedb_bridge.process_cases(c, _ai, limit=3)
    assert res == {"c1": "done"}
    sqls = [s for s, _ in c.log]
    assert sqls[0].startswith("UPDATE cases SET status = 'queued'")
    assert c.statuses() == ["processing", "done"]
    ins = [(i, s, p) for i, (s, p) in enumerate(c.log) if s.startswith("INSERT INTO ai_results")]
    assert len(ins) == 1
    i, s, p = ins[0]
    assert "ON CONFLICT (case_id, task, model, version) DO UPDATE" in s
    assert p[:4] == ("c1", "investwatch", "m", "v") and p[7] == ("JSONB", {"k": 1})
    # processing przed zapisem wyniku, done po nim
    proc = next(j for j, (s2, p2) in enumerate(c.log)
                if s2.startswith("UPDATE cases SET status = %s") and p2[0] == "processing")
    done = next(j for j, (s2, p2) in enumerate(c.log)
                if s2.startswith("UPDATE cases SET status = %s") and p2[0] == "done")
    assert proc < i < done


def test_blad_analizy_ustawia_error_i_nie_przerywa():
    c = FakeConn(ids=("a", "b"))

    def boom(case):
        if case["case_id"] == "a":
            raise ValueError("zepsute")
        return _ai(case)

    res = casedb_bridge.process_cases(c, boom, limit=2)
    assert res == {"a": "error", "b": "done"}
    assert c.rollbacks == 1
    err = [p for s, p in c.log if s.startswith("UPDATE cases SET status = %s") and p[0] == "error"]
    assert err[0][1].startswith("ValueError: zepsute") and err[0][2] == "a"


def _fake_llm():
    def handler(request: httpx.Request) -> httpx.Response:
        from analyzer.rules_llm.registry import ALL_RULE_META
        results = [{"rule_id": r, "verdict": "pass", "confidence": 0.9, "summary": "ok"}
                   for r in ALL_RULE_META]
        return httpx.Response(200, json={"response": json.dumps({"results": results})})

    return OllamaClient(
        client=httpx.Client(transport=httpx.MockTransport(handler), base_url="http://f.invalid"))


def test_tryb_plikowy_z_fake_llm(tmp_path):
    analyze_case = casedb_batch.make_analyzer(_fake_llm())

    def failing(case):
        if case["case_id"] == "zly":
            raise RuntimeError("awaria")
        return analyze_case(case)

    cases = json.loads((FIX / "export.json").read_text(encoding="utf-8"))
    cases.append({"case_id": "zly", "source": "youtube", "url": "u"})
    src = tmp_path / "in.json"
    src.write_text(json.dumps(cases), encoding="utf-8")
    out = tmp_path / "out"
    rows = casedb_batch.run_file(src, out, failing)
    ok = [r for r in rows if "error" not in r]
    assert len(ok) == 2 and any(r["partial_transcript"] for r in ok)
    for r in ok:
        assert (out / f"{r['case_id']}.json").exists()
    assert (out / "zly.error.json").exists()
    cmds = (out / "casedb_commands.txt").read_text(encoding="utf-8").splitlines()
    assert len(cmds) == 2
    assert all(c.startswith("docker compose run --rm casedb ai-result ")
               and "--task investwatch" in c and "--label" in c and "--score" in c
               and "/data/" in c for c in cmds)


@pytest.mark.skipif(not os.environ.get("TEST_DATABASE_URL"), reason="brak TEST_DATABASE_URL")
def test_live_polaczenie_i_claim_zerowego_limitu():
    with casedb_bridge.connect(os.environ["TEST_DATABASE_URL"]) as conn:
        assert isinstance(casedb_bridge.claim(conn, 0), list)
        conn.rollback()

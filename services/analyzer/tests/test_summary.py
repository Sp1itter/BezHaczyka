"""Podsumowanie findingu: szablon, straznik odpowiedzi LLM, worker, backfill."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from analyzer.contracts import AdDocument, Evidence, EvidenceKind, Finding, RuleResult, Verdict
from analyzer.llm import LlmError
from analyzer.summary import build_summary
from analyzer.worker import handle_job

ROOT = Path(__file__).resolve().parents[1]
DOC_ID = "11111111-1111-4111-8111-111111111111"
DOC = {
    "id": DOC_ID,
    "source": "web",
    "url": "https://example.invalid/x",
    "fetched_at": "2026-11-21T14:03:00Z",
    "text": "Zyski do 18% rocznie! Handluj CFD na Bitcoina.",
}


def _rule(rule_id: str, verdict: Verdict, quote: str | None = None) -> RuleResult:
    return RuleResult(
        rule_id=rule_id,
        rule_name=f"Regula {rule_id}",
        engine="LLM",
        verdict=verdict,
        severity=4,
        legal_basis="art. 1 testowej ustawy",
        evidence=Evidence(kind=EvidenceKind.QUOTE, summary="opis dowodu", quote=quote),
    )


def _finding(rules: list[RuleResult], level: str = "high", score: float = 72.4) -> Finding:
    return Finding.model_validate(
        {
            "id": "22222222-2222-4222-8222-222222222222",
            "document_id": DOC_ID,
            "primary_module": 1,
            "modules": [1],
            "routing": {"rule": "R1", "reason": "Reklama CFD.", "scope_gate": "in_scope"},
            "risk_score": score,
            "risk_level": level,
            "rule_results": [r.model_dump(mode="json") for r in rules],
            "entities": {
                "investment_firm": {"name_in_ad": "Firma X", "is_authorized": False},
                "advertiser": {"name": "@jan", "relation_to_firm": "third_party"},
            },
            "created_at": "2026-11-21T14:03:00Z",
        }
    )


class FakeClient:
    def __init__(self, reply=None, error: Exception | None = None):
        self.reply, self.error, self.prompts = reply, error, []

    def generate_json(self, prompt: str) -> dict:
        self.prompts.append(prompt)
        if self.error:
            raise self.error
        return self.reply


FAILS = [_rule("3", Verdict.FAIL, "Zyski do 18% rocznie!"), _rule("5", Verdict.PASS)]


def test_no_violations_is_template_without_llm():
    client = FakeClient(reply={"summary": "nie powinno byc wywolane 3"})
    f = _finding([_rule("3", Verdict.PASS), _rule("5", Verdict.NOT_APPLICABLE)], "low", 12)
    text, engine = build_summary(f, None, client=client)
    assert engine == "template" and client.prompts == []
    assert text.startswith("Nie stwierdzono naruszeń (ryzyko niskie, wynik 12).")
    assert "Oceniono 1 reguł" in text


def test_template_on_llm_error():
    text, engine = build_summary(_finding(FAILS), None, client=FakeClient(error=LlmError("x")))
    assert engine == "template"
    assert text.startswith("Ryzyko wysokie (wynik 72).")
    assert "reguła 3 (Regula 3) — „Zyski do 18% rocznie!”" in text
    assert "Publikujący: @jan (podmiot trzeci)." in text


def test_template_when_llm_disabled():
    client = FakeClient(reply={"summary": "reguła 3"})
    _, engine = build_summary(_finding(FAILS), None, client=client, use_llm=False)
    assert engine == "template" and client.prompts == []


def test_template_truncates_quote():
    f = _finding([_rule("3", Verdict.FAIL, "a" * 300)])
    text, _ = build_summary(f, None, use_llm=False)
    assert "a" * 119 + "…" in text and "a" * 120 not in text


@pytest.mark.parametrize(
    "reply",
    [
        {"summary": ""},
        {"summary": "Ocena wynika z ogólnych wrażeń, bez numeru."},
        {"summary": "Wynik 30% oraz 13 zastrzeżeń."},  # 3 tylko jako czesc liczb
        {"summary": "Reguła 3 naruszona. " + "x" * 700},
        {"nie_summary": "reguła 3"},
        ["reguła 3"],
    ],
)
def test_bad_llm_reply_rejected(reply):
    text, engine = build_summary(_finding(FAILS), None, client=FakeClient(reply=reply))
    assert engine == "template"


def test_good_llm_reply_accepted():
    reply = {"summary": "Wysokie ryzyko wynika z naruszenia reguły 3. Obietnica zysku."}
    client = FakeClient(reply=reply)
    text, engine = build_summary(_finding(FAILS), None, client=client)
    assert (text, engine) == (reply["summary"], "llm")
    assert "reguła 3 (Regula 3)" in client.prompts[0]
    assert "Zyski do 18% rocznie!" in client.prompts[0]
    assert "{risk_level}" not in client.prompts[0]


class FakeStore:
    def __init__(self):
        self.posted = []

    def get_document(self, document_id):
        return AdDocument.model_validate(DOC)

    def previous(self, document_id):
        return None

    def save_vectors(self, doc):
        pass

    def post_finding(self, finding, document=None, summary=None, summary_engine=None):
        self.posted.append((summary, summary_engine))


def test_worker_saves_summary():
    store = FakeStore()
    assert handle_job({"document_id": DOC_ID}, api=store) is not None
    summary, engine = store.posted[0]
    assert engine == "template" and summary


def test_worker_summary_disabled(monkeypatch):
    monkeypatch.setenv("SUMMARY_ENABLED", "0")
    store = FakeStore()
    handle_job({"document_id": DOC_ID}, api=store)
    assert store.posted == [(None, None)]


def test_worker_summary_error_does_not_break_save(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("boom")

    monkeypatch.setattr("analyzer.worker.build_summary", boom)
    store = FakeStore()
    assert handle_job({"document_id": DOC_ID}, api=store) is not None
    assert store.posted == [(None, None)]


@pytest.fixture
def pg_conn():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("brak TEST_DATABASE_URL")
    from casedb import db

    c = db.connect(url)
    c.execute("DROP VIEW IF EXISTS module1_report")
    c.execute(
        "DROP TABLE IF EXISTS change_events, findings, documents, authorized_entities,"
        " knf_entities, ai_results, case_assets, case_content, cases, casedb_migrations CASCADE"
    )
    c.commit()
    db.migrate(c)
    yield c
    c.close()


def test_backfill_on_real_db(pg_conn):
    from casedb import store

    sys.path.insert(0, str(ROOT / "tools"))
    from backfill_summaries import backfill

    ok = _finding(FAILS).model_dump(mode="json")
    store.save_finding(pg_conn, ok, None)
    clean = _finding([_rule("3", Verdict.PASS)], "low", 5).model_dump(mode="json")
    clean["id"] = "33333333-3333-4333-8333-333333333333"
    store.save_finding(pg_conn, clean, None)
    pg_conn.commit()

    client = FakeClient(reply={"summary": "Naruszona reguła 3 (obietnica zysku)."})
    stats = backfill(pg_conn, use_llm=True, client=client)
    assert stats == {"total": 2, "llm": 1, "template": 1, "errors": 0}
    rows = {
        str(r["id"]): r
        for r in pg_conn.execute("SELECT id, summary, summary_engine FROM findings")
    }
    assert rows[ok["id"]]["summary_engine"] == "llm"
    assert rows[clean["id"]]["summary_engine"] == "template"
    assert backfill(pg_conn, use_llm=True, client=client)["total"] == 0  # idempotentne


def test_dbstore_post_finding_writes_summary(pg_conn):
    from analyzer.db_store import DbStore

    f = _finding(FAILS)
    DbStore(conn=pg_conn).post_finding(f, None, summary="Tekst reguła 3.", summary_engine="llm")
    row = pg_conn.execute("SELECT summary, summary_engine FROM findings").fetchone()
    assert row == {"summary": "Tekst reguła 3.", "summary_engine": "llm"}

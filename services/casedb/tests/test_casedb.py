# compliance:allow-file - testowe dane z prawdziwymi URL-ami YouTube/Facebook (bez ruchu sieciowego)
import json
import threading
from pathlib import Path

import pytest
from casedb import cli, export, ingest, store

YT = {
    "url": "https://www.youtube.com/watch?v=NB1HhV6EKG8",
    "title": "XTB dodalo funkcje",
    "channel": "DETERMINACJA",
    "language": "pl",
    "description": "Partnerem odcinka jest XTB",
    "author_comments": [{"comment_id": "c1", "parent_id": None, "author_channel_id": "UC1", "text": "link"}],
    "evidence": [{"field": "description", "type": "organization", "target": "XTB",
                  "quote": "Partnerem odcinka jest XTB", "signals": ["partnerem odcinka"]}],
    "clips": [{"start": 47.28, "end": 57.5, "text": "Partnerem odcinka jest XTB", "targets": ["XTB"],
               "signals": ["partnerem odcinka"], "url": "https://www.youtube.com/watch?v=NB1HhV6EKG8&t=47s"}],
}

FB = {
    "id": "d9aeb3e7-35d2-5336-81a8-ee5b7e7396ba", "source": "facebook",
    "url": "https://www.facebook.com/ads/library/?id=912810501476495",
    "fetched_at": "2026-11-21T14:00:00Z",
    "publisher": {"display_name": "Virtune", "profile_url": "https://facebook.com/1/"},
    "lang": "pl", "title": None, "text": "Inwestuj w ETP",
    "html_path": "s3://raw/d9.html", "screenshots": {"desktop": "s3://shots/d9-1920.png"},
    "media": [{"kind": "video", "path": "s3://media/d9.mp4", "duration_s": 12.0}],
    "transcript": None, "render_probe": {"viewports": {}},
    "embedding": {"model": "bge-m3", "dim": 1024, "vector": [0.1] * 1024},
    "simhash": None, "scope": {"status": "uncertain"},
}


def test_youtube_mapping_is_stable():
    a, b = ingest.from_youtube(YT), ingest.from_youtube({**YT, "url": "https://youtu.be/NB1HhV6EKG8"})
    assert a.case_id == b.case_id == store.case_id_for("https://www.youtube.com/watch?v=NB1HhV6EKG8")
    assert [c.kind for c in a.content] == ["title", "description", "comment", "evidence", "clip"]


def test_facebook_mapping_keeps_document_id_and_drops_embedding():
    c = ingest.from_ad_document(FB)
    assert c.case_id == FB["id"] and c.source_item_id == "912810501476495"
    assert "embedding" not in c.raw
    assert {a.kind for a in c.assets} == {"html", "screenshot", "video"}


def test_add_column_rejects_injection():
    with pytest.raises(ValueError):
        store.add_column(None, "cases", "x; DROP TABLE cases", "text")
    with pytest.raises(ValueError):
        store.add_column(None, "cases", "ok", "text; DROP TABLE cases")


def test_roundtrip_export(conn):
    yt = store.save_case(conn, ingest.from_youtube(YT))
    fb = store.save_case(conn, ingest.from_ad_document(FB))
    store.save_case(conn, ingest.from_youtube(YT))  # ponowny ingest bez duplikatow
    store.add_column(conn, "cases", "risk_score", "double precision")
    store.set_columns(conn, yt, {"risk_score": 0.8})
    store.save_ai_result(conn, yt, "scam_classifier", "bielik-4.5b", {"label": "promo"}, score=0.9)
    conn.commit()

    assert conn.execute("SELECT count(*) AS n FROM cases").fetchone()["n"] == 2
    [doc] = export.export_cases(conn, [yt])
    assert doc["metadata"]["risk_score"] == 0.8
    assert doc["content"]["clip"][0]["start_s"] == 47.28
    assert doc["content"]["clip"][0]["targets"] == ["XTB"]
    assert doc["ai_results"]["scam_classifier"][0]["result"] == {"label": "promo"}
    assert doc["assets"][0]["uri"] == "https://www.youtube.com/watch?v=NB1HhV6EKG8"
    json.dumps(doc)  # musi sie serializowac

    [fbdoc] = export.export_cases(conn, [fb])
    assert fbdoc["metadata"]["publisher"]["display_name"] == "Virtune"
    assert fbdoc["content"]["text"][0]["body"] == "Inwestuj w ETP"


def test_claim_is_exclusive(conn):
    for i in range(10):
        store.save_case(conn, ingest.from_youtube({**YT, "url": f"https://www.youtube.com/watch?v=v{i}"}))
    conn.commit()
    from casedb import db
    got: list[str] = []

    def worker(name):
        with db.connect(conn.info.dsn + " password=" + (conn.info.password or "")) as c:
            got.extend(store.claim(c, name, 4))
            c.commit()

    ts = [threading.Thread(target=worker, args=(f"w{i}",)) for i in range(3)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert len(got) == len(set(got)) == 10


def test_cli_ingest_and_export(conn, tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setenv("DATABASE_URL", conn.info.dsn + " password=" + (conn.info.password or ""))
    src = tmp_path / "wynik.json"
    src.write_text(json.dumps([YT]), encoding="utf-8")
    assert cli.main(["ingest", "youtube", str(src)]) == 0
    out = tmp_path / "out.json"
    assert cli.main(["export", "--claim", "router", "--limit", "5", "-o", str(out)]) == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert len(data) == 1 and data[0]["status"] == "queued"


# --- modul 1 ---------------------------------------------------------------

import uuid

from casedb import registry


def _doc(**kw):
    d = {k: v for k, v in FB.items() if k != "embedding"}
    d.update(kw)
    return d


def test_normalize_name():
    assert store.normalize_name("XTB S.A.") == "xtb"
    assert store.normalize_name("Dom Maklerski BOS S.A.") == "dom maklerski bos"
    assert store.normalize_name("Zażółć  Gęślą Sp. z o.o.") == "zazolc gesla"
    assert store.normalize_name("Interactive Brokers (U.K.) Ltd") == "interactive brokers u k"
    assert store.normalize_name("Trade Republic Bank GmbH") == "trade republic bank"
    assert store.normalize_name("Saxo Bank A/S") == "saxo bank"


def test_content_hash_normalizes_text():
    a = store.content_hash({"title": "Zażółć", "text": "Inwestuj   w ETP", "transcript": None})
    b = store.content_hash({"title": "ZAŻÓŁĆ", "text": "inwestuj w etp\n", "transcript": {"text": ""}})
    assert a == b
    assert a != store.content_hash({"title": "Zażółć", "text": "Inwestuj w ETP", "transcript": {"text": "x"}})


def test_read_registry_csv_packaged_and_custom(tmp_path: Path):
    rows = registry.read_registry_csv(registry.packaged_registry_path())
    assert rows and all(r["knf_id"] and r["name"] for r in rows)
    bos = next(r for r in rows if r["knf_id"] == "DM-BOS")
    assert "Bossa" in bos["aliases"] and "bossa.pl" in bos["domains"]
    f = tmp_path / "r.csv"
    f.write_text("knf_id,name,type,country,register,aliases,domains,handles,source_url\n"
                 "A1,Firma ąę,t,PL,r,,x.pl;y.pl,h1,\n,,,,,,,,\n", encoding="utf-8")
    [r] = registry.read_registry_csv(f)
    assert r["name"] == "Firma ąę" and r["domains"] == ["x.pl", "y.pl"] and r["aliases"] == []
    assert r["source_url"] is None


def test_record_document_new_unchanged_changed(conn):
    er = {"publisher_relation": "third_party", "mentions_authorized_firm": True}
    cid, out = store.record_document(conn, _doc(), entity_resolution=er)
    assert (cid, out) == (FB["id"], "new")
    row = conn.execute("SELECT * FROM cases WHERE case_id = %s", (cid,)).fetchone()
    assert row["status"] == "new" and row["seen_count"] == 1 and row["content_hash"]
    assert row["entity_resolution"] == er

    store.mark_gone(conn, cid)
    cid, out = store.record_document(conn, _doc(), entity_resolution={**er, "disclosure_found": True})
    assert out == "unchanged"
    row = conn.execute("SELECT * FROM cases WHERE case_id = %s", (cid,)).fetchone()
    assert row["seen_count"] == 2 and row["gone_at"] is None
    assert row["entity_resolution"]["disclosure_found"] is True

    store.set_status(conn, cid, "done")
    _, out = store.record_document(conn, _doc(text="Inwestuj w ETP z bonusem"), extra_content=[
        store.Content("evidence", "dowod")])
    assert out == "changed"
    row = conn.execute("SELECT * FROM cases WHERE case_id = %s", (cid,)).fetchone()
    assert row["status"] == "new" and row["seen_count"] == 3
    assert row["entity_resolution"]["disclosure_found"] is True
    kinds = [r["kind"] for r in conn.execute("SELECT kind FROM case_content WHERE case_id = %s", (cid,))]
    assert "evidence" in kinds
    assert conn.execute("SELECT count(*) AS n FROM cases").fetchone()["n"] == 1


def test_record_document_not_qualified_is_skipped(conn):
    cid, out = store.record_document(conn, _doc(), qualified=False)
    assert out == "new"
    assert conn.execute("SELECT status FROM cases WHERE case_id = %s", (cid,)).fetchone()["status"] == "skipped"


def test_vectors_roundtrip(conn):
    cid, _ = store.record_document(conn, _doc())
    assert store.get_document(conn, cid)["embedding"] is None
    store.save_vectors(conn, cid, [0.5] * 1024, "abc123")
    d = store.get_document(conn, cid)
    assert len(d["embedding"]) == 1024 and d["embedding"][0] == 0.5 and d["simhash"] == "abc123"
    assert d["text"] == "Inwestuj w ETP"
    assert store.get_document(conn, str(uuid.uuid4())) is None


def _finding(cid, level="low", **kw):
    return {"id": str(uuid.uuid4()), "document_id": cid, "primary_module": None, "modules": [1, 2],
            "routing": {"reason": "powod"}, "risk_score": 0.4, "risk_level": level,
            "rule_results": [{"rule": "r1"}], "entities": {}, "knn_score": None,
            "created_at": "2026-11-21T10:00:00+00:00", **kw}


def test_finding_latest_and_notify(conn):
    cid, _ = store.record_document(conn, _doc())
    assert store.latest_finding(conn, cid) is None
    f1 = _finding(cid)
    store.save_finding(conn, f1, {"text": "v1"})
    assert conn.execute("SELECT status FROM cases WHERE case_id = %s", (cid,)).fetchone()["status"] == "done"
    f2 = _finding(cid, "high", created_at="2026-11-21T11:00:00+00:00", risk_score=0.9)

    import psycopg
    listener = psycopg.connect(conn.info.dsn + " password=" + (conn.info.password or ""), autocommit=True)
    listener.execute("LISTEN findings_high")
    store.save_finding(conn, f2, {"text": "v2"})
    store.save_finding(conn, {**f2, "risk_score": 0.95})  # upsert, snapshot zostaje
    conn.commit()
    notes = list(listener.notifies(timeout=2, stop_after=2))
    listener.close()
    assert {n.payload for n in notes} == {f2["id"]}

    last = store.latest_finding(conn, cid)
    assert last["id"] == f2["id"] and last["risk_score"] == 0.95
    assert last["document_snapshot"] == {"text": "v2"} and last["primary_module"] is None
    assert conn.execute("SELECT count(*) AS n FROM findings").fetchone()["n"] == 2


def test_change_event(conn):
    cid, _ = store.record_document(conn, _doc())
    f1, f2 = _finding(cid), _finding(cid, "high")
    store.save_finding(conn, f1)
    store.save_finding(conn, f2)
    ev = {"id": str(uuid.uuid4()), "document_id": cid, "kind": "ESKALACJA_RYZYKA",
          "detected_at": "2026-11-21T12:00:00+00:00", "previous_finding_id": f1["id"],
          "current_finding_id": f2["id"], "rule_diff": [{"rule": "r1"}],
          "similarity": {"score": 0.8}, "risk_level_from": "low", "risk_level_to": "high",
          "summary": "Ryzyko wzroslo"}
    store.save_change_event(conn, ev)
    store.save_change_event(conn, ev)
    [row] = conn.execute("SELECT * FROM change_events").fetchall()
    assert row["kind"] == "ESKALACJA_RYZYKA" and row["rule_diff"] == [{"rule": "r1"}]
    assert row["current_finding_id"] is not None and row["risk_level_to"] == "high"


def test_gone_and_recheck(conn):
    ids = [store.record_document(conn, _doc(id=str(uuid.uuid4()), url=f"https://x.pl/{i}", source="www"))[0]
           for i in range(3)]
    conn.execute("UPDATE cases SET last_seen_at = now() - make_interval(hours => %s) WHERE case_id = %s",
                 (10, ids[1]))
    store.mark_gone(conn, ids[2])
    first = conn.execute("SELECT gone_at FROM cases WHERE case_id = %s", (ids[2],)).fetchone()["gone_at"]
    store.mark_gone(conn, ids[2])
    assert conn.execute("SELECT gone_at FROM cases WHERE case_id = %s", (ids[2],)).fetchone()["gone_at"] == first
    got = store.cases_for_recheck(conn, 10)
    assert [g["case_id"] for g in got] == [ids[1], ids[0]] and set(got[0]) == {"case_id", "source", "url"}
    assert [g["case_id"] for g in store.cases_for_recheck(conn, 10, older_than_minutes=60)] == [ids[1]]
    assert store.cases_for_recheck(conn, 10, source="youtube") == []
    assert len(store.cases_for_recheck(conn, 1)) == 1


def test_load_registry(conn):
    rows = registry.read_registry_csv(registry.packaged_registry_path())
    assert store.load_registry(conn, rows) == len(rows)
    rows[0]["name"] = "Nowa Nazwa S.A."
    store.load_registry(conn, rows)
    entries = store.registry_entries(conn)
    assert len(entries) == len(rows)
    assert next(e for e in entries if e["knf_id"] == rows[0]["knf_id"])["normalized_name"] == "nowa nazwa"


def test_report_module1(conn):
    store.load_registry(conn, [{"knf_id": "K1", "name": "XTB S.A.", "type": "dom maklerski",
                                "country": "PL", "aliases": [], "domains": [], "handles": []}])
    er = {"publisher_relation": "third_party", "publisher_name": "Finfluencer", "mentions_authorized_firm": True,
          "firm_is_authorized": True, "registry_knf_id": "K1", "registry_official_name": "XTB S.A.",
          "firm_name_in_ad": "XTB", "disclosure_found": False, "affiliate_link": "https://xtb.com/?ref=1"}
    a, _ = store.record_document(conn, _doc(text="x" * 1500), entity_resolution=er)
    yt, _ = store.record_document(conn, _doc(id=str(uuid.uuid4()), url="https://x.pl/a", source="www"),
                                  entity_resolution={"publisher_relation": "official",
                                                     "mentions_authorized_firm": False})
    store.record_document(conn, _doc(id=str(uuid.uuid4()), url="https://x.pl/b", source="www"),
                          entity_resolution={"publisher_relation": "third_party"})
    store.save_finding(conn, _finding(a, "medium", created_at="2026-11-21T10:00:00+00:00"))
    store.save_finding(conn, _finding(a, "high", created_at="2026-11-21T11:00:00+00:00",
                                      primary_module=1))
    rows = store.report_module1(conn)
    assert {r["case_id"] for r in rows} == {a, rows[0]["case_id"], rows[1]["case_id"]} and len(rows) == 2
    assert yt not in {r["case_id"] for r in rows}
    r = next(r for r in rows if r["case_id"] == a)
    assert len(r["tresc"]) == 1000 and r["advertiser_name"] == "Finfluencer"
    assert r["relation"] == "third_party" and r["disclosure_found"] is False
    assert r["firm_knf_id"] == "K1" and r["firm_type"] == "dom maklerski" and r["firm_country"] == "PL"
    assert r["risk_level"] == "high" and r["primary_module"] == 1 and r["routing_reason"] == "powod"
    assert r["advertiser_handle"] is None and r["seen_count"] == 1
    assert [x["case_id"] for x in store.report_module1(conn, source="facebook")] == [a]
    assert len(store.report_module1(conn, limit=1)) == 1
    assert store.report_module1(conn, since="2999-01-01") == []


def test_cli_init_and_report(conn, tmp_path: Path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", conn.info.dsn + " password=" + (conn.info.password or ""))
    assert cli.main(["init"]) == 0
    assert cli.main(["init"]) == 0
    entries = store.registry_entries(conn)
    curated = registry.read_registry_csv(registry.packaged_registry_path())
    assert sum(e["source"] == "curated" for e in entries) == len(curated)
    assert any(e["source"] == "knf" for e in entries)
    store.record_document(conn, _doc(), entity_resolution={"publisher_relation": "third_party"})
    conn.commit()
    out = tmp_path / "r.csv"
    assert cli.main(["report", "module1", "--format", "csv", "-o", str(out)]) == 0
    assert out.read_text(encoding="utf-8").startswith("case_id,source,url")
    assert cli.main(["recheck-list", "--limit", "5"]) == 0


def test_finding_fills_documents_for_api(conn):
    # Dashboard (services/api) czyta findings LEFT JOIN documents - migawka trafia do documents.
    doc = _doc()
    cid, _ = store.record_document(conn, doc)
    store.save_finding(conn, _finding(cid), doc)
    row = conn.execute("SELECT source, url, title FROM documents WHERE id = %s", (cid,)).fetchone()
    assert row["source"] == doc["source"] and row["url"] == doc["url"]
    # migawka czesciowa: brakujace pola z cases, wiersz aktualizowany
    store.save_finding(conn, _finding(cid), {"text": "nowa tresc"})
    row = conn.execute("SELECT url, text FROM documents WHERE id = %s", (cid,)).fetchone()
    assert row["url"] == doc["url"] and row["text"] == "nowa tresc"
    # bez migawki dokumentu nie ruszamy
    other = str(uuid.uuid4())
    store.save_finding(conn, _finding(other))
    assert conn.execute("SELECT 1 FROM documents WHERE id = %s", (other,)).fetchone() is None


def test_migrate_on_legacy_init_sql_schema(conn):
    # Baza ze starego infra/init.sql (main przed Modulem 1): migracja 002 ma ja doprowadzic do ladu.
    from casedb import db

    conn.execute("DROP VIEW IF EXISTS module1_report")
    conn.execute("DROP TABLE IF EXISTS change_events, findings, documents, authorized_entities,"
                 " ai_results, case_assets, case_content, cases, casedb_migrations CASCADE")
    conn.execute("""
        CREATE TABLE documents (id UUID PRIMARY KEY, source TEXT NOT NULL, url TEXT NOT NULL,
            fetched_at TIMESTAMPTZ NOT NULL, publisher JSONB NOT NULL DEFAULT '{}'::jsonb,
            lang TEXT NOT NULL DEFAULT 'pl', title TEXT, text TEXT NOT NULL DEFAULT '',
            html_path TEXT, screenshots JSONB NOT NULL DEFAULT '{}'::jsonb,
            media JSONB NOT NULL DEFAULT '[]'::jsonb, transcript JSONB, render_probe JSONB,
            embedding vector(1024), simhash TEXT, scope JSONB NOT NULL DEFAULT '{}'::jsonb);
        CREATE TABLE findings (id UUID PRIMARY KEY,
            document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            primary_module INTEGER NOT NULL, modules INTEGER[] NOT NULL DEFAULT '{}',
            routing JSONB NOT NULL DEFAULT '{}'::jsonb, risk_score DOUBLE PRECISION NOT NULL,
            risk_level TEXT NOT NULL, rule_results JSONB NOT NULL DEFAULT '[]'::jsonb,
            entities JSONB NOT NULL DEFAULT '{}'::jsonb, knn_score DOUBLE PRECISION,
            status TEXT NOT NULL DEFAULT 'new', created_at TIMESTAMPTZ NOT NULL DEFAULT now());
        CREATE TABLE authorized_entities (name TEXT NOT NULL, normalized_name TEXT NOT NULL,
            knf_id TEXT PRIMARY KEY, type TEXT, country TEXT);
    """)
    conn.commit()
    db.migrate(conn)
    assert store.load_registry(conn, [{"knf_id": "DM-1", "name": "XTB S.A.", "aliases": ["xtb"]}]) == 1
    cid, _ = store.record_document(conn, _doc())
    store.save_finding(conn, _finding(cid), _doc())
    assert conn.execute("SELECT count(*) AS n FROM documents").fetchone()["n"] == 1
    assert store.latest_finding(conn, cid)["document_snapshot"] is not None

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

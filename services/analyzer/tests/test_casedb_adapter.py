"""Testy adaptera casedb <-> AdDocument/Finding. Bez bazy i bez Ollamy."""

from __future__ import annotations

import json
from pathlib import Path

from analyzer.casedb_adapter import (
    TASK,
    analyzer_version,
    case_to_document,
    finding_to_ai_result,
)
from analyzer.completeness import is_partial
from analyzer.pipeline import analyze

FIX = Path(__file__).resolve().parents[3] / "fixtures"


def _load(p: str) -> dict:
    return json.loads((FIX / p).read_text(encoding="utf-8"))


def test_facebook_z_raw_daje_ten_sam_dokument():
    case = _load("casedb-examples/facebook_case.json")
    doc = case_to_document(case)
    assert doc.id == case["case_id"]
    assert doc.source == "facebook"
    assert doc.render_probe is not None  # raw przeszlo przez model_validate w calosci
    assert "Solan" in doc.text


def test_facebook_bez_raw_sklada_dokument_z_content():
    case = _load("casedb-examples/facebook_case.json")
    case.pop("raw")
    doc = case_to_document(case)
    assert doc.source == "facebook"
    assert doc.render_probe is None
    assert doc.title and doc.title in doc.text
    assert doc.publisher.display_name == "Virtune"


def test_facebook_raw_uzupelnia_transkrypcje_i_media_z_content_assets():
    case = _load("casedb-examples/facebook_case.json")
    case["raw"]["transcript"] = None
    case["content"]["transcript"] = [{"seq": 0, "body": "Pelna mowa", "engine": "whisper",
                                      "segments": [{"start": 0, "end": 2, "text": "Pelna mowa"}]}]
    case["assets"].append({"kind": "video", "uri": "s3://v/a.mp4", "extra": {"duration_s": 7.5}})
    doc = case_to_document(case)
    assert doc.transcript.engine == "whisper" and not is_partial(doc)
    assert [(m.kind, m.path, m.duration_s) for m in doc.media] == [("video", "s3://v/a.mp4", 7.5)]


def test_youtube_klipy_daja_czesciowa_transkrypcje():
    case = _load("casedb-examples/youtube_case.json")
    doc = case_to_document(case)
    assert doc.source == "youtube"
    assert doc.id == case["case_id"]
    # title + description w tej kolejnosci, oddzielone pustymi liniami
    assert doc.text == (
        case["content"]["title"][0]["body"] + "\n\n" + case["content"]["description"][0]["body"])
    assert doc.publisher.display_name == "Szybki Zysk TV"
    assert doc.publisher.handle == "UC_przyklad_01"
    assert is_partial(doc)
    assert doc.transcript.engine == "youtube-captions-clips:partial"
    assert [(s.start, s.end) for s in doc.transcript.segments] == [(12.0, 38.0), (95.0, 120.0)]
    assert doc.media == []  # asset "link" to nie plik


def test_youtube_pelne_napisy_z_raw_lista():
    case = _load("casedb-examples/youtube_case.json")
    case["raw"]["transcript"] = [{"text": "a", "start": 0.0, "duration": 2.0},
                                 {"text": "b", "start": 2.0, "duration": 3.0}]
    doc = case_to_document(case)
    assert doc.transcript.engine == "youtube-captions" and not is_partial(doc)
    assert doc.transcript.text == "a b"
    assert doc.transcript.segments[1].end == 5.0


def test_youtube_pelne_napisy_z_raw_dict_maja_priorytet_nad_klipami():
    case = _load("casedb-examples/youtube_case.json")
    case["raw"]["transcript"] = {"text": "calosc",
                                 "segments": [{"text": "calosc", "start": 0, "end": 9}]}
    doc = case_to_document(case)
    assert doc.transcript.text == "calosc" and not is_partial(doc)


def test_content_transcript_ma_priorytet_nad_raw():
    case = _load("casedb-examples/youtube_case.json")
    case["content"]["transcript"] = [{"seq": 0, "body": "z contentu",
                                      "segments": [{"start": 0, "end": 1, "text": "z contentu"}]}]
    case["raw"]["transcript"] = [{"text": "raw", "start": 0, "duration": 1}]
    assert case_to_document(case).transcript.text == "z contentu"


def test_brak_wszystkiego_nie_rzuca():
    doc = case_to_document({"case_id": "x", "source": "youtube", "url": "u"})
    assert doc.text == "" and doc.transcript is None and doc.media == []


def test_asset_audio_video_trafiaja_do_media():
    case = _load("casedb-examples/youtube_case.json")
    case["assets"] += [{"kind": "audio", "uri": "s3://a.mp3"},
                       {"kind": "screenshot", "uri": "s3://s.png"}]
    doc = case_to_document(case)
    assert [m.kind for m in doc.media] == ["audio"]


def test_finding_to_ai_result_ksztalt():
    doc = case_to_document(_load("casedb-examples/youtube_case.json"))
    finding = analyze(doc)
    ai = finding_to_ai_result(finding, model="m1")
    assert set(ai) == {"task", "model", "version", "label", "score", "result"}
    assert ai["task"] == TASK == "investwatch"
    assert ai["model"] == "m1"
    assert ai["label"] == finding.risk_level.value
    assert ai["score"] == finding.risk_score
    assert ai["result"]["document_id"] == doc.id
    json.dumps(ai)  # serializowalne


def test_wersja_stabilna_i_z_prefiksem():
    assert analyzer_version() == analyzer_version()
    assert analyzer_version().startswith("investwatch-")

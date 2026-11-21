"""E2E na prawdziwym audio (TTS pl-PL) i modelu Whisper. Pomijany bez zaleznosci."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from analyzer.contracts import AdDocument, MediaItem
from analyzer.rules_hybrid import assess_rule_3
from analyzer.stt import make_local_transcriber

WAV = Path(__file__).resolve().parents[1] / "fixtures" / "stt" / "ad_pl_risk_late.wav"


def _model_ready() -> bool:
    try:
        from faster_whisper import WhisperModel

        WhisperModel("small", device="cpu", compute_type="int8", local_files_only=True)
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not WAV.is_file() or not _model_ready(),
    reason="brak faster-whisper, modelu small w cache HF albo pliku fixtures/stt",
)


def test_real_speech_to_rule_3(tmp_path):
    doc = AdDocument(
        id="e2e", source="facebook", url="https://example.invalid/e2e",
        fetched_at=datetime.now(timezone.utc),
        media=[MediaItem(kind="audio", path=str(WAV))],
    )
    tr = make_local_transcriber(tmp_path, model_size="small")(doc)
    assert tr is not None and tr.engine == "faster-whisper:small"
    assert "ryzyk" in tr.text.lower()
    doc.transcript = tr
    res = assess_rule_3(doc)
    assert res.verdict.value in ("fail", "pass")

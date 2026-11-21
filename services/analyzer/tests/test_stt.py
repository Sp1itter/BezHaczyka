"""Testy warstwy STT — bez faster-whisper, z wstrzyknietym transkrybentem."""

from __future__ import annotations

import pytest

from analyzer.contracts import Transcript, TranscriptSegment
from analyzer.stt import (
    RiskTiming,
    SttError,
    normalize_text,
    rate_anomaly,
    risk_timing,
    speech_rate,
    transcribe,
)


def _tr(*rows: tuple[float, float, str]) -> Transcript:
    segs = [TranscriptSegment(start=s, end=e, text=t) for s, e, t in rows]
    return Transcript(engine="t", text=" ".join(r[2] for r in rows), segments=segs)


# --- transcribe ---------------------------------------------------------------


def test_transcribe_with_injected_transcriber():
    calls = []

    def fake(path):
        calls.append(path)
        return [(0.0, 2.0, " Cześć "), (2.0, 4.0, "świat")]

    t = transcribe("a.wav", transcriber=fake)
    assert calls == ["a.wav"]
    assert t.text == "Cześć świat"
    assert [s.text for s in t.segments] == ["Cześć", "świat"]
    assert t.lang == "pl"


def test_transcribe_skips_empty_segments():
    t = transcribe("a.wav", transcriber=lambda p: [(0, 1, "  "), (1, 2, "ok")])
    assert len(t.segments) == 1


def test_transcribe_empty_result():
    t = transcribe("a.wav", transcriber=lambda p: [])
    assert t.text == "" and t.segments == []


def test_transcribe_wraps_errors():
    def boom(path):
        raise ValueError("zly plik")

    with pytest.raises(SttError):
        transcribe("a.wav", transcriber=boom)


def test_transcribe_passes_through_stt_error():
    def boom(path):
        raise SttError("x")

    with pytest.raises(SttError):
        transcribe("a.wav", transcriber=boom)


def test_transcribe_without_library_raises_stt_error():
    try:
        import faster_whisper  # noqa: F401
    except ImportError:
        with pytest.raises(SttError):
            transcribe("a.wav")
    else:
        pytest.skip("faster-whisper zainstalowany")


def test_stt_error_is_runtime_error():
    assert issubclass(SttError, RuntimeError)


# --- normalize ----------------------------------------------------------------


def test_normalize_strips_diacritics():
    assert normalize_text("ŁÓDŹ Zażółć") == "lodz zazolc"


# --- risk_timing --------------------------------------------------------------


def test_risk_timing_empty_transcript():
    assert risk_timing(Transcript(engine="t", text="")) is None


def test_risk_timing_zero_duration():
    assert risk_timing(_tr((0.0, 0.0, "zysk"))) is None


def test_risk_timing_single_segment():
    r = risk_timing(_tr((0, 10, "Zysk i ryzyko")))
    assert r.first_profit_claim_s == 0 and r.first_risk_warning_s == 0
    assert r.gap_s == 0


def test_risk_timing_late_warning():
    t = _tr(
        (5.0, 8.0, "Zyskaj nawet 20% rocznie!"),
        (8.0, 33.0, "Dołącz do nas."),
        (33.8, 34.2, "Inwestowanie wiąże się z ryzykiem."),
    )
    r = risk_timing(t)
    assert isinstance(r, RiskTiming)
    assert r.first_profit_claim_s == 5.0
    assert r.first_risk_warning_s == 33.8
    assert r.gap_s == pytest.approx(28.8)
    assert r.risk_at_fraction == pytest.approx(33.8 / 34.2)
    assert r.total_duration_s == 34.2


def test_risk_timing_no_profit_claims():
    r = risk_timing(_tr((0, 5, "Witamy"), (5, 10, "Uwaga na ryzyko")))
    assert r.first_profit_claim_s is None
    assert r.gap_s is None
    assert r.first_risk_warning_s == 5


def test_risk_timing_no_risk_warning():
    r = risk_timing(_tr((0, 5, "Zarabiaj codziennie"), (5, 10, "Zapisz się")))
    assert r.first_risk_warning_s is None
    assert r.gap_s is None and r.risk_at_fraction is None
    assert r.first_profit_claim_s == 0


def test_risk_timing_warning_fraction_and_clamp():
    r = risk_timing(_tr((0, 5, "zysk"), (5, 10, "ryzyko")))
    assert r.risk_at_fraction == pytest.approx(0.5)
    r2 = risk_timing(_tr((0, 5, "zysk"), (5, 10, "x"), (10, 10, "ryzyko")))
    assert r2.risk_at_fraction == 1.0


def test_risk_before_profit_gives_negative_gap():
    r = risk_timing(_tr((0, 3, "ryzyko straty"), (3, 6, "zysk")))
    assert r.gap_s == -3


def test_risk_timing_polish_inflection():
    for phrase in ("zyskiem", "zyskownych", "zarabiasz", "zarabiają", "stopę zwrotu", "stopa zwrotu"):
        r = risk_timing(_tr((0, 2, phrase), (2, 4, "x")))
        assert r.first_profit_claim_s == 0, phrase
    for phrase in ("ryzykiem", "ryzykowne", "stratę kapitału", "możesz stracić pieniądze"):
        r = risk_timing(_tr((0, 2, phrase), (2, 4, "x")))
        assert r.first_risk_warning_s == 0, phrase


def test_risk_timing_custom_patterns():
    r = risk_timing(
        _tr((0, 2, "bitcoin"), (2, 4, "uwaga")),
        profit_patterns=[r"bitcoin"],
        risk_patterns=[r"uwaga"],
    )
    assert r.first_profit_claim_s == 0 and r.first_risk_warning_s == 2


def test_risk_timing_takes_earliest_match():
    r = risk_timing(_tr((4, 6, "ryzyko"), (0, 2, "ryzyko"), (2, 4, "x")))
    assert r.first_risk_warning_s == 0


# --- speech_rate / rate_anomaly -----------------------------------------------


def test_speech_rate_basic():
    assert speech_rate(TranscriptSegment(start=0, end=2, text="abcd")) == 2.0


def test_speech_rate_zero_duration_no_crash():
    assert speech_rate(TranscriptSegment(start=1, end=1, text="abc")) > 0
    assert speech_rate(TranscriptSegment(start=1, end=1, text="")) == 0


def test_rate_anomaly_too_few_segments():
    t = _tr((0, 1, "aaaa"), (1, 2, "bbbb"))
    assert rate_anomaly(t, t.segments[0]) is None
    empty = Transcript(engine="t", text="")
    assert rate_anomaly(empty, TranscriptSegment(start=0, end=1, text="a")) is None


def test_rate_anomaly_fast_disclaimer():
    t = _tr((0, 10, "a" * 100), (10, 20, "a" * 100), (20, 25, "a" * 100))
    assert rate_anomaly(t, t.segments[2]) == pytest.approx(2.0)
    assert rate_anomaly(t, t.segments[0]) == pytest.approx(10 / 15)


def test_rate_anomaly_single_segment():
    t = _tr((0, 1, "abc"))
    assert rate_anomaly(t, t.segments[0]) is None


def test_rate_anomaly_zero_median():
    t = _tr((0, 1, ""), (1, 2, ""), (2, 3, "abc"))
    assert rate_anomaly(t, t.segments[2]) is None

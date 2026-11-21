"""Kompletnosc materialu — czy wolno wnioskowac z BRAKU czegos w tekscie.

Scraper YouTube oddaje tylko do 2 fragmentow napisow po <= 30 s (klipy wokol
trafien slownika), a nie cala transkrypcje. Brak ostrzezenia o ryzyku w takim
klipie NIE dowodzi, ze ostrzezenia nie ma w filmie. Wniosek "czegos brakuje"
wolno wyciagac tylko z materialu kompletnego.

Kontrakt `Transcript` jest zamrozony, wiec czesciowosc oznaczamy sufiksem
w polu `engine`, np. "youtube-captions-clips:partial".
"""

from __future__ import annotations

from analyzer.contracts import AdDocument, Transcript

PARTIAL_SUFFIX = ":partial"


def mark_partial(engine: str) -> str:
    """Nazwa silnika z oznaczeniem transkrypcji czesciowej (idempotentne)."""
    return engine if engine.endswith(PARTIAL_SUFFIX) else engine + PARTIAL_SUFFIX


def is_partial_transcript(transcript: Transcript | None) -> bool:
    return transcript is not None and transcript.engine.endswith(PARTIAL_SUFFIX)


def is_partial(doc: AdDocument) -> bool:
    """Czy material jest znany tylko we fragmentach."""
    return is_partial_transcript(doc.transcript)

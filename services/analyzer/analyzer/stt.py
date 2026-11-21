"""Warstwa speech-to-text: transkrypcja reklam wideo + os czasu dla reguly 3.

Decyzje projektowe:
- faster-whisper dziala WYLACZNIE na CPU (int8). GPU (8 GB VRAM) jest
  zarezerwowane dla modelu Bielik; Whisper na CPU w pelni wystarcza dla
  30-sekundowych reklam.
- Biblioteka jest importowana LENIWIE, wewnatrz funkcji. Import tego modulu
  dziala bez niej, a testy uzywaja wstrzyknietego `transcriber`.
- Brak danych nigdy nie jest naruszeniem: funkcje zwracaja None albo
  podnosza `SttError` (wolajacy zamienia to na not_applicable).
- Wszystko lokalnie, bez zewnetrznych API.
"""

from __future__ import annotations

import os
import re
import statistics
import tempfile
from pathlib import Path
import unicodedata
from dataclasses import dataclass
from typing import Callable, Iterable, Sequence

from .contracts import AdDocument, Transcript, TranscriptSegment
from .media_fetch import resolve_media

DEFAULT_WHISPER_MODEL = "small"

# Wzorce regex na tekscie znormalizowanym (male litery, bez ogonkow).
# Polski jest fleksyjny, wiec dopasowujemy rdzenie z koncowkami, nie literaly.
DEFAULT_PROFIT_PATTERNS: tuple[str, ...] = (
    r"\bzysk\w*",
    r"\bzarabia\w*",
    r"\bzarob\w*",
    r"\bstop\w*\s+zwrotu",
    # Zawezone do form rzeczownikowych i przymiotnikowych. `dochod\w*` lapalo
    # "dochodzi", "dochodzenie roszczen", "dochodzi swoich praw" — zwroty, ktore
    # w reklamie nie sa obietnica zysku, a dawaly falszywy punkt na osi czasu.
    r"\bdochod(y|u|em|ow|ach|ami|owy|owa|owe|owych|owego)?\b",
)
DEFAULT_RISK_PATTERNS: tuple[str, ...] = (
    r"\bryzyk\w*",
    r"\bstrat\w*\s+kapitalu",
    r"\bmozesz\s+stracic",
    r"\bmozliw\w*\s+strat\w*",
)

# Transkrybent: sciezka -> lista (start, end, tekst).
Transcriber = Callable[[str], Iterable[tuple[float, float, str]]]


class SttError(RuntimeError):
    """Transkrypcja niemozliwa (brak biblioteki, uszkodzony plik, blad modelu).

    Wolajacy MUSI zamienic to na not_applicable - brak transkrypcji nie jest
    dowodem naruszenia.
    """


@dataclass(frozen=True)
class RiskTiming:
    """Polozenie na osi czasu pierwszego twierdzenia o zysku i ostrzezenia o ryzyku.

    gap_s = first_risk_warning_s - first_profit_claim_s; wartosc ujemna oznacza,
    ze ostrzezenie pada PRZED twierdzeniem o zysku.
    """

    first_profit_claim_s: float | None
    first_risk_warning_s: float | None
    gap_s: float | None
    risk_at_fraction: float | None
    total_duration_s: float


def normalize_text(text: str) -> str:
    """Male litery i brak ogonkow (l z kreska nie rozklada sie w NFKD)."""
    lowered = text.lower().replace(chr(0x142), "l")
    decomposed = unicodedata.normalize("NFKD", lowered)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def _default_transcriber(model_size: str) -> Transcriber:
    try:
        from faster_whisper import WhisperModel  # import leniwy
    except ImportError as exc:
        raise SttError("faster-whisper nie jest zainstalowany") from exc

    def run(path: str) -> list[tuple[float, float, str]]:
        try:
            model = WhisperModel(model_size, device="cpu", compute_type="int8")
            segments, _info = model.transcribe(path, language="pl")
            return [(float(s.start), float(s.end), s.text) for s in segments]
        except Exception as exc:  # biblioteka rzuca roznymi typami
            raise SttError(f"transkrypcja nieudana: {exc}") from exc

    return run


def transcribe(
    audio_path: str,
    *,
    model_size: str | None = None,
    transcriber: Transcriber | None = None,
) -> Transcript:
    """Transkrybuje plik audio do `Transcript` z segmentami czasowymi."""
    if transcriber is None:
        size = model_size or os.getenv("WHISPER_MODEL", DEFAULT_WHISPER_MODEL)
        transcriber = _default_transcriber(size)
        engine = f"faster-whisper:{size}"
    else:
        engine = "injected"
    try:
        raw = list(transcriber(str(audio_path)))
    except SttError:
        raise
    except Exception as exc:
        raise SttError(f"transkrypcja nieudana: {exc}") from exc

    segments = [
        TranscriptSegment(start=float(s), end=float(e), text=t.strip())
        for s, e, t in raw
        if t and t.strip()
    ]
    return Transcript(
        engine=engine,
        lang="pl",
        text=" ".join(seg.text for seg in segments),
        segments=segments,
    )


def _first_match_start(
    segments: Sequence[TranscriptSegment], patterns: Sequence[str]
) -> float | None:
    compiled = [re.compile(p) for p in patterns]
    starts = [
        seg.start
        for seg in segments
        if any(rx.search(normalize_text(seg.text)) for rx in compiled)
    ]
    return min(starts) if starts else None


def risk_timing(
    transcript: Transcript,
    *,
    profit_patterns: Sequence[str] | None = None,
    risk_patterns: Sequence[str] | None = None,
) -> RiskTiming | None:
    """Regula 3 na osi czasu. None, gdy nie ma segmentow albo dlugosci materialu."""
    segments = transcript.segments
    if not segments:
        return None
    total = max(seg.end for seg in segments)
    if total <= 0:
        return None

    profit = _first_match_start(
        segments, DEFAULT_PROFIT_PATTERNS if profit_patterns is None else profit_patterns
    )
    risk = _first_match_start(
        segments, DEFAULT_RISK_PATTERNS if risk_patterns is None else risk_patterns
    )
    gap = risk - profit if profit is not None and risk is not None else None
    fraction = min(max(risk / total, 0.0), 1.0) if risk is not None else None
    return RiskTiming(
        first_profit_claim_s=profit,
        first_risk_warning_s=risk,
        gap_s=gap,
        risk_at_fraction=fraction,
        total_duration_s=total,
    )


def speech_rate(segment: TranscriptSegment) -> float:
    """Tempo mowy w znakach na sekunde (zerowa dlugosc zabezpieczona)."""
    return len(segment.text) / max(segment.end - segment.start, 1e-6)


def rate_anomaly(transcript: Transcript, segment: TranscriptSegment) -> float | None:
    """Iloraz tempa segmentu do mediany tempa pozostalych segmentow.

    None, gdy segmentow jest mniej niz 3 albo mediana wynosi zero.
    """
    segments = transcript.segments
    if len(segments) < 3:
        return None
    others = [speech_rate(s) for s in segments if s is not segment]
    if not others:
        return None
    median = statistics.median(others)
    if median <= 0:
        return None
    return speech_rate(segment) / median


# --------------------------------------------------------------------------- #
# Wpiecie w potok: producent transkryptu dla AdDocument
# --------------------------------------------------------------------------- #

# Korpus scrapera: fixtures/demo-ads/facebook/<ad_archive_id>/video.mp4
# Pliki mp4 sa w .gitignore (ok. 29 MB samych page.html, wideo znacznie wiecej),
# wiec leza TYLKO na maszynie, ktora je nagrala.
DEFAULT_MEDIA_NAMES = ("video.mp4", "audio.wav", "audio.m4a")

_AD_ID_RE = re.compile(r"[?&]id=(\d+)")


def ad_archive_id(doc: AdDocument) -> str | None:
    """Identyfikator reklamy z kanonicznego URL-a Meta Ad Library.

    UWAGA: `doc.id` to UUID nadany przez scraper, NIE ad_archive_id. Katalogi
    korpusu sa nazwane ad_archive_id, wiec bez tego wyciagania nie trafimy
    w pliki na dysku.
    """
    m = _AD_ID_RE.search(doc.url or "")
    return m.group(1) if m else None


def resolve_media_path(doc: AdDocument, root: Path) -> Path | None:
    """Znajdz lokalny plik audio/wideo dla dokumentu. None, gdy go nie ma.

    Dwie sciezki, w tej kolejnosci:
      1. `media[].path` wskazuje istniejacy plik lokalny,
      2. katalog korpusu <root>/<ad_archive_id>/ zawiera jeden ze znanych plikow.

    Sciezek `s3://` NIE rozwiazujemy tutaj — pobranie z SeaweedFS nalezy do
    wolajacego, bo wymaga klienta S3 i nie powinno siedziec w warstwie STT.
    """
    for item in doc.media:
        if item.kind not in ("video", "audio"):
            continue
        if item.path and not item.path.startswith("s3://"):
            p = Path(item.path)
            if p.is_file():
                return p

    ad_id = ad_archive_id(doc)
    if ad_id is None:
        return None
    for name in DEFAULT_MEDIA_NAMES:
        p = root / ad_id / name
        if p.is_file():
            return p
    return None


def make_local_transcriber(
    root: Path | str, *, model_size: str | None = None
) -> Callable[[AdDocument], Transcript | None]:
    """Producent transkryptu do podania w AnalyzerConfig.transcriber.

    Szuka pliku na dysku pod `root` i transkrybuje go lokalnie (CPU, int8).
    Zwraca None, gdy pliku nie ma — brak mediow nie jest bledem, tylko
    informacja, ze tej reklamy nie da sie ocenic na osi czasu.

    Uzycie:
        from analyzer.stt import make_local_transcriber
        cfg = build_config(client, transcriber=make_local_transcriber(
            "fixtures/demo-ads/facebook"))
    """
    base = Path(root)
    cache = Path(os.getenv("STT_MEDIA_CACHE") or Path(tempfile.gettempdir()) / "investwatch-media")

    def _transcribe(doc: AdDocument) -> Transcript | None:
        # 1. media[] dokumentu (sciezka, http(s), s3://) przez media_fetch
        path: Path | None = None
        for item in doc.media:
            if item.kind in ("video", "audio") and item.path:
                path = resolve_media(item.path, cache)
                if path is not None:
                    break
        # 2. stara sciezka: korpus pod root po ad_archive_id
        if path is None:
            path = resolve_media_path(doc, base)
        if path is None:
            return None
        return transcribe(str(path), model_size=model_size)

    return _transcribe

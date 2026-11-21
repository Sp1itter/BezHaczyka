"""Adapter wspolnej bazy przypadkow (casedb) <-> potok analizy.

case_to_document: eksport casedb -> AdDocument.
finding_to_ai_result: Finding -> wiersz ai_results.

NIE importujemy pakietu casedb (osobny serwis); znamy tylko ksztalt eksportu:
{case_id, source, url, status, metadata, content{kind:[...]}, assets[], ai_results, raw?}.
Zasada: brak danych -> pole puste / transkrypcja czesciowa, nigdy wyjatek.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from analyzer.completeness import mark_partial
from analyzer.contracts import (
    AdDocument,
    Finding,
    MediaItem,
    Publisher,
    Transcript,
    TranscriptSegment,
)
from analyzer.llm import DEFAULT_MODEL

TASK = "investwatch"

_PKG = Path(__file__).resolve().parent
_VERSION_FILES = ("prompts/*.txt", "config/thresholds.yaml")


def _parse_dt(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _bodies(case: dict, kind: str) -> list[dict]:
    items = (case.get("content") or {}).get(kind) or []
    return sorted(items, key=lambda i: i.get("seq", 0))


def _segments(items: Any) -> list[TranscriptSegment]:
    out: list[TranscriptSegment] = []
    for s in items or []:
        if not isinstance(s, dict) or not (s.get("text") or "").strip():
            continue
        start = s.get("start", s.get("start_s"))
        if start is None:
            continue
        end = s.get("end", s.get("end_s"))
        if end is None:
            end = float(start) + float(s.get("duration") or 0)
        out.append(TranscriptSegment(start=float(start), end=float(end), text=s["text"]))
    return out


def _transcript_from_case(case: dict, lang: str) -> Transcript | None:
    # (a) content.transcript z extra.segments -> pelny
    for item in _bodies(case, "transcript"):
        segs = _segments(item.get("segments"))
        text = item.get("body") or " ".join(s.text for s in segs)
        if text or segs:
            return Transcript(engine=item.get("engine") or "casedb", lang=lang,
                              text=text, segments=segs)
    # (b) raw["transcript"]: lista {text,start,duration} albo dict {text, segments}
    raw_tr = (case.get("raw") or {}).get("transcript")
    if isinstance(raw_tr, list) and raw_tr:
        segs = _segments(raw_tr)
        if segs:
            return Transcript(engine="youtube-captions", lang=lang,
                              text=" ".join(s.text for s in segs), segments=segs)
    elif isinstance(raw_tr, dict) and (raw_tr.get("text") or raw_tr.get("segments")):
        segs = _segments(raw_tr.get("segments"))
        text = raw_tr.get("text") or " ".join(s.text for s in segs)
        return Transcript(engine=raw_tr.get("engine") or "youtube-captions", lang=lang,
                          text=text, segments=segs)
    # (c) klipy (scraper YT oddaje tylko do 2 fragmentow <= 30 s) -> CZESCIOWA
    clips = [c for c in _bodies(case, "clip") if (c.get("body") or "").strip()]
    if clips:
        segs = [
            TranscriptSegment(start=float(c.get("start_s") or 0.0),
                              end=float(c.get("end_s") or c.get("start_s") or 0.0),
                              text=c["body"])
            for c in clips
        ]
        return Transcript(engine=mark_partial("youtube-captions-clips"), lang=lang,
                          text="\n".join(s.text for s in segs), segments=segs)
    return None


def _media_from_assets(case: dict) -> list[MediaItem]:
    media: list[MediaItem] = []
    for a in case.get("assets") or []:
        if a.get("kind") not in ("video", "audio") or not a.get("uri"):
            continue  # "link" do strony YouTube to nie plik
        dur = (a.get("extra") or {}).get("duration_s")
        media.append(MediaItem(kind=a["kind"], path=a["uri"], duration_s=dur))
    return media


def case_to_document(case: dict) -> AdDocument:
    """Eksport casedb (najlepiej z include_raw) -> AdDocument."""
    source = case.get("source") or "www"
    raw = case.get("raw")
    meta = case.get("metadata") or {}
    lang = meta.get("lang") or (raw or {}).get("lang") or "pl"

    if source in ("facebook", "www") and isinstance(raw, dict) and all(
        raw.get(k) for k in ("id", "url")
    ) and "text" in raw:
        try:
            doc = AdDocument.model_validate(raw)
        except ValidationError:
            doc = None
        if doc is not None:
            if doc.transcript is None:
                doc.transcript = _transcript_from_case(case, doc.lang)
            if not doc.media:
                doc.media = _media_from_assets(case)
            return doc

    parts = []
    for kind in ("title", "description", "text"):
        for item in _bodies(case, kind):
            if (item.get("body") or "").strip():
                parts.append(item["body"].strip())
    title = meta.get("title") or next(
        (i["body"] for i in _bodies(case, "title") if i.get("body")), None)
    fetched = _parse_dt(meta.get("fetched_at")) or _parse_dt(meta.get("published_at")) \
        or datetime.now(timezone.utc)
    if fetched.tzinfo is None:
        fetched = fetched.replace(tzinfo=timezone.utc)

    # contracts.AdDocument.source to zwykly str (bez Literal) - "youtube" przechodzi wprost.
    return AdDocument(
        id=case["case_id"],
        source=source,
        url=case.get("url") or "",
        fetched_at=fetched,
        publisher=Publisher(
            handle=meta.get("author_id"),
            display_name=meta.get("author_name"),
            profile_url=meta.get("author_url"),
        ),
        lang=lang,
        title=title,
        text="\n\n".join(parts),
        media=_media_from_assets(case),
        transcript=_transcript_from_case(case, lang),
    )


@lru_cache(maxsize=1)
def analyzer_version() -> str:
    """Wersja analizy = skrot tresci promptow i progow (zmiana promptu = nowy wiersz).

    Brama idempotencji (change_detect.should_analyze) opiera sie na simhashu
    tresci i nie ma wersji, wiec wersje wyliczamy tu, deterministycznie.
    """
    h = hashlib.sha256()
    for pattern in _VERSION_FILES:
        for p in sorted(_PKG.glob(pattern)):
            h.update(p.name.encode())
            h.update(p.read_bytes())
    return "investwatch-" + h.hexdigest()[:12]


def finding_to_ai_result(finding: Finding, model: str | None = None,
                         version: str | None = None) -> dict:
    """Finding -> {task, model, version, label, score, result} dla ai_results."""
    return {
        "task": TASK,
        "model": model or DEFAULT_MODEL,
        "version": version or analyzer_version(),
        "label": finding.risk_level.value if hasattr(finding.risk_level, "value")
        else str(finding.risk_level),
        "score": finding.risk_score,
        "result": finding.model_dump(mode="json"),
    }

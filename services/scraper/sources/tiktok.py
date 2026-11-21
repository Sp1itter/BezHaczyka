"""TikTokSource — szkielet zrodla, domyslnie WYLACZONY (schedule.yaml: enabled: false).

Dziala wylacznie na fixture'ach (`fixtures/demo-ads/tiktok/<id>.json`). Pokazuje, ile kodu
potrzeba na nowe zrodlo: `discover` + `fetch` -> AdDocument, reszta (kolejki, dedup,
resolver, zapis do bazy, analyzer) jest wspolna. Tryb live nie jest zaimplementowany.

Konfiguracja z env: TIKTOK_MODE=replay (jedyny obslugiwany), TIKTOK_FIXTURES_DIR.
"""

from __future__ import annotations

import json
import os
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path

from contracts import AdDocument, Publisher, Transcript, TranscriptSegment

from sources.base import SourceError, SourceGone

DEFAULT_FIXTURES = Path(__file__).resolve().parents[3] / "fixtures" / "demo-ads" / "tiktok"
BASE = "https://www.tiktok.com"
_VIDEO_URL = re.compile(r"^https://(?:www\.)?tiktok\.com/@[\w.\-]+/video/(\d+)")


def video_url(handle: str, video_id: str) -> str:
    return f"{BASE}/@{handle}/video/{video_id}"


def video_id(url: str) -> str | None:
    match = _VIDEO_URL.match(url)
    return match.group(1) if match else None


class TikTokSource:
    name = "tiktok"

    def __init__(self, fixtures_dir: Path = DEFAULT_FIXTURES, mode: str = "replay") -> None:
        if mode != "replay":
            raise SourceError(f"TikTokSource: tryb {mode!r} nie jest zaimplementowany (tylko replay)")
        self.fixtures_dir = Path(fixtures_dir)

    @classmethod
    def from_env(cls) -> TikTokSource:
        return cls(Path(os.getenv("TIKTOK_FIXTURES_DIR", str(DEFAULT_FIXTURES))),
                   os.getenv("TIKTOK_MODE", "replay"))

    def _items(self) -> list[dict]:
        return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(self.fixtures_dir.glob("*.json"))]

    def discover(self, query: str) -> list[str]:
        """URL-e filmow, ktorych opis zawiera fraze (pusta fraza: wszystkie)."""
        q = query.casefold().strip()
        return [video_url(i["author"]["unique_id"], i["id"]) for i in self._items()
                if not q or q in i.get("desc", "").casefold()]

    def fetch(self, url: str) -> AdDocument:
        vid = video_id(url)
        if vid is None:
            raise SourceError(f"to nie jest URL filmu TikTok: {url}")
        path = self.fixtures_dir / f"{vid}.json"
        if not path.is_file():
            raise SourceGone(f"brak filmu {vid}")
        item = json.loads(path.read_text(encoding="utf-8"))
        handle = item["author"]["unique_id"]
        canonical = video_url(handle, vid)
        segments = [TranscriptSegment(start=s["start"], end=s["end"], text=s["text"])
                    for s in item.get("subtitles") or []]
        transcript = (Transcript(engine="tiktok-subtitles", lang=item.get("lang", "pl"),
                                 text=" ".join(s.text for s in segments), segments=segments)
                      if segments else None)
        text = "\n\n".join(p for p in [item.get("desc", ""), "\n".join(item.get("links") or [])] if p)
        return AdDocument(
            id=str(uuid.uuid5(uuid.NAMESPACE_URL, canonical)),
            source=self.name,
            url=canonical,
            fetched_at=datetime.now(UTC),
            publisher=Publisher(handle=f"@{handle}", display_name=item["author"].get("nickname"),
                                profile_url=f"{BASE}/@{handle}"),
            lang=item.get("lang", "pl"),
            text=text,
            transcript=transcript,
        )

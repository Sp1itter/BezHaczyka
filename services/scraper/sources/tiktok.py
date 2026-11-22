"""TikTok: filmy organiczne (finfluencerzy).

TIKTOK_MODE=replay  TikTokSource — fixture'y `fixtures/demo-ads/tiktok/<id>.json` (offline/demo).
TIKTOK_MODE=live    (domyslnie) LiveTikTokSource — odkrywanie wyszukiwarka (ddgs, `site:tiktok.com <fraza>`,
                    bo ekstraktor tagow yt-dlp jest oznaczony jako zepsuty), pobranie metadanych
                    i napisow przez yt-dlp, wideo (<= TIKTOK_VIDEO_MAX_MB) do S3 dla Whispera.

Reklamy z TikTok Ad Library (library.tiktok.com) NIE sa pobierane: publiczne API wyszukiwania
odpowiada 421 "system busy" takze prawdziwej przegladarce (ochrona przed automatami), a jej
obchodzenie jest poza zasadami projektu. Legalna droga: oficjalne Commercial Content API
(wymaga rejestracji aplikacji) — patrz SOURCES.md.
"""

from __future__ import annotations

import json
import os
import re
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from contracts import AdDocument, MediaItem, Publisher, Transcript, TranscriptSegment

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
    def from_env(cls) -> Any:
        mode = os.getenv("TIKTOK_MODE", "live")
        if mode == "live":
            from storage import blob_store_from_env

            return LiveTikTokSource(store=blob_store_from_env(),
                                    video_max_mb=int(os.getenv("TIKTOK_VIDEO_MAX_MB", "30")))
        return cls(Path(os.getenv("TIKTOK_FIXTURES_DIR", str(DEFAULT_FIXTURES))), mode)

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


# --------------------------------------------------------------------------- #
# Tryb live
# --------------------------------------------------------------------------- #

def _vtt_seconds(stamp: str) -> float:
    parts = stamp.replace(",", ".").split(":")
    return sum(float(p) * 60 ** i for i, p in enumerate(reversed(parts)))


def segments_from_vtt(body: str) -> list[TranscriptSegment]:
    """WEBVTT -> segmenty (bez znacznikow i duplikatow kolejnych linii)."""
    out: list[TranscriptSegment] = []
    for block in re.split(r"\n\s*\n", body.replace("\r", "")):
        lines = [ln.strip() for ln in block.strip().split("\n") if ln.strip()]
        arrow = next((i for i, ln in enumerate(lines) if "-->" in ln), None)
        if arrow is None:
            continue
        start, end = (x.strip().split(" ")[0] for x in lines[arrow].split("-->"))
        text = re.sub(r"<[^>]+>", "", " ".join(lines[arrow + 1:])).strip()
        if text and (not out or out[-1].text != text):
            out.append(TranscriptSegment(start=_vtt_seconds(start), end=_vtt_seconds(end), text=text))
    return out


def _ydl_extract(url: str) -> dict:
    import yt_dlp
    from yt_dlp.utils import DownloadError

    try:
        with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True, "noplaylist": True,
                               "socket_timeout": 15, "retries": 1}) as client:
            return client.extract_info(url, download=False) or {}
    except DownloadError as exc:
        msg = str(exc).lower()
        if any(w in msg for w in ("not available", "removed", "private", "404", "does not exist")):
            raise SourceGone(f"film TikTok niedostepny: {url}") from exc
        raise SourceError(f"yt-dlp TikTok: {url}: {exc}") from exc


def _download_text(url: str) -> str:
    import yt_dlp

    with yt_dlp.YoutubeDL({"quiet": True}) as client:
        return client.urlopen(url).read().decode("utf-8", "replace")


def _download_video(url: str, max_bytes: int) -> bytes | None:
    import tempfile

    import yt_dlp

    with tempfile.TemporaryDirectory() as tmp:
        try:
            with yt_dlp.YoutubeDL({"quiet": True, "noplaylist": True, "outtmpl": f"{tmp}/%(id)s.%(ext)s",
                                   "format": "worst[ext=mp4]/worst/best", "max_filesize": max_bytes,
                                   "noprogress": True}) as client:
                client.extract_info(url, download=True)
        except Exception:  # noqa: BLE001 — brak wideo nie blokuje oceny opisu
            return None
        files = sorted(Path(tmp).iterdir())
        return files[0].read_bytes() if files else None


class LiveTikTokSource:
    name = "tiktok"

    def __init__(
        self,
        *,
        store: Any = None,
        search: Callable[[str, int], list[str]] | None = None,
        extract: Callable[[str], dict] = _ydl_extract,
        download_text: Callable[[str], str] = _download_text,
        download_video: Callable[[str], bytes | None] | None = None,
        results_per_query: int = 25,
        video_max_mb: int = 30,
        language: str = "pl",
        suffixes: tuple[str, ...] = ("", "porady"),
    ) -> None:
        if search is None:
            from sources.www_live import ddgs_search

            search = ddgs_search
        self.store = store
        self.search = search
        self.extract = extract
        self.download_text = download_text
        self.download_video = download_video or (lambda url: _download_video(url, video_max_mb * 1024 * 1024))
        self.results_per_query = results_per_query
        self.language = language
        self.suffixes = suffixes or ("",)
        self.last_meta: dict[str, Any] = {}

    def discover(self, query: str) -> list[str]:
        base = query if "tiktok.com" in query else f"site:tiktok.com {query}"
        found: list[str] = []
        errors = []
        for suffix in self.suffixes:  # warianty: ~10 wynikow wyszukiwarki na zapytanie
            try:
                found += self.search(f"{base} {suffix}".strip(), self.results_per_query)
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)
        if errors and not found:
            raise SourceError(f"wyszukiwarka TikTok: {query!r}: {errors[0]}") from errors[0]
        urls: dict[str, None] = {}
        for url in found:
            m = re.match(r"^https://(?:www\.)?tiktok\.com/@([\w.\-]+)/video/(\d+)", url)
            if m:
                urls.setdefault(video_url(m.group(1), m.group(2)))
        return list(urls)

    def _subtitles(self, info: dict) -> list[TranscriptSegment]:
        subs = info.get("subtitles") or {}
        prefixes = (self.language, "pol")  # TikTok: "pol-PL"
        lang = next((k for k in subs if k.lower().startswith(prefixes)), None)
        track = next((t for t in subs.get(lang) or [] if t.get("url")), None) if lang else None
        if not track:
            return []
        try:
            return segments_from_vtt(self.download_text(track["url"]))
        except Exception:  # noqa: BLE001
            return []

    def fetch(self, url: str) -> AdDocument:
        vid = video_id(url)
        if vid is None:
            raise SourceError(f"to nie jest URL filmu TikTok: {url}")
        info = self.extract(url)
        if not info:
            raise SourceError(f"brak metadanych TikTok: {url}")
        handle = (info.get("uploader") or info.get("uploader_id") or url.split("/@")[1].split("/")[0]).lstrip("@")
        canonical = video_url(handle, vid)
        doc_id = str(uuid.uuid5(uuid.NAMESPACE_URL, canonical))
        segments = self._subtitles(info)
        transcript = (Transcript(engine="tiktok-subtitles", lang=self.language,
                                 text=" ".join(s.text for s in segments), segments=segments)
                      if segments else None)
        from sources.www_live import _CANDIDATE_RE

        description = info.get("description") or ""
        # Kwalifikacja: tylko filmy o finansach ida do analizy (i tylko dla nich pobieramy wideo).
        financial = bool(_CANDIDATE_RE.search(description + " " + " ".join(s.text for s in segments)))
        media: list[MediaItem] = []
        if self.store is not None and financial:
            data = self.download_video(canonical)
            if data:
                path = self.store.put("media", f"{doc_id}.mp4", data, "video/mp4")
                media = [MediaItem(kind="video", path=path, duration_s=info.get("duration"))]
        self.last_meta = {"qualified": financial, "transcript_source": "subtitles" if segments else ("video-for-whisper" if media else "none"),
                          "views": info.get("view_count"), "likes": info.get("like_count")}
        title = (info.get("title") or "").strip() or None
        return AdDocument(
            id=doc_id,
            source=self.name,
            url=canonical,
            fetched_at=datetime.now(UTC),
            publisher=Publisher(handle=f"@{handle}", display_name=info.get("channel") or info.get("creator"),
                                profile_url=f"{BASE}/@{handle}"),
            lang=self.language,
            title=title,
            text=info.get("description") or title or "",
            transcript=transcript,
            media=media,
        )

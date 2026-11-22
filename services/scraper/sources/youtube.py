"""YouTubeSource — filmy z YouTube: metadane (yt-dlp) + napisy (youtube-transcript-api).

Kwalifikacja promocji: konkretna firma/domena ze slownika (nigdy samo haslo) i sygnal
promocji w TYM SAMYM zdaniu lub linii; gdy w linii jest URL, musi nalezec do domeny
celu. Dzieki temu „Kurs XTB runal...” w jednej linii i link afiliacyjny innej firmy
w drugiej nie tworza falszywego trafienia.

Konfiguracja wylacznie w konstruktorze (slownik z rejestru KNF: `dictionary_from_registry`).
Rotacja UA/proxy: `net.Rotator`. Brak zmiennych `INVESTWATCH_*`.
"""

from __future__ import annotations

import logging
import math
import re
import unicodedata
import uuid
from collections.abc import Iterator
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

import time

from contracts import AdDocument, MediaItem, Publisher, Transcript, TranscriptSegment
from net import Rotator

from sources.base import SourceBlocked, SourceError, SourceGone

log = logging.getLogger(__name__)

URL = re.compile(r'https?://[^\s<>"“”]+|(?<![\w@/])(?:[\w-]+\.)+[^\W\d_]{2,}(?:[/?#][^\s<>"“”]*)?', re.IGNORECASE)
VIDEO_ID = re.compile(r"[A-Za-z0-9_-]{11}\Z")
WATCH = "https://www.youtube.com/watch?v="
NO_CLIPS_NOTE = "Brak powiazanego fragmentu napisow; timestamp nieustalony."
MIN_ALIAS = 3
MAX_EVIDENCE = 5

DEFAULT_SIGNALS = [
    "gwarantowany zysk", "zysk bez ryzyka", "pewny zysk", "gwarantowana stopa zwrotu",
    "zarabiaj automatycznie", "link partnerski", "link afiliacyjny", "kod polecający",
    "kod promocyjny", "bonus za rejestrację", "partnerem odcinka", "partnerem kanału",
    "partnerem dzisiejszego", "sponsorem odcinka", "we współpracy z",
]


# --------------------------------------------------------------------------- #
# Tekst, cele, sygnaly
# --------------------------------------------------------------------------- #


def normalize(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def host(value: str) -> str:
    try:
        name = urlsplit(value if "://" in value else "https://" + value).hostname
        return name.rstrip(".").encode("idna").decode("ascii").lower() if name else ""
    except (ValueError, UnicodeError):
        return ""


def _url_host(raw: str) -> str:
    return host(raw.rstrip(".,;!)]}"))


def _on_domain(name: str, domain: str) -> bool:
    return bool(domain) and (name == domain or name.endswith("." + domain))


def _group(entry: dict) -> str:
    """Klucz laczacy firme z jej domenami (`group`, a bez niego id bez sufiksu `-domain`)."""
    return str(entry.get("group") or str(entry["id"]).removesuffix("-domain"))


def _domains(dictionary: list[dict]) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for entry in dictionary:
        if entry["type"] == "domain":
            for value in [entry["value"], *entry.get("aliases", [])]:
                if host(value):
                    out.setdefault(_group(entry), set()).add(host(value).removeprefix("www."))
    return out


def find_targets(text: str, dictionary: list[dict]) -> list[dict]:
    """Tylko konkretne firmy/agenci/domeny. Same hasla (`keyword`) nigdy nie kwalifikuja filmu."""
    hits, seen = [], set()
    for entry in dictionary:
        if entry["type"] == "keyword":
            continue
        for value in [entry["value"], *entry.get("aliases", [])]:
            if entry["type"] == "domain":
                domain = host(value).removeprefix("www.")
                occurrences = [m for m in URL.finditer(text) if _on_domain(_url_host(m.group()), domain)]
            else:
                pattern = r"(?<!\w)" + r"\s+".join(re.escape(w) for w in value.split()) + r"(?!\w)"
                occurrences = list(re.finditer(pattern, text, re.IGNORECASE))
            for match in occurrences:
                key = (entry["id"], match.start(), match.end())
                if key in seen:
                    continue
                seen.add(key)
                is_domain = entry["type"] == "domain"
                hits.append({
                    "type": entry["type"], "name": entry["value"], "group": _group(entry),
                    "value": match.group().rstrip(".,;!)]}") if is_domain else match.group(),
                    "start": match.start(), "end": match.end(),
                })
    return hits


def signals_in(text: str, signals: list[str]) -> list[str]:
    text = normalize(text)
    return [s for s in signals if re.search(r"(?<!\w)" + re.escape(normalize(s)) + r"(?!\w)", text)]


def sentences(text: str) -> Iterator[tuple[int, int]]:
    """Zakresy zdan/linii z zachowaniem offsetow; kropka w URL (`xtb.com`) nie dzieli."""
    for line in re.finditer(r"[^\n]+", text):
        start = line.start()
        for part in re.split(r"(?<=[.!?])\s+", line.group()):
            if part.strip():
                begin = text.index(part, start)
                yield begin, begin + len(part)
                start = begin + len(part)


def proximate(text: str, dictionary: list[dict], signals: list[str]) -> list[dict]:
    """Trafienia, w ktorych cel i sygnal sa w jednym zdaniu/linii, a URL (jesli jest) nalezy do celu."""
    domains = _domains(dictionary)
    found = []
    for begin, end in sentences(text):
        sentence = text[begin:end]
        sigs = signals_in(sentence, signals)
        if not sigs:
            continue
        hosts = [_url_host(m.group()) for m in URL.finditer(sentence)]
        for hit in find_targets(sentence, dictionary):
            allowed = domains.get(hit["group"], set())
            if hosts and hit["type"] != "domain" and allowed and not any(_on_domain(h, d) for h in hosts for d in allowed):
                continue
            found.append({**hit, "start": hit["start"] + begin, "end": hit["end"] + begin,
                          "sentence": sentence.strip(), "signals": sigs})
    return found


@lru_cache(maxsize=1)
def language_factory():
    from langdetect import DetectorFactory
    from langdetect.detector_factory import PROFILES_DIRECTORY

    factory = DetectorFactory()
    factory.load_json_profile([p.read_text("utf-8") for p in sorted(Path(PROFILES_DIRECTORY).iterdir()) if p.is_file()])
    factory.set_seed(0)
    return factory


def is_language(text: str, language: str) -> bool:
    """Probki z calego tekstu, nie tylko z wstepu, ktory moze byc mylacy."""
    from langdetect.lang_detect_exception import LangDetectException

    text = " ".join(re.findall(r"[^\W\d_]+", URL.sub(" ", text)))
    if sum(c.isalpha() for c in text) < 80 or len(text.split()) < 12:
        return False
    starts = [0] if len(text) <= 1500 else [0, max(0, len(text) // 2 - 750), len(text) - 1500]
    for start in starts:
        detector = language_factory().create()
        detector.append(text[start : start + 1500])
        try:
            scores = detector.get_probabilities()
        except LangDetectException:
            return False
        if not scores or scores[0].lang != language or scores[0].prob < 0.95:
            return False
    return True


def evidence(text: str, field: str, dictionary: list[dict], signals: list[str]) -> list[dict]:
    items, seen = [], set()
    for hit in proximate(text, dictionary, signals):
        key = (hit["type"], hit["name"])
        if key in seen:
            continue
        seen.add(key)
        items.append({"field": field, "type": hit["type"], "target": hit["name"], "quote": hit["sentence"][:400],
                      "signals": hit["signals"], **({"url": hit["value"]} if hit["type"] == "domain" else {})})
    return items[:MAX_EVIDENCE]


NO_CAPTIONS_BASIS = "firm_mention_no_captions"


def mentions(text: str, field: str, dictionary: list[dict]) -> list[dict]:
    """Wzmianki o firmach z rejestru (bez wymogu sygnalu) - kwalifikacja filmu bez napisow."""
    items, seen = [], set()
    for begin, end in sentences(text):
        sentence = text[begin:end]
        for hit in find_targets(sentence, dictionary):
            key = (hit["type"], hit["name"])
            if key in seen:
                continue
            seen.add(key)
            items.append({"field": field, "type": hit["type"], "target": hit["name"], "quote": sentence.strip()[:400],
                          "signals": [], "basis": NO_CAPTIONS_BASIS,
                          **({"url": hit["value"]} if hit["type"] == "domain" else {})})
    return items[:MAX_EVIDENCE]


def make_clips(segments: list[dict], dictionary: list[dict], signals: list[str], max_seconds: float, max_clips: int) -> list[dict]:
    """Nigdy nie lacz odleglych wzmianek i nie rozszerzaj klipu ponad twardy limit."""
    clips: list[dict] = []
    for i, first in enumerate(segments):
        if clips and first["start"] < clips[-1]["end"]:
            continue
        group: list[dict] = []
        for current in segments[i:]:
            end = current["start"] + current["duration"]
            if end - first["start"] > max_seconds:
                break
            if group and current["start"] - (group[-1]["start"] + group[-1]["duration"]) > 2:
                break
            group.append(current)
            text = " ".join(s["text"] for s in group)
            if not proximate(text, dictionary, signals):
                continue
            while len(group) > 1:
                shorter = " ".join(s["text"] for s in group[1:])
                if not proximate(shorter, dictionary, signals):
                    break
                group, text = group[1:], shorter
            hits = proximate(text, dictionary, signals)
            # Granice napisow to granice dowodu, nie zgadywane granice slow.
            start = max(0, group[0]["start"] - 2)
            clip_end = min(end + 3, start + max_seconds, segments[-1]["start"] + segments[-1]["duration"])
            if clip_end < end:  # zachowaj caly dowod, porzuc opcjonalny kontekst z przodu
                start, clip_end = group[0]["start"], end
            clips.append({"start": round(start, 3), "end": round(clip_end, 3), "text": text,
                          "targets": sorted({h["name"] for h in hits}),
                          "signals": sorted({s for h in hits for s in h["signals"]})})
            break
        if len(clips) >= max_clips:
            break
    return clips


# --------------------------------------------------------------------------- #
# Slownik z rejestru KNF
# --------------------------------------------------------------------------- #


def dictionary_from_registry(entries: list[dict]) -> list[dict]:
    """Wiersze rejestru ({knf_id, name, aliases, domains}) -> wpisy slownika (firma + domeny)."""
    out: list[dict] = []
    for row in entries:
        name, kid = str(row.get("name") or "").strip(), str(row.get("knf_id") or "").strip()
        if not name or not kid:
            continue
        aliases = list(dict.fromkeys(a.strip() for a in row.get("aliases") or [] if len(a.strip()) >= MIN_ALIAS and a.strip() != name))
        out.append({"id": kid, "group": kid, "type": "organization", "value": name, "aliases": aliases})
        domains = dict.fromkeys(d for d in (host(x).removeprefix("www.") for x in row.get("domains") or []) if d)
        out.extend({"id": f"{kid}-domain-{n}", "group": kid, "type": "domain", "value": d} for n, d in enumerate(domains, 1))
    return out


def queries_for(entries: list[dict], phrases: list[str]) -> list[str]:
    """Iloczyn firm (najkrotsza sensowna nazwa/alias) i fraz, np. „XTB kod polecajacy”."""
    out: dict[str, None] = {}
    for row in entries:
        names = [n.strip() for n in [row.get("name") or "", *(row.get("aliases") or [])] if len(n.strip()) >= MIN_ALIAS]
        if not names:
            continue
        short = min(names, key=len)
        out.update((f"{short} {p.strip()}", None) for p in phrases if p.strip())
    return list(out)


# --------------------------------------------------------------------------- #
# Zrodlo
# --------------------------------------------------------------------------- #


class _QuietLogger:
    def debug(self, message): ...
    def info(self, message): ...
    def warning(self, message): ...
    def error(self, message): ...


def video_id(url: str) -> str | None:
    parts = urlsplit(url)
    name = (parts.hostname or "").removeprefix("www.").removeprefix("m.")
    segments = [s for s in parts.path.split("/") if s]
    if name == "youtu.be" and segments:
        candidate = segments[0]
    elif name in ("youtube.com", "music.youtube.com"):
        if segments[:1] in (["shorts"], ["embed"], ["live"]) and len(segments) > 1:
            candidate = segments[1]
        else:
            candidate = (parse_qs(parts.query).get("v") or [""])[0]
    else:
        return None
    return candidate if VIDEO_ID.fullmatch(candidate) else None


# Napisy: endpoint timedtext YouTube blokuje IP (429 "Sorry...") niezaleznie od biblioteki.
# Po 429 przestajemy probowac na CAPTIONS_COOLDOWN_S (stan procesu: SimpleWorker zyje dlugo)
# i od razu idziemy w fallback: audio m4a w S3, ktore analyzer transkrybuje faster-whisperem.
CAPTIONS_COOLDOWN_S = 900
_captions_blocked_until = 0.0
AUDIO_FORMAT = "bestaudio[ext=m4a]/bestaudio[acodec^=mp4a]/worstaudio"


def caption_url(info: dict, language: str) -> str | None:
    """URL napisow json3: najpierw reczne, potem automatyczne (`pl`, `pl-orig`)."""
    for group in ("subtitles", "automatic_captions"):
        tracks = info.get(group) or {}
        for lang in (language, f"{language}-orig"):
            for t in tracks.get(lang) or []:
                if t.get("ext") == "json3" and t.get("url"):
                    return t["url"]
    return None


def captions_from_json3(data: dict) -> list[dict]:
    """json3 YouTube -> segmenty {text, start, duration} (puste linie pomijane)."""
    out = []
    for ev in data.get("events") or []:
        text = re.sub(r"\s+", " ", "".join(seg.get("utf8", "") for seg in ev.get("segs") or [])).strip()
        if not text:
            continue
        out.append({"text": text, "start": ev.get("tStartMs", 0) / 1000, "duration": ev.get("dDurationMs", 0) / 1000})
    return out


class YouTubeSource:
    name = "youtube"

    def __init__(
        self,
        dictionary: list[dict],
        *,
        signals: list[str] | None = None,
        language: str = "pl",
        results_per_query: int = 8,
        max_clip_seconds: int = 30,
        max_clips: int = 2,
        max_comments: int = 10,
        exclude: dict | None = None,
        rotator: Rotator | None = None,
        limiter: Any = None,
        store: Any = None,
        audio_max_s: int = 1200,
    ) -> None:
        if not any(e["type"] != "keyword" for e in dictionary):
            raise ValueError("Podaj konkretne firmy, agentow lub domeny; same hasla nie wystarcza")
        if min(results_per_query, max_clip_seconds, max_clips) <= 0 or max_comments < 0:
            raise ValueError("results_per_query, max_clip_seconds i max_clips musza byc dodatnie")
        exclude = exclude or {}
        if any(f not in ("title", "description", "transcript") for f in exclude):
            raise ValueError("exclude: dozwolone title, description, transcript")
        self.dictionary = dictionary
        self.signals = list(DEFAULT_SIGNALS if signals is None else signals)
        self.language = language
        self.results_per_query = results_per_query
        self.max_clip_seconds = max_clip_seconds
        self.max_clips = max_clips
        self.max_comments = max_comments
        self.exclude = exclude
        self.rotator = rotator or Rotator.from_env()
        self.limiter = limiter
        self.store = store  # audio m4a dla Whispera (fallback, gdy brak napisow)
        self.audio_max_s = audio_max_s
        self._info: dict[str, dict] = {}

    # ------------------------------------------------------------- siec --

    def _wait(self) -> None:
        if self.limiter is not None:
            self.limiter.acquire()

    def _ydl_options(self) -> dict[str, Any]:
        options: dict[str, Any] = {
            "skip_download": True, "quiet": True, "logger": _QuietLogger(), "cachedir": False,
            "noplaylist": True, "socket_timeout": 12, "retries": 1, "extractor_retries": 1,
            "ignore_no_formats_error": True, "getcomments": False,
            "http_headers": self.rotator.headers(),
            "extractor_args": {"youtube": {"skip": ["hls", "dash", "translated_subs"]}},
        }
        proxy = self.rotator.proxy()
        if proxy:
            options["proxy"] = proxy
        return options

    def _extract(self, target: str, options: dict[str, Any]) -> dict | None:
        import yt_dlp
        from yt_dlp.utils import DownloadError

        self._wait()
        try:
            with yt_dlp.YoutubeDL(options) as client:
                return client.extract_info(target, download=False)
        except DownloadError as exc:
            message = str(exc).lower()
            if any(w in message for w in ("unavailable", "private video", "been removed", "terminated", "does not exist")):
                raise SourceGone(f"film niedostepny: {target}") from exc
            if "not a bot" in message or "sign in" in message or "429" in message:
                raise SourceBlocked(f"YouTube blokuje zapytania: {target}") from exc
            raise SourceError(f"yt-dlp: {target}: {exc}") from exc

    def _metadata(self, vid: str) -> dict | None:
        options = self._ydl_options()
        if self.max_comments:
            options["getcomments"] = True
            options["extractor_args"]["youtube"].update(max_comments=[str(self.max_comments)], comment_sort=["top"])
        info = self._extract(WATCH + vid, options)
        if info:
            self._info[vid] = info
        return info

    def _transcript(self, vid: str) -> list[dict]:
        """Napisy z metadanych yt-dlp (json3), bez youtube-transcript-api. 429 -> przerwa."""
        global _captions_blocked_until
        import json

        if time.monotonic() < _captions_blocked_until:
            return []
        url = caption_url(self._info.get(vid) or {}, self.language)
        if not url:
            return []
        import yt_dlp
        from yt_dlp.networking.exceptions import HTTPError

        self._wait()
        try:
            with yt_dlp.YoutubeDL(self._ydl_options()) as client:
                body = client.urlopen(url).read()
        except HTTPError as exc:
            if exc.status == 429:
                _captions_blocked_until = time.monotonic() + CAPTIONS_COOLDOWN_S
                log.warning("napisy YouTube: 429, przerwa %d s (fallback audio dla Whispera)", CAPTIONS_COOLDOWN_S)
            raise
        return [s for s in captions_from_json3(json.loads(body))
                if math.isfinite(s["start"]) and s["start"] >= 0 and s["duration"] >= 0]

    def _audio(self, vid: str) -> bytes | None:
        """Sciezka audio m4a (do Whispera w analyzerze); None przy bledzie/limicie rozmiaru."""
        import tempfile

        import yt_dlp

        self._wait()
        with tempfile.TemporaryDirectory() as tmp:
            options = self._ydl_options() | {"skip_download": False, "format": AUDIO_FORMAT,
                                             "outtmpl": f"{tmp}/%(id)s.%(ext)s", "max_filesize": 60 * 1024 * 1024,
                                             "extractor_args": {}, "getcomments": False}
            try:
                with yt_dlp.YoutubeDL(options) as client:
                    client.extract_info(WATCH + vid, download=True)
            except Exception as exc:  # noqa: BLE001 — brak audio nie blokuje oceny tekstu
                log.info("audio niedostepne (%s): %s", type(exc).__name__, vid)
                return None
            files = sorted(Path(tmp).glob(f"{vid}.*"))
            return files[0].read_bytes() if files else None

    # -------------------------------------------------------- interfejs --

    def discover(self, query: str) -> list[str]:
        options = self._ydl_options() | {"extract_flat": True, "playlistend": self.results_per_query}
        data = self._extract(f"ytsearch{self.results_per_query}:{query}", options)
        urls: dict[str, None] = {}
        for entry in (data or {}).get("entries") or []:
            if entry and VIDEO_ID.fullmatch(entry.get("id") or ""):
                urls[WATCH + entry["id"]] = None
        return list(urls)

    def fetch(self, url: str) -> AdDocument:
        return self.fetch_with_evidence(url)[0]

    def fetch_with_evidence(self, url: str) -> tuple[AdDocument, dict]:
        vid = video_id(url)
        if vid is None:
            raise SourceError(f"to nie jest URL filmu YouTube: {url}")
        canonical = WATCH + vid
        info = self._metadata(vid)
        if not info:
            raise SourceError(f"brak metadanych: {canonical}")
        try:
            captions = self._transcript(vid)
        except Exception as exc:  # noqa: BLE001 — brak napisow nie blokuje oceny tekstu
            log.info("napisy niedostepne (%s): %s", type(exc).__name__, canonical)
            captions = []

        title, description = info.get("title") or "", info.get("description") or ""
        author_comments = self._author_comments(info)
        qualified, found, clips = self._qualify(info, title, description, captions, author_comments)
        for clip in clips:
            if info.get("duration") is not None:
                clip["end"] = min(clip["end"], info["duration"])
            clip["url"] = f"{canonical}&t={math.floor(clip['start'])}s"

        media: list[MediaItem] = []
        transcript_source = "captions" if captions else "none"
        too_long = (info.get("duration") or 0) > self.audio_max_s
        if qualified and not captions and self.store is not None and not too_long:
            audio = self._audio(vid)
            if audio:
                doc_id = str(uuid.uuid5(uuid.NAMESPACE_URL, canonical))
                path = self.store.put("media", f"{doc_id}.m4a", audio, "audio/mp4")
                media = [MediaItem(kind="audio", path=path, duration_s=info.get("duration"))]
                transcript_source = "audio-for-whisper"

        transcript = None
        if captions:
            transcript = Transcript(
                engine="youtube-captions", lang=self.language, text=" ".join(s["text"] for s in captions),
                segments=[TranscriptSegment(start=s["start"], end=s["start"] + s["duration"], text=s["text"]) for s in captions],
            )
        parts = [title, description, *(c["text"] for c in author_comments)]
        doc = AdDocument(
            id=str(uuid.uuid5(uuid.NAMESPACE_URL, canonical)),
            source=self.name,
            url=canonical,
            fetched_at=datetime.now(UTC),
            publisher=Publisher(handle=_handle(info), display_name=info.get("channel") or info.get("uploader"),
                                profile_url=info.get("channel_url") or info.get("uploader_url")),
            lang=self.language,
            title=title or None,
            text="\n\n".join(p for p in parts if p),
            transcript=transcript,
            media=media,
        )
        targets = sorted({e["target"] for e in found} | {t for c in clips for t in c["targets"]})
        meta = {"qualified": qualified, "evidence": found, "clips": clips, "targets": targets,
                "channel_id": info.get("channel_id"), "published_at": _published_at(info),
                "transcript_source": transcript_source}
        if qualified and not clips:
            meta["timestamp_note"] = NO_CLIPS_NOTE
        return doc, meta

    # ------------------------------------------------------- kwalifikacja --

    def _author_comments(self, info: dict) -> list[dict]:
        out, seen = [], set()
        for comment in (info.get("comments") or [])[: self.max_comments]:
            if not info.get("channel_id") or comment.get("author_id") != info["channel_id"]:
                continue
            if not comment.get("id") or comment["id"] in seen:
                continue
            seen.add(comment["id"])
            out.append({"comment_id": comment["id"], "text": comment.get("text") or "",
                        "parent_id": None if comment.get("parent") in (None, "root") else comment["parent"]})
        return out

    def _qualify(self, info, title, description, captions, author_comments) -> tuple[bool, list[dict], list[dict]]:
        spoken = " ".join(s["text"] for s in captions)
        texts = {"title": title, "description": description, "transcript": spoken}
        if any(signals_in(texts[f], phrases) for f, phrases in self.exclude.items()):
            return False, [], []
        if not is_language(spoken if captions else title + "\n" + description, self.language):
            return False, [], []
        clips = make_clips(captions, self.dictionary, self.signals, self.max_clip_seconds, self.max_clips)
        found = evidence(title, "title", self.dictionary, self.signals) + evidence(description, "description", self.dictionary, self.signals)
        for comment in author_comments:
            found.extend({**e, "comment_id": comment["comment_id"]} for e in evidence(comment["text"], "author_comment", self.dictionary, self.signals))
        if not captions and not found:
            # Napisow brak (IpBlocked, wylaczone): nie odrzucamy filmu tylko za to. Wystarczy
            # wzmianka o firmie z rejestru w tytule/opisie (bez sygnalu promocji w tym samym
            # zdaniu) - dowod slabszy, oznaczony `basis`, ocene robi analyzer.
            found = mentions(title, "title", self.dictionary) + mentions(description, "description", self.dictionary)
        return bool(clips or found), found[:MAX_EVIDENCE], clips


def _handle(info: dict) -> str | None:
    for key in ("uploader_id", "channel_handle"):
        value = info.get(key)
        if isinstance(value, str) and value.startswith("@"):
            return value
    for key in ("uploader_url", "channel_url"):
        match = re.search(r"youtube\.com/(@[^/?#]+)", info.get(key) or "")
        if match:
            return match.group(1)
    return None


def _published_at(info: dict) -> str | None:
    raw = info.get("upload_date")
    if isinstance(raw, str) and re.fullmatch(r"\d{8}", raw):
        return datetime(int(raw[:4]), int(raw[4:6]), int(raw[6:]), tzinfo=UTC).isoformat()
    if isinstance(info.get("timestamp"), int | float):
        return datetime.fromtimestamp(info["timestamp"], UTC).isoformat()
    return None

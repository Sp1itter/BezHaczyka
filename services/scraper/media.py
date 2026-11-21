"""Wideo z reklam: bezposredni mp4 z Ad Library, yt-dlp tylko jako fallback.

Kolejnosc wynika z ustalen Fazy 1: `snapshot.videos[].video_hd_url` to
podpisany URL fbcdn, ktory WYGASA — pobieramy go od razu w fetch(), przez
kontekst Playwrighta (te same naglowki i proxy co strona, zero nowych
zaleznosci). yt-dlp (Unlicense) ma ekstraktor dla Ad Library i wchodzi do gry
tylko, gdy JSON nie dal URL-a, a w karcie reklamy jest <video>.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


def download_direct(request_context: Any, url: str, max_bytes: int, timeout_s: float = 60) -> bytes | None:
    """Pobiera mp4 przez `BrowserContext.request`. None przy bledzie lub zbyt duzym pliku."""
    try:
        resp = request_context.get(url, timeout=timeout_s * 1000, max_redirects=3)
    except Exception:  # noqa: BLE001 — siec: degradujemy do braku wideo
        return None
    if not resp.ok:
        return None
    length = resp.headers.get("content-length")
    if length and length.isdigit() and int(length) > max_bytes:
        return None
    body = resp.body()
    return body if 0 < len(body) <= max_bytes else None


def download_ytdlp(page_url: str, max_bytes: int, timeout_s: float = 180) -> bytes | None:
    """Fallback przez yt-dlp (proces potomny, bez importu w procesie workera)."""
    try:
        import yt_dlp  # noqa: F401 — tylko sprawdzenie, czy jest zainstalowany
    except ImportError:
        return None
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "video.%(ext)s"
        cmd = [
            sys.executable, "-m", "yt_dlp",
            "--no-playlist", "--quiet", "--no-warnings",
            "-f", "mp4/best[ext=mp4]/best",
            "--max-filesize", str(max_bytes),
            "-o", str(out),
            page_url,
        ]
        try:
            subprocess.run(cmd, check=True, timeout=timeout_s, capture_output=True)
        except (subprocess.SubprocessError, OSError):
            return None
        files = sorted(Path(tmp).glob("video.*"))
        return files[0].read_bytes() if files else None


def probe_duration(data: bytes) -> float | None:
    """Dlugosc wideo przez ffprobe. None, gdy ffprobe niedostepny."""
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return None
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as fh:
        fh.write(data)
        path = fh.name
    try:
        out = subprocess.run(
            [ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "json", path],
            check=True, timeout=30, capture_output=True, text=True,
        )
        return round(float(json.loads(out.stdout)["format"]["duration"]), 2)
    except (subprocess.SubprocessError, OSError, ValueError, KeyError):
        return None
    finally:
        Path(path).unlink(missing_ok=True)

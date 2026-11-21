"""Rozwiazywanie referencji do mediow (sciezka, http(s), s3://) na plik lokalny.

Zasada: bledy -> None + log, nigdy wyjatek wysadzajacy potok. Zadnych
zahardkodowanych hostow; adres bramki S3 pochodzi ze zmiennej srodowiskowej.
"""

from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path
from urllib.parse import urlparse

import httpx

log = logging.getLogger(__name__)

DEFAULT_MAX_MB = 200
TIMEOUT_S = 60.0
_ALLOWED_EXT = {".mp4", ".webm", ".mov", ".mkv", ".m4a", ".mp3", ".wav", ".ogg", ".aac"}


def _max_bytes() -> int:
    try:
        mb = float(os.getenv("STT_MAX_MEDIA_MB", DEFAULT_MAX_MB))
    except ValueError:
        mb = DEFAULT_MAX_MB
    return int(mb * 1024 * 1024)


def _s3_to_http(ref: str) -> str | None:
    base = (os.getenv("SEAWEEDFS_S3_PUBLIC_URL") or os.getenv("S3_PUBLIC_URL") or "").strip()
    if not base:
        log.warning("media s3:// bez SEAWEEDFS_S3_PUBLIC_URL, pomijam: %s", ref)
        return None
    p = urlparse(ref)
    return f"{base.rstrip('/')}/{p.netloc}{p.path}"


def _download(url: str, cache_dir: Path, client: httpx.Client | None) -> Path | None:
    ext = Path(urlparse(url).path).suffix.lower()
    if ext not in _ALLOWED_EXT:
        ext = ".bin"
    dest = cache_dir / (hashlib.sha256(url.encode("utf-8")).hexdigest() + ext)
    if dest.is_file() and dest.stat().st_size > 0:
        return dest
    limit = _max_bytes()
    part = dest.with_name(dest.name + ".part")
    own = client is None
    cl = client or httpx.Client(timeout=TIMEOUT_S, follow_redirects=True)
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        with cl.stream("GET", url) as resp:
            if resp.status_code != 200:
                log.warning("media %s: HTTP %s", url, resp.status_code)
                return None
            declared = resp.headers.get("content-length")
            if declared and declared.isdigit() and int(declared) > limit:
                log.warning("media %s: %s B ponad limit %s B", url, declared, limit)
                return None
            size = 0
            with part.open("wb") as fh:
                for chunk in resp.iter_bytes():
                    size += len(chunk)
                    if size > limit:
                        log.warning("media %s: przekroczono limit %s B", url, limit)
                        fh.close()
                        part.unlink(missing_ok=True)
                        return None
                    fh.write(chunk)
        if size == 0:
            part.unlink(missing_ok=True)
            return None
        part.replace(dest)
        return dest
    except Exception as exc:  # siec, dysk - nigdy nie wysadzamy potoku
        log.warning("media %s: pobranie nieudane: %s", url, exc)
        try:
            part.unlink(missing_ok=True)
        except OSError:
            pass
        return None
    finally:
        if own:
            cl.close()


def resolve_media(
    ref_path: str, cache_dir: Path | str, *, client: httpx.Client | None = None
) -> Path | None:
    """Zwroc lokalny plik dla referencji albo None."""
    if not ref_path:
        return None
    cache = Path(cache_dir)
    try:
        if ref_path.startswith("s3://"):
            url = _s3_to_http(ref_path)
            return _download(url, cache, client) if url else None
        if ref_path.startswith(("http://", "https://")):
            return _download(ref_path, cache, client)
        if "://" in ref_path:
            log.warning("media: nieobslugiwany schemat: %s", ref_path)
            return None
        p = Path(ref_path)
        return p if p.is_file() else None
    except Exception as exc:
        log.warning("media %s: blad rozwiazywania: %s", ref_path, exc)
        return None

"""Testy media_fetch: lokalne sciezki, http(s) na MockTransport, s3 przez env."""

from __future__ import annotations

import hashlib

import httpx

from analyzer import media_fetch
from analyzer.media_fetch import resolve_media


def _client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_local_existing_file(tmp_path):
    f = tmp_path / "a.mp4"
    f.write_bytes(b"x")
    assert resolve_media(str(f), tmp_path / "cache") == f


def test_missing_and_empty_ref(tmp_path):
    assert resolve_media(str(tmp_path / "nie-ma.mp4"), tmp_path) is None
    assert resolve_media("", tmp_path) is None


def test_http_download_and_cache_reuse(tmp_path):
    calls = []

    def handler(req):
        calls.append(str(req.url))
        return httpx.Response(200, content=b"VIDEO" * 10)

    url = "https://cdn.example.test/v/clip.mp4?sig=1"
    p = resolve_media(url, tmp_path, client=_client(handler))
    assert p is not None and p.read_bytes() == b"VIDEO" * 10
    assert hashlib.sha256(url.encode()).hexdigest() in p.name
    assert p.suffix == ".mp4"
    p2 = resolve_media(url, tmp_path, client=_client(handler))
    assert p2 == p and len(calls) == 1


def test_http_error_status_returns_none(tmp_path):
    p = resolve_media("https://x.test/a.mp4", tmp_path,
                      client=_client(lambda r: httpx.Response(404)))
    assert p is None
    assert not list(tmp_path.glob("*.part"))


def test_http_size_limit(tmp_path, monkeypatch):
    monkeypatch.setenv("STT_MAX_MEDIA_MB", "1")
    big = b"0" * (2 * 1024 * 1024)
    p = resolve_media("https://x.test/a.mp4", tmp_path,
                      client=_client(lambda r: httpx.Response(200, content=big)))
    assert p is None
    assert not list(tmp_path.glob("*.part")) and not list(tmp_path.glob("*.mp4"))


def test_http_size_limit_by_content_length(tmp_path, monkeypatch):
    monkeypatch.setenv("STT_MAX_MEDIA_MB", "1")
    h = {"content-length": str(5 * 1024 * 1024)}
    p = resolve_media("https://x.test/a.mp4", tmp_path,
                      client=_client(lambda r: httpx.Response(200, headers=h, content=b"a")))
    assert p is None


def test_http_exception_returns_none(tmp_path):
    def boom(req):
        raise httpx.ConnectError("blad")

    assert resolve_media("https://x.test/a.mp4", tmp_path, client=_client(boom)) is None


def test_s3_without_env_returns_none(tmp_path, monkeypatch):
    monkeypatch.delenv("SEAWEEDFS_S3_PUBLIC_URL", raising=False)
    assert resolve_media("s3://bucket/ads/1/v.mp4", tmp_path) is None


def test_s3_with_env_maps_to_http(tmp_path, monkeypatch):
    monkeypatch.setenv("SEAWEEDFS_S3_PUBLIC_URL", "http://s3.internal.test:8333/")
    seen = []

    def handler(req):
        seen.append(str(req.url))
        return httpx.Response(200, content=b"abc")

    p = resolve_media("s3://bucket/ads/1/v.mp4", tmp_path, client=_client(handler))
    assert p is not None and p.read_bytes() == b"abc"
    assert seen == ["http://s3.internal.test:8333/bucket/ads/1/v.mp4"]


def test_unknown_scheme(tmp_path):
    assert resolve_media("ftp://x/y.mp4", tmp_path) is None


def test_module_has_no_hardcoded_hosts():
    src = open(media_fetch.__file__, encoding="utf-8").read()
    assert "amazonaws" not in src and "localhost" not in src

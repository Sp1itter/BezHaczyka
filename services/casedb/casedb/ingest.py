"""Mapowanie wynikow scraperow na Case. Bez dostepu do bazy - latwe do testowania."""

from __future__ import annotations

from typing import Any
from urllib.parse import parse_qs, urlparse

from casedb.store import Asset, Case, Content, case_id_for

_EVIDENCE_KEYS = ("field", "type", "target", "signals", "comment_id")


def youtube_video_id(url: str) -> str:
    u = urlparse(url)
    if u.hostname and u.hostname.endswith("youtu.be"):
        return u.path.lstrip("/")
    return (parse_qs(u.query).get("v") or [""])[0] or url


def from_youtube(item: dict[str, Any]) -> Case:
    """Jeden element listy z services/scraper/youtube (wynik.json / scan())."""
    video_id = youtube_video_id(item["url"])
    url = f"https://www.youtube.com/watch?v={video_id}"  # compliance:allow (kanoniczny URL, nie wywolanie)
    content: list[Content] = []
    if item.get("title"):
        content.append(Content("title", item["title"]))
    if item.get("description"):
        content.append(Content("description", item["description"]))
    for c in item.get("author_comments") or []:
        content.append(Content("comment", c.get("text") or "", extra={
            k: c.get(k) for k in ("comment_id", "parent_id", "author_channel_id")}))
    for e in item.get("evidence") or []:
        content.append(Content("evidence", e.get("quote") or "",
                               extra={k: e[k] for k in _EVIDENCE_KEYS if k in e}))
    for clip in item.get("clips") or []:
        content.append(Content("clip", clip.get("text") or "", start_s=clip.get("start"),
                               end_s=clip.get("end"), url=clip.get("url"), extra={
                                   "targets": clip.get("targets", []),
                                   "signals": clip.get("signals", [])}))
    extra = {k: item[k] for k in ("timestamp_note",) if k in item}
    return Case(
        source="youtube", source_item_id=video_id, url=url, case_id=case_id_for(url),
        title=item.get("title"), author_name=item.get("channel"),
        author_id=item.get("channel_id"), lang=item.get("language"),
        published_at=item.get("published_at"), extra=extra, raw=item, content=content,
        assets=[Asset("link", url, label="video")],
    )


def from_ad_document(doc: dict[str, Any], source: str | None = None) -> Case:
    """AdDocument (kontrakt z services/scraper/contracts.py) - FB i przyszly scraper WWW."""
    source = source or doc.get("source") or "www"
    url = doc["url"]
    if source == "facebook":
        item_id = (parse_qs(urlparse(url).query).get("id") or [""])[0] or doc["id"]
    else:
        item_id = url
    publisher = doc.get("publisher") or {}
    content: list[Content] = []
    if doc.get("title"):
        content.append(Content("title", doc["title"]))
    if doc.get("text"):
        content.append(Content("text", doc["text"]))
    transcript = doc.get("transcript")
    if transcript:
        content.append(Content("transcript", transcript.get("text") or "", extra={
            "engine": transcript.get("engine"), "segments": transcript.get("segments", [])}))
    assets: list[Asset] = []
    if doc.get("html_path"):
        assets.append(Asset("html", doc["html_path"], mime="text/html"))
    for viewport, uri in (doc.get("screenshots") or {}).items():
        assets.append(Asset("screenshot", uri, label=viewport, mime="image/png"))
    for m in doc.get("media") or []:
        assets.append(Asset(m["kind"], m["path"], extra={"duration_s": m.get("duration_s")}))
    extra = {
        "publisher": publisher,
        "scope": doc.get("scope") or {},
        "simhash": doc.get("simhash"),
    }
    # Wektor embeddingu jest duzy i liczy go analyzer - nie trzymamy go w raw.
    raw = {k: v for k, v in doc.items() if k != "embedding"}
    return Case(
        source=source, source_item_id=item_id, url=url, case_id=doc.get("id") or case_id_for(url),
        title=doc.get("title"),
        author_name=publisher.get("display_name") or publisher.get("handle"),
        author_id=publisher.get("handle"), author_url=publisher.get("profile_url"),
        lang=doc.get("lang"), fetched_at=doc.get("fetched_at"), extra=extra, raw=raw,
        content=content, assets=assets,
    )

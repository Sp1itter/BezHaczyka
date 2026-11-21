"""Kandydaci spoza Meta: strony korpusu (plan B, `synthetic`) i odtworzenie kandydata z wiersza."""

from __future__ import annotations

import hashlib
import html
import re
from pathlib import Path
from typing import Any

from collector.candidates import from_facebook_node
from collector.scoring import Candidate

_TAG_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>|<[^>]+>", re.DOTALL | re.IGNORECASE)


def html_text(raw: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(_TAG_RE.sub(" ", raw))).strip()


def from_page(path: Path, url: str, query_tag: str, source_type: str = "synthetic") -> Candidate:
    """Strona HTML z dysku -> kandydat. external_id = nazwa pliku (stabilny miedzy file:// i nginx)."""
    text = html_text(path.read_text(encoding="utf-8"))
    links = re.findall(r'href="(https?://[^"]+)"', path.read_text(encoding="utf-8"))
    return Candidate(
        source_type=source_type,
        external_id=path.name if source_type == "synthetic" else hashlib.sha1(url.encode()).hexdigest()[:20],
        url=url,
        query_tag=query_tag,
        text=text,
        primary_text=text,
        publisher_key=f"{source_type}:{path.stem}",
        links=links,
        payload={"text": text, "links": links, "path": str(path)},
    )


def candidate_from_row(row: dict[str, Any]) -> Candidate | None:
    """Odtworzenie kandydata z url_store (do reprioritize)."""
    payload = row.get("payload") or {}
    if row["source_type"] == "facebook" and isinstance(payload.get("node"), dict):
        return from_facebook_node(row["external_id"], payload["node"], row.get("query_tag") or "")
    if "text" in payload:
        return Candidate(
            source_type=row["source_type"], external_id=row["external_id"], url=row["url"],
            query_tag=row.get("query_tag") or "", text=payload["text"], primary_text=payload["text"],
            publisher_key=row.get("publisher_key"), links=payload.get("links", []), payload=payload,
        )
    return None

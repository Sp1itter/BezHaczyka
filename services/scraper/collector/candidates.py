"""Budowa kandydatow poziomu 1 z surowych danych zrodel (bez renderu)."""

from __future__ import annotations

from collector.scoring import Candidate
from sources.meta_json import ad_text, canonical_ad_url, link_urls, primary_body


def _finserv(node: dict) -> bool:
    reg = node.get("regional_regulation_data")
    if not isinstance(reg, dict):
        return False
    fin = reg.get("finserv")
    return bool(isinstance(fin, dict) and fin.get("is_deemed_finserv"))


def from_facebook_node(ad_id: str, node: dict, query_tag: str) -> Candidate:
    """Wezel Meta Ad Library (inline JSON / GraphQL) -> kandydat. Tresc jest w JSON,
    wiec priorytet liczymy bez Playwrighta na 3 viewportach."""
    snap = node.get("snapshot") if isinstance(node.get("snapshot"), dict) else {}
    page_id = str(node.get("page_id") or snap.get("page_id") or "") or None
    return Candidate(
        source_type="facebook",
        external_id=str(ad_id),
        url=canonical_ad_url(ad_id),
        query_tag=query_tag,
        text=ad_text(node),
        primary_text=primary_body(node) or "",
        publisher_key=f"facebook:{page_id}" if page_id else None,
        links=link_urls(node),
        meta_finserv=_finserv(node),
        payload={"node": node, "page_name": node.get("page_name") or snap.get("page_name")},
    )

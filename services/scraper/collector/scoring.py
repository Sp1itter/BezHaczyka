"""Kandydat poziomu 1, klucze deduplikacji i priorytet z edytowalnych wag.

priority = sum(weights[k] * components[k])  (wagi w lexicons.yaml)

components:
    scam_lure            min(trafienia, 2)
    impersonation        1, gdy osoba z personas.json poza jej oficjalnym kanalem
                         albo fraza z impersonation_hook
    instrument           1, gdy jest instrument finansowy
    finfluencer          1, gdy sa sygnaly finfluencerskie
    affiliate            1, gdy link ma ref/aff/affiliate/partner/promo/code (link partnerski);
                         same utm_* to sledzenie kampanii reklamodawcy -> sygnal `tracking` bez wagi
    meta_finserv         1, gdy Meta oznaczyla reklame jako uslugi finansowe
    repeat               log10(1 + seen_count) — kampania powraca
    non_instrument_only  1, gdy tylko nieruchomosci/uslugi, zero instrumentu, scamu, wizerunku
    official_registered  1, gdy publikuje oficjalny kanal osoby z personas.json

Stan: `rejected` (G1: < 20 znakow tresci), `quarantined` (non_instrument_only),
inaczej `queued`.
"""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

from collector.lexicons import Lexicons, normalize

MIN_TEXT_CHARS = 20
_AFFILIATE_RE = re.compile(r"[?&](ref|aff|affiliate|partner|promo|code|coupon)=([^&#\s]+)", re.IGNORECASE)
_TRACKING_RE = re.compile(r"[?&](utm_[a-z]+)=([^&#\s]+)", re.IGNORECASE)
# Hosty „techniczne" — landing w nich nie identyfikuje kampanii.
GENERIC_HOSTS = {
    "facebook.com", "fb.me", "fb.com", "m.me", "messenger.com", "instagram.com", "wa.me",
    "youtube.com", "youtu.be", "l.facebook.com", "lm.facebook.com", "linktr.ee",
}


@dataclass
class Candidate:
    """Jeden kandydat z poziomu 1 (bez renderu)."""

    source_type: str
    external_id: str
    url: str
    query_tag: str
    text: str                      # tresc do slownikow (glowna + tytuly + opisy + linki)
    primary_text: str              # tresc glowna (klucz kreacji)
    publisher_key: str | None
    links: list[str] = field(default_factory=list)
    meta_finserv: bool = False
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class Scored:
    priority: float
    state: str
    signals: dict[str, Any]


def creative_key(publisher_key: str | None, primary_text: str) -> str | None:
    """Ta sama tresc glowna u tego samego publishera = ta sama kreacja (wariant kampanii)."""
    norm = normalize(primary_text)
    if len(norm) < MIN_TEXT_CHARS:
        return None
    digest = hashlib.sha1(norm.encode("utf-8")).hexdigest()[:16]
    return f"{publisher_key or '-'}|{digest}"


def landing_key(url: str | None) -> str | None:
    """Domena + sciezka linku docelowego, bez parametrow (utm) — klucz kampanii miedzy zrodlami."""
    if not url:
        return None
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower().removeprefix("www.")
    if not host or host in GENERIC_HOSTS:
        return None
    return host + (parsed.path.rstrip("/") or "")


def affiliate_params(links: list[str], text: str = "", pattern: re.Pattern[str] = _AFFILIATE_RE) -> list[str]:
    found = []
    for src in [*links, text]:
        for name, value in pattern.findall(src or ""):
            item = f"{name.lower()}={value}"
            if item not in found:
                found.append(item)
    return found


def _publisher_is_official(cand: Candidate, personas) -> bool:
    page_id = (cand.publisher_key or "").split(":", 1)[-1]
    hosts = {landing_key(u).split("/", 1)[0] for u in cand.links if landing_key(u)}
    return any(page_id in p.official_page_ids or hosts & p.official_domains for p in personas)


def score(cand: Candidate, lex: Lexicons, seen_count: int = 1) -> Scored:
    norm = normalize(cand.text)
    hits = {kind: lex.hits(kind, norm) for kind in lex.terms}
    personas = lex.personas_in(norm)
    official = bool(personas) and _publisher_is_official(cand, personas)
    affiliates = affiliate_params(cand.links, cand.text)

    impersonation = bool(hits["impersonation_hook"]) or (bool(personas) and not official)
    scam = len(hits["scam_lure"])
    non_instrument_only = bool(hits["non_instrument"]) and not hits["instrument"] and not scam and not impersonation

    components = {
        "scam_lure": float(min(scam, 2)),
        "impersonation": 1.0 if impersonation else 0.0,
        "instrument": 1.0 if hits["instrument"] else 0.0,
        "finfluencer": 1.0 if hits["finfluencer"] else 0.0,
        "affiliate": 1.0 if affiliates else 0.0,
        "meta_finserv": 1.0 if cand.meta_finserv else 0.0,
        "repeat": round(math.log10(1 + max(seen_count, 1)), 3),
        "non_instrument_only": 1.0 if non_instrument_only else 0.0,
        "official_registered": 1.0 if official else 0.0,
    }
    priority = round(sum(lex.weights.get(k, 0.0) * v for k, v in components.items()), 3)

    if len(normalize(cand.primary_text or cand.text)) < MIN_TEXT_CHARS:
        state = "rejected"
    elif non_instrument_only:
        state = "quarantined"
    else:
        state = "queued"

    signals = {k: v for k, v in hits.items() if v}
    if personas:
        signals["personas"] = [p.name for p in personas]
        signals["persona_official_channel"] = official
    if affiliates:
        signals["affiliate"] = affiliates
    tracking = affiliate_params(cand.links, cand.text, _TRACKING_RE)
    if tracking:
        signals["tracking"] = tracking
    if cand.meta_finserv:
        signals["meta_finserv"] = True
    signals["components"] = components
    return Scored(priority=priority, state=state, signals=signals)


def wants_analysis(priority: float, signals: dict[str, Any], lex: Lexicons) -> bool:
    """Czy poziom 2 ma wyslac dokument do analyzera (drogi tor: Bielik)."""
    if priority >= lex.analyzer_min_priority:
        return True
    lane = lex.instrument_lane_min
    return lane is not None and bool(signals.get("instrument")) and priority >= lane

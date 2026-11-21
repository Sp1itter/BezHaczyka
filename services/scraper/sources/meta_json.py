"""Parsowanie danych Meta Ad Library — czyste funkcje, zero sieci.

Ustalenia z rozpoznania na zywo (21.11.2026, widok niezalogowany, PL):

* Pierwsza strona wynikow (ok. 30 reklam) przychodzi jako INLINE JSON
  w `<script type="application/json">` dokumentu HTML, a nie z `/api/graphql/`.
  Kolejne strony (scroll) przychodza z `/api/graphql/`, czasem jako kilka
  obiektow JSON w osobnych liniach, z prefiksem `for (;;);`.
  Dlatego NIE polegamy na konkretnej sciezce w drzewie (zmienia sie), tylko
  przechodzimy cale drzewo i zbieramy kazdy obiekt, ktory ma `ad_archive_id`
  i slownik `snapshot`. To jest odporne na przestawienia schematu.
* Reklamy DCO (Dynamic Creative, `display_format == "DCO"`) maja w
  `snapshot.body.text` / `title` / `link_description` SZABLONY typu
  `{{product.brand}}`. Prawdziwy tekst jest w `snapshot.cards[]`.
  Bez tej obslugi analyzer dostalby do oceny tekst „{{product.name}}".
* `link_url` zawiera parametry kampanii (`utm_*`, `ref`, `aff`) — to sygnal
  dla Modulu 3 (afiliacja), wiec trafia do `AdDocument.text` w calosci.

Wzorce zaczerpniete (przepisane, nie skopiowane) z kevinzg/facebook-scraper (MIT):
graceful degrade do `None` dla brakujacych pol oraz rozwijanie przekierowan
`l.facebook.com/l.php?u=...` przez parametr `u`.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections.abc import Iterable, Iterator
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse

from contracts import Publisher

# Zrodlo danych tego adaptera. Jedyne miejsce z adresem Meta w kodzie.
AD_LIBRARY_URL = "https://www.facebook.com/ads/library/"  # compliance:allow — zrodlo danych FacebookAdsSource
FACEBOOK_HOME = "https://www.facebook.com/"  # compliance:allow — profil reklamodawcy (publisher.profile_url)

_INLINE_JSON_RE = re.compile(
    r'<script[^>]*type="application/json"[^>]*>(.*?)</script>', re.DOTALL | re.IGNORECASE
)
_PLACEHOLDER_RE = re.compile(r"\{\{[^{}]*\}\}")
_ZERO_WIDTH_RE = re.compile(r"[\u200b-\u200f\u2060\ufeff\u00ad]")
_SPACES_RE = re.compile(r"[ \t\u00a0]+")
_DIGITS_RE = re.compile(r"^\d{5,25}$")

# Hosty, pod ktorymi Meta opakowuje linki wychodzace w przekierowanie.
_REDIRECT_HOSTS = ("l.facebook.com", "lm.facebook.com", "l.instagram.com")


# --------------------------------------------------------------------------- #
# URL-e
# --------------------------------------------------------------------------- #


def canonical_ad_url(ad_archive_id: str) -> str:
    """Kanoniczny URL pojedynczej reklamy — jedyny format zwracany z discover()."""
    if not _DIGITS_RE.match(str(ad_archive_id)):
        raise ValueError(f"niepoprawny ad_archive_id: {ad_archive_id!r}")
    return f"{AD_LIBRARY_URL}?id={ad_archive_id}"


def ad_id_from_url(url: str) -> str:
    """`ad_archive_id` z URL-a Ad Library (parametr `id`)."""
    parsed = urlparse(url)
    if not parsed.netloc.endswith("facebook.com") or not parsed.path.startswith("/ads/library"):
        raise ValueError(f"to nie jest URL Meta Ad Library: {url!r}")
    ids = parse_qs(parsed.query).get("id", [])
    if not ids or not _DIGITS_RE.match(ids[0]):
        raise ValueError(f"brak poprawnego parametru id w URL: {url!r}")
    return ids[0]


def search_url(query: str, country: str = "PL") -> str:
    params = {
        "active_status": "active",
        "ad_type": "all",
        "country": country,
        "q": query,
        "search_type": "keyword_unordered",
        "media_type": "all",
    }
    return f"{AD_LIBRARY_URL}?{urlencode(params)}"


def unwrap_meta_redirect(url: str | None, max_depth: int = 3) -> str | None:
    """Rozwija `l.facebook.com/l.php?u=<cel>` do adresu docelowego.

    Bez zadnego zapytania sieciowego — cel jest w parametrze `u`. Parametry
    celu (`utm_*`, `ref`, `aff`) zostaja nietkniete.
    """
    if not url:
        return url
    for _ in range(max_depth):
        parsed = urlparse(url)
        if parsed.netloc not in _REDIRECT_HOSTS or parsed.path != "/l.php":
            break
        target = parse_qs(parsed.query).get("u", [None])[0]
        if not target:
            break
        url = target
    return url


# --------------------------------------------------------------------------- #
# Wyciaganie wezlow reklam z JSON-a
# --------------------------------------------------------------------------- #


def iter_json_payloads(text: str) -> Iterator[Any]:
    """Obiekty JSON z odpowiedzi Meta: prefiks `for (;;);`, jeden lub wiele w liniach."""
    if not text:
        return
    body = text.lstrip()
    body = body.removeprefix("for (;;);")
    try:
        yield json.loads(body)
        return
    except ValueError:
        pass
    for line in body.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except ValueError:
            continue


def find_ad_nodes(payload: Any) -> dict[str, dict]:
    """Kazdy slownik z `ad_archive_id` i `snapshot: dict`, w calym drzewie.

    Iteracyjnie (jawny stos), bo drzewa Meta sa bardzo glebokie i rekurencja
    potrafi przekroczyc limit Pythona.
    """
    found: dict[str, dict] = {}
    stack: list[Any] = [payload]
    while stack:
        obj = stack.pop()
        if isinstance(obj, dict):
            ad_id = obj.get("ad_archive_id")
            if ad_id is not None and isinstance(obj.get("snapshot"), dict):
                found.setdefault(str(ad_id), obj)
            stack.extend(obj.values())
        elif isinstance(obj, list):
            stack.extend(obj)
    return found


def ads_from_html(html: str) -> dict[str, dict]:
    found: dict[str, dict] = {}
    for match in _INLINE_JSON_RE.finditer(html or ""):
        for payload in iter_json_payloads(match.group(1)):
            for ad_id, node in find_ad_nodes(payload).items():
                found.setdefault(ad_id, node)
    return found


def ads_from_graphql(body: str) -> dict[str, dict]:
    found: dict[str, dict] = {}
    for payload in iter_json_payloads(body):
        for ad_id, node in find_ad_nodes(payload).items():
            found.setdefault(ad_id, node)
    return found


# --------------------------------------------------------------------------- #
# Normalizacja tekstu i mapowanie na AdDocument
# --------------------------------------------------------------------------- #


def clean_text(value: Any) -> str | None:
    """NFKC, bez znakow zerowej szerokosci, bez szablonow DCO, zwiniete spacje.

    Zwraca None, gdy po oczyszczeniu nic nie zostalo (np. sam `{{product.name}}`).
    """
    if isinstance(value, dict):  # snapshot.body bywa {"text": "..."}
        value = value.get("text")
    if not isinstance(value, str):
        return None
    text = unicodedata.normalize("NFKC", value)
    text = _ZERO_WIDTH_RE.sub("", text)
    text = _PLACEHOLDER_RE.sub("", text)
    lines = [_SPACES_RE.sub(" ", line).strip() for line in text.splitlines()]
    text = "\n".join(line for line in lines if line)
    return text or None


def _snapshot(node: dict) -> dict:
    snap = node.get("snapshot")
    return snap if isinstance(snap, dict) else {}


def _cards(node: dict) -> list[dict]:
    cards = _snapshot(node).get("cards")
    return [c for c in cards if isinstance(c, dict)] if isinstance(cards, list) else []


def _first(*values: Any) -> str | None:
    for v in values:
        cleaned = clean_text(v)
        if cleaned:
            return cleaned
    return None


def primary_body(node: dict) -> str | None:
    """Tresc glowna reklamy (to, co w feedzie jest nad grafika)."""
    snap = _snapshot(node)
    return _first(snap.get("body"), *(c.get("body") for c in _cards(node)))


def ad_title(node: dict) -> str | None:
    snap = _snapshot(node)
    return _first(
        snap.get("title"),
        *(c.get("title") for c in _cards(node)),
        snap.get("cta_text"),
    )


def link_urls(node: dict) -> list[str]:
    snap = _snapshot(node)
    raw = [snap.get("link_url"), *(c.get("link_url") for c in _cards(node))]
    extra = snap.get("extra_links")
    if isinstance(extra, list):
        raw.extend(x for x in extra if isinstance(x, str))
    out: list[str] = []
    for url in raw:
        url = unwrap_meta_redirect(url if isinstance(url, str) else None)
        if url and url not in out:
            out.append(url)
    return out


def ad_text(node: dict) -> str:
    """`AdDocument.text` dla reklamy z Ad Library.

    KOLEJNOSC JEST CZESCIA KONTRAKTU tego zrodla: tekst ZACZYNA SIE od tresci
    glownej. Heurystyka „Zobacz wiecej" dla reguly 7 (`feed_fold_evidence`)
    liczy przesuniecie ostrzezenia od poczatku tresci glownej.
    Dalej: tytuly, opisy linkow, podpisy, tresc pozostalych kart (DCO/karuzela),
    na koncu rozwiniete linki docelowe z parametrami.
    """
    snap = _snapshot(node)
    cards = _cards(node)
    parts: list[str | None] = [primary_body(node)]
    parts.append(clean_text(snap.get("title")))
    parts.append(clean_text(snap.get("link_description")))
    parts.append(clean_text(snap.get("caption")))
    for card in cards:
        parts.extend(
            clean_text(card.get(k)) for k in ("body", "title", "link_description", "caption")
        )
    extra_texts = snap.get("extra_texts")
    if isinstance(extra_texts, list):
        parts.extend(clean_text(t) for t in extra_texts)
    parts.extend(link_urls(node))

    out: list[str] = []
    seen: set[str] = set()
    for part in parts:
        if part and part.casefold() not in seen:
            seen.add(part.casefold())
            out.append(part)
    return "\n".join(out)


def video_urls(node: dict) -> list[str]:
    """Bezposrednie (podpisane, wygasajace) URL-e mp4 z fbcdn — HD przed SD."""
    snap = _snapshot(node)
    sources: list[Any] = []
    for key in ("videos", "extra_videos"):
        if isinstance(snap.get(key), list):
            sources.extend(snap[key])
    sources.extend(_cards(node))
    out: list[str] = []
    for item in sources:
        if not isinstance(item, dict):
            continue
        url = item.get("video_hd_url") or item.get("video_sd_url")
        if isinstance(url, str) and url and url not in out:
            out.append(url)
    return out


def has_video(node: dict) -> bool:
    snap = _snapshot(node)
    return bool(video_urls(node)) or snap.get("display_format") == "VIDEO"


def publisher_from(node: dict) -> Publisher:
    """`Publisher` z danych strony reklamodawcy.

    `is_official_firm_channel` ZAWSZE False — scraper nie zna rejestru KNF.
    Nadpisuje go dopiero krok RESOLVER PODMIOTOW w analyzerze.
    """
    snap = _snapshot(node)
    page_id = str(node.get("page_id") or snap.get("page_id") or "") or None
    profile_uri = snap.get("page_profile_uri") if isinstance(snap.get("page_profile_uri"), str) else None

    handle = None
    if profile_uri:
        parsed = urlparse(profile_uri)
        segments = [s for s in parsed.path.split("/") if s]
        if (
            parsed.netloc.endswith(("facebook.com", "instagram.com"))
            and len(segments) == 1
            and segments[0] != "profile.php"
        ):
            handle = f"@{segments[0]}"

    profile_url = profile_uri or (f"{FACEBOOK_HOME}{page_id}" if page_id else None)
    return Publisher(
        handle=handle,
        display_name=clean_text(node.get("page_name") or snap.get("page_name")),
        profile_url=profile_url,
        is_official_firm_channel=False,
    )


def merge_nodes(target: dict[str, dict], new: Iterable[tuple[str, dict]]) -> int:
    """Dokleja nowe wezly, zachowujac kolejnosc pierwszego wystapienia. Zwraca liczbe nowych."""
    added = 0
    for ad_id, node in new:
        if ad_id not in target:
            target[ad_id] = node
            added += 1
    return added

"""Resolver podmiotow Modulu 1: dokument -> EntityResolution (docs/MODUL1-ARCHITEKTURA.md).

Ustala, KTORA firma z rejestru KNF jest reklamowana i KTO ja reklamuje:
  * wzmianka firmy: domena z URL-a w tekscie > dokladna nazwa/alias > fuzzy (rapidfuzz, prog 90),
  * relacja publikujacego: official (kanal firmy), third_party (podmiot trzeci), unknown (brak wzmianki).
Wynik jest zwyklym slownikiem o polach `analyzer.pipeline.EntityResolution`; scraper nie
importuje analyzera (zero importow miedzy serwisami). Normalizacja nazw jest ta sama co
w casedb (`normalize_name`), wiec rejestr i resolver zawsze zgadzaja sie co do kluczy.
"""

from __future__ import annotations

import re
import threading
import time
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import parse_qsl, urlsplit

from casedb.knf import name_key as knf_name_key
from casedb.store import _fold, normalize_name
from contracts import AdDocument
from rapidfuzz import fuzz, process

CACHE_TTL_S = 600
MIN_NAME_LEN = 3  # krotsze aliasy ("DM", "ab") daja same falszywe trafienia
FUZZY_MIN_LEN = 8  # fuzzy tylko dla dluzszych nazw
FUZZY_CUTOFF = 90
KNF_MIN_LEN = 8  # nazwy ze snapshotu: lacznie >= 8 znakow i slowo wyrozniajace
KNF_DISTINCT_LEN = 5
# Ogolne slowa finansowo-korporacyjne: same nie wyrozniaja firmy w zwyklym tekscie.
GENERIC_TOKENS = frozenset(
    "markets market europe european capital group money tech trade trading trader invest investment"
    " investments inwestycje finance financial finanse global international partners securities asset"
    " assets management wealth fund funds fundusz bank broker brokers online services solutions holding"
    " holdings consulting advisors advisory company polska poland the and co de of".split())


def knf_name_matchable(norm: str) -> bool:
    """Nazwa ze snapshotu nadaje sie do dokladnego dopasowania w tekscie."""
    return len(norm) >= KNF_MIN_LEN and any(
        t not in GENERIC_TOKENS and len(t) >= KNF_DISTINCT_LEN for t in norm.split())
# Slowa w nazwie strony swiadczace o stronie fanow/spolecznosci, a nie o kanale firmy.
FAN_TOKENS = frozenset(
    "fan fans club klub community spolecznosc opinie opinia tips porady poradnik news grupa group"
    " forum unofficial nieoficjalny nieoficjalna".split())
FUZZY_MAX_WORDS = 20000

# Priorytet trafienia: domena > dokladna nazwa > fuzzy.
DOMAIN, EXACT, FUZZY = 3, 2, 1
_SCORE = {DOMAIN: 1.0, EXACT: 0.95}
_FUZZY_CAP = 0.94

URL_RE = re.compile(r"(?:https?://|www\.)[^\s<>\"'\\]+", re.IGNORECASE)
_TRAIL = ".,;:!?)]}>\"'"

# Wzorce ujawnien na tekscie po `_fold` (rdzenie: dowolna odmiana ostatniego slowa i link/kod).
_DISCLOSURE_PATTERNS = (
    r"(?<!\w)link\w*\s+(?:partnersk|afiliacyjn|polecajac|referencyjn)\w*",
    r"(?<!\w)kod\w*\s+(?:polecajac|rabatow|promocyjn|referencyjn)\w*",
    r"(?<!\w)wspolprac\w*\s+(?:reklamow|platn|komercyjn)\w*",
    r"(?<!\w)(?:platn|odplatn)\w*\s+(?:wspolprac|partnerstw)\w*",
    r"(?<!\w)we\s+wspolpracy\s+z(?!\w)",
    r"(?<!\w)material\w*\s+(?:sponsorowan|reklamow|promocyjn)\w*",
    r"(?<!\w)sponsor\w*\s+(?:odcink|material|filmu|tego)\w*",
    r"(?<!\w)partner\w*\s+(?:odcink|material|filmu)\w*",
    r"(?<!\w)lokowani\w*\s+produkt\w*",
    r"(?<!\w)post\w*\s+sponsorowan\w*",
    r"(?<!\w)affiliate\s+(?:link|links|disclosure|disclaimer|program|partner)(?!\w)",
    r"(?<!\w)paid\s+(?:partnership|sponsorship)(?!\w)",
    r"(?<!\w)partner\s+links?(?!\w)",
    r"(?<!\w)referral\s+(?:link|code)s?(?!\w)",
    r"(?<!\w)this\s+video\s+is\s+sponsored(?!\w)",
    r"(?<!\w)includes\s+paid\s+promotion(?!\w)",
    r"(?<!\w)commission\s+(?:if|when|at\s+no)(?!\w)",
    r"(?<!\w)fizetett\s+(?:reklam|hirdetes|egyuttmukodes)\w*",
    # hashtagi
    r"(?<![\w#])#(?:reklama|wspolprac|hirdetes)\w*",
    r"(?<![\w#])#(?:sponsorowane|partner|ad|sponsored)(?!\w)",
    # "reklama" w znacznikach [reklama] / (reklama)
    r"[\[(]\s*reklama\s*[\])]",
)
_DISCLOSURE_RE = re.compile("|".join(_DISCLOSURE_PATTERNS))
# Frazy, ktore po zaprzeczeniu ("not sponsored by", "nie ... paid promotion") nie sa ujawnieniem.
_NEGATABLE_RE = re.compile(r"(?<![\w#])(?:sponsored|paid\s+promotion)(?!\w)")
_NEGATION_RE = re.compile(r"(?<!\w)(?:not|no|never|nie|isn'?t|aren'?t|wasn'?t|without)(?!\w)")
# "Reklama" jako cala pierwsza linia albo przed separatorem (nie "Reklama XTB - czy warto?").
_AD_LINE_RE = re.compile(r"[\[(]?\s*reklama\s*(?:$|[:|\])\-\u2013\u2014])")

AFFILIATE_PARAMS = frozenset(
    {"ref", "aff", "affiliate", "partner", "utm_campaign", "utm_source", "promo", "code", "coupon"}
)
AFFILIATE_PATHS = ("/ref/", "/aff/", "/r/")


def fold_words(text: str) -> str:
    """Tekst do porownan slowo po slowie: bez diakrytykow i wielkosci liter, same [a-z0-9]."""
    return re.sub(r"[^a-z0-9]+", " ", _fold(text)).strip()


def host_of(value: str) -> str:
    """Nazwa hosta bez `www.` (pusta, gdy nie da sie ustalic)."""
    try:
        name = urlsplit(value if "://" in value else "//" + value).hostname or ""
    except ValueError:
        return ""
    return name.lower().rstrip(".").removeprefix("www.")


def _on_domain(host: str, domain: str) -> bool:
    return bool(domain) and (host == domain or host.endswith("." + domain))


def surface_form(text: str, norm: str) -> str:
    """Zapis nazwy tak, jak wystepuje w tekscie (a gdy diakrytyki to uniemozliwiaja - forma znormalizowana)."""
    pattern = r"(?<!\w)" + r"[\W_]+".join(re.escape(w) for w in norm.split()) + r"(?!\w)"
    m = re.search(pattern, text, re.IGNORECASE)
    return m.group() if m else norm


def extract_urls(text: str) -> list[str]:
    """URL-e z tekstu (bez znakow interpunkcji na koncu), w kolejnosci wystapienia, bez duplikatow."""
    return list(dict.fromkeys(m.group().rstrip(_TRAIL) for m in URL_RE.finditer(text or "")))


@dataclass
class Firm:
    knf_id: str
    name: str
    names: list[tuple[str, str]]  # (zapis z rejestru, forma znormalizowana)
    domains: set[str]
    handles: set[str]
    source: str = "curated"  # knf: tylko dokladne dopasowanie nazwy
    active: bool = True
    register: str | None = None


@dataclass
class Match:
    firm: Firm
    kind: int
    score: float
    name_in_ad: str | None
    domain: str | None = None
    weight: int = 1


def _handle_key(value: str) -> str:
    return value.strip().lstrip("@").casefold()


@dataclass
class Registry:
    firms: list[Firm] = field(default_factory=list)
    rows: list[dict] = field(default_factory=list)  # surowe wiersze (slownik YouTube)
    agent_keys: frozenset[str] = frozenset()  # name_key aktywnych agentow KNF

    @classmethod
    def from_rows(cls, rows: list[dict], agent_keys: Any = ()) -> Registry:
        firms = []
        for r in rows:
            name = (r.get("name") or "").strip()
            if not name or not r.get("knf_id"):
                continue
            from_knf = r.get("source", "curated") == "knf"
            names: dict[str, str] = {}
            for raw in [name, *(r.get("aliases") or [])]:
                norm = r.get("normalized_name") if raw == name and r.get("normalized_name") else normalize_name(raw)
                if from_knf and not knf_name_matchable(norm):
                    continue  # zbyt ogolna nazwa ze snapshotu - same falszywe trafienia
                if len(norm) >= MIN_NAME_LEN:
                    names.setdefault(norm, raw.strip())
            if from_knf and not names:
                continue
            firms.append(Firm(
                knf_id=r["knf_id"], name=name,
                names=[(raw, norm) for norm, raw in names.items()],
                domains={d for d in (host_of(x) for x in r.get("domains") or []) if d},
                handles={_handle_key(h) for h in r.get("handles") or [] if h.strip()},
                source="knf" if from_knf else "curated",
                active=r.get("active", True) is not False,
                register=r.get("register"),
            ))
        return cls(firms, list(rows), frozenset(agent_keys))

    # Cache procesu: rejestr zmienia sie rzadko, a zadanie fetch odpala sie setki razy.
    _cache: tuple[float, Registry] | None = None
    _lock = threading.Lock()

    @classmethod
    def from_db(cls, conn: Any, *, ttl_s: float = CACHE_TTL_S, force: bool = False) -> Registry:
        from casedb.store import knf_agent_keys, registry_entries

        with cls._lock:
            now = time.monotonic()
            if not force and cls._cache and now - cls._cache[0] < ttl_s:
                return cls._cache[1]
            registry = cls.from_rows(registry_entries(conn), knf_agent_keys(conn))
            cls._cache = (now, registry)
            return registry

    @classmethod
    def clear_cache(cls) -> None:
        with cls._lock:
            cls._cache = None

    # ------------------------------------------------------------ wzmianki --

    def _fuzzy(self, firm: Firm, words: list[str], grams: dict[int, list[str]]) -> Match | None:
        best: Match | None = None
        for raw, norm in firm.names:
            if len(norm) < FUZZY_MIN_LEN:
                continue
            n = len(norm.split())
            if n not in grams:
                grams[n] = [" ".join(words[i:i + n]) for i in range(max(len(words) - n + 1, 0))]
            hit = process.extractOne(norm, grams[n], scorer=fuzz.ratio, score_cutoff=FUZZY_CUTOFF)
            if hit and (best is None or hit[1] > best.score * 100):
                best = Match(firm, FUZZY, min(hit[1] / 100, _FUZZY_CAP), hit[0])
        return best

    def mentions(self, text: str) -> list[Match]:
        """Najlepsze trafienie dla kazdej firmy wymienionej w tekscie (posortowane od najlepszego)."""
        hosts = [h for h in (host_of(u) for u in extract_urls(text)) if h]
        words_text = fold_words(text)
        padded = f" {words_text} "
        words = words_text.split()[:FUZZY_MAX_WORDS]
        grams: dict[int, list[str]] = {}
        found: list[Match] = []
        for firm in self.firms:
            domain = next((d for d in sorted(firm.domains) for h in hosts if _on_domain(h, d)), None)
            exact = next(((raw, norm) for raw, norm in firm.names if f" {norm} " in padded), None)
            if domain:
                weight = sum(_on_domain(h, domain) for h in hosts)
                found.append(Match(firm, DOMAIN, _SCORE[DOMAIN], surface_form(text, exact[1]) if exact else domain, domain, weight))
            elif exact:
                found.append(Match(firm, EXACT, _SCORE[EXACT], surface_form(text, exact[1]), None, padded.count(f" {exact[1]} ")))
            elif firm.source != "knf" and (fz := self._fuzzy(firm, words, grams)) is not None:
                found.append(fz)
        found.sort(key=lambda m: (m.kind, m.score, m.firm.active, m.weight, len(m.name_in_ad)), reverse=True)
        return found

    # --------------------------------------------------------- publikujacy --

    def match_publisher(self, publisher: Any) -> Firm | None:
        """Firma z rejestru, ktora jest tym publikujacym (domena, handle albo nazwa wyswietlana)."""
        return self.match_publisher_basis(publisher)[0]

    def match_publisher_basis(self, publisher: Any) -> tuple[Firm | None, str]:
        """(firma, podstawa): domain | handle | name_exact | name_prefix | none."""
        if publisher is None:
            return None, "none"
        handle = publisher.handle or ""
        profile = publisher.profile_url or ""
        hosts = {h for h in (host_of(profile), host_of(handle) if "." in handle else "") if h}
        keys = {_handle_key(handle)} if handle else set()
        if profile:
            segments = [s for s in urlsplit(profile).path.split("/") if s]
            if segments:
                keys.add(_handle_key(segments[-1]))
        display = normalize_name(publisher.display_name or "")
        for firm in self.firms:
            if any(_on_domain(h, d) for h in hosts for d in firm.domains):
                return firm, "domain"
            if keys & firm.handles:
                return firm, "handle"
            if display and any(display == norm for _, norm in firm.names):
                return firm, "name_exact"
        firm = self._display_prefix(display)
        return (firm, "name_prefix") if firm else (None, "none")

    def _display_prefix(self, display: str) -> Firm | None:
        """Nazwa wyswietlana zaczyna sie od aliasu firmy (np. "XTB Online Investing"); najdluzszy alias.

        Strony fanow/spolecznosci ("XTB Fan Club") nie sa oficjalne - patrz FAN_TOKENS.
        """
        if not display:
            return None
        padded = display + " "
        best: tuple[int, Firm] | None = None
        for firm in self.firms:
            if firm.source != "curated":
                continue
            for _, norm in firm.names:
                if len(norm) >= MIN_NAME_LEN and padded.startswith(norm + " ") and (best is None or len(norm) > best[0]):
                    best = (len(norm), firm)
        if best is None:
            return None
        rest = display[best[0]:].split()
        return None if any(t in FAN_TOKENS for t in rest) else best[1]


# ------------------------------------------------------------------------ API --


def _negated(folded: str, start: int) -> bool:
    """Czy w ~4 slowach przed pozycja jest zaprzeczenie."""
    before = re.findall(r"[\w']+", folded[max(0, start - 60):start])[-4:]
    return any(_NEGATION_RE.fullmatch(w) for w in before)


def has_disclosure(text: str) -> bool:
    folded = _fold(text or "")
    first_line = next((ln for ln in folded.splitlines() if ln.strip()), "")
    if _DISCLOSURE_RE.search(folded) or _AD_LINE_RE.match(first_line.strip()):
        return True
    return any(not _negated(folded, m.start()) for m in _NEGATABLE_RE.finditer(folded))


def _is_affiliate(url: str) -> bool:
    parts = urlsplit(url if "://" in url else "//" + url)
    if any(k.lower() in AFFILIATE_PARAMS for k, _ in parse_qsl(parts.query, keep_blank_values=True)):
        return True
    path = parts.path.lower()
    return any(path.startswith(p) for p in AFFILIATE_PATHS)


def find_affiliate_link(urls: list[str], firm: Firm | None) -> str | None:
    """Pierwszy URL do domeny firmy (a gdy firma nie ma domen - dowolny) z parametrem/sciezka afiliacyjna."""
    for url in urls:
        if firm and firm.domains and not any(_on_domain(host_of(url), d) for d in firm.domains):
            continue
        if _is_affiliate(url):
            return url
    return None


def document_text(doc: AdDocument) -> str:
    transcript = doc.transcript.text if doc.transcript else ""
    return "\n".join(p for p in (doc.title, doc.text, transcript) if p)


def _inactive_reason(firm: Firm) -> str | None:
    """Tylko rejestr cofniete_zezwolenia oznacza cofniete zezwolenie; reszta nieaktywnych to koniec dzialalnosci."""
    if firm.active:
        return None
    return "cofniete_zezwolenie" if firm.register == "cofniete_zezwolenia" else "zakonczona_dzialalnosc"


def resolve(doc: AdDocument, registry: Registry) -> dict:
    """Pola EntityResolution (patrz docs/MODUL1-ARCHITEKTURA.md) dla jednego dokumentu."""
    text = document_text(doc)
    publisher = doc.publisher
    publisher_firm, basis = registry.match_publisher_basis(publisher)
    mentions = registry.mentions(text)
    best = mentions[0] if mentions else None
    if publisher_firm is not None:
        # Wlasny kanal firmy: preferuj wzmianke o niej samej, a gdy jej brak w tekscie,
        # material i tak dotyczy tej firmy (oficjalny profil bez nazwy w tresci).
        own = next((m for m in mentions if m.firm.knf_id == publisher_firm.knf_id), None)
        best = own or best or Match(firm=publisher_firm, name_in_ad=None, score=1.0,
                                    kind=0, weight=0)

    agent = bool(publisher and registry.agent_keys
                 and knf_name_key(publisher.display_name or "") in registry.agent_keys)
    publisher_known = publisher_firm is not None or agent
    if best is None:
        relation, publisher_authorized = "unknown", publisher_known
    elif publisher_firm is not None and publisher_firm.knf_id == best.firm.knf_id:
        relation, publisher_authorized = "official", True
    else:
        relation, publisher_authorized = "third_party", publisher_known

    disclosure = has_disclosure(text)
    affiliate = find_affiliate_link(extract_urls(text), best.firm) if best else None
    return {
        "publisher_relation": relation,
        "publisher_is_authorized": publisher_authorized,
        "publisher_relation_basis": basis,
        "firm_is_authorized": best is not None and best.firm.active,
        "firm_license_active": best.firm.active if best else None,
        "inactive_reason": _inactive_reason(best.firm) if best else None,
        "mentions_authorized_firm": best is not None,
        "publisher_name": (publisher.display_name or publisher.handle) if publisher else None,
        "firm_name_in_ad": best.name_in_ad if best else None,
        "registry_knf_id": best.firm.knf_id if best else None,
        "registry_official_name": best.firm.name if best else None,
        "registry_score": round(best.score, 3) if best else 0.0,
        "disclosure_found": disclosure,
        "affiliate_link": affiliate,
        "affiliate_without_disclosure": affiliate is not None and not disclosure,
    }


def with_official_flag(doc: AdDocument, resolution: dict) -> AdDocument:
    """Kopia dokumentu z `publisher.is_official_firm_channel` zgodnym z wynikiem resolvera."""
    official = resolution.get("publisher_relation") == "official"
    return doc.model_copy(update={"publisher": doc.publisher.model_copy(
        update={"is_official_firm_channel": official})})

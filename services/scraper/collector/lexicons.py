"""Edytowalne slowniki i zapytania collectora (bez redeployu).

Pliki w COLLECTOR_CONFIG_DIR (domyslnie services/scraper/config/):
    lexicons.yaml   wagi, progi, slowniki fraz, plik person
    queries.yaml    zapytania discover per zrodlo
    personas.json   osoby publiczne (wizerunek w reklamach) + ich oficjalne kanaly

`ConfigFile.get()` sprawdza mtime przy KAZDYM wywolaniu i przeladowuje plik.
Bledny plik (YAML/JSON/brak kluczy) jest odrzucany w calosci: zostaje ostatnia
poprawna wersja, a blad trafia do logu — operator nie zatrzyma collectora
literowka w slowniku.
"""

from __future__ import annotations

import json
import logging
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

log = logging.getLogger("collector.config")

LEXICON_KINDS = ("instrument", "non_instrument", "scam_lure", "impersonation_hook", "finfluencer")


def normalize(text: str) -> str:
    """Male litery, bez znakow diakrytycznych, pojedyncze spacje — dla dopasowan slownikowych."""
    text = unicodedata.normalize("NFKD", (text or "").casefold().replace("ł", "l"))
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text).strip()


def _term_re(term: str) -> re.Pattern[str]:
    # Termin dziala jak prefiks slowa ("mieszkan" -> mieszkanie, mieszkaniu), od granicy slowa.
    return re.compile(r"(?<!\w)" + re.escape(normalize(term)))


@dataclass(frozen=True)
class Persona:
    name: str
    variants: tuple[str, ...]
    official_page_ids: frozenset[str]
    official_domains: frozenset[str]


@dataclass
class Lexicons:
    weights: dict[str, float]
    queue_threshold: float
    analyzer_min_priority: float
    instrument_lane_min: float | None
    terms: dict[str, list[str]]
    personas: list[Persona] = field(default_factory=list)
    _compiled: dict[str, list[tuple[str, re.Pattern[str]]]] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        self._compiled = {k: [(t, _term_re(t)) for t in v] for k, v in self.terms.items()}
        self._persona_res = [
            (p, [_term_re(v) for v in (p.name, *p.variants)]) for p in self.personas
        ]

    def hits(self, kind: str, norm_text: str) -> list[str]:
        """Terminy slownika `kind` obecne w znormalizowanym tekscie (bez powtorzen)."""
        return [term for term, rx in self._compiled.get(kind, []) if rx.search(norm_text)]

    def personas_in(self, norm_text: str) -> list[Persona]:
        return [p for p, rxs in self._persona_res if any(rx.search(norm_text) for rx in rxs)]


def parse_lexicons(raw: dict[str, Any], personas: list[Persona]) -> Lexicons:
    if not isinstance(raw, dict) or "lexicon" not in raw or "weights" not in raw:
        raise ValueError("lexicons.yaml: wymagane klucze 'weights' i 'lexicon'")
    lex = raw["lexicon"] or {}
    unknown = set(lex) - set(LEXICON_KINDS)
    if unknown:
        raise ValueError(f"lexicons.yaml: nieznane slowniki {sorted(unknown)}")
    terms = {k: [str(t) for t in (lex.get(k) or [])] for k in LEXICON_KINDS}
    lane = raw.get("instrument_lane_min")
    return Lexicons(
        weights={str(k): float(v) for k, v in raw["weights"].items()},
        queue_threshold=float(raw.get("queue_threshold", 0.0)),
        analyzer_min_priority=float(raw.get("analyzer_min_priority", 3.0)),
        instrument_lane_min=float(lane) if lane is not None else None,
        terms=terms,
        personas=personas,
    )


def parse_personas(raw: Any) -> list[Persona]:
    items = raw.get("personas", []) if isinstance(raw, dict) else raw
    out = []
    for p in items or []:
        out.append(Persona(
            name=str(p["name"]),
            variants=tuple(str(v) for v in p.get("variants", [])),
            official_page_ids=frozenset(str(x) for x in p.get("official_page_ids", [])),
            official_domains=frozenset(str(x).lower() for x in p.get("official_domains", [])),
        ))
    return out


class ConfigFile:
    """Plik konfiguracyjny z przeladowaniem po mtime i zachowaniem ostatniej poprawnej wersji."""

    def __init__(self, path: Path, parse) -> None:
        self.path = Path(path)
        self._parse = parse
        self._mtime: float | None = None
        self._value: Any = None
        self.last_error: str | None = None

    def get(self) -> Any:
        try:
            mtime = self.path.stat().st_mtime
        except OSError as exc:
            if self._value is None:
                raise FileNotFoundError(f"brak pliku konfiguracji {self.path}") from exc
            return self._value
        if mtime != self._mtime:
            try:
                self._value = self._parse(self.path)
                self.last_error = None
                log.info("przeladowano %s", self.path.name)
            except Exception as exc:
                self.last_error = f"{type(exc).__name__}: {exc}"
                log.error("odrzucono %s (zostaje poprzednia wersja): %s", self.path.name, self.last_error)
                if self._value is None:
                    raise
            self._mtime = mtime
        return self._value


def _load_yaml(path: Path) -> Any:
    import yaml

    return yaml.safe_load(path.read_text(encoding="utf-8"))


class CollectorConfigFiles:
    """lexicons.yaml + personas.json + queries.yaml, kazdy przeladowywany niezaleznie."""

    def __init__(self, config_dir: Path) -> None:
        self.dir = Path(config_dir)
        self._personas = ConfigFile(self.dir / "personas.json",
                                    lambda p: parse_personas(json.loads(p.read_text(encoding="utf-8"))))
        self._lexicons = ConfigFile(self.dir / "lexicons.yaml", self._parse_lexicons)
        self._queries = ConfigFile(self.dir / "queries.yaml", self._parse_queries)
        self._personas_seen: Any = None

    def _parse_lexicons(self, path: Path) -> Lexicons:
        personas = self._personas.get() if (self.dir / "personas.json").exists() else []
        self._personas_seen = personas
        return parse_lexicons(_load_yaml(path), personas)

    @staticmethod
    def _parse_queries(path: Path) -> dict[str, list[dict]]:
        raw = _load_yaml(path) or {}
        out: dict[str, list[dict]] = {}
        for source, items in raw.items():
            specs = []
            for item in items or []:
                spec = {"q": str(item["q"]), "tag": str(item.get("tag", "")),
                        "type": str(item.get("type", "keyword_unordered"))}
                specs.append(spec)
            out[str(source)] = specs
        return out

    def lexicons(self) -> Lexicons:
        # zmiana personas.json tez wymusza ponowne zbudowanie slownikow
        if (self.dir / "personas.json").exists() and self._personas.get() is not self._personas_seen:
            self._lexicons._mtime = None
        return self._lexicons.get()

    def queries(self) -> dict[str, list[dict]]:
        return self._queries.get()

    def errors(self) -> dict[str, str]:
        return {f.path.name: f.last_error for f in (self._lexicons, self._queries, self._personas) if f.last_error}

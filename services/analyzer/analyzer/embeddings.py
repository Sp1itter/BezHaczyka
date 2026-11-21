"""Warstwa wektorowa — par. 6.7 design doca.

Specyfikacja wymaga wprost "reprezentacji wektorowej w postaci tokenow
i embeddingow", wiec ta warstwa jest NIEUSUWALNA z zakresu.

Zeby nie byla atrapa, ma trzy zadania:
  1. deduplikacja i rozpoznawanie kampanii (simhash + cosine),
  2. kNN jako druga opinia, niezalezna od LLM,
  3. wyszukiwanie semantyczne w dashboardzie.

Model: bge-m3 przez Ollame (MIT, 1024 wymiary, 8192 tokenow kontekstu).
Swiadomie zamiast sentence-transformers: reuzywa runtime, ktory i tak mamy,
czyli zero torch w obrazie i ~1,2 GB VRAM zamiast kilku.
"""

from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from collections import Counter

from analyzer.contracts import Embedding
from analyzer.llm import LlmError, OllamaClient

SIMHASH_BITS = 64

# Progi dedupu. Dobrane konserwatywnie: lepiej nie zlaczyc dwoch wariantow,
# niz zlaczyc dwie rozne reklamy i ukryc naruszenie przed nadzorca.
NEAR_DUPLICATE_COSINE = 0.95
SAME_CAMPAIGN_COSINE = 0.88
SIMHASH_MAX_DISTANCE = 6


# --------------------------------------------------------------------------- #
# Normalizacja i tokenizacja — "tokeny" z wymogu specyfikacji
# --------------------------------------------------------------------------- #


def normalize(text: str) -> str:
    """Male litery, bez ogonkow, bez interpunkcji, zwiniete spacje."""
    lowered = text.lower()
    decomposed = unicodedata.normalize("NFKD", lowered)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    stripped = stripped.replace("ł", "l")
    stripped = re.sub(r"[^\w\s]", " ", stripped)
    return re.sub(r"\s+", " ", stripped).strip()


def tokenize(text: str) -> list[str]:
    """Tokeny do simhasha. Odrzucamy bardzo krotkie, bo szum."""
    return [t for t in normalize(text).split() if len(t) > 2]


# --------------------------------------------------------------------------- #
# Simhash — lapie warianty niemal identyczne (przestawione slowa, literowki)
# --------------------------------------------------------------------------- #


def simhash(text: str, bits: int = SIMHASH_BITS) -> int:
    tokens = tokenize(text)
    if not tokens:
        return 0

    vector = [0] * bits
    for token, weight in Counter(tokens).items():
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        value = int.from_bytes(digest, "big")
        for i in range(bits):
            if value >> i & 1:
                vector[i] += weight
            else:
                vector[i] -= weight

    out = 0
    for i, v in enumerate(vector):
        if v > 0:
            out |= 1 << i
    return out


def simhash_hex(text: str) -> str:
    """Postac do zapisu w AdDocument.simhash."""
    return f"{simhash(text):016x}"


def hamming_distance(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def is_near_duplicate_simhash(
    text_a: str, text_b: str, max_distance: int = SIMHASH_MAX_DISTANCE
) -> bool:
    return hamming_distance(simhash(text_a), simhash(text_b)) <= max_distance


# --------------------------------------------------------------------------- #
# Embeddingi i cosine — lapia warianty PRZEREDAGOWANE, ktorych simhash nie widzi
# --------------------------------------------------------------------------- #


def cosine(a: list[float], b: list[float]) -> float:
    """Podobienstwo kosinusowe. Zwraca 0.0 dla wektorow zerowych i roznych dlugosci,
    zamiast rzucac — wektor moze przyjsc uszkodzony z bazy."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return max(-1.0, min(1.0, dot / (na * nb)))


def embed_document_text(
    text: str, client: OllamaClient | None = None
) -> Embedding | None:
    """Wektor bge-m3 dla tekstu dokumentu.

    Zwraca None, gdy model jest niedostepny — embedding jest wazny, ale jego
    brak nie moze zablokowac oceny regul. Dedup wtedy opiera sie na samym
    simhashu, co jest degradacja, nie awaria.
    """
    if not text.strip():
        return None
    client = client or OllamaClient()
    try:
        vector = client.embed(text)
    except LlmError:
        return None
    if not vector:
        return None
    return Embedding(model=client.embed_model, dim=len(vector), vector=vector)


# --------------------------------------------------------------------------- #
# Kampanie: grupowanie wariantow tej samej reklamy
# --------------------------------------------------------------------------- #


def classify_similarity(
    cos: float, simhash_dist: int | None = None
) -> str:
    """Jak blisko siebie sa dwa materialy.

    'duplicate'      — ten sam material (ewentualnie literowki)
    'same_campaign'  — przeredagowany wariant tej samej kampanii
    'unrelated'      — rozne materialy

    W dashboardzie 'same_campaign' zwija siedem wierszy w jeden z licznikiem
    wariantow. To realna oszczednosc pracy nadzorcy, nie ozdoba.
    """
    if simhash_dist is not None and simhash_dist <= SIMHASH_MAX_DISTANCE:
        return "duplicate"
    if cos >= NEAR_DUPLICATE_COSINE:
        return "duplicate"
    if cos >= SAME_CAMPAIGN_COSINE:
        return "same_campaign"
    return "unrelated"


def knn_score(
    vector: list[float],
    labelled: list[tuple[list[float], bool]],
    k: int = 5,
) -> float | None:
    """Druga opinia niezalezna od LLM: udzial naruszen wsrod k najblizszych
    sasiadow ze zbioru zlotego, wazony podobienstwem.

    `labelled` to pary (wektor, czy_naruszenie). Zwraca None, gdy zbior jest
    za maly, zeby cokolwiek znaczyl.
    """
    if not vector or len(labelled) < k:
        return None

    scored = sorted(
        ((cosine(vector, v), is_violation) for v, is_violation in labelled),
        key=lambda pair: pair[0],
        reverse=True,
    )[:k]

    weights = sum(max(c, 0.0) for c, _ in scored)
    if weights == 0.0:
        return None
    violations = sum(max(c, 0.0) for c, is_violation in scored if is_violation)
    return round(violations / weights, 3)

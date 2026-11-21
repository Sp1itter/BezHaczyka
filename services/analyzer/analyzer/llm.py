"""Klient Ollamy — Bielik (reguly semantyczne) i bge-m3 (embeddingi).

Po REST, bez dodatkowego SDK: jedna zaleznosc (httpx) mniej do audytu
w lancuchu dostaw, a API Ollamy jest trywialne.

Transport jest WSTRZYKIWANY (`client`), zeby cala logike dalo sie przetestowac
bez dzialajacej Ollamy i bez pobranych 6 GB modeli. Produkcyjnie uzywa sie
domyslnego klienta httpx.
"""

from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass
from pathlib import Path

import httpx

DEFAULT_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
DEFAULT_MODEL = os.getenv(
    "OLLAMA_MODEL", "SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0"
)
DEFAULT_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "bge-m3")

# POWTARZALNOSC. Karta Bielika zaleca temperature 0.2, ale przy 0.1 werdykty
# FAKTYCZNIE zmienialy sie miedzy przebiegami na tym samym materiale: ta sama
# reklama raz lamala reguly 1, 2 i 18, raz tylko 1 i 2. Dla narzedzia
# nadzorczego to nie do przyjecia z dwoch powodow: nadzorca nie moze dostawac
# innego ustalenia przy kazdym odswiezeniu, a demo przed jury musi zachowac
# sie tak samo jak na probie.
# Dlatego temperature 0 (dekodowanie zachlanne) plus staly `seed`.
DEFAULT_TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0"))
DEFAULT_SEED = int(os.getenv("OLLAMA_SEED", "42"))
DEFAULT_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT_S", "120"))

# SZYBKOSC. Ollama 0.5.x domyslnie uzywa num_ctx 2048 i po cichu obcina POCZATEK
# zbyt dlugiego promptu, czyli instrukcje. Dlatego jawnie ustawiamy okno,
# limit generowania i keep_alive (model zostaje w VRAM miedzy dokumentami).
CHARS_PER_TOKEN = 3.5  # szacunek dla polskiego tekstu
TRUNCATION_MARKER = "\n[...]\n"


def _num_ctx() -> int:
    return int(os.getenv("LLM_NUM_CTX", "4096"))


def _num_predict() -> int:
    return int(os.getenv("LLM_NUM_PREDICT", "400"))


def _keep_alive() -> str:
    return os.getenv("LLM_KEEP_ALIVE", "30m")


def fit_material(
    material: str,
    prompt_chars: int = 0,
    num_ctx: int | None = None,
    num_predict: int | None = None,
) -> tuple[str, bool]:
    """Przytnij material tak, by prompt + material + odpowiedz zmiescily sie w num_ctx.

    Zachowuje POCZATEK (70% budzetu) i KONIEC (30%) — ostrzezenia o ryzyku
    czesto stoja na koncu. Zwraca (material, czy_przyciety).
    """
    num_ctx = _num_ctx() if num_ctx is None else num_ctx
    num_predict = _num_predict() if num_predict is None else num_predict
    # 10% zapasu na bledy szacunku
    budget_tokens = (num_ctx - num_predict) * 0.9
    budget = int(budget_tokens * CHARS_PER_TOKEN) - prompt_chars
    budget = max(budget, 200)
    if len(material) <= budget:
        return material, False
    keep = max(budget - len(TRUNCATION_MARKER), 100)
    head = int(keep * 0.7)
    tail = keep - head
    return material[:head] + TRUNCATION_MARKER + material[len(material) - tail :], True


# Wspolny, watkowo-bezpieczny klient httpx (pula polaczen) na adres bazowy.
_SHARED: dict[tuple[str, float], httpx.Client] = {}
_SHARED_LOCK = threading.Lock()


def _shared_client(base_url: str, timeout: float) -> httpx.Client:
    key = (base_url, timeout)
    with _SHARED_LOCK:
        c = _SHARED.get(key)
        if c is None:
            c = httpx.Client(
                base_url=base_url,
                timeout=timeout,
                limits=httpx.Limits(max_connections=16, max_keepalive_connections=8),
            )
            _SHARED[key] = c
        return c


PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


class LlmError(RuntimeError):
    """Ollama niedostepna albo zwrocila cos, czego nie da sie uzyc.

    Reguly MUSZA to lapac i zwracac `not_applicable` — awaria modelu nie jest
    dowodem naruszenia i nie moze wywrocic calego potoku w trakcie demo.
    """


@dataclass
class OllamaClient:
    base_url: str = DEFAULT_BASE_URL
    model: str = DEFAULT_MODEL
    embed_model: str = DEFAULT_EMBED_MODEL
    temperature: float = DEFAULT_TEMPERATURE
    seed: int = DEFAULT_SEED
    timeout: float = DEFAULT_TIMEOUT
    client: httpx.Client | None = None

    def _http(self) -> httpx.Client:
        if self.client is not None:
            return self.client
        return _shared_client(self.base_url, self.timeout)

    # ----------------------------------------------------------------- #
    # Generowanie
    # ----------------------------------------------------------------- #

    def generate_json(self, prompt: str) -> dict:
        """Wywolaj model z wymuszonym JSON-em i zwroc sparsowany slownik.

        `format: "json"` w Ollamie wymusza skladniowo poprawny JSON, ale NIE
        gwarantuje naszego schematu — walidacja kształtu nalezy do wolajacego.
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            # `seed` razem z temperature 0 daje powtarzalne werdykty — wymog demo
            # i uczciwosci wobec nadzorcy (patrz komentarz przy DEFAULT_TEMPERATURE).
            "keep_alive": _keep_alive(),
            "options": {
                "temperature": self.temperature,
                "seed": self.seed,
                "num_ctx": _num_ctx(),
                "num_predict": _num_predict(),
            },
        }
        try:
            resp = self._http().post("/api/generate", json=payload)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise LlmError(f"Ollama niedostepna pod {self.base_url}: {exc}") from exc

        try:
            raw = resp.json()["response"]
        except (KeyError, ValueError) as exc:
            raise LlmError(f"Nieoczekiwana odpowiedz Ollamy: {exc}") from exc

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LlmError(
                f"Model zwrocil niepoprawny JSON: {raw[:200]!r}"
            ) from exc

        if not isinstance(parsed, dict):
            raise LlmError(f"Oczekiwano obiektu JSON, dostano {type(parsed).__name__}")
        return parsed

    # ----------------------------------------------------------------- #
    # Embeddingi
    # ----------------------------------------------------------------- #

    def embed(self, text: str) -> list[float]:
        """Wektor bge-m3 (1024 wymiary).

        Obsluguje oba kształty odpowiedzi Ollamy: nowszy /api/embed
        ("embeddings": [[...]]) i starszy ("embedding": [...]).
        """
        try:
            resp = self._http().post(
                "/api/embed", json={"model": self.embed_model, "input": text}
            )
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPError as exc:
            raise LlmError(f"Ollama (embed) niedostepna: {exc}") from exc
        except ValueError as exc:
            raise LlmError(f"Ollama (embed) zwrocila nie-JSON: {exc}") from exc

        if "embeddings" in data and data["embeddings"]:
            return list(data["embeddings"][0])
        if "embedding" in data:
            return list(data["embedding"])
        raise LlmError(f"Brak wektora w odpowiedzi: {list(data)}")

    # ----------------------------------------------------------------- #
    # Diagnostyka
    # ----------------------------------------------------------------- #

    def health(self) -> bool:
        """Czy Ollama odpowiada. Uzywane przez /health API i przed demo."""
        try:
            resp = self._http().get("/api/tags")
            return resp.status_code == 200
        except httpx.HTTPError:
            return False

    def available_models(self) -> list[str]:
        try:
            resp = self._http().get("/api/tags")
            resp.raise_for_status()
            return [m["name"] for m in resp.json().get("models", [])]
        except (httpx.HTTPError, ValueError, KeyError):
            return []


def load_prompt(name: str) -> str:
    """Wczytaj szablon promptu z analyzer/prompts/.

    Prompty trzymamy w plikach, nie w kodzie — iterujemy je na zbiorze zlotym
    przez cala noc i nie chcemy za kazdym razem ruszac Pythona.
    """
    path = PROMPTS_DIR / name
    if not path.exists():
        raise LlmError(f"Brak szablonu promptu: {path}")
    return path.read_text(encoding="utf-8")

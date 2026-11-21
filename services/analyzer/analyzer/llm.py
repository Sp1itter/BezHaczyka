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
from dataclasses import dataclass
from pathlib import Path

import httpx

DEFAULT_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
DEFAULT_MODEL = os.getenv(
    "OLLAMA_MODEL", "SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0"
)
DEFAULT_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "bge-m3")

# Bielik jest wrazliwy na temperature — karta modelu zaleca 0.2.
# Dla zadan klasyfikacyjnych chcemy powtarzalnosci, wiec jeszcze nizej.
DEFAULT_TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0.1"))
DEFAULT_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT_S", "120"))

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
    timeout: float = DEFAULT_TIMEOUT
    client: httpx.Client | None = None

    def _http(self) -> httpx.Client:
        if self.client is not None:
            return self.client
        return httpx.Client(base_url=self.base_url, timeout=self.timeout)

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
            "options": {"temperature": self.temperature},
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

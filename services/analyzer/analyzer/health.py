"""Endpoint /health — jedyny HTTP wystawiany przez worker analyzera (/scaling jest w analyzer.autoscaler).

Brak Ollamy NIE jest bledem fatalnym: reguly LLM zwracaja wtedy
not_applicable z powodem, reguly DET licza sie normalnie. Status "degraded"
jawnie pokazuje, ze czesc ocen jest niedostepna.
"""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

from analyzer.llm import OllamaClient


def health_payload(llm_client: OllamaClient | None = None, api=None) -> dict:
    """Zwroc stan serwisu w ksztalcie z docs/MODUL1-ARCHITEKTURA.md. Nie rzuca wyjatkow."""
    client = llm_client or OllamaClient()
    try:
        ollama = bool(client.health())
        models = client.available_models() if ollama else []
    except Exception:  # noqa: BLE001 - /health nie moze sam past
        ollama, models = False, []
    return {
        "status": "ok" if ollama else "degraded",
        "ollama": ollama,
        "models": models,
        "profile": os.getenv("PROFILE", "gpu8"),
    }


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 - nazwa narzucona przez http.server
        if self.path == "/health":
            status, payload = 200, health_payload()
        else:
            self.send_response(404)
            self.end_headers()
            return
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        return


HEALTH_PORT = int(os.getenv("HEALTH_PORT", "8081"))


def serve(port: int = HEALTH_PORT) -> None:
    """Uruchom serwer /health (blokuje)."""
    HTTPServer(("0.0.0.0", port), _Handler).serve_forever()  # noqa: S104 - siec compose

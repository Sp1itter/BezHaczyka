"""Klient serwisu api (osoba C) — pobranie dokumentu i wyslanie Findingu.

Transport jest WSTRZYKIWANY (`client`), jak w llm.py, zeby dalo sie testowac
bez dzialajacego API. Dozwolone sa wylacznie adresy lokalne i nazwy serwisow
docker-compose — zadnych adresow zewnetrznych.
"""

from __future__ import annotations

import os
from urllib.parse import urlparse

import httpx
from pydantic import ValidationError

from analyzer.contracts import AdDocument, Finding

DEFAULT_API_URL = "http://api:8000"
DEFAULT_TIMEOUT = float(os.getenv("API_TIMEOUT_S", "30"))
_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


class ApiError(RuntimeError):
    """Blad komunikacji z serwisem api (siec, status HTTP, zly ksztalt)."""


def _check_local(base_url: str) -> None:
    host = urlparse(base_url).hostname or ""
    # Nazwa serwisu compose nie zawiera kropki (api, valkey); FQDN/IP publiczne tak.
    if host in _LOCAL_HOSTS or (host and "." not in host):
        return
    raise ApiError(f"Niedozwolony adres API (tylko lokalny/compose): {base_url}")


class ApiClient:
    def __init__(
        self,
        base_url: str | None = None,
        client: httpx.Client | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.base_url = (base_url or os.getenv("API_BASE_URL", DEFAULT_API_URL)).rstrip("/")
        _check_local(self.base_url)
        self.timeout = timeout
        self.client = client

    def _http(self) -> httpx.Client:
        if self.client is not None:
            return self.client
        return httpx.Client(base_url=self.base_url, timeout=self.timeout)

    def get_document(self, document_id: str) -> AdDocument:
        try:
            resp = self._http().get(f"/documents/{document_id}")
            resp.raise_for_status()
            return AdDocument.model_validate(resp.json())
        except httpx.HTTPError as exc:
            raise ApiError(f"Nie pobrano dokumentu {document_id}: {exc}") from exc
        except (ValueError, ValidationError) as exc:
            raise ApiError(f"Niepoprawny dokument {document_id}: {exc}") from exc

    def post_document(self, doc: AdDocument) -> None:
        # API zwraca 201 (nowy) lub 200 (zaktualizowany); reszta to blad.
        try:
            resp = self._http().post("/documents", json=doc.model_dump(mode="json"))
        except httpx.HTTPError as exc:
            raise ApiError(f"Nie wyslano dokumentu {doc.id}: {exc}") from exc
        if resp.status_code not in (200, 201):
            raise ApiError(f"Nie wyslano dokumentu {doc.id}: HTTP {resp.status_code}")

    def post_finding(self, finding: Finding, *_args, **_kwargs) -> None:
        # Dodatkowe argumenty (dokument, podsumowanie) ignorujemy: API ich nie przyjmuje.
        try:
            resp = self._http().post("/findings", json=finding.model_dump(mode="json"))
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise ApiError(f"Nie wyslano findingu {finding.id}: {exc}") from exc

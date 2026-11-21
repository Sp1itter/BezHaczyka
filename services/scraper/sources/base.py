"""Interfejs zrodla danych — ZAMROZONY (design doc par. 10).

Dodanie nowego zrodla nie rusza rdzenia: implementujesz `discover` i `fetch`.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol, runtime_checkable

from contracts import AdDocument


@runtime_checkable
class Source(Protocol):
    name: str

    def discover(self, query: str) -> Iterable[str]: ...  # -> URL-e

    def fetch(self, url: str) -> AdDocument: ...


class SourceError(Exception):
    """Zrodlo nie zwrocilo uzytecznych danych (zmiana DOM/JSON, timeout)."""


class SourceBlocked(SourceError):
    """Platforma nas zablokowala (checkpoint, ban IP, wymuszone logowanie).

    Osobny typ, bo reakcja jest inna niz przy zwyklym bledzie: NIE ponawiamy
    w petli, tylko otwieramy circuit breaker i przechodzimy na korpus offline
    (par. 10, anty-cel „demo zalezne od wifi").
    """

"""Magazyn danych analyzera oparty o pakiet `casedb` (Postgres).

Ten sam interfejs co ApiClient (`get_document`, `post_finding`), plus operacje
potrzebne do wykrywania zmian. Import casedb jest LENIWY: modul musi sie
importowac takze bez casedb i bez psycopg. Kazda operacja konczy sie commitem,
a kazdy blad jest opakowany w StoreError (podklasa ApiError), wiec worker
obsluguje go tak samo jak blad API.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from pydantic import ValidationError

from analyzer.api_client import ApiError
from analyzer.contracts import AdDocument, ChangeEvent, Finding

log = logging.getLogger(__name__)


class StoreError(ApiError):
    """Blad warstwy danych (polaczenie, SQL, zly ksztalt rekordu)."""


def _casedb():
    """Leniwy import pakietu casedb (store i db)."""
    try:
        from casedb import db, store
    except ImportError as exc:  # pragma: no cover - zalezy od srodowiska
        raise StoreError(f"Brak pakietu casedb: {exc}") from exc
    return db, store


def _vector_of(embedding: object) -> list[float] | None:
    """Wyciaga liste floatow z Embedding / dict / listy."""
    if embedding is None:
        return None
    if isinstance(embedding, dict):
        embedding = embedding.get("vector")
    elif hasattr(embedding, "vector"):
        embedding = embedding.vector
    if not embedding:
        return None
    return [float(x) for x in embedding]


def _normalize_doc(raw: dict) -> dict:
    """Embedding z bazy bywa gola lista - kontrakt wymaga obiektu."""
    raw = dict(raw)
    emb = raw.get("embedding")
    if isinstance(emb, (list, tuple)):
        raw["embedding"] = {"vector": [float(x) for x in emb], "dim": len(emb)} if emb else None
    return raw


class DbStore:
    def __init__(self, conn: Any = None, url: str | None = None) -> None:
        self._conn = conn
        self._url = url or os.getenv("DATABASE_URL")

    def _connection(self):
        if self._conn is None:
            db, _ = _casedb()
            try:
                self._conn = db.connect(self._url)
            except Exception as exc:
                raise StoreError(f"Nie polaczono z baza: {exc}") from exc
        return self._conn

    def close(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

    def _run(self, what: str, fn):
        """Wykonaj operacje z commitem; blad -> rollback + StoreError."""
        _, store = _casedb()
        conn = self._connection()
        try:
            result = fn(store, conn)
            conn.commit()
            return result
        except StoreError:
            raise
        except Exception as exc:
            try:
                conn.rollback()
            except Exception:  # polaczenie moze byc martwe
                self._conn = None
            raise StoreError(f"{what}: {exc}") from exc

    def get_document(self, document_id: str) -> AdDocument:
        raw = self._run(
            f"Nie pobrano dokumentu {document_id}",
            lambda store, conn: store.get_document(conn, document_id),
        )
        if raw is None:
            raise StoreError(f"Brak dokumentu {document_id}")
        try:
            return AdDocument.model_validate(_normalize_doc(raw))
        except (ValueError, ValidationError) as exc:
            raise StoreError(f"Niepoprawny dokument {document_id}: {exc}") from exc

    def post_finding(
        self,
        finding: Finding,
        document: AdDocument | None = None,
        summary: str | None = None,
        summary_engine: str | None = None,
    ) -> None:
        snapshot = document.model_dump(mode="json") if document is not None else None

        # Ponowna analiza tego samego dokumentu AKTUALIZUJE istniejacy finding
        # (to samo id), zamiast dokladac duplikat. save_finding robi upsert po id
        # i nie dotyka kolumn pracy analityka (assignee, review_*, finding_events);
        # status zachowujemy, bo to tez praca analityka (np. triage).
        try:
            existing = self._run(
                f"Nie sprawdzono istniejacego findingu {finding.document_id}",
                lambda store, conn: store.latest_finding(conn, finding.document_id),
            )
        except StoreError as exc:
            log.warning("%s - zapis jako nowy finding", exc)
            existing = None
        if existing:
            finding.id = str(existing["id"])
            if existing.get("status"):
                finding.status = existing["status"]

        self._run(
            f"Nie zapisano findingu {finding.id}",
            lambda store, conn: store.save_finding(
                conn, finding.model_dump(mode="json"), snapshot
            ),
        )
        if summary is not None:
            self.save_summary(finding.id, summary, summary_engine)

    def save_summary(
        self, finding_id: str, summary: str | None, summary_engine: str | None
    ) -> None:
        """Zapis (albo wyczyszczenie, gdy None) podsumowania findingu.

        Osobna transakcja (kolumny z migracji 015): blad nie cofa zapisanego findingu
        i nie leci wyzej.
        """
        try:
            self._run(
                f"Nie zapisano podsumowania {finding_id}",
                lambda store, conn: conn.execute(
                    "UPDATE findings SET summary = %s, summary_engine = %s WHERE id = %s",
                    (summary, summary_engine if summary is not None else None, finding_id),
                ),
            )
        except StoreError as exc:
            log.error("%s", exc)

    def previous(self, document_id: str) -> tuple[Finding, AdDocument] | None:
        """Ostatni zapisany Finding i migawka dokumentu z tamtego przebiegu."""
        raw = self._run(
            f"Nie pobrano poprzedniego findingu {document_id}",
            lambda store, conn: store.latest_finding(conn, document_id),
        )
        if not raw:
            return None
        raw = dict(raw)
        snapshot = raw.pop("document_snapshot", None)
        if not snapshot:
            return None
        try:
            return (
                Finding.model_validate(raw),
                AdDocument.model_validate(_normalize_doc(snapshot)),
            )
        except (ValueError, ValidationError) as exc:
            log.warning("Poprzedni finding %s nieczytelny: %s", document_id, exc)
            return None

    def save_change_event(self, event: ChangeEvent) -> None:
        self._run(
            f"Nie zapisano zdarzenia {event.id}",
            lambda store, conn: store.save_change_event(conn, event.model_dump(mode="json")),
        )

    def save_vectors(self, doc: AdDocument) -> None:
        self._run(
            f"Nie zapisano wektorow {doc.id}",
            lambda store, conn: store.save_vectors(
                conn, doc.id, _vector_of(doc.embedding), doc.simhash
            ),
        )

    def set_status(self, document_id: str, status: str, error: str | None = None) -> None:
        self._run(
            f"Nie ustawiono statusu {document_id}",
            lambda store, conn: store.set_status(conn, document_id, status, error),
        )

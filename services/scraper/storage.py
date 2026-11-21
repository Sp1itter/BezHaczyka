"""Zapis artefaktow (HTML, zrzuty, wideo) do SeaweedFS po S3 API.

URI w AdDocument maja zawsze postac `s3://<bucket>/<klucz>` — takze w trybie
lokalnym, zeby testy i produkcja produkowaly identyczne dokumenty.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Protocol


class BlobStore(Protocol):
    def put(self, bucket: str, key: str, data: bytes, content_type: str) -> str: ...


class LocalBlobStore:
    """Katalog na dysku: `<root>/<bucket>/<klucz>`. Testy i praca bez SeaweedFS."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def put(self, bucket: str, key: str, data: bytes, content_type: str) -> str:
        path = self.root / bucket / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return f"s3://{bucket}/{key}"

    def path_of(self, uri: str) -> Path:
        bucket, _, key = uri.removeprefix("s3://").partition("/")
        return self.root / bucket / key


class S3BlobStore:
    """SeaweedFS (Apache-2.0) przez boto3. Konfiguracja wylacznie z `.env`."""

    def __init__(self, endpoint: str, access_key: str, secret_key: str, region: str = "us-east-1") -> None:
        import boto3  # import leniwy: testy nie wymagaja boto3

        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )
        self._buckets: set[str] = set()

    def _ensure_bucket(self, bucket: str) -> None:
        if bucket in self._buckets:
            return
        try:
            self.client.head_bucket(Bucket=bucket)
        except Exception:  # noqa: BLE001 — brak kubelka = tworzymy
            self.client.create_bucket(Bucket=bucket)
        self._buckets.add(bucket)

    def put(self, bucket: str, key: str, data: bytes, content_type: str) -> str:
        self._ensure_bucket(bucket)
        self.client.put_object(Bucket=bucket, Key=key, Body=data, ContentType=content_type)
        return f"s3://{bucket}/{key}"


def blob_store_from_env() -> BlobStore:
    endpoint = os.getenv("S3_ENDPOINT")
    if endpoint:
        return S3BlobStore(
            endpoint=endpoint,
            access_key=os.environ["S3_ACCESS_KEY"],
            secret_key=os.environ["S3_SECRET_KEY"],
        )
    return LocalBlobStore(os.getenv("SCRAPER_DATA_DIR", "data/blobs"))

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parent / "fixtures"
REPO_ROOT = Path(__file__).resolve().parents[3]


def _launch():
    sync_api = pytest.importorskip("playwright.sync_api")
    pw = sync_api.sync_playwright().start()
    try:
        return pw, pw.chromium.launch(headless=True, args=["--disable-gpu"])
    except Exception as exc:  # noqa: BLE001
        pw.stop()
        pytest.skip(f"Chromium niedostepny (`python -m playwright install chromium`): {exc}")


@pytest.fixture(scope="module")
def browser():
    """Chromium dla testow sondy. Zasieg MODULU: sync API Playwrighta nie pozwala
    na dwie instancje naraz w jednym watku, a FacebookAdsSource startuje wlasna."""
    pw, b = _launch()
    yield b
    b.close()
    pw.stop()


@pytest.fixture(scope="session")
def chromium_available() -> bool:
    """Tylko sprawdzenie (i pominiecie testu, gdy brak Chromium) — nic nie zostaje uruchomione."""
    pw, b = _launch()
    b.close()
    pw.stop()
    return True

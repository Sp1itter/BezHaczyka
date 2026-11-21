"""Testy automatu zgodnosci (tools/check_compliance.py).

Check, ktory tylko swieci na zielono, jest bezwartosciowy — te testy dowodza,
ze detektory FAKTYCZNIE wylapuja naruszenia, a nie przechodza bo nic nie robia.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import check_compliance as cc  # noqa: E402


def _file(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


class TestWylapujeNaruszenia:
    def test_zewnetrzny_adres_jest_wylapywany(self, tmp_path: Path) -> None:
        f = _file(tmp_path, "bad.py", 'URL = "https://api.openai.com/v1/chat"')
        problems = cc.check_external_hosts([f])
        assert problems, "zewnetrzny adres musi byc wylapany"
        assert "api.openai.com" in problems[0]

    def test_zewnetrzne_api_modelu_jest_wylapywane(self, tmp_path: Path) -> None:
        f = _file(tmp_path, "bad.py", "from openai import OpenAI")
        assert cc.check_forbidden_patterns([f])

    def test_colab_jest_wylapywany(self, tmp_path: Path) -> None:
        """Dokladnie ten przypadek: hostowane srodowisko pod wiekszy model."""
        f = _file(tmp_path, "notes.txt", "model odpalamy na Colab")
        problems = cc.check_forbidden_patterns([f])
        assert problems
        assert "on-premise" in problems[0]

    def test_ngrok_jest_wylapywany(self, tmp_path: Path) -> None:
        f = _file(tmp_path, "cfg.yml", "tunnel: ngrok")
        assert cc.check_forbidden_patterns([f])

    def test_minio_jest_wylapywane(self, tmp_path: Path) -> None:
        f = _file(tmp_path, "requirements.txt", "minio==7.2.0\n")
        problems = cc.check_forbidden_deps([f])
        assert problems
        assert "SeaweedFS" in problems[0]

    def test_redis_na_sspl_jest_wylapywany(self, tmp_path: Path) -> None:
        f = _file(tmp_path, "docker-compose.yml", "  image: redis:7.4-alpine\n")
        problems = cc.check_forbidden_deps([f])
        assert problems
        assert "Valkey" in problems[0]

    def test_model_na_licencji_gemma_jest_wylapywany(self, tmp_path: Path) -> None:
        f = _file(
            tmp_path, "requirements.txt", "# mmlw-retrieval-roberta-large-v2\n"
        )
        problems = cc.check_forbidden_deps([f])
        assert problems
        assert "gemma" in problems[0]

    def test_klucz_api_w_kodzie_jest_wylapywany(self, tmp_path: Path) -> None:
        f = _file(tmp_path, "cfg.py", 'KEY = "sk-abcdefghijklmnopqrstuvwxyz0123"')
        assert cc.check_secrets([f])

    def test_plik_env_w_repo_jest_wylapywany(self, tmp_path: Path) -> None:
        f = _file(tmp_path, ".env", "SECRET=1")
        problems = cc.check_secrets([f])
        assert problems
        assert "sekretami" in problems[0]

    def test_nieprzypieta_wersja_jest_wylapywana(self, tmp_path: Path) -> None:
        f = _file(tmp_path, "requirements.txt", "httpx\n")
        problems = cc.check_pinned_versions([f])
        assert problems
        assert "nieprzypieta" in problems[0]


class TestNieZglaszaFalszywychAlarmow:
    def test_localhost_jest_dozwolony(self, tmp_path: Path) -> None:
        f = _file(tmp_path, "ok.py", 'URL = "http://127.0.0.1:11434"')
        assert cc.check_external_hosts([f]) == []

    def test_nazwy_serwisow_docker_sa_dozwolone(self, tmp_path: Path) -> None:
        f = _file(tmp_path, "ok.py", 'URL = "http://ollama:11434"')
        assert cc.check_external_hosts([f]) == []

    def test_atrapa_testowa_jest_dozwolona(self, tmp_path: Path) -> None:
        f = _file(tmp_path, "ok.py", 'URL = "https://example.invalid/x"')
        assert cc.check_external_hosts([f]) == []

    def test_przypieta_wersja_przechodzi(self, tmp_path: Path) -> None:
        f = _file(tmp_path, "requirements.txt", "httpx==0.27.2  # BSD-3\n")
        assert cc.check_pinned_versions([f]) == []

    def test_komentarze_i_puste_linie_sa_pomijane(self, tmp_path: Path) -> None:
        f = _file(tmp_path, "requirements.txt", "# komentarz\n\n-r base.txt\n")
        assert cc.check_pinned_versions([f]) == []


class TestCalegoRepozytorium:
    def test_repozytorium_jest_zgodne(self) -> None:
        """Test odpalany przy kazdym `pytest` — zgodnosc nie moze sie zepsuc
        niezauwazona w trakcie nocnego kodowania."""
        files = cc.tracked_files()
        assert files, "brak plikow sledzonych — uruchom z repozytorium git"

        all_problems: list[str] = []
        for _name, check in cc.CHECKS:
            all_problems.extend(check(files))

        assert all_problems == [], (
            "Naruszona zgodnosc z par. 5 specyfikacji:\n  "
            + "\n  ".join(all_problems)
        )

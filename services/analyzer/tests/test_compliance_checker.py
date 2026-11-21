"""Testy automatu zgodnosci (tools/check_compliance.py).

Check, ktory tylko swieci na zielono, jest bezwartosciowy — te testy dowodza,
ze detektory FAKTYCZNIE wylapuja naruszenia, a nie przechodza bo nic nie robia.

compliance:allow-file
Ten plik Z DEFINICJI zawiera zakazane wzorce jako dane testowe (openai, colab,
minio, klucze sk-*), wiec checker zglaszalby sam siebie. Wyjatek jest jawny
i wypisywany w raporcie checkera, zeby nie dalo sie po cichu wyciszyc
prawdziwego problemu.
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


class TestCelowScrapowania:
    """Rozroznienie, ktorego checker pierwotnie nie mial i zglaszal scraper
    osoby A jako naruszenie.

    "On-premise" z par. 5 specyfikacji znaczy brak zewnetrznych API modeli
    i hostowanych zamiennikow naszych komponentow — NIE "nigdy nie dotykaj
    internetu". Produktem jest monitor tresci w internecie, wiec scraper musi
    siegac do serwisow, ktore monitoruje, a rejestr KNF jest wprost wskazany
    w zalacznikach do zadania jako zrodlo danych.
    """

    @pytest.mark.parametrize(
        "host",
        [
            "https://www.youtube.com/watch?v=abc",
            "https://www.facebook.com/ads/library/?id=1",
            "https://www.instagram.com/p/abc/",
            "https://www.tiktok.com/@konto/video/1",
            "https://www.knf.gov.pl/podmioty/rejestr",
        ],
    )
    def test_cele_scrapowania_i_rejestr_knf_sa_dozwolone(
        self, tmp_path: Path, host: str
    ) -> None:
        f = _file(tmp_path, "src.py", f'URL = "{host}"')
        assert cc.check_external_hosts([f]) == []

    @pytest.mark.parametrize(
        "host",
        [
            "https://broker.example/oferta",
            "https://sub.broker.example/x",
            "https://cos.invalid/y",
            "https://host.test/z",
        ],
    )
    def test_domeny_zarezerwowane_sa_dozwolone(self, tmp_path: Path, host: str) -> None:
        """RFC 2606 / 6761 — nigdy nie wskazuja prawdziwej uslugi, wiec
        fixtures testowe nie potrzebuja markerow."""
        f = _file(tmp_path, "test_x.py", f'URL = "{host}"')
        assert cc.check_external_hosts([f]) == []

    @pytest.mark.parametrize(
        "host",
        [
            "https://jakis-losowy-serwis.com/api",
            "https://tracker.example.org/pixel",
            "https://my-vps.hetzner.cloud/infer",
        ],
    )
    def test_obcy_adres_NADAL_jest_zglaszany(self, tmp_path: Path, host: str) -> None:
        """Straz musi zostac uzyteczna — rozluznienie dotyczy tylko jawnie
        zadeklarowanych zrodel, nie wszystkiego."""
        f = _file(tmp_path, "src.py", f'URL = "{host}"')
        assert cc.check_external_hosts([f]), f"{host} powinien byc zglaszany"

    def test_lista_celow_jest_jawna_i_skonczona(self) -> None:
        """Lista celow scrapowania jest zarazem dokumentacja monitorowanych
        zrodel — nie moze stac sie workiem bez dna."""
        assert len(cc.SCRAPING_TARGETS) < 30
        assert all("." in t for t in cc.SCRAPING_TARGETS)


class TestMechanizmuWyjatkow:
    """Wyjatki sa furtka, wiec musza byc przetestowane dokladniej niz reszta."""

    def test_marker_plikowy_pomija_caly_plik(self, tmp_path: Path) -> None:
        f = _file(
            tmp_path,
            "fixtures.py",
            "# compliance:allow-file\nURL = 'https://api.openai.com'",
        )
        assert cc.is_allowlisted_file(f) is True
        assert cc.check_external_hosts([f]) == []

    def test_marker_plikowy_dziala_tylko_w_naglowku(self, tmp_path: Path) -> None:
        """Marker schowany na koncu dlugiego pliku NIE moze wyciszac calosci."""
        body = "\n".join(f"line {i}" for i in range(40))
        f = _file(
            tmp_path,
            "sneaky.py",
            f"URL = 'https://api.openai.com'\n{body}\n# compliance:allow-file\n",
        )
        assert cc.is_allowlisted_file(f) is False
        assert cc.check_external_hosts([f])

    def test_marker_liniowy_pomija_tylko_swoja_linie(self, tmp_path: Path) -> None:
        f = _file(
            tmp_path,
            "mixed.py",
            "A = 'https://api.openai.com'  # compliance:allow\n"
            "B = 'https://evil.example.com'\n",
        )
        problems = cc.check_external_hosts([f])
        assert len(problems) == 1
        assert "evil.example.com" in problems[0]

    def test_plik_env_jest_zglaszany_nawet_z_markerem(self, tmp_path: Path) -> None:
        """Obecnosc pliku .env w repo to problem niezaleznie od jego tresci —
        marker nie moze tego wyciszyc."""
        f = _file(tmp_path, ".env", "# compliance:allow-file\nSECRET=1")
        problems = cc.check_secrets([f])
        assert problems
        assert "sekretami" in problems[0]


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

"""Testy spojnosci miedzy plikami — wylapuja ciche bledy integracyjne.

Powstaly po przegladzie pracy czterech rownoleglych strumieni. Kazdy test tutaj
odpowiada realnemu bledowi, ktory przeszedl przez testy jednostkowe, bo zaden
pojedynczy modul nie byl zly — rozjechaly sie DWA pliki.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from analyzer import health, worker
from analyzer.stt import DEFAULT_PROFIT_PATTERNS, DEFAULT_RISK_PATTERNS, normalize_text

ANALYZER_ROOT = Path(__file__).resolve().parents[1]


class TestPortHealth:
    """Regresja: Dockerfile sondowal /health na 8081, a health.py nasluchiwal
    na 8001. Oba pliki byly 'poprawne' osobno, a kontener bylby unhealthy
    na demie, mimo w pelni dzialajacego workera."""

    def test_dockerfile_sonduje_ten_sam_port_co_health(self) -> None:
        dockerfile = (ANALYZER_ROOT / "Dockerfile").read_text(encoding="utf-8")
        porty = set(re.findall(r"127\.0\.0\.1:(\d+)/health", dockerfile))
        assert porty, "Dockerfile nie sonduje /health — HEALTHCHECK zniknal?"
        assert porty == {str(health.HEALTH_PORT)}, (
            f"Dockerfile sonduje porty {porty}, a health.HEALTH_PORT to "
            f"{health.HEALTH_PORT}. Kontener bylby unhealthy."
        )

    def test_worker_startuje_serwer_health(self) -> None:
        """Regresja: serve() istnialo, ale nikt go nie wolal, wiec endpoint
        nigdy nie wstawal."""
        assert hasattr(worker, "_start_health_server")
        import inspect

        zrodlo = inspect.getsource(worker.main)
        assert "_start_health_server" in zrodlo, (
            "main() nie startuje serwera /health — HEALTHCHECK bedzie pukal w pustke"
        )


class TestWzorcowOsiCzasu:
    """Regresja: `dochod\\w*` lapalo polskie zwroty, ktore nie sa obietnica zysku."""

    @pytest.mark.parametrize(
        "zdanie",
        [
            "dochodzi do tego oplata manipulacyjna",
            "w razie sporu dochodzenie roszczen trwa dlugo",
            "klient dochodzi swoich praw w sadzie",
        ],
    )
    def test_falszywi_przyjaciele_nie_sa_twierdzeniem_o_zysku(self, zdanie: str) -> None:
        norm = normalize_text(zdanie)
        trafienia = [p for p in DEFAULT_PROFIT_PATTERNS if re.search(p, norm)]
        assert trafienia == [], (
            f"{zdanie!r} nie jest obietnica zysku, a pasuje do {trafienia}. "
            "Dalo by to falszywy punkt na osi czasu reguly 3."
        )

    @pytest.mark.parametrize(
        "zdanie",
        [
            "dochod pasywny 18 procent rocznie",
            "wysokie dochody z inwestycji",
            "najbardziej dochodowy produkt w ofercie",
            "zysk do 18 procent",
            "zarobisz krocie",
            "stopa zwrotu ponad rynek",
        ],
    )
    def test_prawdziwe_obietnice_zysku_sa_lapane(self, zdanie: str) -> None:
        norm = normalize_text(zdanie)
        assert any(re.search(p, norm) for p in DEFAULT_PROFIT_PATTERNS), (
            f"{zdanie!r} JEST obietnica zysku, a nie zostala wykryta"
        )

    @pytest.mark.parametrize(
        "zdanie",
        [
            "inwestowanie wiaze sie z ryzykiem",
            "ryzyko utraty kapitalu",
            "mozesz stracic czesc srodkow",
            "mozliwa strata calego kapitalu",
        ],
    )
    def test_ostrzezenia_o_ryzyku_sa_lapane(self, zdanie: str) -> None:
        norm = normalize_text(zdanie)
        assert any(re.search(p, norm) for p in DEFAULT_RISK_PATTERNS), (
            f"{zdanie!r} JEST ostrzezeniem o ryzyku, a nie zostalo wykryte"
        )


class TestFleksjiWRouterze:
    """Regresja: RECOMMENDATION_SIGNALS dopasowywalo literalnie, wiec
    "rekomendacji" i "rekomendacje" nie pasowaly do literalu "rekomendacja".
    Router przepuszczalby wiekszosc realnych ofert doradczych do triage
    zamiast do Modulu 3. Zgloszone przy przegladzie Modulu 3."""

    @pytest.mark.parametrize(
        "zdanie",
        [
            "rekomendujemy akcje X",
            "rekomendacja kupna akcji",
            "w naszej rekomendacji akcji",
            "rekomendacje dla akcji spolki",
            "nasze rekomendacjami sie kierujemy",
            "sygnaly kupna od nas",
            "zarzadzamy portfelami klientow",
            "wskazemy instrumenty do zakupu",
        ],
    )
    def test_rekomendacje_w_roznych_przypadkach(self, zdanie: str) -> None:
        from analyzer.router import has_investment_recommendation

        assert has_investment_recommendation(zdanie), (
            f"{zdanie!r} JEST rekomendacja inwestycyjna — router musi to wykryc, "
            "inaczej oferta trafi do triage zamiast do Modulu 3"
        )

    @pytest.mark.parametrize(
        "zdanie",
        [
            "polecamy nasz newsletter",
            "zapraszamy do kontaktu z nami",
            "jestesmy na rynku od 20 lat",
        ],
    )
    def test_falszywi_przyjaciele_nie_sa_rekomendacja(self, zdanie: str) -> None:
        from analyzer.router import has_investment_recommendation

        assert not has_investment_recommendation(zdanie), (
            f"{zdanie!r} nie jest rekomendacja instrumentu finansowego"
        )

    def test_procent_jest_obietnica_zysku(self) -> None:
        """Zastapilo goly literal '%' i bezsensowny literal 'do 1'."""
        from analyzer.router import has_profit_claims

        assert has_profit_claims("do 18% rocznie")
        assert has_profit_claims("12,5 % w skali roku")
        assert not has_profit_claims("nasza siedziba jest w Warszawie")

    def test_normalize_jest_publiczne(self) -> None:
        """Modul 3 importowal prywatne _normalize. Teraz jest publiczny
        odpowiednik, a alias pozostaje dla zgodnosci."""
        from analyzer import router

        assert hasattr(router, "normalize")
        assert router._normalize is router.normalize


class TestZaleznosci:
    def test_redis_jest_przypiety_jawnie(self) -> None:
        """rq ciagnie redis tranzytywnie, ale zasada weryfikowalnego lancucha
        dostaw (par. 5 specyfikacji) wymaga jawnego przypiecia."""
        req = (ANALYZER_ROOT / "requirements.txt").read_text(encoding="utf-8")
        assert re.search(r"^redis==", req, re.M), "redis musi byc przypiety jawnie"

    def test_wszystkie_zaleznosci_maja_przypieta_wersje(self) -> None:
        req = (ANALYZER_ROOT / "requirements.txt").read_text(encoding="utf-8")
        for linia in req.splitlines():
            pakiet = linia.split("#")[0].strip()
            if not pakiet or pakiet.startswith("-"):
                continue
            assert "==" in pakiet, f"wersja nieprzypieta: {pakiet!r}"

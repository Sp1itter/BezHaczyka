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


class TestPowtarzalnosciModelu:
    """Regresja: przy temperature 0.1 werdykty Bielika zmienialy sie miedzy
    przebiegami na TYM SAMYM materiale — ta sama reklama raz lamala reguly
    1, 2 i 18, raz tylko 1 i 2.

    Dla narzedzia nadzorczego to nie do przyjecia: nadzorca nie moze dostawac
    innego ustalenia przy kazdym odswiezeniu, a demo przed jury musi zachowac
    sie tak samo jak na probie. Stad temperature 0 i staly seed.
    """

    def test_temperatura_zero_i_staly_seed(self) -> None:
        from analyzer.llm import DEFAULT_SEED, DEFAULT_TEMPERATURE

        assert DEFAULT_TEMPERATURE == 0.0, (
            "temperature > 0 przywraca niedeterminizm werdyktow"
        )
        assert isinstance(DEFAULT_SEED, int)

    def test_seed_jest_wysylany_do_ollamy(self) -> None:
        """Sam temperature 0 nie wystarcza — bez seeda llama.cpp moze dalej
        roznic sie miedzy procesami."""
        import json as _json

        import httpx

        from analyzer.llm import OllamaClient

        przechwycone: dict = {}

        def handler(request: httpx.Request) -> httpx.Response:
            przechwycone.update(_json.loads(request.content))
            return httpx.Response(200, json={"response": "{}"})

        client = OllamaClient(
            client=httpx.Client(
                transport=httpx.MockTransport(handler), base_url="http://fake"
            )
        )
        client.generate_json("prompt")
        assert przechwycone["options"]["temperature"] == 0.0
        assert "seed" in przechwycone["options"]


class TestZgodnosciKolejkiMiedzySerwisami:
    """Regresja na bombe integracyjna znaleziona przy inwentaryzacji.

    Analyzer mial rq==1.16.2, scraper rq==2.9.1, a oba serwisy nadaja i odbieraja
    na TYCH SAMYCH kolejkach Valkeya. RQ zmienilo format zadan miedzy 1.x i 2.x,
    wiec zadanie nadane przez scraper moglo byc nieodczytywalne dla naszego
    workera. Detonowaloby to w momencie wlaczenia harmonogramu.
    """

    def _wersja(self, req: Path, pakiet: str) -> str | None:
        if not req.exists():
            return None
        m = re.search(rf"^{pakiet}==([\w.]+)", req.read_text(encoding="utf-8"), re.M)
        return m.group(1) if m else None

    @pytest.mark.parametrize("pakiet", ["rq", "redis"])
    def test_wersje_kolejki_identyczne_w_obu_serwisach(self, pakiet: str) -> None:
        nasza = self._wersja(ANALYZER_ROOT / "requirements.txt", pakiet)
        scraper_req = ANALYZER_ROOT.parent / "scraper" / "requirements.txt"
        ich = self._wersja(scraper_req, pakiet)
        if ich is None:
            pytest.skip("brak requirements scrapera")
        assert nasza == ich, (
            f"{pakiet}: analyzer ma {nasza}, scraper {ich}. Oba serwisy uzywaja "
            "tych samych kolejek — rozjechane wersje RQ psuja odczyt zadan."
        )


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


class TestBudowanieZCasedb:
    def test_dockerfile_kontekst_services_i_casedb(self) -> None:
        d = (ANALYZER_ROOT / "Dockerfile").read_text(encoding="utf-8")
        assert "COPY analyzer/requirements.txt" in d
        assert "COPY analyzer/analyzer/" in d
        assert "COPY analyzer/tools/ ./tools/" in d
        assert "COPY casedb /tmp/casedb" in d and "pip install --no-cache-dir /tmp/casedb" in d

    def test_psycopg_ta_sama_wersja_co_casedb(self) -> None:
        pyproject = ANALYZER_ROOT.parent / "casedb" / "pyproject.toml"
        if not pyproject.exists():
            pytest.skip("brak casedb")
        ich = re.search(r"psycopg\[binary\]==([\w.]+)", pyproject.read_text(encoding="utf-8"))
        nasza = re.search(
            r"^psycopg\[binary\]==([\w.]+)",
            (ANALYZER_ROOT / "requirements.txt").read_text(encoding="utf-8"),
            re.M,
        )
        assert ich and nasza and ich.group(1) == nasza.group(1)

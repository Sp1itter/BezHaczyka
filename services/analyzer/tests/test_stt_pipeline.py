"""Testy wpiecia transkrypcji w potok.

Regresja na realna luke: stt.py byl napisany i przetestowany, ale NIKT go nie
wywolywal — martwy kod. Transkrypt pojawial sie w AdDocument tylko wtedy, gdy
ktos wstrzyknal go z gory.

Kluczowa wlasnosc, ktorej pilnuja te testy: transkrypcja dzieje sie PRZED brama
zakresu i PRZED routerem, i jej warunkiem jest obecnosc MEDIOW, nie modul.
Uzaleznienie transkrypcji od modulu to problem jajka i kury — modul wyznacza
router, router czyta sygnaly z tekstu, a w reklamie wideo te sygnaly moga
istniec wylacznie w narracji.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from analyzer.contracts import (
    AdDocument,
    MediaItem,
    ScopeStatus,
    Transcript,
    TranscriptSegment,
)
from analyzer.pipeline import AnalyzerConfig, EntityResolution, analyze
from analyzer.stt import ad_archive_id, make_local_transcriber, resolve_media_path

NARRACJA_Z_INSTRUMENTEM = (
    "Czesc, dzis pokazuje jak handlowac kontraktami na roznice z dzwignia "
    "i zarabiac osiemnascie procent rocznie."
)


def _doc(*, media: bool, text: str = "Link w bio!", url: str | None = None) -> AdDocument:
    return AdDocument(
        id="uuid-abc",
        source="tiktok",
        url=url or "https://example.invalid/ads/library/?id=912810501476495",
        fetched_at=datetime(2026, 11, 21, tzinfo=timezone.utc),
        text=text,
        media=(
            [MediaItem(kind="video", path="s3://media/uuid-abc.mp4", duration_s=34.2)]
            if media
            else []
        ),
    )


def _fake_transcriber(doc: AdDocument) -> Transcript:
    return Transcript(
        engine="test",
        lang="pl",
        text=NARRACJA_Z_INSTRUMENTEM,
        segments=[TranscriptSegment(start=4.2, end=8.1, text=NARRACJA_Z_INSTRUMENTEM)],
    )


class TestWywolaniaTranskrypcji:
    def test_transkrybuje_gdy_sa_media_i_brak_transkryptu(self):
        doc = _doc(media=True)
        analyze(doc, EntityResolution(), AnalyzerConfig(transcriber=_fake_transcriber))
        assert doc.transcript is not None
        assert "kontraktami na roznice" in doc.transcript.text

    def test_nie_transkrybuje_bez_mediow(self):
        """Warunek jest MEDIALNY — reklama tekstowa nie wola Whispera."""
        wolania: list[str] = []

        def licznik(doc: AdDocument) -> Transcript:
            wolania.append(doc.id)
            return _fake_transcriber(doc)

        doc = _doc(media=False)
        analyze(doc, EntityResolution(), AnalyzerConfig(transcriber=licznik))
        assert wolania == []
        assert doc.transcript is None

    def test_nie_nadpisuje_istniejacego_transkryptu(self):
        """Gdy scraper osoby A juz dostarczyl transkrypt, nie liczymy go drugi raz."""
        doc = _doc(media=True)
        doc.transcript = Transcript(engine="scraper", lang="pl", text="juz jest", segments=[])

        def nie_wolaj(doc: AdDocument) -> Transcript:
            raise AssertionError("transkrypt juz byl, nie wolno liczyc ponownie")

        analyze(doc, EntityResolution(), AnalyzerConfig(transcriber=nie_wolaj))
        assert doc.transcript.engine == "scraper"

    def test_brak_producenta_nie_wywraca_analizy(self):
        doc = _doc(media=True)
        f = analyze(doc, EntityResolution(), AnalyzerConfig(transcriber=None))
        assert doc.transcript is None
        assert f.id

    def test_awaria_transkrypcji_nie_wywraca_analizy(self):
        """Padnięty Whisper degraduje ocene, nie przewraca jej."""

        def padajacy(doc: AdDocument) -> Transcript:
            raise RuntimeError("ffmpeg nie znalezony")

        doc = _doc(media=True)
        f = analyze(doc, EntityResolution(), AnalyzerConfig(transcriber=padajacy))
        assert doc.transcript is None
        assert f.id, "Finding musi powstac mimo awarii transkrypcji"

    def test_producent_zwracajacy_none_jest_ok(self):
        doc = _doc(media=True)
        analyze(doc, EntityResolution(), AnalyzerConfig(transcriber=lambda d: None))
        assert doc.transcript is None


class TestKolejnosciEtapow:
    """Sedno sprawy: transkrypt MUSI wplywac na brame zakresu i na router."""

    def test_instrument_tylko_w_narracji_wchodzi_do_zakresu(self):
        """Bez transkrypcji brama dalaby `uncertain` i reklama wypadlaby
        z analizy, mimo ze narracja wprost mowi o kontraktach na roznice."""
        bez = _doc(media=True)
        analyze(bez, EntityResolution(), AnalyzerConfig(transcriber=None))
        assert bez.scope.status is ScopeStatus.UNCERTAIN

        z_transkryptem = _doc(media=True)
        analyze(
            z_transkryptem,
            EntityResolution(),
            AnalyzerConfig(transcriber=_fake_transcriber),
        )
        assert z_transkryptem.scope.status is ScopeStatus.IN_SCOPE
        assert z_transkryptem.scope.instrument_wrapper == "cfd"

    def test_simhash_obejmuje_transkrypt(self):
        """Embedding i simhash licza sie PO transkrypcji, inaczej dedup nie
        rozpoznalby dwoch wariantow tego samego spotu."""
        bez = _doc(media=True)
        analyze(bez, EntityResolution(), AnalyzerConfig(transcriber=None))
        z_nim = _doc(media=True)
        analyze(z_nim, EntityResolution(), AnalyzerConfig(transcriber=_fake_transcriber))
        assert bez.simhash != z_nim.simhash


class TestResolveraPlikow:
    def test_wyciaga_ad_archive_id_z_url(self):
        doc = _doc(media=True)
        assert ad_archive_id(doc) == "912810501476495"

    def test_doc_id_to_nie_ad_archive_id(self):
        """Pulapka: doc.id to UUID nadany przez scraper, a katalogi korpusu
        sa nazwane ad_archive_id."""
        doc = _doc(media=True)
        assert doc.id != ad_archive_id(doc)

    def test_url_bez_id_daje_none(self):
        doc = _doc(media=True, url="https://example.invalid/bez-parametru")
        assert ad_archive_id(doc) is None

    def test_znajduje_plik_w_katalogu_korpusu(self, tmp_path: Path):
        katalog = tmp_path / "912810501476495"
        katalog.mkdir()
        (katalog / "video.mp4").write_bytes(b"udawane wideo")
        assert resolve_media_path(_doc(media=True), tmp_path) == katalog / "video.mp4"

    def test_brak_pliku_daje_none(self, tmp_path: Path):
        assert resolve_media_path(_doc(media=True), tmp_path) is None

    def test_sciezka_s3_nie_jest_rozwiazywana_lokalnie(self, tmp_path: Path):
        """Pobranie z SeaweedFS nalezy do wolajacego, nie do warstwy STT."""
        assert resolve_media_path(_doc(media=True), tmp_path) is None

    def test_producent_zwraca_none_gdy_brak_pliku(self, tmp_path: Path):
        """Nie wola Whispera i nie rzuca — brak mediow to informacja, nie blad."""
        transcriber = make_local_transcriber(tmp_path)
        assert transcriber(_doc(media=True)) is None


class TestKorpusuNaTejMaszynie:
    def test_korpus_nie_ma_plikow_wideo(self):
        """Dokumentuje stan faktyczny: pliki mp4 sa w .gitignore i lezą tylko
        na maszynie, ktora je nagrala. Bez nich sciezka STT jest nieuruchamialna,
        niezaleznie od naszego kodu. Gdy pliki sie pojawia, ten test padnie —
        i to bedzie DOBRA wiadomosc, wtedy go usunac."""
        korpus = Path(__file__).resolve().parents[3] / "fixtures" / "demo-ads" / "facebook"
        if not korpus.is_dir():
            pytest.skip("brak korpusu scrapera")
        assert list(korpus.glob("*/*.mp4")) == [], (
            "Pojawily sie pliki wideo — wlacz transcriber w score_corpus.py "
            "i usun ten test"
        )

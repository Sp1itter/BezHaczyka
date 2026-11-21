"""Testy warstwy wykonawczej autoskalera — odczyt stanu kolejek i flaga workera.

Dwie luki zgloszone uczciwie przez implementatora Czesci A i naprawione po
przegladzie:

1. `pool.PoolExecutor` startuje workery jako
   `python -m analyzer.worker --queue <nazwa>`, ale worker TEJ FLAGI NIE MIAL —
   uzywal stalej QUEUE_NAME. Domyslny spawn by sie nie uruchomil, a autoskaler
   moglby obslugiwac wylacznie q:gpu.
2. `health.STATE_PROVIDER` zwracal pusta liste, wiec /scaling nigdy nie
   pokazywalo prawdziwego backlogu — endpoint byl atrapa.
"""

from __future__ import annotations

import pytest

from analyzer.scaling import (
    QueueState,
    decide,
    load_scaling_config,
    make_valkey_state_provider,
    read_queue_states,
    scaling_payload,
)
from analyzer.worker import QUEUE_NAME, parse_args

CFG = load_scaling_config()


class TestFlagiKolejkiWWorkerze:
    def test_domyslna_kolejka_to_gpu(self) -> None:
        assert parse_args([]) == QUEUE_NAME == "q:gpu"

    @pytest.mark.parametrize("kolejka", ["q:ingest", "q:render", "q:gpu"])
    def test_flaga_queue_wybiera_kolejke(self, kolejka: str) -> None:
        """Bez tego autoskaler mogl startowac wylacznie workery q:gpu."""
        assert parse_args(["--queue", kolejka]) == kolejka

    def test_domyslny_spawn_executora_uzywa_istniejacej_flagi(self) -> None:
        """Regresja: spawn i worker musza sie zgadzac co do nazwy flagi."""
        import inspect

        from analyzer import pool

        zrodlo = inspect.getsource(pool)
        assert "--queue" in zrodlo, "executor startuje workera inna flaga niz --queue"
        parse_args(["--queue", "q:ingest"])  # nie rzuca => flaga istnieje


class TestOdczytuStanuKolejek:
    def test_czyta_backlog_i_workerow_z_wstrzyknietych_czytnikow(self) -> None:
        stany = read_queue_states(
            CFG,
            backlog_reader=lambda n: {"ingest": 25, "render": 1, "gpu": 9}[n],
            worker_counter=lambda n: 2,
        )
        assert {s.name for s in stany} == set(CFG.queues)
        assert next(s for s in stany if s.name == "ingest").backlog == 25
        assert all(s.workers == 2 for s in stany)

    def test_idle_zawsze_zero_bo_licznik_nalezy_do_petli_orkiestratora(self) -> None:
        """Konsekwencja jest bezpieczna: przy idle_s = 0 skalowanie W DOL
        z powodu BEZCZYNNOSCI nigdy sie nie odpala, wiec /scaling nie proponuje
        wygaszania workera na podstawie danych, ktorych nie ma.

        Uwaga: `workers=1` jest celowe. Przy wiekszej liczbie zadzialaloby
        przyciecie do `max_workers` (render ma max 2, gpu max 1) i decyzja
        spadlaby z INNEGO powodu niz bezczynnosc — co jest poprawne, ale nie
        o tym jest ten test.
        """
        stany = read_queue_states(CFG, backlog_reader=lambda n: 0, worker_counter=lambda n: 1)
        assert all(s.idle_s == 0.0 for s in stany)
        for d in decide(stany, CFG):
            assert d.desired >= d.current, "bez danych o bezczynnosci nie schodzimy w dol"

    def test_przekroczenie_max_workers_jest_przycinane_niezaleznie_od_idle(self) -> None:
        """Dopelnienie powyzszego: gdy workerow jest WIECEJ niz pozwala limit,
        autoskaler je redukuje nawet przy idle_s = 0 — to inny powod niz
        bezczynnosc i jest pozadany."""
        stany = read_queue_states(CFG, backlog_reader=lambda n: 0, worker_counter=lambda n: 3)
        decyzje = {d.queue: d for d in decide(stany, CFG)}
        assert decyzje["render"].desired == CFG.queues["render"].max_workers
        assert decyzje["gpu"].desired == CFG.queues["gpu"].max_workers

    def test_awaria_odczytu_daje_zera_a_nie_wyjatek(self) -> None:
        """/scaling nie moze padac, gdy kolejka nie odpowiada."""

        def padajacy(_name: str) -> int:
            raise RuntimeError("Valkey nie odpowiada")

        stany = read_queue_states(CFG, backlog_reader=padajacy, worker_counter=padajacy)
        assert all(s.backlog == 0 and s.workers == 0 for s in stany)

    def test_skalowanie_w_gore_dziala_na_prawdziwym_backlogu(self) -> None:
        stany = read_queue_states(
            CFG, backlog_reader=lambda n: 50, worker_counter=lambda n: 1
        )
        decyzje = {d.queue: d for d in decide(stany, CFG)}
        assert decyzje["ingest"].desired == 2
        assert decyzje["gpu"].capped_by == "ollama_endpoints", (
            "gpu nie moze przekroczyc liczby endpointow — workery bez modeli "
            "nie daja przepustowosci"
        )


class TestDostawcyStanu:
    def test_dostawca_zjada_awarie_i_zwraca_pusta_liste(self, monkeypatch) -> None:
        """Na maszynie bez Valkeya /scaling ma zwrocic pusta liste, nie 500.

        Awarie wymuszamy monkeypatchem, a NIE prawdziwa proba polaczenia:
        pierwsza wersja tego testu faktycznie siegala do Valkeya i wydluzyla
        caly zestaw z 1,9 s do 43,8 s na samych timeoutach. Test, ktory czeka
        na siec, jest testem zepsutym.
        """
        import analyzer.scaling as sc

        def padajacy(*_a, **_k):
            raise RuntimeError("Valkey nie odpowiada")

        monkeypatch.setattr(sc, "read_queue_states", padajacy)
        assert sc.make_valkey_state_provider(CFG)() == []

    def test_dostawca_zwraca_stany_gdy_odczyt_dziala(self, monkeypatch) -> None:
        import analyzer.scaling as sc

        oczekiwane = [QueueState("ingest", backlog=3, workers=1, idle_s=0.0)]
        monkeypatch.setattr(sc, "read_queue_states", lambda *_a, **_k: oczekiwane)
        assert sc.make_valkey_state_provider(CFG)() == oczekiwane

    def test_payload_z_prawdziwego_odczytu_jest_serializowalny(self) -> None:
        import json

        stany = read_queue_states(
            CFG, backlog_reader=lambda n: 7, worker_counter=lambda n: 1
        )
        json.dumps(scaling_payload(stany, CFG))

"""Testy czystej funkcji decyzyjnej autoskalera."""

from dataclasses import replace

from analyzer.scaling import (
    DEFAULT_SCALING_CONFIG,
    QueueState,
    decide,
)

CFG = DEFAULT_SCALING_CONFIG
CFG_HARD_MAX_5 = replace(CFG, hard_max_total=5)


def test_brak_backlogu_nie_zmienia_liczby_workerow():
    d = decide([QueueState("q:ingest", backlog=0, workers=2, idle_s=10)], CFG)
    assert d[0].desired == 2


def test_backlog_powyzej_progu_zwieksza_o_jeden():
    d = decide([QueueState("q:ingest", backlog=10, workers=1, idle_s=0)], CFG)
    assert d[0].desired == 2
    assert "10" in d[0].reason


def test_skalowanie_w_dol_wymaga_pustej_kolejki_I_bezczynnosci():
    # Review Focus 3: bez obu warunkow autoskaler oscyluje
    assert decide([QueueState("q:ingest", 0, 3, idle_s=10)], CFG)[0].desired == 3
    assert decide([QueueState("q:ingest", 5, 3, idle_s=999)], CFG)[0].desired == 3
    assert decide([QueueState("q:ingest", 0, 3, idle_s=300)], CFG)[0].desired == 2


def test_nie_schodzi_ponizej_min_ani_nie_rosnie_powyzej_max():
    assert decide([QueueState("q:ingest", 0, 1, idle_s=999)], CFG)[0].desired == 1
    d = decide([QueueState("q:ingest", 100, 4, idle_s=0)], CFG)[0]
    assert d.desired == 4 and d.capped_by == "max_workers"


def test_gpu_nie_przekracza_pojemnosci_ollamy():
    # Konfiguracja obejsc walidacje (max 9 > 4): decide() i tak przycina do OLLAMA_NUM_PARALLEL * endpointy.
    wide = replace(CFG, queues={**CFG.queues, "q:gpu": replace(CFG.queues["q:gpu"], max_workers=9)})
    d = decide([QueueState("q:gpu", backlog=50, workers=4, idle_s=0)], wide)[0]
    assert d.desired == 4 and d.capped_by == "ollama_parallel"


def test_gpu_rosnie_do_max_przy_duzym_backlogu():
    d = decide([QueueState("q:gpu", backlog=50, workers=1, idle_s=0)], CFG)[0]
    assert d.desired == 2 and d.capped_by is None


def test_gpu_schodzi_o_jeden_po_progu_bezczynnosci_60s():
    assert decide([QueueState("q:gpu", 0, 3, idle_s=59)], CFG)[0].desired == 3
    assert decide([QueueState("q:gpu", 0, 3, idle_s=60)], CFG)[0].desired == 2


def test_limit_globalny_przycina_deterministycznie():
    # Review Focus 2: dwa przebiegi na tych samych danych daja ten sam wynik
    stany = [
        QueueState("q:ingest", 20, 4, 0),
        QueueState("q:render", 1, 2, 0),
        QueueState("q:gpu", 5, 1, 0),
    ]
    a = decide(stany, CFG_HARD_MAX_5)
    b = decide(stany, CFG_HARD_MAX_5)
    assert [x.desired for x in a] == [x.desired for x in b]
    assert sum(x.desired for x in a) <= 5
    assert any(x.capped_by == "hard_max_total" for x in a)


def test_limit_globalny_zdejmuje_z_kolejki_o_najmniejszym_backlogu():
    stany = [
        QueueState("q:ingest", 20, 4, 0),
        QueueState("q:render", 1, 2, 0),
        QueueState("q:gpu", 5, 1, 0),
    ]
    wynik = {x.queue: x.desired for x in decide(stany, CFG_HARD_MAX_5)}
    assert wynik == {"q:ingest": 3, "q:render": 1, "q:gpu": 1}


def test_remis_backlogu_rozstrzyga_nazwa_alfabetycznie():
    stany = [QueueState("q:render", 2, 2, 0), QueueState("q:ingest", 2, 2, 0)]
    cfg = replace(CFG, hard_max_total=3)
    wynik = {x.queue: x.desired for x in decide(stany, cfg)}
    assert wynik == {"q:ingest": 1, "q:render": 2}


def test_nieznana_kolejka_jest_pomijana_bez_wyjatku():
    d = decide([QueueState("nieznana", 5, 1, 0), QueueState("q:ingest", 0, 1, 0)], CFG)
    assert [x.queue for x in d] == ["q:ingest"]


def test_reason_jest_zdaniem_po_polsku():
    for s in (
        QueueState("q:ingest", 12, 1, 0),
        QueueState("q:ingest", 0, 3, 999),
        QueueState("q:ingest", 0, 2, 1),
        QueueState("q:gpu", 50, 1, 0),
    ):
        reason = decide([s], CFG)[0].reason
        assert len(reason) > 20
        assert " " in reason and reason == reason.strip()

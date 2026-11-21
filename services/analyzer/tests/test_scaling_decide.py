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
    d = decide([QueueState("ingest", backlog=0, workers=2, idle_s=10)], CFG)
    assert d[0].desired == 2


def test_backlog_powyzej_progu_zwieksza_o_jeden():
    d = decide([QueueState("ingest", backlog=10, workers=1, idle_s=0)], CFG)
    assert d[0].desired == 2
    assert "10" in d[0].reason


def test_skalowanie_w_dol_wymaga_pustej_kolejki_I_bezczynnosci():
    # Review Focus 3: bez obu warunkow autoskaler oscyluje
    assert decide([QueueState("ingest", 0, 3, idle_s=10)], CFG)[0].desired == 3
    assert decide([QueueState("ingest", 5, 3, idle_s=999)], CFG)[0].desired == 3
    assert decide([QueueState("ingest", 0, 3, idle_s=300)], CFG)[0].desired == 2


def test_nie_schodzi_ponizej_min_ani_nie_rosnie_powyzej_max():
    assert decide([QueueState("ingest", 0, 1, idle_s=999)], CFG)[0].desired == 1
    d = decide([QueueState("ingest", 100, 4, idle_s=0)], CFG)[0]
    assert d.desired == 4 and d.capped_by == "max_workers"


def test_gpu_nie_przekracza_liczby_endpointow():
    d = decide([QueueState("gpu", backlog=50, workers=1, idle_s=0)], CFG)[0]
    assert d.desired == 1 and d.capped_by == "ollama_endpoints"


def test_limit_globalny_przycina_deterministycznie():
    # Review Focus 2: dwa przebiegi na tych samych danych daja ten sam wynik
    stany = [
        QueueState("ingest", 20, 4, 0),
        QueueState("render", 1, 2, 0),
        QueueState("gpu", 5, 1, 0),
    ]
    a = decide(stany, CFG_HARD_MAX_5)
    b = decide(stany, CFG_HARD_MAX_5)
    assert [x.desired for x in a] == [x.desired for x in b]
    assert sum(x.desired for x in a) <= 5
    assert any(x.capped_by == "hard_max_total" for x in a)


def test_limit_globalny_zdejmuje_z_kolejki_o_najmniejszym_backlogu():
    stany = [
        QueueState("ingest", 20, 4, 0),
        QueueState("render", 1, 2, 0),
        QueueState("gpu", 5, 1, 0),
    ]
    wynik = {x.queue: x.desired for x in decide(stany, CFG_HARD_MAX_5)}
    assert wynik == {"ingest": 3, "render": 1, "gpu": 1}


def test_remis_backlogu_rozstrzyga_nazwa_alfabetycznie():
    stany = [QueueState("render", 2, 2, 0), QueueState("ingest", 2, 2, 0)]
    cfg = replace(CFG, hard_max_total=3)
    wynik = {x.queue: x.desired for x in decide(stany, cfg)}
    assert wynik == {"ingest": 1, "render": 2}


def test_nieznana_kolejka_jest_pomijana_bez_wyjatku():
    d = decide([QueueState("nieznana", 5, 1, 0), QueueState("ingest", 0, 1, 0)], CFG)
    assert [x.queue for x in d] == ["ingest"]


def test_reason_jest_zdaniem_po_polsku():
    for s in (
        QueueState("ingest", 12, 1, 0),
        QueueState("ingest", 0, 3, 999),
        QueueState("ingest", 0, 2, 1),
        QueueState("gpu", 50, 1, 0),
    ):
        reason = decide([s], CFG)[0].reason
        assert len(reason) > 20
        assert " " in reason and reason == reason.strip()

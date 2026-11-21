"""Testy przyspieszenia Bielika: opcje zapytania, wspolny klient, obcinanie
materialu, rownolegle wsady (kolejnosc jak w wersji sekwencyjnej)."""

from __future__ import annotations

import json
import threading
import time
from datetime import datetime, timezone

import httpx

from analyzer.contracts import AdDocument, Engine, Relation, Evidence, EvidenceKind, RuleResult, Verdict
from analyzer.llm import OllamaClient, fit_material
from analyzer.pipeline import AnalyzerConfig, EntityResolution, analyze

ENT = EntityResolution(publisher_relation=Relation.OFFICIAL, publisher_is_authorized=True)


def _doc(text: str = "Fundusz XYZ. Inwestuj teraz, zysk gwarantowany.") -> AdDocument:
    return AdDocument(
        id="d1",
        source="web",
        url="https://example.invalid/x",
        fetched_at=datetime(2026, 11, 22, tzinfo=timezone.utc),
        text=text,
    )


def test_opcje_wysylane_przy_kazdym_wywolaniu(monkeypatch):
    monkeypatch.setenv("LLM_NUM_CTX", "3000")
    monkeypatch.setenv("LLM_NUM_PREDICT", "123")
    monkeypatch.setenv("LLM_KEEP_ALIVE", "10m")
    bodies = []

    def handler(req: httpx.Request) -> httpx.Response:
        bodies.append(json.loads(req.content))
        return httpx.Response(200, json={"response": "{}"})

    c = OllamaClient(client=httpx.Client(transport=httpx.MockTransport(handler), base_url="http://f"))
    c.generate_json("x")
    b = bodies[0]
    assert b["keep_alive"] == "10m"
    assert b["format"] == "json"
    assert b["options"]["temperature"] == 0
    assert b["options"]["seed"] == 42
    assert b["options"]["num_ctx"] == 3000
    assert b["options"]["num_predict"] == 123


def test_domyslne_opcje(monkeypatch):
    for k in ("LLM_NUM_CTX", "LLM_NUM_PREDICT", "LLM_KEEP_ALIVE"):
        monkeypatch.delenv(k, raising=False)
    bodies = []

    def handler(req):
        bodies.append(json.loads(req.content))
        return httpx.Response(200, json={"response": "{}"})

    c = OllamaClient(client=httpx.Client(transport=httpx.MockTransport(handler), base_url="http://f"))
    c.generate_json("x")
    assert bodies[0]["options"]["num_ctx"] == 4096
    assert bodies[0]["options"]["num_predict"] == 400
    assert bodies[0]["keep_alive"] == "30m"


def test_wspolny_klient_http_jest_reuzywany():
    c = OllamaClient()
    assert c._http() is c._http()


def test_fit_material_krotki_bez_zmian():
    assert fit_material("krotki tekst", prompt_chars=1000) == ("krotki tekst", False)


def test_fit_material_dlugi_zachowuje_poczatek_i_koniec():
    text = "POCZATEK " + "a" * 20000 + " KONIEC"
    out, truncated = fit_material(text, prompt_chars=2000, num_ctx=4096, num_predict=400)
    assert truncated
    assert out.startswith("POCZATEK")
    assert out.endswith("KONIEC")
    assert "[...]" in out
    # prompt + material miesci sie w (num_ctx - num_predict) przy ~3.5 zn/token
    assert (2000 + len(out)) / 3.5 < 4096 - 400


def _res(rid: str, v: Verdict = Verdict.PASS) -> RuleResult:
    return RuleResult(
        rule_id=rid, rule_name="r", engine=Engine.LLM, verdict=v, confidence=1.0,
        severity=1, legal_basis="x", evidence=Evidence(kind=EvidenceKind.ABSENCE, summary="s"),
    )


def _mk_runner(rids, delay):
    def runner(doc):
        time.sleep(delay)
        return [_res(r) for r in rids]
    return runner


def _ids(cfg):
    f = analyze(_doc(), ENT, cfg)
    return [r.rule_id for r in f.rule_results]


def test_rownolegle_wyniki_w_kolejnosci_sekwencyjnej(monkeypatch):
    # pierwszy runner najwolniejszy: kolejnosc nie moze zalezec od czasu konca
    runners = (
        _mk_runner(["a1", "a2"], 0.15),
        _mk_runner(["b1"], 0.01),
        _mk_runner(["c1", "c2"], 0.05),
    )
    monkeypatch.setenv("LLM_BATCH_CONCURRENCY", "1")
    seq = _ids(AnalyzerConfig(module2_runners=runners))
    monkeypatch.setenv("LLM_BATCH_CONCURRENCY", "4")
    par = _ids(AnalyzerConfig(module2_runners=runners))
    assert seq == par
    assert [i for i in par if i[0] in "abc"] == ["a1", "a2", "b1", "c1", "c2"]


def test_rownolegle_faktycznie_rownolegle(monkeypatch):
    seen = []
    lock = threading.Lock()

    def runner(doc):
        with lock:
            seen.append(threading.current_thread().name)
        time.sleep(0.2)
        return []

    monkeypatch.setenv("LLM_BATCH_CONCURRENCY", "4")
    t = time.perf_counter()
    analyze(_doc(), ENT, AnalyzerConfig(module2_runners=(runner,) * 4))
    assert time.perf_counter() - t < 0.6
    assert len(set(seen)) > 1


def test_awaria_runnera_w_trybie_rownoleglym(monkeypatch):
    def broken(doc):
        raise RuntimeError("boom")

    monkeypatch.setenv("LLM_BATCH_CONCURRENCY", "4")
    f = analyze(_doc(), ENT, AnalyzerConfig(module2_runners=(_mk_runner(["a"], 0), broken, _mk_runner(["c"], 0))))
    ids = [r.rule_id for r in f.rule_results]
    assert ids.index("a") < ids.index("c")
    crashed = [r for r in f.rule_results if r.rule_id == "?"]
    assert len(crashed) == 1
    assert ids.index("a") < f.rule_results.index(crashed[0]) < ids.index("c")

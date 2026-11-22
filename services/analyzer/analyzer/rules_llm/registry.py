"""Rejestr regul Modulu 2 wystawianych przez warstwe LLM.

Spina cztery wsady (batch_1..batch_4) w jedna liste runnerow gotowa do
AnalyzerConfig(module2_runners=...).

UWAGA: nie wszystkie z 18 regul sa nasze. Tu NIE brakuje regul, ktore
trzeba dopisac:
  - reguly 4, 5, 6, 7, 8 sa deterministyczne i liczy je osoba A z geometrii
    renderu (services/scraper).
Nasze sa reguly LLM (1, 2, 9, 10, 11, 12a, 12b, 14, 15, 16, 17, 18) oraz
hybrydowe 3 i 13 (analyzer/rules_hybrid.py), ktore korzystaja z RenderProbe
od osoby A.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from functools import lru_cache, partial
import os

from analyzer.contracts import RuleResult
from analyzer.llm import OllamaClient
from analyzer.pipeline import AnalyzerConfig, RuleRunner
from analyzer.rules_llm import batch_1, batch_2, batch_3, batch_4

# (modul wsadu, funkcja ewaluacji) w kolejnosci wsadow.
_BATCHES = (
    (batch_1, batch_1.evaluate_batch_1),
    (batch_2, batch_2.evaluate_batch_2),
    (batch_3, batch_3.evaluate_batch_3),
    (batch_4, batch_4.evaluate_batch_4),
)


def _merge_meta() -> dict[str, tuple[str, int, str]]:
    """Scal RULE_META wsadow; kolizja rule_id to blad konfiguracji."""
    merged: dict[str, tuple[str, int, str]] = {}
    owner: dict[str, str] = {}
    for module, _fn in _BATCHES:
        for rule_id, meta in module.RULE_META.items():
            if rule_id in merged:
                raise ValueError(
                    f"Kolizja rule_id {rule_id!r}: wystepuje w {owner[rule_id]} "
                    f"i {module.__name__}"
                )
            merged[rule_id] = meta
            owner[rule_id] = module.__name__
    return merged


def _with_hybrid(meta: dict[str, tuple[str, int, str]]) -> dict[str, tuple[str, int, str]]:
    """Dolacz reguly hybrydowe, ktore nie naleza do zadnego wsadu LLM.

    Regula 3 laczy wykrycie semantyczne twierdzen o zyskach z POMIAREM
    odleglosci do ostrzezenia (geometria RenderProbe, znaki albo sekundy);
    regula 13 mierzy, czy wyniki historyczne nie sa najwiekszym elementem
    (czcionka z RenderProbe). Zadna nie jest czystym wsadem LLM ani regula
    DET osoby A.
    """
    from analyzer.rules_hybrid import RULE_3_META, RULE_13_META

    for rule_id in ("3", "13"):
        if rule_id in meta:
            raise ValueError(
                f"Kolizja rule_id {rule_id!r} miedzy wsadem LLM a regula hybrydowa"
            )
    return {**meta, "3": RULE_3_META, "13": RULE_13_META}


ALL_RULE_META: dict[str, tuple[str, int, str]] = _with_hybrid(_merge_meta())


def _rule_sort_key(rule_id: str) -> tuple[int, str]:
    m = re.match(r"(\d+)(.*)", rule_id)
    return (int(m.group(1)), m.group(2)) if m else (10**6, rule_id)


def module2_runners(client: OllamaClient | None = None) -> tuple[RuleRunner, ...]:
    """Runnery Modulu 2: cztery wsady LLM plus reguly hybrydowe 3 i 13.

    `client` trafia do kazdego wsadu. Reguly 3 i 13 go nie potrzebuja — 3 mierzy
    odleglosc miedzy obietnica zysku a ostrzezeniem deterministycznie
    (geometria RenderProbe, znaki albo sekundy transkrypcji), wiec dziala
    takze przy padnietym modelu; 13 porownuje czcionki z RenderProbe.
    """
    from analyzer.rules_hybrid import rule_3_runner, rule_13_runner

    runners: list[RuleRunner] = []
    for _module, fn in _BATCHES:
        runner = partial(fn, client=client)
        runner.__name__ = fn.__name__  # type: ignore[attr-defined]
        runners.append(runner)
    runners.append(rule_3_runner)
    runners.append(rule_13_runner)
    return tuple(runners)


def build_config(client: OllamaClient | None = None, **kwargs) -> AnalyzerConfig:
    """AnalyzerConfig z pelnym zestawem runnerow Modulu 2.

    Dodatkowe kwargs trafiaja do AnalyzerConfig (np. scope_override).
    """
    kwargs.setdefault("module3_client", client or OllamaClient())
    return AnalyzerConfig(module2_runners=module2_runners(client), **kwargs)


@lru_cache(maxsize=1)
def default_config() -> AnalyzerConfig:
    """Pelny potok produkcyjny: wsady LLM, reguly hybrydowe, embeddingi, Whisper.

    Jedno zrodlo prawdy dla workera RQ i mostu casedb. Wczesniej worker wolal
    analyze(..., config=None), a pipeline podstawial pusty AnalyzerConfig -
    zadanie ze scrapera dostawalo same placeholdery, bez zadnej reguly LLM.

    STT_ENABLED=0 wylacza transkrypcje (np. maszyna bez faster-whisper).
    STT_MEDIA_ROOT - katalog z plikami wideo korpusu (sciezka po ad_archive_id).
    """
    client = OllamaClient()
    transcriber = None
    if os.getenv("STT_ENABLED", "1") != "0":
        from analyzer.stt import make_local_transcriber

        transcriber = make_local_transcriber(
            os.getenv("STT_MEDIA_ROOT", "fixtures/demo-ads/facebook"),
            model_size=os.getenv("WHISPER_MODEL") or None,
        )
    return build_config(client, embed_client=client, transcriber=transcriber)


def expected_rule_ids() -> tuple[str, ...]:
    """Posortowane rule_id, ktore powinny wrocic z pelnej analizy.

    Tylko reguly faktycznie zaimplementowane w naszych wsadach (patrz
    docstring modulu: 4-8 sa po stronie osoby A).
    """
    return tuple(sorted(ALL_RULE_META, key=_rule_sort_key))


def coverage_report(results: Iterable[RuleResult]) -> dict:
    """Ile regul z ALL_RULE_META wrocilo w wyniku, ile brakuje i ktore."""
    returned = {r.rule_id for r in results}
    expected = expected_rule_ids()
    present = [rid for rid in expected if rid in returned]
    missing = [rid for rid in expected if rid not in returned]
    return {
        "expected": len(expected),
        "returned": len(present),
        "missing": len(missing),
        "missing_rule_ids": missing,
        "complete": not missing,
    }

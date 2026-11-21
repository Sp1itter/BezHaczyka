"""Wsad nr 2 — reguly 9, 10, 11.

JEDNO wywolanie modelu zwraca trzy RuleResult. Cala logike (mapowanie
werdyktow, weryfikacja cytatu, obsluga awarii) wykonuje `batching.evaluate_batch`.
"""

from __future__ import annotations

from analyzer.contracts import AdDocument, RuleResult
from analyzer.llm import OllamaClient
from analyzer.rules_llm.batching import evaluate_batch
from analyzer.rules_llm.lang_consistency import apply_rule_10_override

PROMPT_FILE = "batch_2.txt"

# rule_id -> (nazwa, severity, podstawa prawna)
RULE_META: dict[str, tuple[str, int, str]] = {
    "9": (
        "Zrozumiałość dla grupy docelowej",
        3,
        "art. 44 ust. 2 lit. d rozporządzenia del. 2017/565",
    ),
    "10": (
        "Spójność językowa",
        3,
        "art. 44 ust. 2 lit. f rozporządzenia del. 2017/565",
    ),
    "11": (
        "Porównania produktów / usług",
        3,
        "art. 44 ust. 3 rozporządzenia del. 2017/565",
    ),
}

# Reguly, dla ktorych `fail` oznacza BRAK czegos wymaganego. Tu zadna:
# kazde `fail` twierdzi, ze w materiale cos JEST (zargon, obcy jezyk, porownanie).
FAIL_MEANS_ABSENCE: set[str] = set()


def evaluate_batch_2(
    doc: AdDocument,
    client: OllamaClient | None = None,
) -> list[RuleResult]:
    """Ocen reguly 9, 10, 11 jednym wywolaniem modelu."""
    results = evaluate_batch(
        doc,
        client,
        prompt_file=PROMPT_FILE,
        rule_meta=RULE_META,
        fail_means_absence=FAIL_MEANS_ABSENCE,
    )
    # Regula 10 jest HYBRYDOWA: spojnosc jezykowa da sie zmierzyc, a Bielik 4.5B
    # konsekwentnie uznawal angielskie ostrzezenie w polskiej reklamie za zgodne.
    # Deterministyczny pomiar ma pierwszenstwo; przy niepewnym pomiarze
    # (np. material za krotki) zostaje werdykt modelu.
    return apply_rule_10_override(results, doc.analyzable_text, RULE_META)

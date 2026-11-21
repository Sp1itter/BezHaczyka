"""Wsad nr 4 — reguly 15, 16.

JEDNO wywolanie modelu zwraca dwa RuleResult. Cala logike (mapowanie
werdyktow, weryfikacja cytatu, obsluga awarii) wykonuje `batching.evaluate_batch`.
"""

from __future__ import annotations

from analyzer.contracts import AdDocument, RuleResult
from analyzer.llm import OllamaClient
from analyzer.rules_llm.batching import evaluate_batch

PROMPT_FILE = "batch_4.txt"

# rule_id -> (nazwa, severity, podstawa prawna)
RULE_META: dict[str, tuple[str, int, str]] = {
    "15": (
        "Prognozy przyszłych wyników",
        4,
        "art. 44 ust. 6 rozporządzenia del. 2017/565",
    ),
    "16": (
        "Informacja podatkowa",
        2,
        "art. 44 ust. 7 rozporządzenia del. 2017/565",
    ),
}

# Reguly, dla ktorych `fail` oznacza BRAK czegos wymaganego. Tu zadna:
# `fail` oznacza prognoze / wzmianke o podatkach, ktore w materiale SA
# (a brakuje przy nich zastrzezenia), wiec mozna je zacytowac.
FAIL_MEANS_ABSENCE: set[str] = set()


def evaluate_batch_4(
    doc: AdDocument,
    client: OllamaClient | None = None,
) -> list[RuleResult]:
    """Ocen reguly 15, 16 jednym wywolaniem modelu."""
    return evaluate_batch(
        doc,
        client,
        prompt_file=PROMPT_FILE,
        rule_meta=RULE_META,
        fail_means_absence=FAIL_MEANS_ABSENCE,
    )

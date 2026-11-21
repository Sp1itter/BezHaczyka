"""Wsad nr 3 — reguly 12a, 12b, 14.

JEDNO wywolanie modelu zwraca trzy RuleResult. Cala logike (mapowanie
werdyktow, weryfikacja cytatu, obsluga awarii) wykonuje `batching.evaluate_batch`.
"""

from __future__ import annotations

from analyzer.contracts import AdDocument, RuleResult
from analyzer.llm import OllamaClient
from analyzer.rules_llm.batching import evaluate_batch

PROMPT_FILE = "batch_3.txt"

# rule_id -> (nazwa, severity, podstawa prawna)
RULE_META: dict[str, tuple[str, int, str]] = {
    "12a": (
        "Wyniki historyczne: okres i zakres",
        3,
        "art. 44 ust. 4 rozporządzenia del. 2017/565",
    ),
    "12b": (
        "Wyniki historyczne: warunki i waluta",
        3,
        "art. 44 ust. 4 rozporządzenia del. 2017/565",
    ),
    "14": (
        "Ostrzeżenie przy wynikach historycznych",
        4,
        "art. 44 ust. 4 lit. d rozporządzenia del. 2017/565",
    ),
}

# 12b i 14: `fail` znaczy, ze wymaganego ostrzezenia NIE MA — nie ma czego
# cytowac, wiec brak cytatu jest poprawny i nie obniza confidence.
# 12a: `fail` moze dotyczyc wyrywkowego fragmentu, ktory w materiale JEST.
FAIL_MEANS_ABSENCE: set[str] = {"12b", "14"}


def evaluate_batch_3(
    doc: AdDocument,
    client: OllamaClient | None = None,
) -> list[RuleResult]:
    """Ocen reguly 12a, 12b, 14 jednym wywolaniem modelu."""
    return evaluate_batch(
        doc,
        client,
        prompt_file=PROMPT_FILE,
        rule_meta=RULE_META,
        fail_means_absence=FAIL_MEANS_ABSENCE,
    )

"""Prompt wsadowy nr 1 — reguly 1, 2, 17, 18.

JEDNO wywolanie Bielika zwraca cztery RuleResult. Osiemnascie osobnych
requestow na dokument zabilo by przepustowosc przy 8 GB VRAM.

Odpornosc jest tu wazniejsza niz elegancja: model moze nie odpowiedziec,
zwrocic brakujaca regule, nieznany werdykt albo zmyslony cytat. Zadna z tych
sytuacji nie moze wywrocic potoku ani wyprodukowac falszywego naruszenia
na oczach jury.
"""

from __future__ import annotations

from analyzer.contracts import AdDocument, RuleResult
from analyzer.llm import OllamaClient
from analyzer.rules_llm.batching import evaluate_batch, quote_is_verifiable

__all__ = ["RULE_META", "evaluate_batch_1", "quote_is_verifiable"]

PROMPT_FILE = "batch_1.txt"

# rule_id -> (nazwa, severity, podstawa prawna)
RULE_META: dict[str, tuple[str, int, str]] = {
    "1": (
        "Identyfikacja firmy",
        3,
        "art. 44 ust. 2 lit. a rozporządzenia del. 2017/565",
    ),
    "2": (
        "Oznaczenie reklamy",
        3,
        "art. 24 ust. 3 MiFID II",
    ),
    "17": (
        "Zakaz sugerowania aprobaty organu nadzoru",
        5,
        "art. 44 ust. 8 rozporządzenia del. 2017/565",
    ),
    "18": (
        "Nadzór jako argument bezpieczeństwa",
        5,
        "art. 44 ust. 8 rozporządzenia del. 2017/565",
    ),
}

# Reguly, dla ktorych `fail` oznacza BRAK czegos wymaganego — wtedy nie ma
# czego cytowac i brak cytatu jest poprawny.
# Dla regul 17 i 18 `fail` twierdzi, ze w materiale COS JEST, wiec cytat
# musi istniec i dac sie odnalezc.
FAIL_MEANS_ABSENCE = {"1", "2"}


def evaluate_batch_1(
    doc: AdDocument,
    client: OllamaClient | None = None,
) -> list[RuleResult]:
    """Ocen reguly 1, 2, 17, 18 jednym wywolaniem modelu."""
    return evaluate_batch(
        doc,
        client,
        prompt_file=PROMPT_FILE,
        rule_meta=RULE_META,
        fail_means_absence=FAIL_MEANS_ABSENCE,
    )

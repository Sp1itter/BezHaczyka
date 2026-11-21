"""Smoke test na zywo — uruchom DOPIERO gdy Ollama dziala i modele sa pobrane.

Cala logika jest juz pokryta testami na MockTransport (tests/test_llm.py).
Ten skrypt sprawdza tylko to, czego testy nie moga: czy prawdziwy Bielik
rozumie nasz prompt i zwraca nasz schemat.

Uruchomienie (z services/analyzer):
    python tools/smoke_llm.py
"""

from __future__ import annotations

import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analyzer.contracts import AdDocument, Verdict  # noqa: E402
from analyzer.llm import OllamaClient  # noqa: E402
from analyzer.rules_llm.batch_1 import evaluate_batch_1  # noqa: E402

# Material celowo lamiacy reguly 2 i 18: brak oznaczenia reklamy
# oraz nadzor uzyty jako argument bezpieczenstwa.
MATERIAL = (
    "Inwestuj z XYZ Dom Maklerski S.A. i zarabiaj do 18% rocznie! "
    "Nasza inwestycja jest w pełni bezpieczna — spełniamy rygorystyczne "
    "wymogi nadzorcze KNF. Zacznij już dziś, liczba miejsc ograniczona."
)

EXPECTED_FAILS = {"2", "18"}


def main() -> int:
    client = OllamaClient()

    print(f"Ollama: {client.base_url}")
    if not client.health():
        print("BLAD: Ollama nie odpowiada.")
        print("  1) winget install Ollama.Ollama")
        print("  2) ollama pull SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0")
        return 1

    models = client.available_models()
    print(f"Dostepne modele ({len(models)}): {', '.join(models) or '-'}")
    if client.model not in models:
        print(f"UWAGA: brak modelu {client.model} — pobierz go lub ustaw OLLAMA_MODEL.")
        return 1

    doc = AdDocument(
        id="smoke",
        source="web",
        url="https://example.invalid/smoke",
        fetched_at=datetime.now(timezone.utc),
        text=MATERIAL,
    )

    print(f"\nModel: {client.model}  (temperature={client.temperature})")
    print("Oceniam reguly 1, 2, 17, 18 jednym wywolaniem...\n")

    started = time.perf_counter()
    results = evaluate_batch_1(doc, client)
    elapsed = time.perf_counter() - started

    for r in results:
        mark = {"fail": "X", "pass": ".", "not_applicable": "?"}[r.verdict.value]
        print(f"[{mark}] regula {r.rule_id:>3} ({r.rule_name})")
        print(f"      werdykt: {r.verdict.value}  confidence: {r.confidence}")
        print(f"      {r.evidence.summary}")
        if r.evidence.quote:
            print(f'      cytat: "{r.evidence.quote}"')
        print()

    print(f"Czas jednego wywolania wsadowego: {elapsed:.1f} s")
    print("(Jesli > 30 s, rozwaz mniejszy quant albo krotszy prompt —")
    print(" przy 18 regulach na dokument przepustowosc ma znaczenie.)\n")

    got_fails = {r.rule_id for r in results if r.verdict is Verdict.FAIL}
    na = [r.rule_id for r in results if r.verdict is Verdict.NOT_APPLICABLE]

    if na:
        print(f"UWAGA: reguly {na} wyszly not_applicable — sprawdz prompt.")

    missing = EXPECTED_FAILS - got_fails
    if missing:
        print(
            f"UWAGA: oczekiwalismy `fail` dla regul {sorted(missing)}, "
            "a model ich nie zlapal. Iteruj prompt na tym materiale."
        )
        return 1

    print(f"OK: model poprawnie wykryl naruszenia regul {sorted(got_fails)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

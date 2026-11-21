"""Benchmark czasu analizy jednego dokumentu (Bielik na zywo).

Mierzy `analyze()` (wsady LLM) i opcjonalnie `build_summary` dla N dokumentow
z fixtures. Kazdy pomiar powtarzany --repeat razy, raportujemy min.
Dziala na starym i nowym kodzie (steruj LLM_BATCH_CONCURRENCY w srodowisku).

    LLM_BATCH_CONCURRENCY=1 python tools/bench_llm.py --n 5 --repeat 2 --summary
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analyzer.contracts import AdDocument  # noqa: E402
from analyzer.pipeline import analyze  # noqa: E402
from analyzer.rules_llm.registry import build_config  # noqa: E402
from analyzer.summary import build_summary  # noqa: E402

CASES = Path(__file__).resolve().parents[3] / "fixtures" / "module2-cases" / "cases.json"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", default=str(CASES))
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--repeat", type=int, default=2)
    ap.add_argument("--summary", action="store_true", help="mierz tez podsumowanie")
    args = ap.parse_args()

    raw = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    entries = raw["cases"] if isinstance(raw, dict) else raw
    # najdluzsze teksty = najbardziej realistyczne obciazenie
    entries = sorted(entries, key=lambda e: -len(e["doc"].get("text", "")))[: args.n]
    config = build_config()
    print(f"concurrency={os.getenv('LLM_BATCH_CONCURRENCY', '(brak)')}")
    totals = []
    for e in entries:
        doc = AdDocument.model_validate(e["doc"])
        best_a = best_s = float("inf")
        for _ in range(args.repeat):
            t = time.perf_counter()
            finding = analyze(doc, config)
            best_a = min(best_a, time.perf_counter() - t)
            if args.summary:
                t = time.perf_counter()
                build_summary(finding, doc)
                best_s = min(best_s, time.perf_counter() - t)
        tot = best_a + (best_s if args.summary else 0)
        totals.append(tot)
        s = f" summary={best_s:5.1f}s" if args.summary else ""
        print(f"{e['id'][:40]:40} len={len(doc.text):5} analyze={best_a:5.1f}s{s}")
    print(f"MEDIANA={sorted(totals)[len(totals)//2]:.1f}s SREDNIA={sum(totals)/len(totals):.1f}s")


if __name__ == "__main__":
    main()

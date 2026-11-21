"""Smoke STT: transkrypcja pliku + regula 3 na osi czasu.

Uzycie (z services/analyzer):
    .venv/Scripts/python.exe tools/smoke_stt.py fixtures/stt/ad_pl_risk_late.wav [rozmiar_modelu]
"""

from __future__ import annotations

import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analyzer.contracts import AdDocument, MediaItem  # noqa: E402
from analyzer.rules_hybrid import assess_rule_3  # noqa: E402
from analyzer.stt import transcribe  # noqa: E402


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    path, size = argv[0], (argv[1] if len(argv) > 1 else "small")
    t0 = time.perf_counter()
    tr = transcribe(path, model_size=size)
    dt = time.perf_counter() - t0
    print(f"engine={tr.engine} czas={dt:.1f}s segmentow={len(tr.segments)}")
    for s in tr.segments:
        print(f"  [{s.start:6.2f} - {s.end:6.2f}] {s.text}")
    doc = AdDocument(
        id="smoke", source="facebook", url="https://example.invalid/smoke",
        fetched_at=datetime.now(timezone.utc),
        media=[MediaItem(kind="audio", path=path)], transcript=tr,
    )
    res = assess_rule_3(doc)
    print(f"regula 3: {res.verdict.value}")
    print(f"  {res.evidence.summary}")
    print(f"  measured={res.evidence.measured}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

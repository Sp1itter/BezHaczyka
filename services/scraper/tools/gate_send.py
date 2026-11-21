"""GATE: wyslij jedna reklame przez prawdziwy fetch_job (replay -> resolver -> casedb -> q:gpu).

    .venv\\Scripts\\python.exe tools\\gate_send.py [--id 912810501476495]

Wymaga zmiennych: DATABASE_URL (casedb), VALKEY_URL (Valkey u Pawla).
FB_MODE ustawiany na replay, zeby GATE nie zalezal od sieci i Meta.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--id", default="912810501476495", help="ad_archive_id z fixtures/demo-ads/facebook/")
    args = ap.parse_args()
    missing = [v for v in ("DATABASE_URL", "VALKEY_URL") if not os.getenv(v)]
    if missing:
        print(f"Brak zmiennych: {', '.join(missing)}", file=sys.stderr)
        return 2
    os.environ.setdefault("FB_MODE", "replay")

    from rq import Queue

    from jobs import DEFAULT_OUTPUT_QUEUE, _redis, fetch_job
    from sources.meta_json import canonical_ad_url

    result = fetch_job("facebook", canonical_ad_url(args.id))
    waiting = Queue(os.getenv("SCRAPER_OUTPUT_QUEUE") or DEFAULT_OUTPUT_QUEUE, connection=_redis()).count
    print(f"case_id = {result['case_id']}  outcome = {result['outcome']}")
    print(f"q:gpu: {waiting} zadan w kolejce (0 = worker juz pobral)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""GATE 1: wyslij jedna reklame przez prawdziwy fetch_job (replay -> API -> q:gpu).

    .venv\\Scripts\\python.exe tools\\gate_send.py [--id 912810501476495]

Wymaga zmiennych: API_BASE_URL (stub API), VALKEY_URL (Valkey u Pawla).
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
    missing = [v for v in ("API_BASE_URL", "VALKEY_URL") if not os.getenv(v)]
    if missing:
        print(f"Brak zmiennych: {', '.join(missing)}", file=sys.stderr)
        return 2
    os.environ.setdefault("FB_MODE", "replay")

    from rq import Queue

    from jobs import ANALYSIS_QUEUE, _redis, fetch_job
    from sources.meta_json import canonical_ad_url

    doc = fetch_job(canonical_ad_url(args.id))
    waiting = Queue(ANALYSIS_QUEUE, connection=_redis()).count
    print(f"document_id = {doc['id']}")
    print(f"GET  {os.environ['API_BASE_URL']}/documents/{doc['id']}")
    print(f"q:gpu: {waiting} zadan w kolejce (0 = worker juz pobral)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

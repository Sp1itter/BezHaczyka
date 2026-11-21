"""Pomiar przepustowosci renderu: czas pobrania (fetch) jednej reklamy i reklamy/min na worker.

    python tools/bench_render.py --source facebook --n 5           (ostatnie N przypadkow z bazy)
    python tools/bench_render.py --source facebook --url <url> ...  (konkretne URL-e)

Uzywa tego samego `jobs.build_source` co worker (limiter i breaker we wspolnym Valkey,
wiec pomiar respektuje FB_MIN_INTERVAL_S i nie zwieksza ruchu do platformy).
Nie zapisuje nic w bazie; zrzuty/HTML trafiaja do magazynu blobow pod tym samym kluczem co zwykle.
Wynik (JSON) idzie na stdout.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def latest_urls(source: str, n: int) -> list[str]:
    from casedb import db

    with db.connect() as conn:
        rows = conn.execute(
            "SELECT url FROM cases WHERE source = %s AND gone_at IS NULL ORDER BY last_seen_at DESC LIMIT %s",
            (source, n),
        ).fetchall()
    return [r["url"] for r in rows]


def bench(source_name: str, urls: list[str]) -> dict:
    import jobs

    redis = jobs._redis()
    source = jobs.build_source(source_name, redis)
    times: list[float] = []
    errors: list[str] = []
    for url in urls:
        t0 = time.monotonic()
        try:
            jobs._fetch(source, source_name, url)
        except Exception as exc:  # noqa: BLE001 — pomiar ma przejsc przez wszystkie URL-e
            errors.append(f"{url}: {type(exc).__name__}: {exc}"[:300])
            continue
        times.append(time.monotonic() - t0)
    mean = statistics.mean(times) if times else None
    return {
        "source": source_name,
        "n": len(urls),
        "ok": len(times),
        "seconds": [round(t, 1) for t in times],
        "mean_s": round(mean, 1) if mean else None,
        "ads_per_min_per_worker": round(60 / mean, 2) if mean else None,
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--source", default="facebook")
    p.add_argument("--n", type=int, default=5)
    p.add_argument("--url", action="append", default=[])
    args = p.parse_args(argv)
    urls = args.url or latest_urls(args.source, args.n)
    print(json.dumps(bench(args.source, urls), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

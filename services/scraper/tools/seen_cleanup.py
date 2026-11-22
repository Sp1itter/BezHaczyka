"""Zdejmuje z `<zrodlo>:seen` URL-e, ktorych nie ma w bazie (nieudane pobrania sprzed poprawki A1).

    python tools/seen_cleanup.py [--source facebook] [--dry-run]

Do 22.11 discover dodawal URL do `seen` PRZED pobraniem, wiec reklama, ktorej fetch padl,
nie wracala nigdy. Po zdjeciu z `seen` nastepny discover sprobuje ja ponownie.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SOURCES = ("facebook", "youtube", "www", "tiktok")


def stale_members(source: str, members: list[str], known_case_ids: set[str]) -> list[str]:
    """Elementy `seen`, dla ktorych nie ma przypadku w bazie."""
    from casedb.store import case_id_for
    from sources.meta_json import canonical_ad_url

    def url_of(m: str) -> str:
        return canonical_ad_url(m) if source == "facebook" else m

    return [m for m in members if case_id_for(url_of(m)) not in known_case_ids]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--source", choices=SOURCES, action="append")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    from casedb import db
    from redis import Redis

    redis = Redis.from_url(os.getenv("VALKEY_URL", "redis://valkey:6379/0"))
    with db.connect() as conn:
        known = {str(r["case_id"] if isinstance(r, dict) else r[0]) for r in conn.execute("SELECT case_id FROM cases").fetchall()}
    for source in args.source or SOURCES:
        key = f"{source}:seen"
        members = [m.decode() if isinstance(m, bytes) else m for m in redis.smembers(key)]
        stale = stale_members(source, members, known)
        if stale and not args.dry_run:
            redis.srem(key, *stale)
        print(f"{key}: {len(members)} w zbiorze, {len(stale)} bez przypadku w bazie"
              f"{' (dry-run)' if args.dry_run else ' -> usuniete'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

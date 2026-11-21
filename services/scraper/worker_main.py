"""Launcher workera RQ: python worker_main.py <kolejka> [<kolejka> ...]."""
from __future__ import annotations

import argparse
import logging
import os


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Worker RQ InvestWatch")
    parser.add_argument("queues", nargs="+", help="nazwy kolejek, np. q:ingest q:render")
    args = parser.parse_args(argv)

    from redis import Redis  # lenie — import dopiero przy uruchomieniu
    from rq import Queue, Worker

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    conn = Redis.from_url(os.getenv("VALKEY_URL", "redis://valkey:6379/0"))
    Worker([Queue(name, connection=conn) for name in args.queues], connection=conn).work()


if __name__ == "__main__":
    main()

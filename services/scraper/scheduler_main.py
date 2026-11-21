"""Launcher harmonogramu (CronJob Modulu 1): python scheduler_main.py."""
from __future__ import annotations

import logging
import os
from typing import Any

import jobs

log = logging.getLogger("scheduler_main")
JOB_PREFIX = "fb-discover-"


def register(scheduler: Any) -> int:
    """Anuluje stare zadania fb-discover-*, rejestruje aktualne; zwraca liczbe fraz."""
    for job in list(scheduler.get_jobs()):
        if str(job.id).startswith(JOB_PREFIX):
            scheduler.cancel(job)  # restart nie dubluje CronJobow
    return jobs.schedule_facebook(scheduler)


def main() -> None:
    from redis import Redis
    from rq_scheduler import Scheduler

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    conn = Redis.from_url(os.getenv("VALKEY_URL", "redis://valkey:6379/0"))
    scheduler = Scheduler(queue_name="q:ingest", connection=conn, interval=int(os.getenv("SCHEDULER_POLL_S", "10")))
    n = register(scheduler)
    log.info("Zarejestrowano %d fraz FB", n)
    if n == 0:
        log.warning("FB_QUERIES puste — harmonogram nic nie uruchomi")
    scheduler.run()


if __name__ == "__main__":
    main()

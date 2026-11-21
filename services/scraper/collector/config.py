"""Konfiguracja collectora i floty z `.env` (zero sekretow w kodzie)."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CONFIG_DIR = Path(__file__).resolve().parents[1] / "config"


@dataclass
class CollectorConfig:
    database_url: str | None = None          # COLLECTOR_DATABASE_URL (Postgres); brak = SQLite
    sqlite_path: Path = Path("data/collector/url_store.sqlite")
    config_dir: Path = DEFAULT_CONFIG_DIR
    state_dir: Path = Path("data/collector")  # flaga pauzy, stats.json, dokumenty
    interval_s: float = 50.0                  # przerwa miedzy zapytaniami collectora
    jitter_s: float = 15.0
    max_queries_per_hour: int = 60
    lease_s: float = 300.0
    max_attempts: int = 3
    retry_after_s: float = 120.0
    blocked_pause_s: float = 1800.0
    idle_sleep_s: float = 10.0
    analyze: bool = True                      # poziom 2 wysyla do analyzera (API + q:gpu)

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> CollectorConfig:
        env = os.environ if env is None else env
        return cls(
            database_url=env.get("COLLECTOR_DATABASE_URL") or None,
            sqlite_path=Path(env.get("COLLECTOR_DB_PATH", "data/collector/url_store.sqlite")),
            config_dir=Path(env.get("COLLECTOR_CONFIG_DIR", str(DEFAULT_CONFIG_DIR))),
            state_dir=Path(env.get("COLLECTOR_STATE_DIR", "data/collector")),
            interval_s=float(env.get("COLLECTOR_INTERVAL_S", 50)),
            jitter_s=float(env.get("COLLECTOR_JITTER_S", 15)),
            max_queries_per_hour=int(env.get("COLLECTOR_MAX_QUERIES_PER_HOUR", 60)),
            lease_s=float(env.get("FLEET_LEASE_S", 300)),
            max_attempts=int(env.get("FLEET_MAX_ATTEMPTS", 3)),
            retry_after_s=float(env.get("FLEET_RETRY_AFTER_S", 120)),
            blocked_pause_s=float(env.get("COLLECTOR_BLOCKED_PAUSE_S", 1800)),
            idle_sleep_s=float(env.get("FLEET_IDLE_SLEEP_S", 10)),
            analyze=env.get("COLLECTOR_ANALYZE", "1").strip().lower() not in ("0", "false", "no"),
        )

    @property
    def pause_flag(self) -> Path:
        return self.state_dir / "PAUSED"

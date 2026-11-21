"""CLI collectora i floty (PowerShell, z services\\scraper):

    .venv\\Scripts\\python.exe -m collector run                  # poziom 1: non-stop
    .venv\\Scripts\\python.exe -m collector once                 # poziom 1: jedno przejscie po zapytaniach
    .venv\\Scripts\\python.exe -m collector fleet                # poziom 2: non-stop
    .venv\\Scripts\\python.exe -m collector fleet --until-empty  # poziom 2: do oprozenia kolejki
    .venv\\Scripts\\python.exe -m collector ctl stats|pause|resume|reprioritize|errors
    .venv\\Scripts\\python.exe -m collector seed-synthetic       # plan B: strony korpusu jako kandydaci
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from collector.collect import reprioritize, run_collector, write_stats
from collector.config import CollectorConfig
from collector.fleet import run_fleet
from collector.lexicons import CollectorConfigFiles
from collector.scoring import creative_key, landing_key, score
from collector.store import open_store
from collector.synthetic import from_page

DEMO_ADS = Path(__file__).resolve().parents[3] / "fixtures" / "demo-ads"


def _fb_source_factory():
    from sources.facebook import FacebookAdsSource, FacebookConfig
    from state import CircuitBreaker, RateLimiter

    cfg = FacebookConfig.from_env()
    cfg.mode = "live"
    return FacebookAdsSource(
        config=cfg,
        limiter=RateLimiter(cfg.min_interval_s),
        breaker=CircuitBreaker(threshold=cfg.breaker_threshold, cooldown_s=cfg.breaker_cooldown_s),
    )


def seed_synthetic(store, files, corpus_dir: Path, tag: str) -> dict[str, str]:
    lex = files.lexicons()
    out = {}
    for page in sorted(corpus_dir.glob("*.html")):
        cand = from_page(page, page.resolve().as_uri(), tag)
        res = store.upsert(cand, score(cand, lex), creative_key(cand.publisher_key, cand.primary_text),
                           landing_key(cand.links[0] if cand.links else None))
        out[page.name] = res.state
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="collector", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("run")
    sub.add_parser("once")
    f = sub.add_parser("fleet")
    f.add_argument("--worker")
    f.add_argument("--max", type=int)
    f.add_argument("--until-empty", action="store_true")
    c = sub.add_parser("ctl")
    c.add_argument("action", choices=["stats", "pause", "resume", "reprioritize", "errors"])
    s = sub.add_parser("seed-synthetic")
    s.add_argument("--dir", type=Path, default=DEMO_ADS)
    s.add_argument("--tag", default="kontrolowany")
    args = ap.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    sys.stdout.reconfigure(encoding="utf-8")
    cfg = CollectorConfig.from_env()
    cfg.state_dir.mkdir(parents=True, exist_ok=True)
    files = CollectorConfigFiles(cfg.config_dir)
    store = open_store(cfg.database_url, cfg.sqlite_path)

    if args.cmd in ("run", "once"):
        n = None if args.cmd == "run" else len(files.queries().get("facebook", []))
        run_collector(store, files, cfg, _fb_source_factory, max_iterations=n)
    elif args.cmd == "fleet":
        result = run_fleet(store, files, cfg, worker=args.worker, max_items=args.max,
                           stop_when_empty=args.until_empty)
        print(json.dumps(result, ensure_ascii=False))
    elif args.cmd == "seed-synthetic":
        print(json.dumps(seed_synthetic(store, files, args.dir, args.tag), ensure_ascii=False, indent=2))
    elif args.action == "pause":
        cfg.pause_flag.write_text("pauza collectora — flota dziala dalej\n", encoding="utf-8")
        print(f"collector wstrzymany ({cfg.pause_flag})")
    elif args.action == "resume":
        cfg.pause_flag.unlink(missing_ok=True)
        print("collector wznowiony")
    elif args.action == "reprioritize":
        print(json.dumps(reprioritize(store, files), ensure_ascii=False))
    elif args.action == "errors":
        print(json.dumps(files.errors(), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(write_stats(store, cfg), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

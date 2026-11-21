"""Analiza przypadkow casedb prawdziwym potokiem (Modul 2 + reszta).

Tryb plikowy (bez bazy):
    python tools/casedb_batch.py --in export.json --out DIR
Tryb bazodanowy (DATABASE_URL):
    python tools/casedb_batch.py --db --limit 10 [--source youtube]

Uruchamiac z services/analyzer.
"""

from __future__ import annotations

import argparse
import json
import logging
import shlex
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analyzer import casedb_adapter  # noqa: E402
from analyzer.completeness import is_partial  # noqa: E402
from analyzer.contracts import Verdict  # noqa: E402
from analyzer.llm import OllamaClient  # noqa: E402
from analyzer.pipeline import analyze  # noqa: E402
from analyzer.rules_llm.registry import build_config, coverage_report  # noqa: E402

log = logging.getLogger("casedb_batch")


def summarize(doc, finding) -> dict:
    fails = sum(1 for r in finding.rule_results if r.verdict is Verdict.FAIL)
    na = sum(1 for r in finding.rule_results if r.verdict is Verdict.NOT_APPLICABLE)
    cov = coverage_report(finding.rule_results)
    return {"risk_score": finding.risk_score, "risk_level": finding.risk_level.value,
            "coverage": f"{cov['returned']}/{cov['expected']}",
            "rules_fail": fails, "rules_na": na, "rules_total": len(finding.rule_results),
            "partial_transcript": is_partial(doc)}


def make_analyzer(client: OllamaClient | None = None):
    """analyze_case(case) -> ai_result; potok zbudowany jak w registry.build_config."""
    if client is None:
        from analyzer.rules_llm.registry import default_config

        config = default_config()
        client = config.embed_client  # ten sam OllamaClient
    else:
        config = build_config(client)

    def analyze_case(case: dict) -> dict:
        doc = casedb_adapter.case_to_document(case)
        finding = analyze(doc, None, config)
        ai = casedb_adapter.finding_to_ai_result(finding, model=client.model)
        ai["summary"] = summarize(doc, finding)  # tylko dla tego narzedzia, nie do bazy
        return ai

    return analyze_case


def run_file(in_path: Path, out_dir: Path, analyze_case) -> list[dict]:
    data = json.loads(in_path.read_text(encoding="utf-8"))
    cases = data if isinstance(data, list) else [data]
    out_dir.mkdir(parents=True, exist_ok=True)
    commands: list[str] = []
    rows: list[dict] = []
    for case in cases:
        cid = case.get("case_id", "?")
        try:
            ai = analyze_case(case)
        except Exception as exc:  # noqa: BLE001 - blad jednego przypadku nie przerywa reszty
            log.exception("Przypadek %s nieudany", cid)
            (out_dir / f"{cid}.error.json").write_text(
                json.dumps({"case_id": cid, "error": f"{type(exc).__name__}: {exc}"},
                           ensure_ascii=False, indent=2), encoding="utf-8")
            rows.append({"case_id": cid, "error": str(exc)})
            continue
        (out_dir / f"{cid}.json").write_text(
            json.dumps(ai["result"], ensure_ascii=False, indent=2), encoding="utf-8")
        commands.append(
            f"docker compose run --rm casedb ai-result {cid} --task {ai['task']} "
            f"--model {shlex.quote(ai['model'])} --version {ai['version']} "
            f"--label {ai['label']} --score {ai['score']} /data/{cid}.json"
        )
        rows.append({"case_id": cid, **ai.get("summary", {})})
    (out_dir / "casedb_commands.txt").write_text("\n".join(commands) + "\n", encoding="utf-8")
    return rows


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--in", dest="in_path")
    p.add_argument("--out")
    p.add_argument("--db", action="store_true")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--source")
    # Przypadek, przy ktorym proces padl, zostaje w queued/processing; --retry
    # przejmuje go ponownie (razem z error). Uzywac, gdy nie dziala inny worker.
    p.add_argument("--retry", action="store_true",
                   help="przejmij takze przypadki queued/processing/error")
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO)
    if not args.db and not (args.in_path and args.out):
        p.error("podaj --in i --out albo --db")
    analyze_case = make_analyzer()
    if args.db:
        from analyzer import casedb_bridge

        with casedb_bridge.connect() as conn:
            statuses = ("new", "queued", "processing", "error") if args.retry else ("new",)
            res = casedb_bridge.process_cases(conn, analyze_case, limit=args.limit,
                                              source=args.source, statuses=statuses)
        for cid, st in res.items():
            print(f"{cid} {st}")
        return 0 if all(s == "done" for s in res.values()) else 1
    rows = run_file(Path(args.in_path), Path(args.out), analyze_case)
    for r in rows:
        print(json.dumps(r, ensure_ascii=False))
    return 0 if not any("error" in r for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())

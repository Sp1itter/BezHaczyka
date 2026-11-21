"""Ewaluacja trafnosci regul Modulu 2 na SYNTETYCZNYM zbiorze regresyjnym.

Zbior: fixtures/module2-cases/cases.json (napisany przez zespol, nie realne
reklamy). Dla kazdego przypadku puszcza PRAWDZIWY potok `analyze()` i porownuje
werdykty z etykietami `expected` — tylko dla regul, ktore przypadek celowo testuje.

Metryki per regula (fail = pozytyw):
    TP: oczekiwane fail, dostane fail      FN: oczekiwane fail, dostane cos innego
    FP: oczekiwane pass/NA, dostane fail   TN: oczekiwane pass/NA, dostane nie-fail
    accuracy = trafienia dokladnego werdyktu (3 klasy) / liczba ocen

Reguly 4-8 (DET): gdy potok zwrocil wypelniacz (nie ocenil), wynik jest oznaczony
"oczekiwane, niezaimplementowane" i wylaczony z macierzy pomylek.

Uruchomienie (z services/analyzer):
    ./.venv/Scripts/python.exe tools/eval_rules.py            # Ollama/Bielik na zywo
    ./.venv/Scripts/python.exe tools/eval_rules.py --rule 12a # jedna regula
    ./.venv/Scripts/python.exe tools/eval_rules.py --offline  # bez modelu (fake klient)
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analyzer.contracts import AdDocument, Relation, Verdict  # noqa: E402
from analyzer.det_placeholders import DET_RULES, REASON_NO_PROBE, REASON_NO_RESULT  # noqa: E402
from analyzer.pipeline import EntityResolution, analyze  # noqa: E402
from analyzer.rules_llm.registry import build_config, expected_rule_ids  # noqa: E402

# tools/ -> analyzer/ -> services/ -> korzen repo
DEFAULT_CASES_PATH = (
    Path(__file__).resolve().parents[3] / "fixtures" / "module2-cases" / "cases.json"
)
DEFAULT_RESULTS_PATH = DEFAULT_CASES_PATH.with_name("eval_results.json")

VALID_VERDICTS = {v.value for v in Verdict}
PENDING = "oczekiwane, niezaimplementowane"


def valid_rule_ids() -> set[str]:
    """Reguly, dla ktorych wolno ustawiac etykiete: nasze 12+2 oraz DET 4-8."""
    return set(expected_rule_ids()) | set(DET_RULES)


@dataclass
class Case:
    id: str
    opis: str
    expected: dict[str, str]
    doc: AdDocument


def load_cases(path: Path | str | None = None) -> list[Case]:
    """Wczytaj i zwaliduj przypadki. Rzuca ValueError przy blednej etykiecie."""
    p = Path(path) if path is not None else DEFAULT_CASES_PATH
    raw = json.loads(p.read_text(encoding="utf-8"))
    valid = valid_rule_ids()
    cases: list[Case] = []
    seen: set[str] = set()
    for entry in raw["cases"]:
        cid = entry["id"]
        if cid in seen:
            raise ValueError(f"Powtorzone id przypadku: {cid}")
        seen.add(cid)
        expected = {str(k): str(v) for k, v in entry["expected"].items()}
        for rule_id, verdict in expected.items():
            if rule_id not in valid:
                raise ValueError(f"{cid}: nieznana regula {rule_id!r}")
            if verdict not in VALID_VERDICTS:
                raise ValueError(f"{cid}: nieznany werdykt {verdict!r} dla reguly {rule_id}")
        cases.append(
            Case(
                id=cid,
                opis=entry.get("opis", ""),
                expected=expected,
                doc=AdDocument.model_validate(entry["doc"]),
            )
        )
    return cases


# --------------------------------------------------------------------------- #
# Metryki
# --------------------------------------------------------------------------- #


@dataclass
class Row:
    case_id: str
    rule_id: str
    expected: str
    got: str
    summary: str = ""
    quote: str | None = None
    pending: bool = False

    @property
    def match(self) -> bool:
        return self.expected == self.got


@dataclass
class RuleStats:
    rule_id: str
    tp: int = 0
    fp: int = 0
    fn: int = 0
    tn: int = 0
    exact: int = 0
    pending: int = 0
    mismatches: list[Row] = field(default_factory=list)

    @property
    def n(self) -> int:
        return self.tp + self.fp + self.fn + self.tn

    @property
    def accuracy(self) -> float | None:
        return self.exact / self.n if self.n else None


def _rule_sort_key(rule_id: str) -> tuple[int, str]:
    digits = "".join(c for c in rule_id if c.isdigit())
    return (int(digits) if digits else 10**6, rule_id)


def compute_metrics(rows: list[Row]) -> dict[str, RuleStats]:
    """Zlicz TP/FP/FN/TN per regula; wiersze `pending` tylko zliczaj osobno."""
    stats: dict[str, RuleStats] = {}
    for row in rows:
        st = stats.setdefault(row.rule_id, RuleStats(row.rule_id))
        if row.pending:
            st.pending += 1
            continue
        exp_fail = row.expected == Verdict.FAIL.value
        got_fail = row.got == Verdict.FAIL.value
        if exp_fail and got_fail:
            st.tp += 1
        elif exp_fail:
            st.fn += 1
        elif got_fail:
            st.fp += 1
        else:
            st.tn += 1
        if row.match:
            st.exact += 1
        else:
            st.mismatches.append(row)
    return dict(sorted(stats.items(), key=lambda kv: _rule_sort_key(kv[0])))


def _pct(x: float | None) -> str:
    return "  -  " if x is None else f"{x * 100:4.0f}%"


def format_table(stats: dict[str, RuleStats]) -> str:
    lines = [
        f"{'regula':<7}{'N':>3}{'TP':>4}{'FP':>4}{'FN':>4}{'TN':>4}{'acc':>7}{'oczek.':>8}",
        "-" * 41,
    ]
    for st in stats.values():
        lines.append(
            f"{st.rule_id:<7}{st.n:>3}{st.tp:>4}{st.fp:>4}{st.fn:>4}{st.tn:>4}"
            f"{_pct(st.accuracy):>7}{st.pending or '':>8}"
        )
    n = sum(s.n for s in stats.values())
    exact = sum(s.exact for s in stats.values())
    lines.append("-" * 41)
    lines.append(f"{'razem':<7}{n:>3}{'':>16}{_pct(exact / n if n else None):>7}")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Uruchomienie potoku
# --------------------------------------------------------------------------- #


class FakeClient:
    """Klient bez modelu: kazde wywolanie zwraca pusta liste wynikow, wiec reguly
    LLM daja not_applicable, a reguly deterministyczne (3, 10, 13, DET) licza sie normalnie."""

    def generate_json(self, prompt: str) -> dict:
        return {"results": []}


def _entities(doc: AdDocument) -> EntityResolution:
    name = doc.publisher.display_name
    return EntityResolution(
        publisher_relation=Relation.OFFICIAL,
        publisher_is_authorized=True,
        publisher_name=name,
        firm_name_in_ad=name,
    )


def _is_placeholder(summary: str) -> bool:
    return summary.startswith((REASON_NO_PROBE, REASON_NO_RESULT))


def run_case(case: Case, client, only_rule: str | None = None) -> list[Row]:
    finding = analyze(case.doc, _entities(case.doc), build_config(client))
    by_id = {r.rule_id: r for r in finding.rule_results}
    rows: list[Row] = []
    for rule_id, expected in case.expected.items():
        if only_rule and rule_id != only_rule:
            continue
        res = by_id.get(rule_id)
        if res is None:
            rows.append(Row(case.id, rule_id, expected, "brak_wyniku", "regula nie wrocila z potoku"))
            continue
        got = res.verdict.value
        pending = (
            rule_id in DET_RULES
            and got == Verdict.NOT_APPLICABLE.value
            and expected != got
            and _is_placeholder(res.evidence.summary)
        )
        rows.append(
            Row(case.id, rule_id, expected, got, res.evidence.summary, res.evidence.quote, pending)
        )
    return rows


def _real_client():
    from analyzer.llm import OllamaClient

    client = OllamaClient()
    if not client.health():
        raise SystemExit("BLAD: Ollama nie odpowiada na " + str(client.base_url))
    return client


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--cases", default=str(DEFAULT_CASES_PATH))
    ap.add_argument("--out", default=str(DEFAULT_RESULTS_PATH))
    ap.add_argument("--rule", help="ogranicz do jednej reguly, np. 12a")
    ap.add_argument("--offline", action="store_true", help="fake klient zamiast Ollamy")
    args = ap.parse_args(argv)

    cases = load_cases(args.cases)
    if args.rule:
        cases = [c for c in cases if args.rule in c.expected]
    client = FakeClient() if args.offline else _real_client()

    rows: list[Row] = []
    started = time.perf_counter()
    for i, case in enumerate(cases, 1):
        t0 = time.perf_counter()
        case_rows = run_case(case, client, args.rule)
        rows.extend(case_rows)
        bad = sum(1 for r in case_rows if not r.match and not r.pending)
        print(f"[{i}/{len(cases)}] {case.id}: {time.perf_counter() - t0:.1f}s, rozbieznosci: {bad}",
              file=sys.stderr, flush=True)

    stats = compute_metrics(rows)
    print(format_table(stats))
    mism = [r for r in rows if not r.match and not r.pending]
    pend = [r for r in rows if r.pending]
    print(f"\nRozbieznosci ({len(mism)}):")
    for r in mism:
        print(f"- {r.case_id} regula {r.rule_id}: oczekiwane={r.expected} dostane={r.got}\n    {r.summary[:300]}")
    if pend:
        print(f"\n{PENDING} ({len(pend)}): " + ", ".join(f"{r.case_id}/{r.rule_id}" for r in pend))

    out = {
        "synthetic": True,
        "offline": args.offline,
        "elapsed_s": round(time.perf_counter() - started, 1),
        "per_rule": {
            k: {
                "n": s.n, "tp": s.tp, "fp": s.fp, "fn": s.fn, "tn": s.tn,
                "accuracy": s.accuracy, "pending": s.pending,
            }
            for k, s in stats.items()
        },
        "mismatches": [
            {"case": r.case_id, "rule": r.rule_id, "expected": r.expected, "got": r.got,
             "summary": r.summary, "quote": r.quote}
            for r in mism
        ],
        "pending": [{"case": r.case_id, "rule": r.rule_id, "expected": r.expected,
                     "status": PENDING} for r in pend],
        "rows": [
            {"case": r.case_id, "rule": r.rule_id, "expected": r.expected, "got": r.got,
             "pending": r.pending}
            for r in rows
        ],
    }
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nZapisano {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

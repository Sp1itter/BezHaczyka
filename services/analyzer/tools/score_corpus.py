"""Przepuszcza korpus 8 reklam z Meta Ad Library przez prawdziwy potok i zapisuje wyniki.

Skrypt powtarzalny: wypelnia pola `score`, `coverage`, `has_render_probe`
i `failed_rules` w fixtures/gold/labels.json, ZACHOWUJAC etykiety reczne
(`is_violation`, `note`). Etykiet nie wylicza z score'u - to osad czlowieka.

Ograniczenie: RenderProbe powstaje w Playwrighcie. Dla reklamy z gotowym
kompletem (fixtures/contract-examples/) uzywamy go razem z wynikami regul DET
4-8. Pozostale dokumenty buduje sie z node.json.gz BEZ render_probe: reguly DET
odpadaja, a regula 3 schodzi z osi geometrii na os tekstu. Pole
`has_render_probe` zapisuje te roznice w danych.

Wymaga dzialajacej Ollamy (LLM + bge-m3). Jedna reklama to ok. 23 s.

Uruchomienie (z services/analyzer):
    ./.venv/Scripts/python.exe tools/score_corpus.py
    ./.venv/Scripts/python.exe tools/score_corpus.py --no-write   # tylko tabela
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ANALYZER_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ANALYZER_ROOT.parents[1]
SCRAPER_ROOT = REPO_ROOT / "services" / "scraper"
# meta_json.py robi plaski `from contracts import Publisher` - potrzebny katalog scrapera
sys.path.insert(0, str(ANALYZER_ROOT))
sys.path.insert(1, str(SCRAPER_ROOT))

from analyzer.contracts import AdDocument, Publisher, RuleResult, Verdict  # noqa: E402
from analyzer.llm import OllamaClient  # noqa: E402
from analyzer.pipeline import analyze  # noqa: E402
from analyzer.rules_llm.registry import build_config  # noqa: E402
from analyzer.scoring import coverage  # noqa: E402
from sources.meta_json import ad_text, ad_title, canonical_ad_url, publisher_from  # noqa: E402

DEMO_DIR = REPO_ROOT / "fixtures" / "demo-ads" / "facebook"
EXAMPLES = REPO_ROOT / "fixtures" / "contract-examples"
GOLD_PATH = REPO_ROOT / "fixtures" / "gold" / "labels.json"
RESULTS_PATH = REPO_ROOT / "fixtures" / "gold" / "corpus_results.json"

CORPUS = (
    "1416188807395560", "1685589429005115", "1688659872622573", "1700487841682444",
    "28815441858041693", "675484101807418", "912810501476495", "986443020999266",
)
# reklama z kompletem render_probe + wyniki regul DET 4-8 (wygenerowane przez scraper)
FULL_PROBE_ID = "912810501476495"


def doc_from_node(ad_id: str) -> AdDocument:
    """AdDocument z node.json.gz: BEZ render_probe, BEZ mediow, BEZ transkrypcji."""
    raw = gzip.decompress((DEMO_DIR / ad_id / "node.json.gz").read_bytes())
    node = json.loads(raw)
    return AdDocument(
        id=ad_id,
        source="facebook",
        url=canonical_ad_url(ad_id),
        fetched_at=datetime.now(timezone.utc),
        publisher=Publisher.model_validate(publisher_from(node).model_dump()),
        lang="pl",
        title=ad_title(node),
        text=ad_text(node),
    )


def load_case(ad_id: str) -> tuple[AdDocument, list[RuleResult] | None]:
    """Zwraca dokument i (opcjonalnie) gotowe wyniki DET."""
    if ad_id == FULL_PROBE_ID:
        doc = AdDocument.model_validate_json(
            (EXAMPLES / "facebook_ad_document.json").read_text(encoding="utf-8"))
        det = [RuleResult.model_validate(r) for r in json.loads(
            (EXAMPLES / "rule_result_facebook.json").read_text(encoding="utf-8"))]
        return doc, det
    return doc_from_node(ad_id), None


def score_one(ad_id: str, config) -> dict:
    doc, det = load_case(ad_id)
    finding = analyze(doc, config=config, det_results=det)
    results = finding.rule_results
    # Bierzemy score i poziom WPROST Z POTOKU, nie przeliczamy ich tutaj.
    # Wczesniej ten skrypt wolal risk_level(score) bez wynikow regul, wiec
    # omijal eskalacje po najciezszym naruszeniu i poziom rozjechal sie
    # z tym, co faktycznie produkuje analyzer.
    return {
        "id": ad_id,
        "score": finding.risk_score,
        "risk_level": finding.risk_level.value,
        "coverage": coverage(results),
        "has_render_probe": doc.render_probe is not None,
        "failed_rules": sorted((r.rule_id for r in results if r.verdict is Verdict.FAIL), key=int),
        "n_rules": len(results),
        "text_len": len(doc.text),
    }


def print_table(rows: list[dict]) -> None:
    print(f"{'id':<18}{'score':>7} {'poziom':<8}{'cover':>7} {'probe':<6} fail")
    for r in rows:
        print(f"{r['id']:<18}{r['score']:>7.1f} {r['risk_level']:<8}{r['coverage']:>7.3f} "
              f"{str(r['has_render_probe']):<6} {','.join(r['failed_rules']) or '-'}")


def update_gold(rows: list[dict]) -> None:
    """Nadpisuje pola liczone, zachowuje is_violation i note. Brak recznej etykiety = pominiecie."""
    gold = json.loads(GOLD_PATH.read_text(encoding="utf-8")) if GOLD_PATH.exists() else {"version": 1, "items": []}
    by_id = {str(i.get("id")): i for i in gold.get("items", [])}
    items = []
    for r in rows:
        old = by_id.get(r["id"])
        if old is None or not isinstance(old.get("is_violation"), bool):
            print(f"POMINIETO {r['id']}: brak recznej etykiety is_violation w {GOLD_PATH.name}", file=sys.stderr)
            continue
        items.append({
            "id": r["id"],
            "source": f"fixtures/demo-ads/facebook/{r['id']}/",
            "score": r["score"],
            "coverage": r["coverage"],
            "has_render_probe": r["has_render_probe"],
            "failed_rules": r["failed_rules"],
            "is_violation": old["is_violation"],
            "note": old.get("note", ""),
        })
    gold["items"] = items
    GOLD_PATH.write_text(json.dumps(gold, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-write", action="store_true", help="tylko tabela, bez zapisu zbioru zlotego")
    args = ap.parse_args()

    client = OllamaClient()
    if not client.health():
        print("BLAD: Ollama nie odpowiada.", file=sys.stderr)
        return 1
    config = build_config(client, embed_client=client)

    rows = []
    for ad_id in CORPUS:
        print(f"analizuje {ad_id} ...", flush=True)
        rows.append(score_one(ad_id, config))
    print()
    print_table(rows)

    RESULTS_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not args.no_write:
        update_gold(rows)
        print(f"\nzapisano {GOLD_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

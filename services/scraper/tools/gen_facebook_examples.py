"""Artefakty handoffu dla osob B i C z prawdziwego nagrania (replay snapshotu).

    python tools/gen_facebook_examples.py [--id <ad_archive_id>]

Zapisuje do fixtures/contract-examples/:
    facebook_ad_document.json   AdDocument z replayu zamrozonego snapshotu
    rule_result_facebook.json   lista RuleResult dla regul 4–8 tego dokumentu

Oba pliki sa SANITYZOWANE: kazdy adres http(s) dostaje host `example.invalid`,
sciezka i parametry (`?id=`, `utm_*`, `ref`, `aff`) zostaja. Tego wymaga
tools/check_compliance.py (brak zewnetrznych adresow w sledzonych plikach).
Niesanityzowane zrodlo to fixtures/demo-ads/facebook/<ad_archive_id>/.

Bez --id wybiera z korpusu reklame z ostrzezeniem o ryzyku w tresci (zeby R6/R7
mialy co ocenic); gdy takiej nie ma, pierwsza z korpusu.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from contracts import AdDocument
from sources.facebook import DEFAULT_FIXTURES, FacebookAdsSource, FacebookConfig, feed_fold_evidence
from sources.facebook_rules import facebook_det_results
from sources.meta_json import ad_text, ads_from_html, canonical_ad_url
from storage import LocalBlobStore

OUT = Path(__file__).resolve().parents[3] / "fixtures" / "contract-examples"


def pick_ad(fixtures: Path) -> str:
    ids = sorted(p.name for p in fixtures.iterdir() if (p / "page.html").is_file())
    if not ids:
        raise SystemExit(f"brak nagran w {fixtures} — uruchom record_fb_fixtures.py")
    for ad_id in ids:
        node = ads_from_html((fixtures / ad_id / "page.html").read_text(encoding="utf-8")).get(ad_id)
        if node and feed_fold_evidence(ad_text(node)):
            return ad_id
    return ids[0]


SANITIZED_HOST = "example.invalid"
_URL_RE = re.compile(r"(?i)\bhttps?://[^/\s?#\"'<>]+")


def sanitize(value: Any) -> Any:
    """Podmienia host kazdego adresu http(s) na `example.invalid`, w calym drzewie JSON.

    Sciezka, `?id=` i parametry kampanii zostaja. Adresy `s3://` nie sa ruszane.
    """
    if isinstance(value, str):
        return _URL_RE.sub(f"https://{SANITIZED_HOST}", value)
    if isinstance(value, list):
        return [sanitize(v) for v in value]
    if isinstance(value, dict):
        return {k: sanitize(v) for k, v in value.items()}
    return value


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--id", help="ad_archive_id z korpusu")
    ap.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURES)
    args = ap.parse_args()
    ad_id = args.id or pick_ad(args.fixtures)

    with tempfile.TemporaryDirectory() as tmp:
        src = FacebookAdsSource(
            config=FacebookConfig(mode="replay", fixtures_dir=args.fixtures, min_interval_s=0),
            store=LocalBlobStore(tmp),
        )
        doc = src.fetch(canonical_ad_url(ad_id))
    results = facebook_det_results(doc)

    golden = sanitize(doc.model_dump(mode="json"))
    AdDocument.model_validate(golden)  # sanityzacja nie moze zlamac kontraktu
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "facebook_ad_document.json").write_text(
        json.dumps(golden, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "rule_result_facebook.json").write_text(
        json.dumps(sanitize([r.model_dump(mode="json") for r in results]), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    print(f"reklama {ad_id} -> {OUT / 'facebook_ad_document.json'}")
    for r in results:
        print(f"  R{r.rule_id:<2} {r.engine.value:<6} {r.verdict.value:<15} {r.evidence.summary[:90]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

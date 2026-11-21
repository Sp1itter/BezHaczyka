"""Eksport pelnych AdDocument korpusu FB dla analyzera (zbior zloty) i casedb.

    .venv\\Scripts\\python.exe tools\\export_gold_documents.py

Dla kazdej reklamy z fixtures/demo-ads/facebook/<ad_archive_id>/ robi replay
(Playwright, offline), liczy RuleResult R4-R8 (facebook_det_results) i zapisuje
do fixtures/gold/documents/:

    <ad_archive_id>.json        AdDocument z render_probe na 3 viewportach
    <ad_archive_id>.det.json    lista RuleResult R4-R8 (pole det_results zadania q:gpu)
    facebook_all.json           lista wszystkich AdDocument (wejscie `casedb ingest facebook`)

Pliki sa zsanityzowane tak samo jak przyklady kontraktowe (host -> example.invalid,
sciezka i ?id= zostaja), bo tools/check_compliance.py skanuje sledzone JSON-y.
Pliki wideo nie sa eksportowane: analyzer znajduje je jako
fixtures/demo-ads/facebook/<ad_archive_id>/video.mp4 (stt.resolve_media_path).
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from contracts import AdDocument, RuleResult
from sources.facebook import DEFAULT_FIXTURES, FacebookAdsSource, FacebookConfig
from sources.facebook_rules import facebook_det_results
from sources.meta_json import ad_id_from_url
from storage import LocalBlobStore
from tools.gen_facebook_examples import sanitize

OUT = Path(__file__).resolve().parents[3] / "fixtures" / "gold" / "documents"


def _dump(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def export(fixtures: Path, out: Path) -> list[str]:
    """Eksportuje caly korpus; zwraca liste ad_archive_id."""
    out.mkdir(parents=True, exist_ok=True)
    exported: list[str] = []
    documents: list[dict] = []
    with tempfile.TemporaryDirectory() as tmp:
        src = FacebookAdsSource(
            config=FacebookConfig(mode="replay", fixtures_dir=fixtures, min_interval_s=0, max_ads_per_run=1000),
            store=LocalBlobStore(tmp),
        )
        for url in src.discover(""):
            ad_id = ad_id_from_url(url)
            doc = src.fetch(url)
            det = [r.model_dump(mode="json") for r in facebook_det_results(doc)]
            doc_json = sanitize(doc.model_dump(mode="json"))
            det_json = sanitize(det)
            AdDocument.model_validate(doc_json)  # sanityzacja nie moze zlamac kontraktu
            for r in det_json:
                RuleResult.model_validate(r)
            _dump(out / f"{ad_id}.json", doc_json)
            _dump(out / f"{ad_id}.det.json", det_json)
            documents.append(doc_json)
            exported.append(ad_id)
            print(f"OK  {ad_id}  viewporty={sorted(doc.render_probe.viewports) if doc.render_probe else []}"
                  f"  media={len(doc.media)}")
    _dump(out / "facebook_all.json", documents)
    return exported


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURES)
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()
    ids = export(args.fixtures, args.out)
    print(f"wyeksportowano {len(ids)} reklam -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

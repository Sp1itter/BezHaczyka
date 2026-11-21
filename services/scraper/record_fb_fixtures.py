"""Nagrywanie korpusu offline dla FacebookAdsSource (par. 10 — demo bez wifi).

Uruchomic WIECZOREM PRZED DEMO, na spokojnej sieci, z malym limitem:

    python record_fb_fixtures.py --query "inwestycje" --max 6
    python record_fb_fixtures.py --id 2271445423694435 --id 1638352724350480

Zapisuje do FB_FIXTURES_DIR (domyslnie fixtures/demo-ads/facebook/<ad_archive_id>/):
    page.html      zamrozony snapshot (render/freeze.js), ok. 3 MB
    node.json.gz   surowy wezel reklamy z JSON Meta (opcjonalny przy replay)
    video.mp4      gdy reklama ma wideo (w .gitignore — tylko lokalnie)

Potem `FB_MODE=replay` (albo `auto`) odtwarza te reklamy w calosci offline.
Recznie dopisz `labels.json` (etykiety regul), jak dla reszty fixtures/demo-ads.
"""

from __future__ import annotations

import argparse
import logging
import shutil
import tempfile

from sources.facebook import FacebookAdsSource, FacebookConfig
from sources.meta_json import canonical_ad_url
from storage import LocalBlobStore


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--query", help="fraza wyszukiwania w Ad Library (kraj z FB_COUNTRY)")
    ap.add_argument("--id", action="append", default=[], help="ad_archive_id (mozna wiele razy)")
    ap.add_argument("--max", type=int, default=6, help="limit reklam z --query")
    args = ap.parse_args()
    if not args.query and not args.id:
        ap.error("podaj --query albo --id")

    logging.basicConfig(level=logging.INFO, format="%(name)s %(message)s")
    config = FacebookConfig.from_env()
    config.mode = "live"
    config.max_ads_per_run = args.max
    config.record_dir = config.fixtures_dir
    with tempfile.TemporaryDirectory() as tmp:
        source = FacebookAdsSource(config=config, store=LocalBlobStore(tmp))
        urls = [canonical_ad_url(i) for i in args.id]
        if args.query:
            urls += source.discover(args.query)
        for url in urls:
            doc = source.fetch(url)
            blob = LocalBlobStore(tmp)
            for media in doc.media:  # wideo do korpusu (lokalnie, *.mp4 jest w .gitignore)
                target = config.fixtures_dir / url.rsplit("=", 1)[-1] / "video.mp4"
                shutil.copyfile(blob.path_of(media.path), target)
            print(f"OK  {url}  ->  {config.fixtures_dir / url.rsplit('=', 1)[-1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

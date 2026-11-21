"""Sanityzacja zlotych przykladow dla fixtures/contract-examples (tools/gen_facebook_examples.py)."""

from __future__ import annotations

import json
import re

import pytest

from tests.conftest import REPO_ROOT
from tools.gen_facebook_examples import SANITIZED_HOST, sanitize

AD_LIB = "https://www.facebook.com/ads/library/?id=912810501476495"  # compliance:allow — wejscie testu sanityzacji
LANDING = "https://www.virtune.com/pl/sol?utm_source=meta&utm_campaign=sol&ref=x&aff=y"  # compliance:allow — j.w.


def test_host_replaced_path_and_params_kept():
    assert sanitize(AD_LIB) == "https://example.invalid/ads/library/?id=912810501476495"
    assert sanitize(LANDING) == "https://example.invalid/pl/sol?utm_source=meta&utm_campaign=sol&ref=x&aff=y"


def test_urls_inside_text_and_nested_structures():
    doc = {"text": f"Sprawdź {LANDING}\nWięcej: {AD_LIB}", "a": [{"b": AD_LIB}], "n": 1, "z": None}
    out = sanitize(doc)
    assert out["n"] == 1 and out["z"] is None
    assert "virtune.com" not in out["text"] and "facebook.com" not in json.dumps(out)
    assert out["text"].startswith("Sprawdź https://example.invalid/pl/sol?utm_source=meta")


def test_uppercase_scheme_and_s3_untouched():
    assert sanitize("HTTPS://WWW.VIRTUNE.COM") == f"https://{SANITIZED_HOST}"
    assert sanitize("s3://shots/abc-1920.png") == "s3://shots/abc-1920.png"


@pytest.mark.parametrize("name", ["facebook_ad_document.json", "rule_result_facebook.json"])
def test_committed_examples_have_no_external_hosts(name):
    path = REPO_ROOT / "fixtures" / "contract-examples" / name
    if not path.exists():
        pytest.skip(f"brak {name}")
    hosts = set(re.findall(r"(?i)https?://([A-Za-z0-9_.\-]+)", path.read_text(encoding="utf-8")))
    assert hosts <= {SANITIZED_HOST}, hosts

from __future__ import annotations

import json

import pytest

from sources.meta_json import (
    AD_LIBRARY_URL,
    ad_id_from_url,
    ad_text,
    ad_title,
    ads_from_graphql,
    ads_from_html,
    canonical_ad_url,
    clean_text,
    find_ad_nodes,
    link_urls,
    primary_body,
    publisher_from,
    search_url,
    unwrap_meta_redirect,
    video_urls,
)
from tests.conftest import FIXTURES

FB = "https://www.facebook.com"  # compliance:allow — dane testowe adaptera Meta
REDIRECT = "https://l.facebook.com/l.php?u="  # compliance:allow — dane testowe adaptera Meta
AD_ID = "1234567890123456"


def _node(**snapshot):
    return {"ad_archive_id": AD_ID, "page_id": "1", "page_name": "Inwestor PL", "snapshot": snapshot}


# ------------------------------------------------------------------ URL-e --


def test_canonical_url_roundtrip():
    url = canonical_ad_url(AD_ID)
    assert url == f"{AD_LIBRARY_URL}?id={AD_ID}"
    assert ad_id_from_url(url) == AD_ID


def test_ad_id_from_redirected_url():
    """Meta przepisuje ?id= na wariant z parametrami strony — id musi przetrwac."""
    url = f"{AD_LIBRARY_URL}?active_status=active&country=PL&id={AD_ID}&search_type=page&view_all_page_id=1"
    assert ad_id_from_url(url) == AD_ID


@pytest.mark.parametrize(
    "url",
    [
        f"{AD_LIBRARY_URL}?q=inwestycje",
        f"{AD_LIBRARY_URL}?id=abc",
        "https://example.invalid/ads/library/?id=1234567890123456",
        f"{FB}/skarbiecpl/",
    ],
)
def test_ad_id_from_url_rejects(url):
    with pytest.raises(ValueError):
        ad_id_from_url(url)


def test_canonical_rejects_non_numeric():
    with pytest.raises(ValueError):
        canonical_ad_url("1; DROP")


def test_search_url_targets_pl_active_keyword():
    url = search_url("forex sygnały")
    assert "country=PL" in url and "active_status=active" in url and "q=forex+sygna" in url


def test_unwrap_meta_redirect_keeps_target_params():
    wrapped = REDIRECT + "https%3A%2F%2Fexample.invalid%2Fk%3Futm_campaign%3Da%26aff%3Db&h=AT0"
    assert unwrap_meta_redirect(wrapped) == "https://example.invalid/k?utm_campaign=a&aff=b"
    assert unwrap_meta_redirect("https://example.invalid/") == "https://example.invalid/"
    assert unwrap_meta_redirect(None) is None


# --------------------------------------------------------- wyciaganie JSON --


def test_graphql_body_with_prefix_and_multiple_lines():
    line1 = json.dumps({"data": {"x": [_node(body={"text": "A"})]}})
    other = dict(_node(body={"text": "B"}), ad_archive_id="2222222222222222")
    line2 = json.dumps({"data": {"deep": {"deeper": [other]}}})
    found = ads_from_graphql("for (;;);" + line1 + "\n" + line2)
    assert set(found) == {AD_ID, "2222222222222222"}


def test_find_ad_nodes_ignores_objects_without_snapshot():
    assert find_ad_nodes({"ad_archive_id": "1", "snapshot": None}) == {}


def test_find_ad_nodes_survives_very_deep_tree():
    tree: dict = _node(body={"text": "x"})
    for _ in range(5000):  # rekurencja by tu padla
        tree = {"n": tree}
    assert AD_ID in find_ad_nodes(tree)


def test_ads_from_html_reads_inline_script():
    html = (FIXTURES / "facebook" / AD_ID / "page.html").read_text(encoding="utf-8")
    assert list(ads_from_html(html)) == [AD_ID]


# ------------------------------------------------------- mapowanie / DCO --


def test_clean_text_drops_dco_placeholders_and_zero_width():
    assert clean_text({"text": "{{product.brand}}"}) is None
    assert clean_text("Zysk\u200b  {{x}} 18% rocznie ") == "Zysk 18% rocznie"


def test_dco_ad_uses_cards_not_placeholders():
    node = json.loads(json.dumps(ads_from_html(
        (FIXTURES / "facebook" / AD_ID / "page.html").read_text(encoding="utf-8")
    )[AD_ID]))
    text = ad_text(node)
    assert "{{" not in text
    assert text.startswith("Chcesz zarabiać więcej")  # tresc glowna ZAWSZE pierwsza
    assert ad_title(node) == "Zyski do 18% rocznie!"
    assert primary_body(node).endswith("ryzykiem utraty kapitału.")
    # rozwiniety link docelowy z parametrami kampanii i afiliacji
    assert "https://example.invalid/kurs?utm_source=meta&utm_campaign=sygnaly24&aff=jan77" in text
    assert "ref=jan" in text


def test_ad_text_deduplicates_repeated_parts():
    node = _node(body={"text": "Tekst"}, title="Tekst", caption="tekst")
    assert ad_text(node) == "Tekst"


def test_link_urls_unwraps_and_dedups():
    node = _node(link_url="https://example.invalid/?utm_campaign=x",
                 cards=[{"link_url": REDIRECT + "https%3A%2F%2Fexample.invalid%2F%3Futm_campaign%3Dx"}])
    assert link_urls(node) == ["https://example.invalid/?utm_campaign=x"]


def test_video_urls_prefers_hd_and_reads_cards():
    node = _node(videos=[{"video_hd_url": "hd1", "video_sd_url": "sd1"}],
                 cards=[{"video_sd_url": "sd2"}, {"body": "x"}])
    assert video_urls(node) == ["hd1", "sd2"]


@pytest.mark.parametrize(
    "uri,handle",
    [
        (f"{FB}/skarbiecpl/", "@skarbiecpl"),
        (f"{FB}/profile.php?id=1", None),
        ("https://example.invalid/x/", None),
    ],
)
def test_publisher_handle(uri, handle):
    pub = publisher_from(_node(page_profile_uri=uri))
    assert pub.handle == handle
    assert pub.display_name == "Inwestor PL"
    assert pub.is_official_firm_channel is False  # nadpisuje dopiero resolver w analyzerze


def test_publisher_without_profile_uri_falls_back_to_page_id():
    pub = publisher_from(_node())
    assert pub.profile_url == f"{FB}/1"
    assert pub.handle is None

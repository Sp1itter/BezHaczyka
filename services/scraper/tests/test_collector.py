"""Dwupoziomowy pipeline: collector (URL-e) i flota (fetch + DET + analyzer)."""

from __future__ import annotations

import gzip
import json
import os
import shutil
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from collector.candidates import from_facebook_node
from collector.collect import collect_facebook_query, reprioritize, run_collector
from collector.config import CollectorConfig
from collector.fleet import process_one, run_fleet
from collector.lexicons import CollectorConfigFiles
from collector.scoring import Candidate, affiliate_params, creative_key, landing_key, score, wants_analysis
from collector.store import SqliteUrlStore, open_store
from contracts import AdDocument
from sources.base import SourceBlocked
from tests.conftest import REPO_ROOT

CONFIG = Path(__file__).resolve().parents[1] / "config"
FB_CORPUS = REPO_ROOT / "fixtures" / "demo-ads" / "facebook"
GOLDEN = REPO_ROOT / "fixtures" / "contract-examples" / "facebook_ad_document.json"
REAL_ESTATE = {"1416188807395560", "1685589429005115", "675484101807418", "986443020999266", "28815441858041693"}
SQUABER = ("1688659872622573", "1700487841682444")
VIRTUNE = "912810501476495"


# ---------------------------------------------------------------- fixtures --


@pytest.fixture
def files(tmp_path) -> CollectorConfigFiles:
    cfg_dir = tmp_path / "config"
    shutil.copytree(CONFIG, cfg_dir)
    return CollectorConfigFiles(cfg_dir)


@pytest.fixture
def cfg(tmp_path) -> CollectorConfig:
    return CollectorConfig(state_dir=tmp_path / "state", interval_s=0, jitter_s=0, idle_sleep_s=0,
                           retry_after_s=60, blocked_pause_s=600)


def _stores(tmp_path):
    yield SqliteUrlStore(tmp_path / "url_store.sqlite")
    url = os.getenv("COLLECTOR_TEST_DATABASE_URL")
    if url:
        store = open_store(url)
        store._execute("DELETE FROM url_store")
        yield store


@pytest.fixture(params=["sqlite", "postgres"])
def store(request, tmp_path):
    if request.param == "postgres" and not os.getenv("COLLECTOR_TEST_DATABASE_URL"):
        pytest.skip("brak COLLECTOR_TEST_DATABASE_URL")
    stores = list(_stores(tmp_path))
    return stores[0] if request.param == "sqlite" else stores[1]


def real_nodes() -> dict[str, dict]:
    return {d.name: json.loads(gzip.decompress((d / "node.json.gz").read_bytes()))
            for d in sorted(FB_CORPUS.iterdir())}


class FakeSource:
    def __init__(self, nodes=None, blocked=False):
        self.nodes, self.blocked, self.calls = nodes or {}, blocked, []

    def discover_nodes(self, query, search_type="keyword_unordered"):
        self.calls.append((query, search_type))
        if self.blocked:
            raise SourceBlocked("checkpoint")
        return self.nodes


def cand(text: str, **kw) -> Candidate:
    base = {"source_type": "synthetic", "external_id": kw.pop("external_id", "x1"),
            "url": "https://example.invalid/x", "query_tag": "t", "text": text, "primary_text": text,
            "publisher_key": kw.pop("publisher_key", "web:example.invalid")}
    base.update(kw)
    return Candidate(**base)


# ---------------------------------------------------------------- scoring --


def test_scam_with_public_figure_gets_top_priority(files):
    text = ("Jan Przykladowy ujawnia sekret: z 1000 zł do 15 000 zł miesięcznie dzięki platformie AI. "
            "Gwarantowany zysk bez ryzyka!")
    s = score(cand(text), files.lexicons())
    assert s.state == "queued"
    assert s.priority >= 9.0
    assert s.signals["personas"] == ["Jan Przykladowy"]
    assert s.signals["persona_official_channel"] is False


def test_persona_on_official_channel_is_not_impersonation(files):
    text = "Jan Przykladowy zaprasza na konferencję spółki o wynikach kwartalnych i dywidendzie."
    c = cand(text, publisher_key="facebook:000000000000000")
    s = score(c, files.lexicons())
    assert s.signals["persona_official_channel"] is True
    assert s.signals["components"]["impersonation"] == 0.0


def test_real_estate_is_quarantined_not_analyzed(files):
    s = score(cand("Nowe apartamenty inwestycyjne nad morzem. Mieszkanie z widokiem, zysk z wynajmu."),
              files.lexicons())
    assert s.state == "quarantined" and s.priority < 0


def test_short_text_rejected(files):
    assert score(cand("Kup teraz!"), files.lexicons()).state == "rejected"


def test_utm_is_tracking_not_affiliation():
    links = ["https://example.invalid/a?utm_source=facebook&utm_campaign=x"]
    assert affiliate_params(links) == []
    assert affiliate_params(["https://example.invalid/a?ref=jan77&aff=9"]) == ["ref=jan77", "aff=9"]


def test_analyzer_threshold_and_optional_instrument_lane(files):
    lex = files.lexicons()
    assert wants_analysis(3.0, {}, lex) and not wants_analysis(2.9, {"instrument": ["etp"]}, lex)
    lex.instrument_lane_min = 2.0
    assert wants_analysis(2.1, {"instrument": ["etp"]}, lex)
    assert not wants_analysis(2.1, {}, lex)


def test_keys():
    assert landing_key("https://www.example.invalid/kurs/?utm_campaign=a") == "example.invalid/kurs"
    assert landing_key("http://fb.me/") is None
    assert creative_key("facebook:1", "Ta sama tresc reklamy, dluzsza niz dwadziescia znakow") == \
        creative_key("facebook:1", "ta  SAMA treść reklamy, dłuższa niż dwadzieścia znaków")


# ------------------------------------------------------ poziom 1 na danych --


def test_collect_real_meta_nodes_filters_noise_and_merges_duplicates(store, files):
    nodes = real_nodes()
    rep = collect_facebook_query(store, files, FakeSource(nodes), {"q": "inwestycje", "tag": "test"})
    assert rep.found == 8 and rep.created == 8
    rows = {r["external_id"]: r for r in store.rows(("queued", "quarantined", "merged", "rejected"))}
    for ad_id in REAL_ESTATE:
        assert rows[ad_id]["state"] == "quarantined", ad_id
    squaber = sorted(rows[a]["state"] for a in SQUABER)
    assert squaber == ["merged", "queued"]  # ta sama kreacja: jedna praca, nie dwie
    assert rows[VIRTUNE]["state"] == "queued"
    assert rows[VIRTUNE]["signals"]["instrument"]
    stats = store.stats()
    assert stats["by_state"]["quarantined"] == 5 and stats["by_state"]["merged"] == 1
    assert stats["noise_ratio"] == 0.75


def test_second_pass_does_not_duplicate(store, files):
    src = FakeSource(real_nodes())
    collect_facebook_query(store, files, src, {"q": "a", "tag": "t"})
    rep = collect_facebook_query(store, files, src, {"q": "b", "tag": "t"})
    assert rep.created == 0 and rep.seen_again == 8
    assert store.stats()["total"] == 8
    assert all(r["seen_count"] >= 2 for r in store.rows(("queued", "quarantined")))


def test_reprioritize_after_lexicon_change(store, files):
    collect_facebook_query(store, files, FakeSource(real_nodes()), {"q": "a", "tag": "t"})
    path = files.dir / "lexicons.yaml"
    path.write_text(path.read_text(encoding="utf-8").replace("non_instrument_only: -4.0", "non_instrument_only: 0.0")
                    .replace("  non_instrument: [mieszkan", "  non_instrument: [zzzz, mieszkan_x"), encoding="utf-8")
    os.utime(path, (time.time() + 5, time.time() + 5))
    changed = reprioritize(store, files)
    assert sum(changed.values()) >= 1
    assert store.get(next(r["id"] for r in store.rows(("queued",)) if r["external_id"] == "1416188807395560"))


# ------------------------------------------------------------ kolejka --


def _queue(store, files, n=3):
    lex = files.lexicons()
    ids = []
    for i in range(n):
        c = cand(f"Kontrakty CFD i akcje z dźwignią, sygnały dla klientów numer {i}", external_id=f"c{i}",
                 publisher_key=f"web:p{i}")
        ids.append(store.upsert(c, score(c, lex), creative_key(c.publisher_key, c.primary_text), None).id)
    return ids


def test_claim_is_exclusive_and_ordered(store, files):
    _queue(store, files, 2)
    a, b = store.claim("w1"), store.claim("w2")
    assert a and b and a["id"] != b["id"]
    assert store.claim("w3") is None


def test_expired_lease_returns_to_pool(store, files):
    _queue(store, files, 1)
    first = store.claim("w1", lease_s=10)
    assert store.claim("w2") is None
    later = datetime.now(UTC) + timedelta(seconds=20)
    again = store.claim("w2", now=later)
    assert again["id"] == first["id"] and again["attempts"] == 2


def test_fail_backoff_then_error(store, files):
    (row_id,) = _queue(store, files, 1)
    store.claim("w")
    assert store.fail(row_id, "boom", max_attempts=2, retry_after_s=60) == "retry"
    assert store.claim("w") is None  # backoff
    store.claim("w", now=datetime.now(UTC) + timedelta(seconds=61))
    assert store.fail(row_id, "boom", max_attempts=2) == "error"
    assert store.get(row_id)["state"] == "error"


# ---------------------------------------------------- petla collectora --


def test_pause_stops_collector_only(store, files, cfg):
    cfg.state_dir.mkdir(parents=True)
    cfg.pause_flag.write_text("x")
    src = FakeSource(real_nodes())
    run_collector(store, files, cfg, lambda: src, max_iterations=2, sleep=lambda s: None)
    assert src.calls == []
    # flota dalej przerabia kolejke
    _queue(store, files, 1)
    assert run_fleet(store, files, cfg, fetcher=lambda r: _golden(), handoff=lambda d: None,
                     stop_when_empty=True, sleep=lambda s: None)


def test_blocked_source_pauses_without_retry_storm(store, files, cfg):
    slept = []
    src = FakeSource(blocked=True)
    reports = run_collector(store, files, cfg, lambda: src, max_iterations=2, sleep=slept.append)
    assert len(src.calls) == 2 and all(r.error for r in reports)
    assert slept.count(cfg.blocked_pause_s) == 2
    assert json.loads((cfg.state_dir / "stats.json").read_text(encoding="utf-8"))["total"] == 0


def test_round_robin_over_queries_and_exact_phrase(store, files, cfg):
    src = FakeSource({})
    run_collector(store, files, cfg, lambda: src, max_iterations=3, sleep=lambda s: None)
    assert [c[0] for c in src.calls] == ["gwarantowany zysk", "dochód pasywny", "platforma inwestycyjna"]
    assert src.calls[0][1] == "keyword_exact_phrase"


# ------------------------------------------------------------- flota --


def _golden() -> AdDocument:
    return AdDocument.model_validate(json.loads(GOLDEN.read_text(encoding="utf-8")))


def test_fleet_sends_only_priority_to_analyzer(store, files, cfg):
    lex = files.lexicons()
    high = cand("Jan Przykladowy ujawnia sekret: gwarantowany zysk z platformy AI, z 1000 zł dziennie.",
                external_id="hi", publisher_key="web:a")
    low = cand("Akcje i ETF na giełdzie dla każdego, prowadź rachunek maklerski u nas.",
               external_id="lo", publisher_key="web:b")
    for c in (high, low):
        store.upsert(c, score(c, lex), creative_key(c.publisher_key, c.primary_text), None)
    sent = []
    result = run_fleet(store, files, cfg, fetcher=lambda r: _golden(), handoff=sent.append,
                       stop_when_empty=True, sleep=lambda s: None)
    assert result == {"done": 1, "fetched": 1}
    assert len(sent) == 1
    states = {r["external_id"]: r for r in store.rows(("done", "fetched"))}
    assert states["hi"]["state"] == "done" and states["lo"]["state"] == "fetched"
    assert states["hi"]["document_id"] == _golden().id
    assert (cfg.state_dir / "documents" / f"{_golden().id}.json").is_file()


def test_fleet_fetch_error_and_handoff_error_are_retried(store, files, cfg):
    (row_id,) = _queue(store, files, 1)

    def bad_fetch(row):
        raise RuntimeError("timeout")

    assert process_one(store, files, cfg, "w", bad_fetch, None) == "retry"
    store._execute(f"UPDATE url_store SET locked_until = NULL, state = 'queued' WHERE id = {row_id}")
    store.set_priority(row_id, 5.0, "queued", {"instrument": ["cfd"]})

    def bad_handoff(doc):
        raise ConnectionError("api down")

    assert process_one(store, files, cfg, "w", lambda r: _golden(), bad_handoff) == "retry"
    assert "handoff" in store.get(row_id)["last_error"]


# ------------------------------------------------------------ UA i proxy --


def test_user_agents_and_proxy_list_from_env():
    from sources.facebook import FacebookAdsSource, FacebookConfig

    env = {"USER_AGENTS": "UA-1||UA-2", "PROXY_URLS": "http://p1.invalid:3128, http://p2.invalid:3128"}
    c = FacebookConfig.from_env(env)
    assert c.user_agents == ["UA-1", "UA-2"]
    assert c.proxies == ["http://p1.invalid:3128", "http://p2.invalid:3128"]
    assert FacebookConfig.from_env({"SCRAPER_PROXY": "http://p.invalid:1"}).proxies == ["http://p.invalid:1"]

    seen = []

    class FakeBrowser:
        def new_context(self, **kw):
            seen.append(kw)
            return object()

    src = FacebookAdsSource(config=c)
    for _ in range(3):
        src._new_context(FakeBrowser(), "desktop")
    assert [k["proxy"]["server"] for k in seen] == ["http://p1.invalid:3128", "http://p2.invalid:3128",
                                                    "http://p1.invalid:3128"]
    assert all(k["user_agent"] in ("UA-1", "UA-2") for k in seen)


def test_no_proxy_by_default():
    from sources.facebook import FacebookAdsSource, FacebookConfig

    seen = []

    class FakeBrowser:
        def new_context(self, **kw):
            seen.append(kw)

    FacebookAdsSource(config=FacebookConfig.from_env({}))._new_context(FakeBrowser(), "desktop")
    assert "proxy" not in seen[0] and "user_agent" not in seen[0]


# ------------------------------------------------------------ konfiguracja --


def test_broken_lexicon_keeps_last_good_version(files):
    good = files.lexicons()
    path = files.dir / "lexicons.yaml"
    path.write_text("weights: [to: nie, jest: slownik", encoding="utf-8")
    os.utime(path, (time.time() + 5, time.time() + 5))
    assert files.lexicons() is good
    assert "lexicons.yaml" in files.errors()


def test_unknown_lexicon_kind_rejected(files):
    files.lexicons()  # najpierw poprawna wersja
    path = files.dir / "lexicons.yaml"
    path.write_text(path.read_text(encoding="utf-8") + "  nowy_slownik: [x]\n", encoding="utf-8")
    os.utime(path, (time.time() + 5, time.time() + 5))
    files.lexicons()
    assert "nieznane slowniki" in files.errors()["lexicons.yaml"]


def test_candidate_from_real_node_has_text_without_render():
    node = real_nodes()[VIRTUNE]
    c = from_facebook_node(VIRTUNE, node, "t")
    assert c.url.endswith(f"?id={VIRTUNE}") and "Solan" in c.text and c.publisher_key.startswith("facebook:")

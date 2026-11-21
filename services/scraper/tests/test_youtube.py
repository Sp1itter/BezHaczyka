# compliance:allow-file - testowe adresy w danych wejsciowych (ruch sieciowy zamockowany)
from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest
import sources.youtube as yt
from net import Rotator
from sources.base import SourceBlocked, SourceError, SourceGone
from sources.youtube import (
    YouTubeSource,
    dictionary_from_registry,
    find_targets,
    is_language,
    make_clips,
    proximate,
    queries_for,
)

PL = "W tym odcinku przedstawiamy warunki oferty i wyjaśniamy, na co należy uważać przed wpłaceniem własnych pieniędzy. "
DICT = [
    {"id": "company", "type": "organization", "value": "Firma Przykład", "aliases": ["Przykład SA"]},
    {"id": "site", "type": "domain", "value": "broker.example"},
    {"id": "person", "type": "agent", "value": "Agent Przykładowy"},
]
SIGNALS = ["gwarantowany zysk", "załóż konto", "link partnerski", "bez ryzyka", "link afiliacyjny"]
XTB = [
    {"id": "xtb", "type": "organization", "value": "XTB", "aliases": ["XTB S.A."]},
    {"id": "xtb-domain", "type": "domain", "value": "xtb.com"},
    {"id": "wal", "type": "organization", "value": "Walutomat"},
    {"id": "wal-domain", "type": "domain", "value": "walutomat.pl"},
]
VID = "aaaaaaaaaaa"


def segs(*texts):
    return [{"text": t, "start": i * 6, "duration": 5} for i, t in enumerate(texts)]


def make(**kw):
    kw.setdefault("signals", SIGNALS)
    kw.setdefault("rotator", Rotator(["UA"], []))
    return YouTubeSource(kw.pop("dictionary", DICT), **kw)


def patched(monkeypatch, src, info, captions=()):
    monkeypatch.setattr(src, "_metadata", lambda vid: info)
    monkeypatch.setattr(src, "_transcript", lambda vid: list(captions))
    return src


def info(description="", **extra):
    return {"id": VID, "title": "Oferta", "description": description, "channel_id": "UCa", **extra}


# --- falszywe trafienia ------------------------------------------------------


def test_signal_in_other_line_and_foreign_url_is_not_evidence():
    text = (
        "Kurs XTB runął po decyzji banku centralnego.\n"
        "👉 Black Friday w InvestingPRO: https://www.investing-referral.com/x\n"
        "Walutomat: https://www.walutomat.pl/?ref=afil\n"
        "Wszystkie nasze linki to link afiliacyjny, dziękuję za wsparcie."
    )
    assert yt.evidence(text, "description", XTB, SIGNALS) == []


def test_same_sentence_with_own_domain_url_passes():
    text = "Konto w XTB założysz z mojego linku partnerskiego: https://www.xtb.com/pl?ref=abc"
    found = yt.evidence(text, "description", XTB, ["linku partnerskiego", "link partnerski"])
    assert {e["target"] for e in found} == {"XTB", "xtb.com"}
    assert any(e["type"] == "domain" and e["url"].startswith("https://www.xtb.com") for e in found)


def test_foreign_url_in_same_line_rejects_org_hit():
    text = "XTB to świetny broker, link afiliacyjny: https://www.walutomat.pl/?ref=1"
    targets = {h["name"] for h in proximate(text, XTB, SIGNALS)}
    assert "XTB" not in targets and "Walutomat" in targets


def test_sentence_split_keeps_dots_inside_urls():
    text = "Kurs XTB spadł. Link afiliacyjny: https://www.xtb.com/pl?ref=a. Dziękuję"
    hits = proximate(text, XTB, SIGNALS)
    assert {h["name"] for h in hits} == {"XTB", "xtb.com"}
    assert all(h["sentence"].startswith("Link afiliacyjny") for h in hits)


# --- logika przeniesiona z demo ----------------------------------------------


def test_domain_host_not_query_or_lookalike():
    text = "https://evil.example?x=broker.example notbroker.example broker.example.evil.org https://sub.broker.example/?aff=1"
    assert [h["value"] for h in find_targets(text, DICT)] == ["https://sub.broker.example/?aff=1"]


def test_keywords_never_qualify():
    kw = [{"id": "k", "type": "keyword", "value": "inwestowanie"}]
    assert find_targets("inwestowanie", kw) == []
    with pytest.raises(ValueError):
        YouTubeSource(kw)


def test_clip_short_with_target_and_signal():
    r = make_clips(segs(PL, "Firma Przykład oferuje gwarantowany zysk.", "Opisujemy szczegóły."), DICT, SIGNALS, 30, 2)
    assert len(r) == 1 and r[0]["end"] - r[0]["start"] <= 30
    assert r[0]["targets"] == ["Firma Przykład"] and "gwarantowany zysk" in r[0]["signals"]
    assert 4 <= r[0]["start"] and r[0]["end"] <= 14


def test_distant_target_does_not_create_clip():
    data = [{"text": PL + " Firma Przykład.", "start": 0, "duration": 5}, {"text": "Załóż konto.", "start": 600, "duration": 5}]
    assert make_clips(data, DICT, SIGNALS, 30, 2) == []


def test_repeated_hits_never_expand_into_whole_film():
    data = [{"text": "Firma Przykład. Gwarantowany zysk.", "start": i * 10, "duration": 5} for i in range(100)]
    clips = make_clips(data, DICT, SIGNALS, 30, 2)
    assert len(clips) <= 2 and all(c["end"] - c["start"] <= 30 for c in clips)


def test_language_filter():
    assert not is_language("ETF broker.example", "pl")
    assert not is_language("This video explains the investment offer and account registration. Please read all the terms and conditions before depositing money into your account.", "pl")
    assert is_language(PL * 3, "pl")
    english = "This video explains the investment offer and account registration. Read the terms and conditions before depositing money. "
    assert not is_language(PL * 80 + english * 400, "pl")


# --- fetch / discover (bez sieci) ---------------------------------------------


def test_fetch_qualified_document(monkeypatch):
    src = patched(
        monkeypatch, make(),
        info(
            PL + " Firma Przykład: gwarantowany zysk. " + PL * 3,
            uploader_id="@kanal", channel="Kanał", channel_url="https://www.youtube.com/@kanal",
            upload_date="20261105", duration=60,
            comments=[
                {"id": "c1", "author_id": "UCa", "text": "Komentarz autora", "parent": "root"},
                {"id": "c2", "author_id": "UCother", "text": "Cudzy"},
            ],
        ),
        segs(PL, "Firma Przykład oferuje gwarantowany zysk.", "Koniec."),
    )
    doc, meta = src.fetch_with_evidence(f"https://youtu.be/{VID}")
    url = f"https://www.youtube.com/watch?v={VID}"
    assert doc.id == str(uuid.uuid5(uuid.NAMESPACE_URL, url)) and doc.url == url and doc.source == "youtube"
    assert doc.publisher.handle == "@kanal" and doc.publisher.display_name == "Kanał"
    assert doc.publisher.profile_url == "https://www.youtube.com/@kanal"
    assert doc.text.startswith("Oferta\n\n") and doc.text.endswith("Komentarz autora") and "Cudzy" not in doc.text
    assert doc.transcript.engine == "youtube-captions" and doc.transcript.segments[1].end == 11
    assert doc.media == []
    assert meta["qualified"] and meta["targets"] == ["Firma Przykład"]
    assert meta["channel_id"] == "UCa" and meta["published_at"].startswith("2026-11-05")
    assert meta["clips"][0]["url"].endswith("&t=4s") and meta["evidence"]
    assert src.fetch(url).id == doc.id


def test_not_qualified_without_promotion_or_when_excluded(monkeypatch):
    neutral = patched(monkeypatch, make(), info(PL), segs(PL, "Firma Przykład publikuje wyniki kwartalne."))
    doc, meta = neutral.fetch_with_evidence(VID_URL := f"https://www.youtube.com/watch?v={VID}")
    assert not meta["qualified"] and doc.url == VID_URL
    desc = PL + " Firma Przykład: gwarantowany zysk."
    excluded = patched(monkeypatch, make(exclude={"title": ["oferta"]}), info(desc))
    assert not excluded.fetch_with_evidence(VID_URL)[1]["qualified"]
    english = patched(monkeypatch, make(), info("Firma Przykład: gwarantowany zysk."))
    assert not english.fetch_with_evidence(VID_URL)[1]["qualified"]


def test_text_evidence_without_captions(monkeypatch):
    src = patched(monkeypatch, make(), info(PL + " Załóż konto: https://broker.example/?ref=1"))
    doc, meta = src.fetch_with_evidence(f"{yt.WATCH}{VID}")
    assert meta["qualified"] and meta["clips"] == [] and doc.transcript is None
    assert meta["evidence"][0]["target"] == "broker.example"


def test_transcript_failure_is_not_fatal(monkeypatch):
    src = make()
    monkeypatch.setattr(src, "_metadata", lambda vid: info(PL))

    def boom(vid):
        raise RuntimeError("blocked")

    monkeypatch.setattr(src, "_transcript", boom)
    assert src.fetch(f"{yt.WATCH}{VID}").transcript is None


def test_invalid_url_and_gone(monkeypatch):
    src = make()
    with pytest.raises(SourceError):
        src.fetch("https://example.com/x")

    class Boom:
        def __init__(self, options): ...
        def __enter__(self): return self
        def __exit__(self, *a): ...
        def extract_info(self, url, download):
            raise self.error

    from yt_dlp.utils import DownloadError

    for message, exc in [("Video unavailable", SourceGone), ("Private video", SourceGone),
                         ("Sign in to confirm you're not a bot", SourceBlocked), ("boom", SourceError)]:
        Boom.error = DownloadError(message)
        monkeypatch.setattr("yt_dlp.YoutubeDL", Boom)
        with pytest.raises(exc):
            src.fetch(f"{yt.WATCH}{VID}")


def test_discover_canonical_unique_and_limiter(monkeypatch):
    calls, opts = [], []

    class Client:
        def __init__(self, options): opts.append(options)
        def __enter__(self): return self
        def __exit__(self, *a): ...
        def extract_info(self, url, download):
            calls.append(url)
            return {"entries": [{"id": VID}, {"id": "bbbbbbbbbbb"}, {"id": VID}, {"id": "zly"}, None]}

    ticks = []
    src = make(limiter=SimpleNamespace(acquire=lambda: ticks.append(1)), rotator=Rotator(["UA-x"], ["http://p:1"]), results_per_query=3)
    monkeypatch.setattr("yt_dlp.YoutubeDL", Client)
    assert src.discover("XTB kod") == [f"{yt.WATCH}{VID}", f"{yt.WATCH}bbbbbbbbbbb"]
    assert calls == ["ytsearch3:XTB kod"] and ticks == [1]
    assert opts[0]["http_headers"]["User-Agent"] == "UA-x" and opts[0]["proxy"] == "http://p:1"


# --- slownik z rejestru -------------------------------------------------------


def test_dictionary_from_registry_and_queries():
    rows = [{"knf_id": "DM1", "name": "XTB S.A.", "aliases": ["XTB", "X", "ab"], "domains": ["https://www.xtb.com/pl", "xtb.pl"]},
            {"knf_id": "", "name": "Bez id", "aliases": [], "domains": []}]
    d = dictionary_from_registry(rows)
    assert d[0] == {"id": "DM1", "group": "DM1", "type": "organization", "value": "XTB S.A.", "aliases": ["XTB"]}
    assert [(e["type"], e["value"]) for e in d[1:]] == [("domain", "xtb.com"), ("domain", "xtb.pl")]
    assert queries_for(rows[:1], ["kod polecający", "link partnerski"]) == ["XTB kod polecający", "XTB link partnerski"]
    # laczenie z domena przez group: obca domena w linii odrzuca trafienie firmy
    assert proximate("XTB link partnerski https://obca.pl/x", d, SIGNALS) == []
    assert proximate("XTB link partnerski https://xtb.pl/x", d, SIGNALS)


def test_no_captions_qualifies_on_firm_mention_in_title_or_description(monkeypatch):
    """Brak napisow (np. IpBlocked) nie odrzuca filmu: wystarczy firma z rejestru w opisie."""
    src = patched(monkeypatch, make(), info(PL * 2 + " Dzisiaj o tym, co robi Firma Przykład."))
    doc, meta = src.fetch_with_evidence(f"{yt.WATCH}{VID}")
    assert doc.transcript is None and meta["qualified"]
    assert meta["evidence"][0]["target"] == "Firma Przykład"
    assert meta["evidence"][0]["basis"] == yt.NO_CAPTIONS_BASIS and meta["evidence"][0]["signals"] == []


def test_firm_mention_without_signal_needs_missing_captions(monkeypatch):
    """Z napisami zostaje dotychczasowa, scisla kwalifikacja (cel + sygnal w jednym zdaniu)."""
    src = patched(monkeypatch, make(), info(PL * 2 + " Dzisiaj o tym, co robi Firma Przykład."), segs(PL, PL))
    assert not src.fetch_with_evidence(f"{yt.WATCH}{VID}")[1]["qualified"]

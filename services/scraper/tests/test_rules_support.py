"""Wsparcie zrodla facebook dla regul 5, 7, 8 (decyzje Fazy 1)."""

from __future__ import annotations

from sources.facebook import (
    FEED_FOLD_CHARS,
    PLATFORM_TYPOGRAPHY_REASON,
    feed_fold_evidence,
    platform_rule_override,
)


def test_rules_4_5_and_8_not_applicable_for_facebook():
    for rule in ("4", "5", "8", 4, 5, 8):
        assert platform_rule_override(rule, "facebook") == ("not_applicable", PLATFORM_TYPOGRAPHY_REASON)


def test_other_rules_and_sources_untouched():
    assert platform_rule_override("7", "facebook") is None
    assert platform_rule_override("6", "facebook") is None
    for rule in ("4", "5", "8"):
        assert platform_rule_override(rule, "web") is None
        assert platform_rule_override(rule, "instagram") is None
    assert platform_rule_override("5", "web") is None


def test_warning_beyond_feed_fold():
    body = "A" * 200 + ". Inwestowanie wiąże się z ryzykiem utraty kapitału."
    ev = feed_fold_evidence(body)
    assert ev is not None and ev.beyond_fold
    assert ev.risk_offset_chars > FEED_FOLD_CHARS
    assert ev.quote == "Inwestowanie wiąże się z ryzykiem utraty kapitału."
    assert ev.measured() == {
        "risk_offset_chars": float(ev.risk_offset_chars),
        "fold_chars": float(FEED_FOLD_CHARS),
        "beyond_fold": 1.0,
    }


def test_warning_above_fold():
    ev = feed_fold_evidence("Ryzyko utraty kapitału! Zarabiaj z nami.")
    assert ev is not None and not ev.beyond_fold and ev.risk_offset_chars == 0


def test_bez_ryzyka_is_a_promise_not_a_warning():
    assert feed_fold_evidence("Zarabiaj bez ryzyka, gwarantowany zysk 20%!") is None


def test_no_warning_returns_none():
    assert feed_fold_evidence("Kup kurs tradingu, zyski 18% rocznie.") is None
    assert feed_fold_evidence(None) is None


def test_cfd_retail_loss_disclosure_detected():
    body = "x" * 130 + " 74% rachunków inwestorów detalicznych traci pieniądze."
    ev = feed_fold_evidence(body)
    assert ev is not None and ev.beyond_fold


def test_rhetorical_question_about_risky_assets_is_not_a_warning():
    """Regresja z nagrania (reklama 675484101807418): to pytanie, nie ostrzezenie."""
    body = "W co inwestują nasi Klienci? " * 5 + "Czy inwestują w ryzykowne aktywa, np. kryptowaluty?"
    assert feed_fold_evidence(body) is None


def test_quote_is_not_cut_at_abbreviation():
    body = "x" * 130 + ". Inwestycje, np. w akcje, wiążą się z ryzykiem utraty kapitału. Zapraszamy!"
    ev = feed_fold_evidence(body)
    assert ev is not None
    assert ev.quote == "Inwestycje, np. w akcje, wiążą się z ryzykiem utraty kapitału."


def test_english_and_cfd_style_warnings():
    assert feed_fold_evidence("Capital at risk. Trade now.") is not None
    assert feed_fold_evidence("Trading CFDs involves high risk of losing money.") is not None

"""Testy zbioru zlotego fixtures/gold/labels.json (prawdziwy korpus 8 reklam).

Pilnuja ksztaltu danych, nie wartosci score'ow (te zaleza od modelu).
"""

from __future__ import annotations

import json

import pytest

from tools import evaluate

GOLD = evaluate.DEFAULT_GOLD_PATH


@pytest.fixture(scope="module")
def items() -> list[dict]:
    return json.loads(GOLD.read_text(encoding="utf-8"))["items"]


def test_zbior_zloty_ma_osiem_pozycji(items) -> None:
    assert len(items) == 8
    assert len({i["id"] for i in items}) == 8


def test_kazda_pozycja_ma_komplet_pol(items) -> None:
    for i in items:
        assert isinstance(i["score"], (int, float)) and not isinstance(i["score"], bool)
        assert 0 <= i["score"] <= 100
        assert isinstance(i["coverage"], (int, float)) and 0 <= i["coverage"] <= 1
        assert isinstance(i["is_violation"], bool)
        assert isinstance(i["has_render_probe"], bool)
        assert isinstance(i["failed_rules"], list)
        assert isinstance(i["note"], str) and i["note"].strip()


def test_tylko_jedna_reklama_ma_render_probe(items) -> None:
    """Pozostale 7 zbudowano z node.json.gz bez Playwrighta - ta roznica ma byc w danych."""
    with_probe = [i["id"] for i in items if i["has_render_probe"]]
    assert with_probe == ["912810501476495"]


def test_evaluate_wczytuje_zbior_zloty() -> None:
    gold = evaluate.load_gold(GOLD)
    assert len(gold) == 8
    assert all(g.score is not None for g in gold)

"""Unit tests — the small functions, on inputs you can check by hand. No browser.

- **Cleaning** (Part 1, Step 1): prices, card text, price lines, one card's rows.
  The inputs are copied from the real Lakeshore Lattes cards.
- **Matching** (Part 2): normalizing names, the top suggestions and their scores,
  the confidence bands, and recording the owner's answer. The names are the ones
  the rival menus actually use — including the ones built to fool a matcher.
- **Where our price stands** (Part 3): price_position, on prices you can check by hand.
"""

import pandas as pd
import pytest

from helpers import assert_unmodified, snapshot
from rivals import (
    ABOVE_ALL,
    ABOVE_AVERAGE,
    AT_AVERAGE,
    BELOW_ALL,
    BELOW_AVERAGE,
    NEW_ITEM,
    card_rows,
    clean_card_lines,
    clean_price,
    match_band,
    normalize_name,
    parse_price_line,
    price_position,
    record_decision,
    top_candidates,
)

MATCHA_CARD = ("NEW!\nMatcha Latte\nV\n\nS $5.05 · L $6.25\n\n"
               "Ceremonial-grade matcha whisked with steamed milk.")
AVOCADO_CARD = ("NEW!\nAvocado Toast\nV GF\n\n$8.50\n\n"
                "Smashed avocado, lemon and chili flakes on sourdough.")
SPECIAL_CARD = ("Croissant, Almond\n\nBaked this morning\n\n$3.95\n\n"
                "Twice-baked croissant filled with almond cream.")


# --- Part 1, Step 1: cleaning ------------------------------------------------------


@pytest.mark.parametrize("text, expected", [
    ("$4.75", 4.75),
    (" $8.50 ", 8.50),
    ("$1,029.00", 1029.0),
    ("3.10", 3.10),
])
def test_clean_price(text, expected):
    assert clean_price(text) == expected


def test_clean_card_lines_drops_blanks_badges_and_tags():
    assert clean_card_lines(MATCHA_CARD) == [
        "Matcha Latte",
        "S $5.05 · L $6.25",
        "Ceremonial-grade matcha whisked with steamed milk.",
    ], "drop blank lines, 'NEW!' and dietary tags like 'V'"


def test_clean_card_lines_drops_a_line_of_several_tags():
    assert clean_card_lines(AVOCADO_CARD)[:2] == ["Avocado Toast", "$8.50"], (
        "'V GF' is a line made only of tags — drop it too"
    )


@pytest.mark.parametrize("line, expected", [
    ("S $5.05 · L $6.25", [("S", 5.05), ("L", 6.25)]),
    ("S $2.15 · M $2.60 · L $3.05", [("S", 2.15), ("M", 2.60), ("L", 3.05)]),
    ("$8.50", [("Each", 8.50)]),
])
def test_parse_price_line(line, expected):
    assert parse_price_line(line) == expected


def test_card_rows_one_row_per_size():
    rows = card_rows("Lakeshore Lattes", "Tea & More", MATCHA_CARD)
    assert rows == [
        {"cafe": "Lakeshore Lattes", "category": "Tea & More", "item": "Matcha Latte",
         "size": "S", "price": 5.05},
        {"cafe": "Lakeshore Lattes", "category": "Tea & More", "item": "Matcha Latte",
         "size": "L", "price": 6.25},
    ]


def test_card_rows_food_and_the_price_line():
    assert card_rows("Lakeshore Lattes", "Breakfast", AVOCADO_CARD) == [
        {"cafe": "Lakeshore Lattes", "category": "Breakfast", "item": "Avocado Toast",
         "size": "Each", "price": 8.50},
    ]
    rows = card_rows("Lakeshore Lattes", "Bakery", SPECIAL_CARD)
    assert [(r["item"], r["size"], r["price"]) for r in rows] == [
        ("Croissant, Almond", "Each", 3.95)], "the price line is the first line with a '$' in it"


# --- Part 2: matching ---------------------------------------------------------------------


@pytest.mark.parametrize("name, expected", [
    ("Caffè Americano", "americano"),          # accent + filler word
    ("Cold-Brew Coffee", "cold brew"),          # punctuation + filler
    ("Bagel w/ Cream Cheese", "bagel cream cheese"),
    ("Egg & Cheese Breakfast Sandwich", "egg cheese breakfast sandwich"),
    ("Croissant, Almond", "croissant almond"),
    ("PSL", "psl"),
])
def test_normalize_name(name, expected):
    assert normalize_name(name) == expected


OURS = ["Drip Coffee", "Espresso", "Americano", "Iced Americano", "Latte", "Cappuccino",
        "Mocha Latte", "Pumpkin Spice Latte", "Cold Brew", "Chai Latte", "Hot Chocolate"]


@pytest.mark.parametrize("name, best, score", [
    ("Americano, Iced", "Iced Americano", 100),   # word order ignored
    ("Cappucino", "Cappuccino", 95),              # spelling slip
    ("Café Latte", "Latte", 100),                 # accent + filler
    ("Matcha Latte", "Mocha Latte", 87),          # looks alike, isn't
    ("Mochaccino", "Cappuccino", 70),             # is a mocha, scores as a cappuccino
])
def test_top_candidates_best_match(name, best, score):
    found = top_candidates(name, OURS)
    assert found[0] == (best, score), f"{name!r}: expected ({best!r}, {score}), got {found[0]}"


def test_top_candidates_shape():
    found = top_candidates("Americano, Iced", ["Americano", "Iced Americano", "Latte"])
    assert [name for name, _ in found] == ["Iced Americano", "Americano", "Latte"], "best first"
    assert all(isinstance(score, int) for _, score in found), "scores are whole numbers"
    assert len(top_candidates("Latte", OURS)) == 3, "three suggestions by default"
    assert len(top_candidates("Latte", OURS, limit=5)) == 5
    assert top_candidates("Latte", []) == []


@pytest.mark.parametrize("score, band", [
    (100, "auto"), (90, "auto"), (89, "review"), (70, "review"), (69, "unlikely"), (0, "unlikely"),
])
def test_match_band(score, band):
    assert match_band(score) == band


def test_record_decision_adds_and_replaces():
    decisions = pd.DataFrame([
        {"cafe": "Canal Street Coffee", "item": "PSL", "matched_to": NEW_ITEM},
        {"cafe": "Canal Street Coffee", "item": "Brewed Coffee", "matched_to": "Drip Coffee"},
    ])
    before = snapshot(decisions)
    out = record_decision(decisions, "Canal Street Coffee", "PSL", "Pumpkin Spice Latte")
    assert list(out.columns) == ["cafe", "item", "matched_to"]
    assert out.values.tolist() == [
        ["Canal Street Coffee", "Brewed Coffee", "Drip Coffee"],
        ["Canal Street Coffee", "PSL", "Pumpkin Spice Latte"],
    ], "the new answer replaces the old one for the same item, and goes last"
    assert list(out.index) == [0, 1], "plain index"
    assert_unmodified(decisions, before, "record_decision")


def test_record_decision_first_answer():
    empty = pd.DataFrame(columns=["cafe", "item", "matched_to"])
    out = record_decision(empty, "Lakeshore Lattes", "Matcha Latte", NEW_ITEM)
    assert out.values.tolist() == [["Lakeshore Lattes", "Matcha Latte", NEW_ITEM]]


# --- Part 3: where our price stands ----------------------------------------------------


@pytest.mark.parametrize("ours, low, average, high, expected", [
    (4.00, 4.20, 4.50, 4.80, BELOW_ALL),
    (5.00, 4.20, 4.50, 4.80, ABOVE_ALL),
    (4.30, 4.20, 4.50, 4.80, BELOW_AVERAGE),
    (4.20, 4.20, 4.50, 4.80, BELOW_AVERAGE),     # ties the cheapest rival: not below all
    (4.70, 4.20, 4.50, 4.80, ABOVE_AVERAGE),
    (4.50, 4.20, 4.50, 4.80, AT_AVERAGE),
    (3.75, 3.75, 3.75, 3.75, AT_AVERAGE),         # one rival, same price
    (3.50, 3.75, 3.75, 3.75, BELOW_ALL),          # one rival
])
def test_price_position(ours, low, average, high, expected):
    assert price_position(ours, low, average, high) == expected

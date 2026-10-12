"""
settings.py — where things live, and the few decisions the code shares.  *(Provided.)*

Everything the rest of the package needs to *find* — the rival sites, the data
files, the cache — and the settings that more than one function must agree on:
the matching thresholds and the words that do not help tell two menu items apart.
You do not change this file, but you do need to read it.
"""

import os

# --- Where the rival sites are --------------------------------------------------------
# The three cafés are published at SITE_URL. Open it in Chrome and right-click →
# Inspect to see what your scrapers should select. The tests do not use the internet:
# they serve the copy in site/ from your own machine and point RIVALS_SITE at it.
SITE_URL = os.environ.get("RIVALS_SITE", "https://ist356.github.io/coffee-rivals")

CAFES = {
    # name shown everywhere          folder under SITE_URL
    "Lakeshore Lattes": "lakeshore",
    "Hilltop Grind": "hilltop",
    "Canal Street Coffee": "canal",
}
OUR_CAFE = "Salt City Coffee"
# Canal Street's prices differ by shop; we compare against this one.
CANAL_SHOP = "Westcott"


def cafe_url(cafe: str) -> str:
    """The menu page for one café, e.g. cafe_url("Hilltop Grind") -> ".../hilltop/"."""
    return f"{SITE_URL.rstrip('/')}/{CAFES[cafe]}/"


# --- Files ----------------------------------------------------------------------------
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(REPO_ROOT, "data")
CACHE_DIR = os.path.join(REPO_ROOT, "cache")

OUR_MENU_FILE = os.path.join(DATA_DIR, "salt_city_menu.csv")  # our own menu
CATEGORIES_FILE = os.path.join(DATA_DIR, "categories.csv")  # (cafe, category) -> kind

# The scraper writes here; Part 2 and 3 read it. An environment variable can point
# the pages somewhere else — the tests use that to hand them a known dataset.
MENUS_FILE = os.environ.get("RIVALS_MENUS_FILE", os.path.join(CACHE_DIR, "menus.csv"))
# The owner's matching decisions. The review page adds to it; it is meant to be
# committed, so the decisions survive the next scrape.
DECISIONS_FILE = os.environ.get("RIVALS_DECISIONS_FILE",
                                os.path.join(DATA_DIR, "item_matches.csv"))

# Every café sizes drinks S, M and L; food is "Each".
SIZES = ["S", "M", "L", "Each"]
MENU_COLUMNS = ["cafe", "category", "kind", "item", "size", "price"]
DECISION_COLUMNS = ["cafe", "item", "matched_to"]

# Where our price stands against the rivals' (analysis.price_position). Use these
# names in your code instead of typing the emoji.
BELOW_ALL = "👍👍 Lowest Price"  # lower than every rival
BELOW_AVERAGE = "👍 Lower than average"
AT_AVERAGE = "👉👈 Average"
ABOVE_AVERAGE = "👎 Higher than average"
ABOVE_ALL = "👎👎 Highest Price"  # higher than every rival

# --- Matching -------------------------------------------------------------------------
AUTO_MATCH = 90  # at or above: matched without asking the owner
REVIEW = 70  # at or above (below AUTO_MATCH): the top suggestion is preselected
NEW_ITEM = "(new item)"  # the owner's answer when an item matches nothing on the list

# Words that appear in menu names but say nothing about *which* drink it is.
# "Caffe Latte" and "Latte" are the same thing; so are "Cold-Brew Coffee" and
# "Cold Brew".
FILLER_WORDS = {"caffe", "cafe", "coffee", "hot", "the", "and", "with", "w", "tea"}

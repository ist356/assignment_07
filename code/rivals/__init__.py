"""
rivals — what is everyone else charging?  *(Provided for you.)*

    from rivals import build_dataset, match_items, compare_prices

The package, part by part:

    settings.py   where the sites and files are, matching thresholds   (given)
    cleaning.py   Part 1, Step 1 — scraped text into clean values       (you)
    scrapers.py   Part 1, Step 2 — one scraper per rival café           (you)
    menus.py      Part 1, Step 3 — everything into one dataset          (you)
    matching.py   Part 2 — which of their items are ours?               (you)
    analysis.py   Part 3 — price comparison and gap analysis            (you)
    runner.py     run the scraper from Streamlit                        (given)

Same as Assignments 04–06: every name below must exist in its module, even before
you have written its body, or `import rivals` fails and every test goes red at
once. That is why the stubs keep every function signature.
"""

from .analysis import (
    add_canonical,
    compare_prices,
    gap_analysis,
    price_position,
    price_table,
)
from .cleaning import card_rows, clean_card_lines, clean_price, parse_price_line
from .matching import (
    match_band,
    match_items,
    normalize_name,
    record_decision,
    top_candidates,
)
from .menus import add_kinds, build_dataset, load_our_menu, menus_table
from .runner import run_scraper
from .scrapers import scrape_canal, scrape_hilltop, scrape_lakeshore
from .settings import (
    ABOVE_ALL,
    ABOVE_AVERAGE,
    AT_AVERAGE,
    BELOW_ALL,
    BELOW_AVERAGE,
    CACHE_DIR,
    CAFES,
    DECISIONS_FILE,
    MENUS_FILE,
    NEW_ITEM,
    OUR_CAFE,
    cafe_url,
)

__all__ = [
    "clean_price", "clean_card_lines", "parse_price_line", "card_rows",
    "scrape_lakeshore", "scrape_hilltop", "scrape_canal",
    "load_our_menu", "menus_table", "add_kinds", "build_dataset",
    "normalize_name", "top_candidates", "match_band", "match_items", "record_decision",
    "add_canonical", "price_table", "price_position", "compare_prices", "gap_analysis",
    "run_scraper",
    "CACHE_DIR", "CAFES", "OUR_CAFE", "NEW_ITEM", "MENUS_FILE", "DECISIONS_FILE",
    "cafe_url",
    "BELOW_ALL", "BELOW_AVERAGE", "AT_AVERAGE", "ABOVE_AVERAGE", "ABOVE_ALL",
]

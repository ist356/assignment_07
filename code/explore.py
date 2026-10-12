"""
explore.py — run everything one step at a time and look at what comes back. (Provided.)

Tests do not stop at breakpoints; this script does. Set a breakpoint on any line
below (or inside one of your functions) and run it with
Run and Debug -> "Python Debugger: Current File".

The browser is invisible (headless — the dev container has no screen), so each
scraper step also saves a screenshot of the page it ended on in cache/. Open it in
VS Code to see what your scraper saw. A step you have not written yet returns None;
the script says so and stops.
"""

import os

import pandas as pd
from playwright.sync_api import sync_playwright

from rivals import (
    CACHE_DIR,
    add_canonical,
    build_dataset,
    compare_prices,
    gap_analysis,
    match_items,
    price_table,
    scrape_canal,
    scrape_hilltop,
    scrape_lakeshore,
)
from rivals.settings import DECISION_COLUMNS, DECISIONS_FILE

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 12)


def show(label: str, result) -> None:
    """Print one step's result, or stop with a hint if the step is not written yet."""
    print(f"\n=== {label}")
    if result is None:
        print("    returned None — this function is still a stub. Write it, run again.")
        raise SystemExit(0)
    if isinstance(result, pd.DataFrame):
        print(f"    {result.shape[0]} rows x {result.shape[1]} columns")
        print(result.head(12))
    else:
        print(f"    {len(result)} rows; the first three:")
        for row in result[:3]:
            print("   ", row)


os.makedirs(CACHE_DIR, exist_ok=True)
rows = []
with sync_playwright() as playwright:
    # Containers (Codespaces, the grader) have very little shared memory;
    # without this flag Chromium can crash as soon as it opens a page.
    browser = playwright.chromium.launch(headless=True,
                                       args=["--disable-dev-shm-usage"])
    page = browser.new_page()
    for name, scraper in [("lakeshore", scrape_lakeshore), ("hilltop", scrape_hilltop),
                          ("canal", scrape_canal)]:
        result = scraper(page)
        page.screenshot(path=os.path.join(CACHE_DIR, f"{name}.png"), full_page=True)
        show(f"Part 1: scrape_{name}  (screenshot: cache/{name}.png)", result)
        rows.extend(result)
    browser.close()

menus = build_dataset(rows)
show("Part 1: build_dataset", menus)

if os.path.exists(DECISIONS_FILE):
    decisions = pd.read_csv(DECISIONS_FILE)
else:
    decisions = pd.DataFrame(columns=DECISION_COLUMNS)
matches = match_items(menus, decisions)
show("Part 2: match_items", matches)
if matches is not None:
    print("\n   ", matches["status"].value_counts().to_dict())

canonical = add_canonical(menus, matches)
show("Part 3: add_canonical", canonical)
show("Part 3: compare_prices", compare_prices(price_table(canonical)))
show("Part 3: gap_analysis", gap_analysis(canonical))

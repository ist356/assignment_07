"""
scrape_menus.py — scrape the rivals and save one dataset.  *(Provided.)*

Run it from the repository root, naming the cafés to scrape (none means all three):

    python code/scrape_menus.py
    python code/scrape_menus.py "Hilltop Grind" "Canal Street Coffee"

It opens a browser you can't see (headless), runs a scraper per café, builds the
dataset (our menu plus theirs) and writes it to cache/menus.csv. The Scrape page
runs this program for you (runner.py); running it yourself in a terminal shows
every message it prints.

It is the glue for Part 1, and it only works once the functions it calls do:
your three scrapers (scrapers.py) and build_dataset (menus.py). Read it to see how
they fit together:

    cafes <- the names given on the command line (sys.argv[1:]), or every name in
             CAFES when none were given
    with sync_playwright() as playwright:
        launch Chromium headless, open a page
        for each café: print its name, call its scraper (SCRAPERS[cafe](page)),
                       print how many rows came back, add them to one list
        close the browser
    build_dataset(the rows), make sure cache/ exists, write it to MENUS_FILE
    (index=False), and print where it went and how many rows it has
"""

import os
import sys

from playwright.sync_api import sync_playwright

from rivals import (
    CAFES,
    MENUS_FILE,
    build_dataset,
    scrape_canal,
    scrape_hilltop,
    scrape_lakeshore,
)

SCRAPERS = {
    "Lakeshore Lattes": scrape_lakeshore,
    "Hilltop Grind": scrape_hilltop,
    "Canal Street Coffee": scrape_canal,
}


def main(cafes: list[str]) -> None:
    """Scrape `cafes` and write the dataset (ours plus theirs) to MENUS_FILE."""
    rows = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        for cafe in cafes:
            print(f"Scraping {cafe}...", flush=True)
            cafe_rows = SCRAPERS[cafe](page)
            print(f"  {len(cafe_rows)} rows", flush=True)
            rows.extend(cafe_rows)
        browser.close()

    dataset = build_dataset(rows)
    os.makedirs(os.path.dirname(MENUS_FILE), exist_ok=True)
    dataset.to_csv(MENUS_FILE, index=False)
    print(f"Wrote {len(dataset)} rows to {MENUS_FILE}", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:] or list(CAFES))

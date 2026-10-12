"""Pipeline & app tests — the scrapers, the dataset, matching, the analysis, the pages.

- **The scrapers** run a real (invisible) Chromium against the three cafés — not the
  published site, but the copy in site/, served from your own machine for the
  length of the test run. No internet needed, and the menus never change under you.
- **The dataset, matching and analysis** run on tests/fixtures/menus.csv — what a
  correct scrape produces — so a Part 2 or Part 3 test passes when *that* part is
  right, even if your scrapers aren't finished. The owner's decisions for Part 3 are
  tests/fixtures/item_matches.csv: every review question answered correctly.
- **The pages** are driven with Streamlit's AppTest, pointed at those same files
  (and a temporary decisions file, so your own data/item_matches.csv is never
  touched). The Scrape page test swaps the scraper for a stand-in.
"""

import functools
import os
import shutil
import subprocess
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import pandas as pd
import pytest
from playwright.sync_api import sync_playwright

import rivals
from helpers import (
    assert_unmodified,
    fixture,
    load_app,
    metrics,
    no_exception,
    page_text,
    repo_path,
    snapshot,
    widget,
)
from rivals import (
    NEW_ITEM,
    add_canonical,
    add_kinds,
    build_dataset,
    compare_prices,
    gap_analysis,
    match_items,
    menus_table,
    price_table,
    scrape_canal,
    scrape_hilltop,
    scrape_lakeshore,
)

SCRAPE_PAGE = "code/pages/1_Scrape.py"
REVIEW_PAGE = "code/pages/2_Review_Matches.py"
ANALYSIS_PAGE = "code/pages/3_Analysis.py"
ROW_KEYS = ["cafe", "category", "item", "size", "price"]


def expected_rows(cafe: str) -> list[list]:
    """What a correct scrape of one café returns, from the recorded dataset."""
    menus = fixture("menus.csv")
    return menus[menus["cafe"] == cafe][ROW_KEYS].values.tolist()


def scraped(rows: list[dict]) -> list[list]:
    return [[row[key] for key in ROW_KEYS] for row in rows]


def no_decisions() -> pd.DataFrame:
    return pd.DataFrame(columns=["cafe", "item", "matched_to"])


# --- A local copy of the three cafés, and a browser ----------------------------------------


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@pytest.fixture(scope="session")
def site_url():
    """Serve site/ on a free local port for the whole test run."""
    handler = functools.partial(QuietHandler, directory=repo_path("site"))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as playwright:
        chromium = playwright.chromium.launch(headless=True)
        yield chromium
        chromium.close()


@pytest.fixture
def page(browser, site_url, monkeypatch):
    """A fresh browser tab, with settings.SITE_URL pointed at the local copy."""
    monkeypatch.setattr(rivals.settings, "SITE_URL", site_url)
    tab = browser.new_page()
    tab.set_default_timeout(15_000)
    yield tab
    tab.close()


# --- Part 1: the scrapers -------------------------------------------------------------------


def test_scrape_lakeshore(page):
    rows = scrape_lakeshore(page)
    assert scraped(rows) == expected_rows("Lakeshore Lattes"), (
        "every card in every section, one row per size, in page order"
    )


def test_scrape_hilltop(page):
    rows = scrape_hilltop(page)
    assert scraped(rows) == expected_rows("Hilltop Grind"), (
        "every table melted to one row per size, in page order"
    )


def test_scrape_canal(page):
    rows = scrape_canal(page)
    assert scraped(rows) == expected_rows("Canal Street Coffee"), (
        "every item (keep clicking Show more), one row per size from its item page"
    )


def test_scrape_canal_other_shop(page):
    downtown = scrape_canal(page, shop="Downtown")
    westcott = expected_rows("Canal Street Coffee")
    assert [row["item"] for row in downtown] == [row[2] for row in westcott]
    assert [round(row["price"] - base[4], 2) for row, base in zip(downtown, westcott)] == \
        [0.30] * len(westcott), "choose the shop you are given — Downtown is $0.30 more"


def test_scrape_menus_script(site_url, tmp_path):
    out = tmp_path / "menus.csv"
    env = dict(os.environ, RIVALS_SITE=site_url, RIVALS_MENUS_FILE=str(out))
    result = subprocess.run([sys.executable, repo_path("code", "scrape_menus.py"),
                             "Lakeshore Lattes", "Hilltop Grind"],
                            capture_output=True, text=True, env=env, timeout=240)
    assert result.returncode == 0, f"scrape_menus.py failed:\n{result.stderr[-1500:]}"
    assert out.exists(), "write the dataset to MENUS_FILE"
    written = pd.read_csv(out)
    want = fixture("menus.csv")
    want = want[want["cafe"].isin(["Salt City Coffee", "Lakeshore Lattes", "Hilltop Grind"])]
    assert written.values.tolist() == want.values.tolist(), (
        "only the cafés named on the command line, plus our own menu, via build_dataset"
    )


# --- Part 1: one dataset --------------------------------------------------------------------


def test_menus_table():
    rows = [{"cafe": "X", "category": "C", "item": "Latte", "size": "M", "price": 4.0,
             "description": "Espresso and milk."}]
    out = menus_table(rows)
    assert list(out.columns) == ROW_KEYS, "exactly the five columns, extra keys left out"
    assert out.values.tolist() == [["X", "C", "Latte", "M", 4.0]]
    assert list(menus_table([]).columns) == ROW_KEYS, "an empty list still has the columns"


def test_add_kinds():
    menus = pd.DataFrame({"cafe": ["Hilltop Grind", "Hilltop Grind", "Canal Street Coffee"],
                          "category": ["Pastries", "Not Coffee", "Food"],
                          "item": ["Scone", "Chai", "Toast"]})
    menus.loc[3] = ["Canal Street Coffee", "Merch", "Mug"]
    before = snapshot(menus)
    out = add_kinds(menus, pd.read_csv(repo_path("data", "categories.csv")))
    assert out["kind"].tolist()[:3] == ["food", "drink", "food"]
    assert pd.isna(out["kind"].iloc[3]), "a category not in categories.csv gets a missing kind"
    assert out["item"].tolist() == menus["item"].tolist(), "every row kept, in order"
    assert_unmodified(menus, before, "add_kinds")


def test_build_dataset():
    recorded = fixture("menus.csv")
    rivals_only = recorded[recorded["cafe"] != "Salt City Coffee"]
    rows = rivals_only[ROW_KEYS].to_dict("records")
    out = build_dataset(rows)
    assert list(out.columns) == ["cafe", "category", "kind", "item", "size", "price"]
    assert out.values.tolist() == recorded.values.tolist(), (
        "our menu first, then the rivals' rows, with kind looked up"
    )
    assert list(out.index) == list(range(len(out))), "plain index"


# --- Part 2: matching -----------------------------------------------------------------------


def by_item(matches: pd.DataFrame) -> dict:
    return {(row["cafe"], row["item"]): row for row in matches.to_dict("records")}


def test_match_items_shape():
    menus = fixture("menus.csv")
    before = snapshot(menus)
    out = match_items(menus, no_decisions())
    assert list(out.columns) == ["cafe", "item", "kind", "status", "matched_to", "score", "suggestions"]
    assert len(out) == 46, "one row per distinct rival (cafe, item) — 46 of them"
    assert out["cafe"].unique().tolist() == ["Lakeshore Lattes", "Hilltop Grind", "Canal Street Coffee"]
    assert_unmodified(menus, before, "match_items")


def test_match_items_without_decisions():
    out = by_item(match_items(fixture("menus.csv"), no_decisions()))
    cappucino = out[("Hilltop Grind", "Cappucino")]
    assert (cappucino["status"], cappucino["matched_to"], cappucino["score"]) == ("auto", "Cappuccino", 95)
    assert out[("Lakeshore Lattes", "Cold-Brew Coffee")]["matched_to"] == "Cold Brew"
    matcha = out[("Lakeshore Lattes", "Matcha Latte")]
    assert matcha["status"] == "unreviewed" and pd.isna(matcha["matched_to"]), (
        "87 is below AUTO_MATCH: the owner decides — it is not a mocha latte"
    )
    assert matcha["suggestions"][0] == ("Mocha Latte", 87)
    assert out[("Canal Street Coffee", "PSL")]["status"] == "unreviewed"
    statuses = pd.Series([row["status"] for row in out.values()]).value_counts().to_dict()
    assert statuses == {"auto": 28, "unreviewed": 18}, statuses


def test_match_items_suggestions_are_same_kind():
    out = by_item(match_items(fixture("menus.csv"), no_decisions()))
    muffin = out[("Lakeshore Lattes", "Blueberry Muffin")]
    assert muffin["suggestions"][0] == ("Blueberry Scone", 71)
    names = [name for name, _ in muffin["suggestions"]]
    assert "Blueberry Scone" in names and not {"Latte", "Cold Brew"} & set(names), (
        "only compare food with food and drinks with drinks"
    )


def test_match_items_with_the_owners_decisions():
    out = by_item(match_items(fixture("menus.csv"), fixture("item_matches.csv")))
    assert all(row["status"] != "unreviewed" for row in out.values()), "every item decided"
    assert out[("Canal Street Coffee", "PSL")]["matched_to"] == "Pumpkin Spice Latte"
    assert (out[("Lakeshore Lattes", "Matcha Latte")]["status"],
            out[("Lakeshore Lattes", "Matcha Latte")]["matched_to"]) == ("owner", "Matcha Latte"), (
        "NEW_ITEM means the item keeps its own name"
    )
    canal_matcha = out[("Canal Street Coffee", "Matcha Latte")]
    assert (canal_matcha["status"], canal_matcha["matched_to"]) == ("auto", "Matcha Latte"), (
        "once Lakeshore's Matcha Latte is on the list, Canal's matches it automatically"
    )
    toast = {out[(cafe, "Avocado Toast")]["matched_to"]
             for cafe in ["Lakeshore Lattes", "Hilltop Grind", "Canal Street Coffee"]}
    assert toast == {"Avocado Toast"}
    statuses = pd.Series([row["status"] for row in out.values()]).value_counts().to_dict()
    assert statuses == {"auto": 34, "owner": 12}, statuses


def test_match_items_owner_wins_over_auto():
    decisions = pd.DataFrame([{"cafe": "Hilltop Grind", "item": "Cappucino", "matched_to": NEW_ITEM}])
    row = by_item(match_items(fixture("menus.csv"), decisions))[("Hilltop Grind", "Cappucino")]
    assert (row["status"], row["matched_to"]) == ("owner", "Cappucino"), (
        "a saved decision wins even when the score would have matched automatically"
    )


# --- Part 3: analysis -----------------------------------------------------------------------


def decided_menus() -> pd.DataFrame:
    menus = fixture("menus.csv")
    return add_canonical(menus, match_items(menus, fixture("item_matches.csv")))


def test_add_canonical():
    menus = fixture("menus.csv")
    matches = match_items(menus, no_decisions())
    before = snapshot(menus)
    out = add_canonical(menus, matches)
    assert list(out.columns) == list(menus.columns) + ["canonical"]
    assert len(out) == len(menus), "every row kept"
    ours = out[out["cafe"] == "Salt City Coffee"]
    assert (ours["canonical"] == ours["item"]).all(), "our items keep their own names"
    hilltop = out[(out["cafe"] == "Hilltop Grind") & (out["item"] == "Cappucino")]
    assert set(hilltop["canonical"]) == {"Cappuccino"}
    psl = out[(out["cafe"] == "Canal Street Coffee") & (out["item"] == "PSL")]
    assert psl["canonical"].isna().all(), "unreviewed items have no canonical name yet"
    assert_unmodified(menus, before, "add_canonical")


def test_compare_prices():
    out = compare_prices(price_table(decided_menus()))
    assert list(out.columns) == ["canonical", "size", "our_price", "Canal Street Coffee",
                                 "Hilltop Grind", "Lakeshore Lattes", "rival_avg", "our_position"]
    assert len(out) == 36, "every (item, size) that we and at least one rival both sell"
    assert out[["canonical", "size"]].values.tolist()[:4] == [
        ["Almond Croissant", "Each"], ["Americano", "S"], ["Americano", "M"], ["Americano", "L"]], (
        "price_table's order: by item, sizes S, M, L"
    )
    latte = out[(out["canonical"] == "Latte") & (out["size"] == "M")].iloc[0]
    assert latte[["our_price", "Canal Street Coffee", "Hilltop Grind", "rival_avg", "our_position"]].tolist() == [
        4.45, 4.75, 4.60, 4.68, rivals.BELOW_ALL], "the average of the rivals that sell it, rounded"
    assert pd.isna(latte["Lakeshore Lattes"]), "Lakeshore sells no M"
    positions = out.set_index(["canonical", "size"])["our_position"]
    assert positions[("Almond Croissant", "Each")] == rivals.ABOVE_ALL
    assert positions[("Americano", "M")] == rivals.BELOW_AVERAGE
    assert positions[("Breakfast Sandwich", "Each")] == rivals.ABOVE_AVERAGE
    assert positions[("Iced Americano", "M")] == rivals.AT_AVERAGE, "one rival, same price"
    assert positions.value_counts().to_dict() == {
        rivals.BELOW_AVERAGE: 15, rivals.BELOW_ALL: 10, rivals.ABOVE_ALL: 7,
        rivals.ABOVE_AVERAGE: 3, rivals.AT_AVERAGE: 1}
    assert list(out.index) == list(range(len(out))), "plain index"


def test_gap_analysis():
    out = gap_analysis(decided_menus())
    assert list(out.columns) == ["canonical", "kind", "where", "rivals", "sold_by"]
    only_them = out[out["where"] == "only them"]
    assert only_them[["canonical", "rivals"]].values.tolist()[:2] == [["Avocado Toast", 3],
                                                                    ["Bagel w/ Cream Cheese", 2]], (
        "only them first, the most-sold first"
    )
    assert len(only_them) == 8
    assert sorted(out[out["where"] == "only us"]["canonical"]) == [
        "Cinnamon Roll", "Oat Milk Cortado", "Salt City Sea Salt Latte"]
    assert (out["where"] == "both").sum() == 14
    assert out["where"].tolist()[:8] == ["only them"] * 8 and out["where"].iloc[-1] == "both"
    toast = out[out["canonical"] == "Avocado Toast"].iloc[0]
    assert toast["sold_by"] == "Canal Street Coffee, Hilltop Grind, Lakeshore Lattes"


# --- The pages ------------------------------------------------------------------------------


@pytest.fixture
def app_files(tmp_path, monkeypatch):
    """Point the pages at the recorded dataset and a scratch copy of the decisions."""
    decisions = tmp_path / "item_matches.csv"
    monkeypatch.setattr(rivals, "MENUS_FILE", repo_path("tests", "fixtures", "menus.csv"))
    monkeypatch.setattr(rivals, "DECISIONS_FILE", str(decisions))
    return decisions


def test_scrape_page_shows_the_dataset(app_files):
    app = load_app(SCRAPE_PAGE)
    no_exception(app, SCRAPE_PAGE)
    assert "Salt City: Scrape the Rivals" in page_text(app)
    assert metrics(app) == {"Cafés": "3", "Items": "46", "Rows": "101"}, metrics(app)
    assert len(app.dataframe) >= 1, "show the dataset with st.dataframe"
    assert widget(app.multiselect, "cafes", "multiselect").value == list(rivals.CAFES)


def test_scrape_page_runs_the_scraper(app_files, monkeypatch):
    calls = []

    def fake_run_scraper(cafes):
        calls.append(list(cafes))
        return subprocess.CompletedProcess(["x"], 0, stdout="Scraping...\nWrote 77 rows to menus.csv\n",
                                           stderr="")

    monkeypatch.setattr(rivals, "run_scraper", fake_run_scraper)
    app = load_app(SCRAPE_PAGE)
    widget(app.multiselect, "cafes", "multiselect").set_value(["Hilltop Grind"])
    widget(app.button, "scrape", "button").click()
    app.run()
    no_exception(app, SCRAPE_PAGE)
    assert calls == [["Hilltop Grind"]], "clicking Scrape runs run_scraper(the chosen cafés) once"
    assert any("Wrote 77 rows" in str(s.value) for s in app.success), (
        "show the scraper's last line of output with st.success"
    )


def test_scrape_page_before_any_scrape(app_files, monkeypatch, tmp_path):
    monkeypatch.setattr(rivals, "MENUS_FILE", str(tmp_path / "missing.csv"))
    app = load_app(SCRAPE_PAGE)
    no_exception(app, SCRAPE_PAGE)
    assert app.info, "no dataset yet: say so with st.info"
    assert not app.dataframe


def test_review_page_first_question(app_files):
    app = load_app(REVIEW_PAGE)
    no_exception(app, REVIEW_PAGE)
    assert metrics(app) == {"Matched automatically": "28", "Decided by you": "0",
                            "Waiting for review": "18"}, metrics(app)
    assert "Lakeshore Lattes: Matcha Latte" in page_text(app), "the first unreviewed item"
    choice = widget(app.selectbox, "choice", "selectbox")
    assert choice.value == "Mocha Latte", (
        "a score of REVIEW or more preselects the top suggestion (here, a wrong one)"
    )
    assert "87" in choice.options[0] and NEW_ITEM in choice.options, (
        "the suggestions show their scores; NEW_ITEM is always a choice"
    )


def test_review_page_save(app_files):
    app = load_app(REVIEW_PAGE)
    widget(app.selectbox, "choice", "selectbox").set_value(NEW_ITEM)
    widget(app.button, "save", "button").click()
    app.run()
    no_exception(app, REVIEW_PAGE)
    saved = pd.read_csv(app_files)
    assert saved.values.tolist() == [["Lakeshore Lattes", "Matcha Latte", NEW_ITEM]], (
        "Save writes the answer to DECISIONS_FILE with record_decision"
    )
    assert "Lakeshore Lattes: London Fog" in page_text(app), "then the next item"
    assert widget(app.selectbox, "choice", "selectbox").value == NEW_ITEM, (
        "a score below REVIEW preselects NEW_ITEM"
    )
    assert metrics(app)["Decided by you"] == "1"


def test_review_page_skip(app_files):
    app = load_app(REVIEW_PAGE)
    widget(app.button, "skip", "button").click()
    app.run()
    no_exception(app, REVIEW_PAGE)
    assert "Lakeshore Lattes: London Fog" in page_text(app), "Skip moves to the next item"
    assert not app_files.exists() or pd.read_csv(app_files).empty, "and saves nothing"


def test_review_page_all_done(app_files):
    shutil.copy(repo_path("tests", "fixtures", "item_matches.csv"), app_files)
    app = load_app(REVIEW_PAGE)
    no_exception(app, REVIEW_PAGE)
    assert metrics(app)["Waiting for review"] == "0"
    assert app.success, "nothing left to review: say so with st.success"


def test_analysis_page(app_files):
    shutil.copy(repo_path("tests", "fixtures", "item_matches.csv"), app_files)
    app = load_app(ANALYSIS_PAGE)
    no_exception(app, ANALYSIS_PAGE)
    assert "Salt City: Prices and Gaps" in page_text(app)
    assert metrics(app) == {"Priced below the market": "25", "Priced above the market": "10"}
    assert [tab.label for tab in app.tabs] == ["Prices", "Gaps"]
    assert not app.warning, "everything is reviewed: no warning"
    prices = [df.value for df in app.dataframe if "our_position" in df.value.columns]
    assert prices and len(prices[0]) == 36, "with no products picked, show every item and size"
    gaps = [df.value for df in app.dataframe if "where" in df.value.columns]
    assert any((g["where"] == "only them").all() and len(g) == 8 for g in gaps), "the 'only them' table"


def test_analysis_page_product_filter(app_files):
    shutil.copy(repo_path("tests", "fixtures", "item_matches.csv"), app_files)
    app = load_app(ANALYSIS_PAGE)
    products = widget(app.multiselect, "products", "multiselect")
    assert "Latte" in products.options and products.value == [], "nothing picked to start"
    products.set_value(["Latte", "Espresso"])
    app.run()
    no_exception(app, ANALYSIS_PAGE)
    shown = [df.value for df in app.dataframe if "our_position" in df.value.columns][0]
    assert sorted(set(shown["canonical"])) == ["Espresso", "Latte"] and len(shown) == 6, (
        "only the picked products, every size"
    )


def test_analysis_page_warns_about_unreviewed(app_files):
    app = load_app(ANALYSIS_PAGE)
    no_exception(app, ANALYSIS_PAGE)
    assert any("18" in str(w.value) for w in app.warning), (
        "say how many items still need review, with st.warning"
    )

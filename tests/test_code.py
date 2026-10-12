"""Code structure tests — read the source and check how it is built.

The other tests check what your functions *return*. These check *how*: that each
scraper uses the technique its site calls for, that the matcher scores with
rapidfuzz and keeps the owner's decisions, that the analysis uses pandas'
merge and group-by instead of loops, and that the two pages you write assemble
the package instead of redoing it.

Everything here reads the **parsed** source (`ast`), so a technique mentioned in
a comment does not count. When a test fails, the message names the file and the
thing it was looking for.
"""

import ast

from helpers import repo_path

CLEANING = "code/rivals/cleaning.py"
SCRAPERS = "code/rivals/scrapers.py"
MENUS = "code/rivals/menus.py"
MATCHING = "code/rivals/matching.py"
ANALYSIS = "code/rivals/analysis.py"
SCRAPE_PAGE = "code/pages/1_Scrape.py"
ANALYSIS_PAGE = "code/pages/3_Analysis.py"
PAGES = (SCRAPE_PAGE, ANALYSIS_PAGE)  # the Review page is provided


def source(script: str) -> str:
    with open(repo_path(script), encoding="utf-8") as fh:
        return fh.read()


def parse(script: str) -> ast.Module:
    return ast.parse(source(script), filename=script)


def calls(tree: ast.AST) -> list:
    return [node for node in ast.walk(tree) if isinstance(node, ast.Call)]


def call_name(node: ast.Call) -> str:
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    if isinstance(node.func, ast.Name):
        return node.func.id
    return ""


def called_names(tree: ast.AST) -> set:
    return {call_name(node) for node in calls(tree)}


def calls_named(tree: ast.AST, name: str) -> list:
    return [node for node in calls(tree) if call_name(node) == name]


def keyword_names(node: ast.Call) -> set:
    return {keyword.arg for keyword in node.keywords}


def function(tree: ast.Module, name: str) -> ast.FunctionDef:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"function {name}() not found")


def imported_modules(tree: ast.Module) -> set:
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module.split(".")[0])
    return modules


def strings(tree: ast.AST) -> list:
    return [node.value for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)]


def names_used(tree: ast.AST) -> set:
    return {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}


# --- Part 1 ---------------------------------------------------------------------------------


def test_cleaning_is_plain_python():
    """No browser, no pandas: the cleaning functions work on strings."""
    tree = parse(CLEANING)
    assert not imported_modules(tree) & {"playwright", "pandas", "requests"}, (
        f"{CLEANING}: cleaning works on strings — it should not import playwright, pandas or requests"
    )
    assert "findall" in called_names(function(tree, "parse_price_line")), (
        f"{CLEANING}: parse_price_line should find every price with re.findall(...)"
    )
    assert {"clean_card_lines", "parse_price_line"} <= called_names(function(tree, "card_rows")), (
        f"{CLEANING}: card_rows should call clean_card_lines() and parse_price_line()"
    )


def test_each_scraper_uses_its_technique():
    """Selectors and the ~ sibling; read_html + melt; select, click, wait and crawl."""
    tree = parse(SCRAPERS)
    lakeshore = function(tree, "scrape_lakeshore")
    assert "query_selector_all" in called_names(lakeshore), (
        f"{SCRAPERS}: scrape_lakeshore should find the headings and cards with query_selector_all"
    )
    assert any(text.strip().startswith("~") for text in strings(lakeshore)), (
        f"{SCRAPERS}: scrape_lakeshore should reach each grid with a '~ ...' sibling selector"
    )
    assert {"inner_text", "card_rows"} <= called_names(lakeshore), (
        f"{SCRAPERS}: scrape_lakeshore should hand each card's inner_text() to card_rows()"
    )
    hilltop = called_names(function(tree, "scrape_hilltop"))
    assert {"read_html", "melt"} <= hilltop, (
        f"{SCRAPERS}: scrape_hilltop should read the tables with pd.read_html and reshape with .melt"
    )
    canal = called_names(function(tree, "scrape_canal"))
    for step in ("select_option", "click", "get_attribute"):
        assert step in canal, f"{SCRAPERS}: scrape_canal should call {step}()"
    assert canal & {"wait_for_selector", "wait_for_function", "wait_for"}, (
        f"{SCRAPERS}: scrape_canal should wait for the page's JavaScript (wait_for_selector / wait_for_function)"
    )
    assert canal & {"goto"} and "urljoin" in canal, (
        f"{SCRAPERS}: scrape_canal should visit each item page: page.goto(urljoin(base, href))"
    )


def test_dataset_steps_use_pandas():
    tree = parse(MENUS)
    assert "merge" in called_names(function(tree, "add_kinds")), f"{MENUS}: add_kinds should merge"
    built = called_names(function(tree, "build_dataset"))
    for step in ("concat", "load_our_menu", "menus_table", "add_kinds"):
        assert step in built, f"{MENUS}: build_dataset should call {step}()"


# --- Part 2 ---------------------------------------------------------------------------------


def test_matching_uses_rapidfuzz():
    tree = parse(MATCHING)
    assert "rapidfuzz" in imported_modules(tree), f"{MATCHING} should import rapidfuzz"
    top = function(tree, "top_candidates")
    assert "extract" in called_names(top), f"{MATCHING}: top_candidates should use process.extract(...)"
    assert "token_sort_ratio" in {node.attr for node in ast.walk(top) if isinstance(node, ast.Attribute)}, (
        f"{MATCHING}: top_candidates should score with fuzz.token_sort_ratio"
    )
    assert "normalize_name" in called_names(top), f"{MATCHING}: compare normalized names"
    matcher = called_names(function(tree, "match_items"))
    assert "top_candidates" in matcher, f"{MATCHING}: match_items should call top_candidates()"
    assert "concat" in called_names(function(tree, "record_decision")), (
        f"{MATCHING}: record_decision should pd.concat the kept rows and the new answer"
    )


# --- Part 3 ---------------------------------------------------------------------------------


def test_analysis_uses_pandas():
    tree = parse(ANALYSIS)
    gaps = function(tree, "gap_analysis")
    merges = calls_named(gaps, "merge")
    assert any("indicator" in keyword_names(node) for node in merges), (
        f"{ANALYSIS}: gap_analysis should merge with indicator=True"
    )
    assert "groupby" in called_names(gaps), f"{ANALYSIS}: gap_analysis should count rivals with a groupby"
    compare = called_names(function(tree, "compare_prices"))
    assert {"min", "mean", "max", "price_position"} <= compare, (
        f"{ANALYSIS}: compare_prices should use .min / .mean / .max across the rival columns "
        "and price_position() for each row"
    )
    for name in ("compare_prices", "gap_analysis", "add_canonical"):
        loops = [n for n in ast.walk(function(tree, name)) if isinstance(n, (ast.For, ast.While))]
        assert not loops, f"{ANALYSIS}: {name} should use pandas, not a for/while loop"


# --- The pages ------------------------------------------------------------------------------


def test_pages_assemble_the_package():
    expected = {
        SCRAPE_PAGE: ({"run_scraper", "multiselect", "button", "dataframe", "download_button", "metric"}),
        ANALYSIS_PAGE: ({"match_items", "add_canonical", "compare_prices", "gap_analysis", "tabs",
                         "multiselect", "isin", "metric", "dataframe"}),
    }
    for page, needed in expected.items():
        tree = parse(page)
        called = called_names(tree)
        assert "rivals" in imported_modules(tree), f"{page} should import from the rivals package"
        missing = needed - called
        assert not missing, f"{page} should call {sorted(missing)}"
        assert not called & {"scrape_lakeshore", "scrape_hilltop", "scrape_canal", "sync_playwright",
                             "groupby", "pivot_table", "extract"}, (
            f"{page}: the page assembles — scraping, matching and grouping belong in the package"
        )
        assert "print" not in called and "input" not in called, f"{page}: use widgets, not the console"

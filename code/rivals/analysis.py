"""
analysis.py — Part 3: where are we high or low, and what are we missing?

Two questions the owner asked, answered from the dataset (Part 1) once every rival
item has a name on our list (Part 2):

1. **Prices.** For everything we and at least one rival both sell, in the same
   size: our price next to each rival's, their average, and where we stand —
   below all of them (the best place to be), below or above their average, or
   above all of them.
2. **Gaps.** What we sell that nobody else does (a reason to come to us), and what
   the rivals sell that we don't — ranked by how many of them sell it, because
   something all three offer is a stronger hint than something one does.

The docstrings say what each function returns; tests/test_pipeline.py says how it
is checked.
"""

import pandas as pd

from .settings import (
    ABOVE_ALL,
    ABOVE_AVERAGE,
    AT_AVERAGE,
    BELOW_ALL,
    BELOW_AVERAGE,
    OUR_CAFE,
    SIZES,
)


def add_canonical(menus: pd.DataFrame, matches: pd.DataFrame) -> pd.DataFrame:
    """`menus` plus a `canonical` column: the one name every café's item goes by.

    Our rows: their own `item`. Rival rows: the `matched_to` from `matches` for
    that (`cafe`, `item`) — missing for items the owner has not reviewed yet.
    Every row of `menus` is kept, in order; `menus` itself is not changed.
    """
    # TODO: your code here
    pass


def price_table(menus: pd.DataFrame) -> pd.DataFrame:
    """Price per (canonical item, size) per café.  *(Provided.)*

    Rows are (`canonical`, `size`), sizes in menu order (S, M, L, Each); columns
    are the cafés; values are prices. Rows with no canonical name (not reviewed
    yet) are left out.
    """
    known = menus.dropna(subset=["canonical"])
    table = known.pivot_table(index=["canonical", "size"], columns="cafe",
                              values="price", aggfunc="first")
    order = {size: rank for rank, size in enumerate(SIZES)}
    return table.sort_index(key=lambda level: level.map(order) if level.name == "size"
                            else level)


def price_position(ours: float, low: float, average: float, high: float) -> str:
    """Where our price stands against the rivals' prices for the same item and size.

    `low`, `average` and `high` are the rivals' lowest, average and highest price.
    Returns one of the five labels in settings — the names, not the text:

        ours below `low`                 -> BELOW_ALL       "👍👍 Lowest Price"
        ours above `high`                -> ABOVE_ALL       "👎👎 Highest Price"
        otherwise, ours below `average`  -> BELOW_AVERAGE   "👍 Lower than average"
        otherwise, ours above `average`  -> ABOVE_AVERAGE   "👎 Higher than average"
        otherwise (ours equals average)  -> AT_AVERAGE      "👉👈 Average"

    Check them in that order: with one rival, low, average and high are the same.
    """
    # TODO: your code here
    pass


def compare_prices(prices: pd.DataFrame) -> pd.DataFrame:
    """Our price next to every rival's, for every item and size we both sell.

    `prices` is price_table's result. Returns one row per (canonical, size) where
    we have a price *and* at least one rival does, in price_table's order, with
    columns:

        canonical  size  our_price  <one column per rival>  rival_avg  our_position

    - `our_price`: the settings.OUR_CAFE column, renamed.
    - the rival columns: every other column of `prices`, in the same order
      (missing where that rival doesn't sell it).
    - `rival_avg`: the average of the rivals' prices, ignoring missing ones,
      rounded to 2 places.
    - `our_position`: price_position(our_price, the rivals' lowest, rival_avg, the
      rivals' highest) for that row.

    Plain index.
    """
    # TODO: your code here
    pass


def gap_analysis(menus: pd.DataFrame) -> pd.DataFrame:
    """Which items only we sell, which only rivals sell, and which we both do.

    `menus` must have a `canonical` column (add_canonical). Rival rows with no
    canonical name (unreviewed) are left out. Returns one row per (canonical, kind):

        canonical  kind  where  rivals  sold_by

    - `where`: "only us", "only them" or "both" — an outer merge of our items with
      the rivals' items with `indicator=True`, its `_merge` column relabelled.
    - `rivals`: how many different rivals sell it (0 for "only us").
    - `sold_by`: those rivals' names, sorted, joined with ", " ("" for "only us").

    Sorted by `where` ("only them" first, then "only us", then "both"), then
    `rivals` (most first), then `canonical`; plain index.
    """
    # TODO: your code here
    pass

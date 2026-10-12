"""
2_Review_Matches.py — Part 2: the owner decides what the matcher can't.  *(Provided.)*

match_items() matches what it is sure of and leaves the rest "unreviewed". This
page shows those one at a time: the rival's item, its best suggestions with their
scores, and the choice to call it a new item. Save writes the answer to
data/item_matches.csv, so it is never asked again — not even after next month's
scrape. Skip moves on without answering (st.session_state remembers what was
skipped while the page is open).

You don't write this page — it runs on the functions you write in matching.py
(match_items, match_band, record_decision). When those are right, the page works,
and pytest tests/test_pipeline.py -k review_page passes. Read it: it is a good
example of st.session_state and of a page that only *assembles* the package.
"""

import os

import pandas as pd
import streamlit as st

from rivals import (
    DECISIONS_FILE,
    MENUS_FILE,
    NEW_ITEM,
    OUR_CAFE,
    match_band,
    match_items,
    record_decision,
)
from rivals.settings import DECISION_COLUMNS

st.title("Salt City: Review Matches")

if not os.path.exists(MENUS_FILE):
    st.info("No menus yet — scrape them on the Scrape page first.")
    st.stop()

menus = pd.read_csv(MENUS_FILE)
if os.path.exists(DECISIONS_FILE):
    decisions = pd.read_csv(DECISIONS_FILE)
else:
    decisions = pd.DataFrame(columns=DECISION_COLUMNS)
matches = match_items(menus, decisions)

if "skipped" not in st.session_state:
    st.session_state["skipped"] = []

m1, m2, m3 = st.columns(3)
m1.metric("Matched automatically", int((matches["status"] == "auto").sum()))
m2.metric("Decided by you", int((matches["status"] == "owner").sum()))
m3.metric("Waiting for review", int((matches["status"] == "unreviewed").sum()))

waiting = matches[matches["status"] == "unreviewed"]
skipped = st.session_state["skipped"]
pairs = zip(waiting["cafe"], waiting["item"])
to_review = waiting[[pair not in skipped for pair in pairs]]

if waiting.empty:
    st.success("Every rival item is matched. On to the Analysis page.")
elif to_review.empty:
    st.info(f"You skipped all {len(waiting)} remaining items.")
    if st.button("Start over with the skipped items", key="unskip"):
        st.session_state["skipped"] = []
        st.rerun()
else:
    item = to_review.iloc[0]
    st.subheader(f"{item['cafe']}: {item['item']}")
    st.caption(f"Item 1 of {len(to_review)} waiting · {item['kind']}")
    rows = menus[(menus["cafe"] == item["cafe"]) & (menus["item"] == item["item"])]
    st.write(" · ".join(f"{size} ${price:.2f}" for size, price in
                        zip(rows["size"], rows["price"])))

    # Choices: the suggestions (best first), "new item", then every other name of
    # the same kind already on the list.
    suggested = [name for name, _score in item["suggestions"]]
    labels = {name: f"{name} ({score})" for name, score in item["suggestions"]}
    ours = menus[(menus["cafe"] == OUR_CAFE) & (menus["kind"] == item["kind"])]
    on_list = set(ours["item"])
    on_list |= set(matches[(matches["kind"] == item["kind"])]["matched_to"].dropna())
    others = sorted(on_list - set(suggested))
    options = suggested + [NEW_ITEM] + others
    preselect = 0 if match_band(item["score"]) == "review" else len(suggested)

    choice = st.selectbox("Which of our items is it?", options, index=preselect,
                          format_func=lambda name: labels.get(name, name), key="choice")
    save, skip = st.columns(2)
    if save.button("Save", key="save"):
        decisions = record_decision(decisions, item["cafe"], item["item"], choice)
        decisions.to_csv(DECISIONS_FILE, index=False)
        del st.session_state["choice"]  # the next item starts from its own preselection
        st.rerun()
    if skip.button("Skip", key="skip"):
        st.session_state["skipped"].append((item["cafe"], item["item"]))
        del st.session_state["choice"]
        st.rerun()

st.subheader("Every rival item")
st.dataframe(matches[["cafe", "item", "status", "matched_to", "score"]],
             hide_index=True)

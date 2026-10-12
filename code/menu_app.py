"""
menu_app.py — the front door of the app.  *(Provided.)*

Run it:  Run and Debug -> "Streamlit Run: Current File"  (with this file open)
    or:  streamlit run code/menu_app.py

Streamlit turns every file in code/pages/ into a page in the sidebar, in file-name
order. You write those three pages:

    pages/1_Scrape.py           Part 1 — scrape the rivals into one dataset
    pages/2_Review_Matches.py   Part 2 — the owner decides what the matcher can't
    pages/3_Analysis.py         Part 3 — prices and gaps
"""

import os

import pandas as pd
import streamlit as st

from rivals import CAFES, DECISIONS_FILE, MENUS_FILE, cafe_url

st.title("Salt City: What Is Everyone Else Charging?")
st.markdown(
    "Three cafés nearby sell what we sell, and none of them offers a download. "
    "This app scrapes their menus, matches their items to ours, and shows where "
    "our prices sit and what we don't sell yet. Work through the pages in the "
    "sidebar in order."
)

st.subheader("The rivals")
for cafe in CAFES:
    st.markdown(f"- [{cafe}]({cafe_url(cafe)})")

st.subheader("Where things stand")
col1, col2 = st.columns(2)
if os.path.exists(MENUS_FILE):
    menus = pd.read_csv(MENUS_FILE)
    col1.metric("Menu rows scraped", len(menus))
else:
    col1.metric("Menu rows scraped", 0)
if os.path.exists(DECISIONS_FILE):
    col2.metric("Owner decisions saved", len(pd.read_csv(DECISIONS_FILE)))
else:
    col2.metric("Owner decisions saved", 0)

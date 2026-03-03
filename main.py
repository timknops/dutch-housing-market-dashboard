import streamlit as st

from pages.market_overview import render as market_overview

st.set_page_config(page_title="Dutch Housing Market", layout="wide")
st.title("Dutch Housing Market Dashboard")

tab1, tab2, tab3 = st.tabs(
    ["Market Overview", "Regional Analysis", "Affordability"]
)

with tab1:
    market_overview()

with tab2:
    st.info("Regional Analysis — coming soon.")

with tab3:
    st.info("Affordability — coming soon.")

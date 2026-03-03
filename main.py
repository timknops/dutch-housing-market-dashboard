import streamlit as st

from data.fetch_cbs import fetch_quarterly_prices

st.set_page_config(page_title="Dutch Housing Market", layout="wide")
st.title("Dutch Housing Market Dashboard")

prices = fetch_quarterly_prices()

national = prices[prices["region"] == "Nederland"].sort_values("date")

st.subheader("National average purchase price (quarterly)")
st.line_chart(national, x="date", y="avg_price")

st.subheader("Raw data preview")
st.dataframe(prices.head(50))

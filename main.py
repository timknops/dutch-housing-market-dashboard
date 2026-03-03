import streamlit as st

from data.fetch_cbs import fetch_quarterly_prices
from data.fetch_ecb import fetch_mortgage_rates

st.set_page_config(page_title="Dutch Housing Market", layout="wide")
st.title("Dutch Housing Market Dashboard")

prices = fetch_quarterly_prices()
rates = fetch_mortgage_rates()

national = prices[prices["region"] == "Nederland"].sort_values("date")
aggregate_rate = rates[rates["fixation"] == "AM"].sort_values("date")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Average purchase price (quarterly)")
    st.caption(
        "Source: CBS: average sale price of existing owner-occupied homes."
    )
    st.line_chart(
        national.rename(columns={"avg_price": "avg price (€)"}),
        x="date",
        y="avg price (€)",
    )

with col2:
    st.subheader("Mortgage interest rate (monthly)")
    st.caption(
        "Source: ECB: average rate on new mortgage loans in the Netherlands."
    )
    st.line_chart(
        aggregate_rate.rename(columns={"rate": "rate (%)"}),
        x="date",
        y="rate (%)",
    )

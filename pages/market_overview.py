import pandas as pd
import streamlit as st

from data.fetch_cbs import fetch_quarterly_prices
from data.fetch_ecb import fetch_mortgage_rates


def show_caption():
    st.header("Market Overview")
    st.caption(
        "Most home buyers finance their purchase"
        " with a mortgage, so the **monthly cost**"
        " depends on both the house price and the"
        " interest rate. When rates drop, buyers"
        " can afford to bid more, pushing prices"
        " up. When rates rise, the same budget"
        " buys less house, cooling prices."
    )


def show_kpis(national, aggregate_rate):
    latest = national.iloc[-1]
    prev_year = national[national["year"] == latest["year"] - 1].iloc[-1]
    price_yoy = (latest["avg_price"] - prev_year["avg_price"]) / prev_year[
        "avg_price"
    ]

    latest_rate = aggregate_rate.iloc[-1]["rate"]
    rate_1y_ago = aggregate_rate[
        aggregate_rate["date"] <= latest["date"] - pd.DateOffset(years=1)
    ].iloc[-1]["rate"]
    rate_change = latest_rate - rate_1y_ago

    latest_sales = national.iloc[-1]["n_sales"]
    prev_year_sales = prev_year["n_sales"]
    sales_yoy = (
        (latest_sales - prev_year_sales) / prev_year_sales
        if prev_year_sales
        else 0
    )

    k1, k2, k3, k4 = st.columns(4)
    k1.metric(
        "Avg purchase price",
        f"€{latest['avg_price']:,.0f}",
        f"{price_yoy:+.1%} YoY",
    )
    k2.metric(
        "Mortgage rate", f"{latest_rate:.2f}%", f"{rate_change:+.2f}pp YoY"
    )
    k3.metric("Houses sold", f"{latest_sales:,.0f}", f"{sales_yoy:+.1%} YoY")
    k4.metric("Period", f"{latest['period']}")
    st.divider()


def show_national_trends(national, aggregate_rate):
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Average purchase price")
        st.caption(
            "Source: CBS, owner-occupied homes, quarterly."
        )
        st.line_chart(
            national.rename(
                columns={"avg_price": "avg price (€)"}
            ),
            x="date",
            y="avg price (€)",
        )

    with col2:
        st.subheader("Mortgage interest rate")
        st.caption(
            "Source: ECB, new mortgage loans, monthly."
        )
        st.line_chart(
            aggregate_rate.rename(
                columns={"rate": "rate (%)"}
            ),
            x="date",
            y="rate (%)",
        )

    st.divider()


def show_province_price_over_time(prices):
    st.subheader("Average price by province over time")

    provinces = prices[prices["region"].str.endswith("(PV)")].copy()
    provinces["province"] = provinces["region"].str.replace(
        r"\s*\(PV\)", "", regex=True
    )

    all_provinces = sorted(provinces["province"].unique())
    selected = st.multiselect(
        "Select provinces to compare",
        all_provinces,
        default=["Noord-Holland", "Zuid-Holland", "Groningen", "Limburg"],
    )

    if selected:
        filtered = provinces[provinces["province"].isin(selected)]
        pivot = filtered.pivot_table(
            index="date", columns="province", values="avg_price"
        )
        st.line_chart(pivot)
    else:
        st.warning("Select at least one province.")


def render():
    show_caption()

    prices = fetch_quarterly_prices()
    rates = fetch_mortgage_rates()

    national = prices[prices["region"] == "Nederland"].sort_values("date")
    aggregate_rate = rates[rates["fixation"] == "AM"].sort_values("date")

    show_kpis(national, aggregate_rate)
    show_national_trends(national, aggregate_rate)
    show_province_price_over_time(prices)

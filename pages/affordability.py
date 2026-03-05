import streamlit as st
import pandas as pd
import plotly.express as px

from data.fetch_cbs import fetch_municipal_prices, fetch_demographics

st.header("Housing Affordability & Demographics")
st.caption(
    "This page explores how housing affordability relates to income, "
    "housing supply and demographic characteristics across municipalities."
)

# ========================
# Load & merge data
# ========================

df_prices = fetch_municipal_prices()
df_demo = fetch_demographics()

# Use the most recent year available in both datasets
latest_price_year = df_prices["year"].max()
latest_demo_year = df_demo["year"].max()

df_prices = df_prices[df_prices["year"] == latest_price_year]
df_demo = df_demo[df_demo["year"] == latest_demo_year]

df = pd.merge(df_prices, df_demo, on="region", how="inner")
df = df.dropna(subset=["avg_price", "income", "houses", "households"])

# Derived metrics using REAL income data
df["price_income_ratio"] = df["avg_price"] / df["income"]
df["housing_pressure"] = df["households"] / df["houses"]

# ========================
# KPI metrics
# ========================

col1, col2, col3 = st.columns(3)

col1.metric("Average House Price", f"€{df['avg_price'].mean():,.0f}")
col2.metric("Price / Income Ratio", f"{df['price_income_ratio'].mean():.2f}")
col3.metric("Housing Pressure", f"{df['housing_pressure'].mean():.2f}")

st.divider()

# ========================
# Income vs house price
# ========================

st.subheader("Income vs Housing Prices")

fig = px.scatter(
    df,
    x="income",
    y="avg_price",
    hover_name="region",
    trendline="ols",
    title="Income vs Average House Price by Municipality",
    labels={"income": "Avg Disposable Income (€)", "avg_price": "Avg House Price (€)"},
)
st.plotly_chart(fig, use_container_width=True)

# ========================
# Housing supply analysis
# ========================

st.subheader("Housing Supply vs Households")

fig2 = px.scatter(
    df,
    x="houses",
    y="households",
    hover_name="region",
    trendline="ols",
    title="Housing Supply vs Households by Municipality",
    labels={"houses": "Total Dwellings", "households": "Private Households"},
)
st.plotly_chart(fig2, use_container_width=True)

# ========================
# Affordability distribution
# ========================

st.subheader("Price to Income Ratio Distribution")

fig3 = px.histogram(
    df,
    x="price_income_ratio",
    nbins=30,
    title="Distribution of Price to Income Ratios",
    labels={"price_income_ratio": "Price / Income Ratio"},
)
st.plotly_chart(fig3, use_container_width=True)

# ========================
# Affordability table
# ========================

st.subheader("Municipal Affordability Ranking")

table = df.sort_values("price_income_ratio", ascending=False)

st.dataframe(
    table[["region", "avg_price", "income", "price_income_ratio", "housing_pressure"]]
    .reset_index(drop=True)
    .head(25),
    use_container_width=True,
)
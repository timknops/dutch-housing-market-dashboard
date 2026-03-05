import streamlit as st
import pandas as pd
import plotly.express as px

from data.fetch_cbs import fetch_municipal_prices

st.header("Regional Housing Analysis")
st.caption(
    "This section explores differences in housing prices across Dutch municipalities."
)

# ========================
# Load data
# ========================

df = fetch_municipal_prices()
df = df.dropna(subset=["avg_price", "region", "year"])

latest_year = df["year"].max()
df = df[df["year"] == latest_year]

df = df[~df["region"].str.endswith("(PV)")]
df = df[df["region"] != "Nederland"]

national_avg = df["avg_price"].mean()

# ========================
# Top expensive municipalities
# ========================

st.subheader(f"Most Expensive Municipalities ({latest_year})")

top = df.sort_values("avg_price", ascending=False).head(15)

fig = px.bar(
    top.sort_values("avg_price"),
    x="avg_price",
    y="region",
    orientation="h",
    title=f"Top 15 Most Expensive Municipalities ({latest_year})",
    labels={"avg_price": "Avg Price (€)", "region": ""},
)
fig.update_layout(yaxis_tickfont_size=11)
st.plotly_chart(fig, use_container_width=True)

# ========================
# Cheapest municipalities
# ========================

st.subheader(f"Most Affordable Municipalities ({latest_year})")

cheap = df.sort_values("avg_price").head(15)

fig2 = px.bar(
    cheap.sort_values("avg_price", ascending=False),
    x="avg_price",
    y="region",
    orientation="h",
    title=f"15 Most Affordable Municipalities ({latest_year})",
    labels={"avg_price": "Avg Price (€)", "region": ""},
)
fig2.update_layout(yaxis_tickfont_size=11)
st.plotly_chart(fig2, use_container_width=True)

# ========================
# Distribution of prices
# ========================

st.subheader("Distribution of Housing Prices")
st.caption(
    "Each bar shows how many municipalities fall in that price range. "
    "The red dashed line is the average across all municipalities. "
    "Use the dropdown below to see exactly which municipalities are in each bar."
)

fig3 = px.histogram(
    df,
    x="avg_price",
    nbins=40,
    title=f"Distribution of Average House Prices ({latest_year})",
    labels={"avg_price": "Avg Price (€)"},
)
fig3.add_vline(
    x=national_avg,
    line_dash="dash",
    line_color="#FF4B4B",
    annotation_text=f"Average: €{national_avg:,.0f}",
    annotation_position="top right",
    annotation_font_color="#FF4B4B",
)
st.plotly_chart(fig3, use_container_width=True)

# Dropdown to look up municipalities per price range
st.markdown("**Which municipalities are in a price range?**")

bin_size = 50_000
price_min = int(df["avg_price"].min() // bin_size * bin_size)
price_max = int(df["avg_price"].max() // bin_size * bin_size) + bin_size
bins = list(range(price_min, price_max + bin_size, bin_size))
bin_labels = [f"€{b:,.0f} – €{b + bin_size:,.0f}" for b in bins[:-1]]

selected_bin = st.selectbox("Select a price range", bin_labels)
selected_idx = bin_labels.index(selected_bin)
bin_low = bins[selected_idx]
bin_high = bins[selected_idx + 1]

munis_in_bin = (
    df[(df["avg_price"] >= bin_low) & (df["avg_price"] < bin_high)][["region", "avg_price"]]
    .sort_values("avg_price", ascending=False)
    .reset_index(drop=True)
)

if munis_in_bin.empty:
    st.info("No municipalities in this price range.")
else:
    st.write(f"**{len(munis_in_bin)} municipalities** in this range:")
    st.dataframe(munis_in_bin, use_container_width=True)

st.divider()

# ========================
# Price over time for selected municipalities
# ========================

st.subheader("Price Over Time by Municipality")

df_all = fetch_municipal_prices()
df_all = df_all.dropna(subset=["avg_price", "region", "year"])
df_all = df_all[~df_all["region"].str.endswith("(PV)")]
df_all = df_all[df_all["region"] != "Nederland"]

all_regions = sorted(df_all["region"].unique())
selected = st.multiselect(
    "Select municipalities to compare",
    all_regions,
    default=all_regions[:4] if len(all_regions) >= 4 else all_regions,
)

if selected:
    filtered = df_all[df_all["region"].isin(selected)]
    fig4 = px.line(
        filtered,
        x="year",
        y="avg_price",
        color="region",
        title="Average House Price Over Time",
        labels={"avg_price": "Avg Price (€)", "year": "Year", "region": "Municipality"},
    )
    st.plotly_chart(fig4, use_container_width=True)
else:
    st.warning("Select at least one municipality.")

st.divider()

# ========================
# Data table
# ========================

st.subheader(f"All Municipal Data ({latest_year})")

st.dataframe(
    df[["region", "avg_price"]]
    .sort_values("avg_price", ascending=False)
    .reset_index(drop=True),
    use_container_width=True,
)
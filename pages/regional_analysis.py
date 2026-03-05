import streamlit as st
import pandas as pd
import plotly.express as px
import altair as alt
import unicodedata
from typing import cast

from data.fetch_cbs import fetch_municipal_prices
from data.province_municipality_map import PROVINCE_MUNICIPALITIES


# ========================
# Helpers (from main branch)
# ========================


def _normalize_name(value: str) -> str:
    value = value.strip().lower()
    value = (
        value.replace("\u2019", "'").replace("\u2018", "'").replace("`", "'")
    )
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    return " ".join(value.split())


def _resolve_hardcoded_municipalities(
    province: str,
    available_municipalities: list[str],
) -> list[str]:
    wanted = PROVINCE_MUNICIPALITIES.get(province, [])
    normalized_lookup: dict[str, list[str]] = {}
    for municipality in available_municipalities:
        key = _normalize_name(municipality)
        normalized_lookup.setdefault(key, []).append(municipality)
    resolved: list[str] = []
    seen: set[str] = set()
    for municipality in wanted:
        for match in normalized_lookup.get(_normalize_name(municipality), []):
            if match not in seen:
                resolved.append(match)
                seen.add(match)
    return sorted(resolved)


# ========================
# Load data
# ========================

st.header("Regional Housing Analysis")
st.caption(
    "This section explores differences in housing prices across Dutch municipalities."
)

df_all = fetch_municipal_prices()
df_all = df_all.dropna(subset=["avg_price", "region", "year"])
df_all = df_all[
    ~df_all["region"].str.contains(r"\((?:PV|LD)\)$", regex=True, na=False)
]
df_all = df_all[df_all["region"] != "The Netherlands"]

latest_year = int(df_all["year"].max())
df = df_all[df_all["year"] == latest_year].copy()

national_avg = df["avg_price"].mean()

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
    df[(df["avg_price"] >= bin_low) & (df["avg_price"] < bin_high)][
        ["region", "avg_price"]
    ]
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

st.divider()

# ========================
# Province drill-down (from main branch)
# ========================

st.subheader("Municipality / Province Drill-down")

recent_start = latest_year - 9
recent = df_all[df_all["year"].between(recent_start, latest_year)]
municipalities_with_recent = recent.groupby("region")["avg_price"].apply(
    lambda s: s.notna().any()
)
valid_municipalities = set(
    municipalities_with_recent[municipalities_with_recent].index.tolist()
)

available_municipalities = sorted(
    m
    for m in df["region"].dropna().unique().tolist()
    if m in valid_municipalities
)

all_provinces = sorted(list(PROVINCE_MUNICIPALITIES.keys()))
default_province = "Noord-Holland"
default_index = (
    all_provinces.index(default_province)
    if default_province in all_provinces
    else 0
)

selected_province = st.selectbox(
    "Select province", all_provinces, index=default_index
)

hardcoded_municipalities = [
    m
    for m in _resolve_hardcoded_municipalities(
        selected_province, available_municipalities
    )
    if m in valid_municipalities
]
municipality_options = (
    hardcoded_municipalities
    if hardcoded_municipalities
    else available_municipalities
)

selected_municipalities = st.multiselect(
    "Select municipalities to compare",
    municipality_options,
    default=municipality_options,
    key=f"municipality_select_{selected_province}",
)

if selected_municipalities:
    selection = df_all[df_all["region"].isin(selected_municipalities)].copy()
    trend = cast(
        pd.DataFrame,
        selection.groupby(["year", "region"], as_index=False)[
            "avg_price"
        ].mean(),
    )

    st.subheader("Municipality Price Trends")
    chart = (
        alt.Chart(trend)
        .mark_line()
        .encode(
            x=alt.X("year:Q", axis=alt.Axis(format="d", title="Year")),
            y=alt.Y("avg_price:Q", title="Average Purchase Price (€)"),
            color=alt.Color(
                "region:N",
                title="Municipality",
                legend=alt.Legend(orient="right", direction="vertical"),
            ),
            tooltip=[
                "region:N",
                alt.Tooltip("year:Q", format=".0f"),
                "avg_price:Q",
            ],
        )
        .properties(height=420)
        .interactive()
    )
    st.altair_chart(chart, use_container_width=True)
else:
    st.warning("Select at least one municipality to show the chart.")

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

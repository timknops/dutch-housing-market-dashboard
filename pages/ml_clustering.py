import plotly.express as px
import streamlit as st

from data.fetch_cbs import (
    fetch_energy_consumption,
    fetch_municipal_prices,
)
from data.fetch_ecb import fetch_mortgage_rates
from ml.clustering import (
    CLUSTER_FEATURES,
    SEGMENT_DESCRIPTIONS,
    compute_municipality_features,
    run_clustering,
)

st.header("Housing Market Segments")
st.caption(
    "Every dot below is a Dutch municipality, profiled using "
    "three datasets: **CBS house prices**, **ECB mortgage "
    "rates**, and **CBS energy consumption**. We use machine "
    "learning (k-means) to group them into distinct types of "
    "housing markets."
)

# ------------------------------------------------------------------
# Data & clustering (cached)
# ------------------------------------------------------------------


@st.cache_data(show_spinner="Computing municipality features…")
def _get_features():
    return compute_municipality_features(
        fetch_municipal_prices(),
        fetch_mortgage_rates(),
        fetch_energy_consumption(),
    )


@st.cache_data(show_spinner="Running clustering…")
def _cluster(n_clusters: int):
    return run_clustering(_get_features(), n_clusters=n_clusters)


# ------------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------------

NICE = {
    "latest_price": "Price",
    "cagr": "Growth (all time)",
    "recent_growth": "Growth (last 5 yr)",
    "volatility": "Stability",
    "rate_sensitivity": "Rate sensitivity",
    "avg_gas": "Gas use",
    "avg_elec": "Electricity use",
}

n_clusters = st.sidebar.slider(
    "Number of groups", 2, 8, 4
)
x_axis = st.sidebar.selectbox(
    "X axis", CLUSTER_FEATURES,
    index=CLUSTER_FEATURES.index("latest_price"),
    format_func=lambda c: NICE[c],
)
y_axis = st.sidebar.selectbox(
    "Y axis", CLUSTER_FEATURES,
    index=CLUSTER_FEATURES.index("recent_growth"),
    format_func=lambda c: NICE[c],
)

result = _cluster(n_clusters)
features = result.features.copy()
features["cluster"] = result.labels
features["segment"] = (
    features["cluster"].map(result.segment_map)
)
features = features.reset_index()

# ------------------------------------------------------------------
# Elbow chart (collapsed)
# ------------------------------------------------------------------

with st.expander("Why this number of groups?", expanded=False):
    st.caption(
        "Lower = municipalities fit their group better. "
        "The 'elbow' is where adding more groups stops "
        "helping much."
    )
    elbow_fig = px.line(
        x=list(range(2, 9)),
        y=result.inertias,
        markers=True,
        labels={
            "x": "Number of groups",
            "y": "Spread within groups",
        },
    )
    elbow_fig.add_vline(
        x=n_clusters, line_dash="dash",
        annotation_text=f"Current: {n_clusters}",
    )
    elbow_fig.update_layout(
        margin=dict(t=20, b=40), height=300,
    )
    st.plotly_chart(elbow_fig, use_container_width=True)

# ------------------------------------------------------------------
# Main scatter
# ------------------------------------------------------------------

st.subheader("All municipalities at a glance")

fig = px.scatter(
    features,
    x=x_axis, y=y_axis,
    color="segment",
    hover_name="region",
    hover_data={
        "latest_price": ":€,.0f",
        "recent_growth": ":.1%",
        "avg_gas": ":,.0f",
        "segment": True,
    },
    labels=NICE,
    height=500,
)
fig.update_traces(marker=dict(size=8, opacity=0.75))
fig.update_layout(
    legend=dict(
        orientation="h", yanchor="bottom", y=1.02,
        title_text="",
    ),
    margin=dict(t=30, b=40),
)
for ax, col, setter in [
    ("x", x_axis, fig.update_layout),
    ("y", y_axis, fig.update_layout),
]:
    if col in ("cagr", "recent_growth"):
        setter(**{f"{ax}axis_tickformat": ".0%"})
    elif col == "latest_price":
        setter(**{
            f"{ax}axis_tickprefix": "€",
            f"{ax}axis_tickformat": ",",
        })
    elif col == "avg_gas":
        setter(**{f"{ax}axis_ticksuffix": " m³"})
    elif col == "avg_elec":
        setter(**{f"{ax}axis_ticksuffix": " kWh"})

st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------------
# Group overview (descriptions + bar chart in one section)
# ------------------------------------------------------------------

st.subheader("The groups")

active_segments = [
    name for name in SEGMENT_DESCRIPTIONS
    if name in features["segment"].values
]
cols = st.columns(len(active_segments))
for col, name in zip(cols, active_segments):
    n = int((features["segment"] == name).sum())
    with col:
        st.markdown(f"**{name}**")
        st.caption(f"{n} municipalities — {SEGMENT_DESCRIPTIONS[name]}")

compare_metric = st.selectbox(
    "Compare groups by",
    CLUSTER_FEATURES,
    index=0,
    format_func=lambda c: NICE[c],
)

seg_avg = (
    features.groupby("segment")[compare_metric]
    .mean()
    .sort_values(ascending=False)
    .reset_index()
)

bar_fig = px.bar(
    seg_avg, x="segment", y=compare_metric,
    color="segment", labels=NICE, text_auto=True,
)
bar_fig.update_layout(
    showlegend=False, xaxis_title="",
    margin=dict(t=20, b=40),
)
if compare_metric in ("cagr", "recent_growth"):
    bar_fig.update_layout(yaxis_tickformat=".1%")
    bar_fig.update_traces(texttemplate="%{y:.1%}")
elif compare_metric == "latest_price":
    bar_fig.update_layout(
        yaxis_tickprefix="€", yaxis_tickformat=","
    )
    bar_fig.update_traces(texttemplate="€%{y:,.0f}")
elif compare_metric in ("avg_gas", "avg_elec"):
    bar_fig.update_traces(texttemplate="%{y:,.0f}")
else:
    bar_fig.update_traces(texttemplate="%{y:.3f}")

st.plotly_chart(bar_fig, use_container_width=True)

# ------------------------------------------------------------------
# Municipality lookup
# ------------------------------------------------------------------

st.subheader("Find your municipality")

selected = st.selectbox(
    "Search",
    sorted(features["region"].unique()),
    index=None,
    placeholder="Type a municipality name…",
)

if selected:
    row = features[features["region"] == selected].iloc[0]
    segment = row["segment"]

    st.info(
        f"**{segment}** — "
        f"{SEGMENT_DESCRIPTIONS.get(segment, '')}"
    )

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Price", f"€{row['latest_price']:,.0f}")
    k2.metric(
        "Growth (5 yr)", f"{row['recent_growth']:.1%}/yr"
    )
    rs = row["rate_sensitivity"]
    rs_label = (
        "Strong" if rs < -0.4
        else "Moderate" if rs < -0.15
        else "Weak"
    )
    k3.metric("Rate sensitivity", rs_label)
    k4.metric("Gas use", f"{row['avg_gas']:,.0f} m³/yr")

    seg_peers = features[
        features["segment"] == row["segment"]
    ]
    n_peers = len(seg_peers)

    st.caption(
        f"Compared to the **{n_peers - 1}** other "
        f"municipalities in this group:"
    )

    KEY_FEATURES = [
        "latest_price", "recent_growth",
        "avg_gas", "rate_sensitivity",
    ]

    for feat in KEY_FEATURES:
        vals = seg_peers[feat]
        rank = int((vals < row[feat]).sum()) + 1
        pct = rank / n_peers

        if feat == "avg_gas":
            word = (
                "low" if pct <= 0.33
                else "average" if pct <= 0.66
                else "high"
            )
        elif feat == "rate_sensitivity":
            word = (
                "less sensitive"
                if pct <= 0.33
                else "average"
                if pct <= 0.66
                else "more sensitive"
            )
        else:
            word = (
                "low" if pct <= 0.33
                else "average" if pct <= 0.66
                else "high"
            )

        st.progress(
            min(pct, 1.0),
            text=f"**{NICE[feat]}** — {word} for this group",
        )

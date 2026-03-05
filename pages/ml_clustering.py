import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from data.fetch_cbs import (
    fetch_energy_consumption,
    fetch_municipal_prices,
)
from ml.clustering import (
    CLUSTER_FEATURES,
    SEGMENT_DESCRIPTIONS,
    compute_municipality_features,
    run_clustering,
)

st.header("Housing Market Segments")
st.caption(
    "Every dot below is a Dutch municipality, profiled using "
    "three datasets: **CBS house prices** and **CBS energy consumption**. "
    "We use machine learning (k-means) to group them into distinct types of "
    "housing markets."
)

# ------------------------------------------------------------------
# Data & clustering (cached)
# ------------------------------------------------------------------


@st.cache_data(show_spinner=False)
def _cached_prices():
    return fetch_municipal_prices()


@st.cache_data(show_spinner=False)
def _cached_energy():
    return fetch_energy_consumption()


@st.cache_data(show_spinner=False)
def _get_features():
    return compute_municipality_features(
        _cached_prices(),
        _cached_energy(),
    )


@st.cache_data(show_spinner=False)
def _cluster(n_clusters: int):
    return run_clustering(_get_features(), n_clusters=n_clusters)


# ------------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------------

_BASE_COLORS = {
    "Expensive, Growing Fast": "#E15759",
    "Expensive, Slow Growth": "#4E79A7",
    "Affordable, Growing Fast": "#F28E2B",
    "Affordable, Slow Growth": "#76B7B2",
}
_OVERFLOW_PALETTE = [
    "#59A14F",
    "#B07AA1",
    "#FF9DA7",
    "#9C755F",
    "#EDC948",
    "#BAB0AC",
]


def _build_color_map(segment_names: list[str]) -> dict[str, str]:
    color_map: dict[str, str] = {}
    used: set[str] = set()
    overflow = iter(_OVERFLOW_PALETTE)
    for name in segment_names:
        if name in _BASE_COLORS:
            color = _BASE_COLORS[name]
        else:
            color = next((c for c in overflow if c not in used), "#AAAAAA")
        color_map[name] = color
        used.add(color)
    return color_map


def _segment_description(name: str) -> str:
    if name in SEGMENT_DESCRIPTIONS:
        return SEGMENT_DESCRIPTIONS[name]
    base = name.replace(" II", "").replace(" III", "")
    return SEGMENT_DESCRIPTIONS.get(
        base, "A market subgroup with similar characteristics."
    )


DISPLAY_NAMES = {
    "latest_price": "Price",
    "recent_growth": "Growth (last 5 yr)",
    "avg_gas": "Gas use",
    "avg_elec": "Electricity use",
}

n_clusters = st.sidebar.slider("Number of groups", 2, 8, 4)
x_axis = st.sidebar.selectbox(
    "X axis",
    CLUSTER_FEATURES,
    index=CLUSTER_FEATURES.index("latest_price"),
    format_func=lambda c: DISPLAY_NAMES[c],
)
y_axis = st.sidebar.selectbox(
    "Y axis",
    CLUSTER_FEATURES,
    index=CLUSTER_FEATURES.index("recent_growth"),
    format_func=lambda c: DISPLAY_NAMES[c],
)

_status_box = st.empty()
with _status_box.status("Preparing data…", expanded=True) as _status:
    st.write("Fetching CBS house prices…")
    _cached_prices()
    st.write("Fetching CBS energy consumption…")
    _cached_energy()
    st.write("Computing municipality features…")
    _get_features()
    st.write(f"Running k-means clustering (k={n_clusters})…")
    result = _cluster(n_clusters)
    _status.update(label="Ready", state="complete", expanded=False)
_status_box.empty()

features = result.features.copy()
features["cluster"] = result.labels
features["segment"] = features["cluster"].map(result.segment_map)
features = features.reset_index()

SEGMENT_COLORS = _build_color_map(list(result.segment_map.values()))

# ------------------------------------------------------------------
# Elbow chart (collapsed)
# ------------------------------------------------------------------

with st.expander("Why this number of groups?", expanded=False):
    st.caption(
        "**Inertia** (left axis): lower means municipalities fit "
        "their group better. **Silhouette** (right axis): higher "
        "means groups are better separated. Look for the inertia "
        "elbow and the silhouette peak."
    )
    ks = list(range(2, 9))
    elbow_fig = make_subplots(specs=[[{"secondary_y": True}]])
    elbow_fig.add_trace(
        go.Scatter(
            x=ks,
            y=result.inertias,
            name="Inertia",
            mode="lines+markers",
            line=dict(color="#4E79A7"),
        ),
        secondary_y=False,
    )
    elbow_fig.add_trace(
        go.Scatter(
            x=ks,
            y=result.silhouette_scores,
            name="Silhouette",
            mode="lines+markers",
            line=dict(color="#F28E2B"),
        ),
        secondary_y=True,
    )
    elbow_fig.add_vline(
        x=n_clusters,
        line_dash="dash",
        annotation_text=f"Current: {n_clusters}",
    )
    elbow_fig.update_layout(
        margin=dict(t=20, b=40),
        height=300,
        xaxis_title="Number of groups",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    elbow_fig.update_yaxes(title_text="Inertia", secondary_y=False)
    elbow_fig.update_yaxes(title_text="Silhouette score", secondary_y=True)
    st.plotly_chart(elbow_fig, use_container_width=True)

# ------------------------------------------------------------------
# Main scatter
# ------------------------------------------------------------------

st.subheader("All municipalities at a glance")

fig = px.scatter(
    features,
    x=x_axis,
    y=y_axis,
    color="segment",
    color_discrete_map=SEGMENT_COLORS,
    hover_name="region",
    hover_data={
        "latest_price": ":€,.0f",
        "recent_growth": ":.1%",
        "avg_gas": ":,.0f",
        "segment": True,
    },
    labels=DISPLAY_NAMES,
    height=500,
)
fig.update_traces(marker=dict(size=8, opacity=0.75))
fig.update_layout(
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
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
        setter(
            **{
                f"{ax}axis_tickprefix": "€",
                f"{ax}axis_tickformat": ",",
            }
        )
    elif col == "avg_gas":
        setter(**{f"{ax}axis_ticksuffix": " m³"})
    elif col == "avg_elec":
        setter(**{f"{ax}axis_ticksuffix": " kWh"})

st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------------
# Group overview (descriptions + bar chart in one section)
# ------------------------------------------------------------------

st.subheader("The groups")

active_segments = sorted(features["segment"].unique())
_n_cols = min(len(active_segments), 4)
_desc_cols = st.columns(_n_cols)
for i, name in enumerate(active_segments):
    n_muni = int((features["segment"] == name).sum())
    with _desc_cols[i % _n_cols]:
        st.markdown(f"**{name}**")
        st.caption(f"{n_muni} municipalities — {_segment_description(name)}")

compare_metric = st.selectbox(
    "Compare groups by",
    CLUSTER_FEATURES,
    index=0,
    format_func=lambda c: DISPLAY_NAMES[c],
)

seg_avg = (
    features.groupby("segment")[compare_metric]
    .mean()
    .sort_values(ascending=False)
    .reset_index()
)

bar_fig = px.bar(
    seg_avg,
    x="segment",
    y=compare_metric,
    color="segment",
    color_discrete_map=SEGMENT_COLORS,
    labels=DISPLAY_NAMES,
    text_auto=True,
)
bar_fig.update_layout(
    showlegend=False,
    xaxis_title="",
    margin=dict(t=20, b=40),
)
if compare_metric in ("cagr", "recent_growth"):
    bar_fig.update_layout(yaxis_tickformat=".1%")
    bar_fig.update_traces(texttemplate="%{y:.1%}")
elif compare_metric == "latest_price":
    bar_fig.update_layout(yaxis_tickprefix="€", yaxis_tickformat=",")
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

    st.info(f"**{segment}** — " f"{_segment_description(segment)}")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Price", f"€{row['latest_price']:,.0f}")
    k2.metric("Growth (5 yr)", f"{row['recent_growth']:.1%}/yr")
    k3.metric("Gas use", f"{row['avg_gas']:,.0f} m³/yr")
    k4.metric("Electricity use", f"{row['avg_elec']:,.0f} kWh/yr")

    seg_peers = features[features["segment"] == row["segment"]]
    n_peers = len(seg_peers)

    st.caption(
        f"Compared to the **{n_peers - 1}** other "
        f"municipalities in this group:"
    )

    KEY_FEATURES = ["latest_price", "recent_growth", "avg_gas", "avg_elec"]

    for feat in KEY_FEATURES:
        vals = seg_peers[feat]
        rank = int((vals < row[feat]).sum()) + 1
        pct = rank / n_peers
        word = "low" if pct <= 0.33 else "average" if pct <= 0.66 else "high"
        st.progress(
            min(pct, 1.0),
            text=f"**{DISPLAY_NAMES[feat]}** — {word} for this group",
        )

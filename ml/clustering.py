"""Municipality market segmentation via k-means clustering.

Computes per-municipality features from the CBS annual price data and
groups them into interpretable market segments.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


# ---------------------------------------------------------------------------
# Feature computation
# ---------------------------------------------------------------------------

def compute_municipality_features(
    municipal_prices: pd.DataFrame,
    mortgage_rates: pd.DataFrame,
    energy_consumption: pd.DataFrame,
) -> pd.DataFrame:
    """Derive clustering features per municipality.

    Combines CBS municipal prices, ECB mortgage rates, and
    CBS energy consumption data.

    Returns a DataFrame indexed by region with columns:
      latest_price, cagr, recent_growth, volatility,
      rate_sensitivity, avg_gas, avg_elec, n_years
    """
    df = municipal_prices.copy()

    recent_regions = df[df["year"] >= 2020]["region"].unique()
    df = df[df["region"].isin(recent_regions)]

    grp = df.groupby("region")

    latest_price = grp.apply(
        lambda g: g.loc[g["year"].idxmax(), "avg_price"],
        include_groups=False,
    ).rename("latest_price")

    n_years = grp["year"].count().rename("n_years")

    def _cagr(g):
        g = g.sort_values("year")
        p0, p1 = g["avg_price"].iloc[0], g["avg_price"].iloc[-1]
        n = g["year"].iloc[-1] - g["year"].iloc[0]
        if n <= 0 or p0 <= 0:
            return np.nan
        return (p1 / p0) ** (1 / n) - 1

    cagr = grp.apply(
        _cagr, include_groups=False
    ).rename("cagr")

    def _recent_growth(g):
        g = g.sort_values("year")
        last5 = g[g["year"] >= g["year"].max() - 4]
        if len(last5) < 2:
            return np.nan
        n = last5["year"].iloc[-1] - last5["year"].iloc[0]
        return (
            last5["avg_price"].iloc[-1]
            / last5["avg_price"].iloc[0]
        ) ** (1 / n) - 1

    recent_growth = grp.apply(
        _recent_growth, include_groups=False
    ).rename("recent_growth")

    def _volatility(g):
        g = g.sort_values("year")
        returns = g["avg_price"].pct_change().dropna()
        return returns.std() if len(returns) >= 2 else np.nan

    volatility = grp.apply(
        _volatility, include_groups=False
    ).rename("volatility")

    # --- Rate sensitivity (combines CBS + ECB) ---
    annual_rate = (
        mortgage_rates[mortgage_rates["fixation"] == "AM"]
        .assign(year=lambda d: d["date"].dt.year)
        .groupby("year")["rate"]
        .mean()
    )
    rate_chg = annual_rate.diff().rename("rate_chg")

    df_with_growth = df.sort_values(["region", "year"]).copy()
    df_with_growth["price_chg"] = (
        df_with_growth.groupby("region")["avg_price"]
        .pct_change()
    )
    df_with_growth = df_with_growth.merge(
        rate_chg, on="year", how="left"
    ).dropna(subset=["price_chg", "rate_chg"])

    def _rate_corr(g):
        if len(g) < 4:
            return np.nan
        return g["price_chg"].corr(g["rate_chg"])

    rate_sensitivity = (
        df_with_growth.groupby("region")
        .apply(_rate_corr, include_groups=False)
        .rename("rate_sensitivity")
    )

    features = pd.concat(
        [
            latest_price, cagr, recent_growth,
            volatility, rate_sensitivity, n_years,
        ],
        axis=1,
    )

    # Merge energy consumption data (CBS 86159NED)
    energy = energy_consumption.set_index("region")[
        ["avg_gas", "avg_elec"]
    ]
    features = features.join(energy, how="left")

    return features.dropna()


# ---------------------------------------------------------------------------
# Clustering
# ---------------------------------------------------------------------------

CLUSTER_FEATURES = [
    "latest_price",
    "cagr",
    "recent_growth",
    "volatility",
    "rate_sensitivity",
    "avg_gas",
    "avg_elec",
]

SEGMENT_DESCRIPTIONS = {
    "Expensive, Growing Fast": (
        "Houses are expensive and prices have been rising "
        "quickly in recent years."
    ),
    "Expensive, Slow Growth": (
        "Houses are expensive but price growth has slowed "
        "down recently."
    ),
    "Affordable, Growing Fast": (
        "Houses are still relatively affordable, but prices "
        "are catching up quickly."
    ),
    "Affordable, Slow Growth": (
        "Houses are affordable and prices have stayed "
        "fairly flat in recent years."
    ),
}


@dataclass
class ClusterResult:
    features: pd.DataFrame
    labels: pd.Series
    centers: pd.DataFrame
    segment_map: dict[int, str]
    inertias: list[float]


def _assign_segment_names(
    centers: pd.DataFrame,
) -> dict[int, str]:
    """Heuristically map cluster IDs to readable segment names."""
    c = centers.copy()
    median_price = c["latest_price"].median()
    median_growth = c["recent_growth"].median()

    mapping = {}
    for idx, row in c.iterrows():
        expensive = row["latest_price"] >= median_price
        growing = row["recent_growth"] >= median_growth
        if expensive and not growing:
            name = "Expensive, Slow Growth"
        elif expensive and growing:
            name = "Expensive, Growing Fast"
        elif not expensive and growing:
            name = "Affordable, Growing Fast"
        else:
            name = "Affordable, Slow Growth"
        mapping[idx] = name

    # Deduplicate if two clusters get the same name
    seen: dict[str, int] = {}
    for idx, name in list(mapping.items()):
        if name in seen:
            mapping[idx] = f"{name} II"
        seen[name] = idx

    return mapping


def run_clustering(
    features: pd.DataFrame,
    n_clusters: int = 4,
) -> ClusterResult:
    """Run k-means on municipality features."""
    X = features[CLUSTER_FEATURES].copy()

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Elbow data (for display)
    inertias = []
    for k in range(2, 9):
        km = KMeans(n_clusters=k, n_init=10, random_state=42)
        km.fit(X_scaled)
        inertias.append(km.inertia_)

    km = KMeans(
        n_clusters=n_clusters, n_init=10, random_state=42
    )
    labels = pd.Series(
        km.fit_predict(X_scaled),
        index=features.index,
        name="cluster",
    )

    centers_scaled = pd.DataFrame(
        km.cluster_centers_,
        columns=CLUSTER_FEATURES,
    )
    centers = pd.DataFrame(
        scaler.inverse_transform(centers_scaled),
        columns=CLUSTER_FEATURES,
    )

    segment_map = _assign_segment_names(centers)

    return ClusterResult(
        features=features,
        labels=labels,
        centers=centers,
        segment_map=segment_map,
        inertias=inertias,
    )

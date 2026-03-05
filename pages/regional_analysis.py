import streamlit as st
import pandas as pd
import altair as alt
import unicodedata
from typing import cast

from data.fetch_cbs import fetch_municipal_prices
from data.province_municipality_map import (
    PROVINCE_MUNICIPALITIES,
    PROVINCE_NAME_ALIASES,
)

def _normalize_name(value: str) -> str:
    value = value.strip().lower()
    value = value.replace("’", "'").replace("‘", "'").replace("`", "'")
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    return " ".join(value.split())


def _resolve_hardcoded_municipalities(
    province: str,
    available_municipalities: list[str],
) -> list[str]:
    canonical_province = PROVINCE_NAME_ALIASES.get(province, province)
    wanted = PROVINCE_MUNICIPALITIES.get(canonical_province, [])

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

def show_caption() -> None:
    st.header("Regional Analysis")
    st.caption(
        "Compare average purchase prices across Dutch municipalities "
        "(annual CBS data)."
    )

def show_region_drilldown(prices: pd.DataFrame) -> None:
    st.subheader("Municipality/Province drill-down")
    # In CBS table 83625ENG, provinces are tagged with (PV)
    # while municipalities are usually plain names without a suffix.
    provinces = prices[prices["region"].str.endswith("(PV)")].copy()
    provinces["province"] = provinces["region"].str.replace(r"\s*\(PV\)", "", regex=True)

    municipalities = prices[
        ~prices["region"].str.contains(r"\((?:PV|LD)\)$", regex=True, na=False)
        & (prices["region"] != "The Netherlands")
    ].copy()

    latest_year = int(municipalities["year"].max())
    municipalities_latest = municipalities[municipalities["year"] == latest_year].copy()

    all_provinces = sorted(cast(list[str], provinces["province"].unique().tolist()))
    selected_province = st.selectbox(
        "Select province",
        all_provinces,
        index=all_provinces.index("Noord-Holland"),
    )

    available_municipalities = sorted(
        cast(list[str], municipalities_latest["region"].dropna().unique().tolist())
    )
    hardcoded_municipalities = _resolve_hardcoded_municipalities(
        selected_province,
        available_municipalities,
    )

    if hardcoded_municipalities:
        municipality_options = hardcoded_municipalities
    else:
        municipality_options = available_municipalities

    selected_municipalities = st.multiselect(
        "Select municipalities to compare",
        municipality_options,
        default=municipality_options,
        key=f"municipality_select_{selected_province}",
    )

    st.caption(
        f"Selected province: {selected_province}. "
        f"Municipality options are based on {latest_year} data and matched against the hardcoded map."
    )
    st.write(f"Selected municipalities: {len(selected_municipalities)}")

    if selected_municipalities:
        selection = municipalities[
            municipalities["region"].isin(selected_municipalities)
        ].copy()
        trend = cast(
            pd.DataFrame,
            selection.groupby(["year", "region"], as_index=False)["avg_price"].mean(),
        )

        st.subheader("Municipality price trends")
        base_chart = alt.Chart(trend)  # pyright: ignore[reportUnknownArgumentType]
        line_chart = base_chart.mark_line()  # pyright: ignore[reportUnknownMemberType]
        chart = (
            line_chart
            .encode(
                x=alt.X("year:Q", axis=alt.Axis(format="d", title="Year")),
                y=alt.Y("avg_price:Q", title="Average purchase price (EUR)"),
                color=alt.Color(
                    "region:N",
                    title="Municipality",
                    legend=alt.Legend(orient="right", direction="vertical"),
                ),
                tooltip=["region:N", alt.Tooltip("year:Q", format=".0f"), "avg_price:Q"],
            )
            .properties(height=420)
            .interactive()
        )
        st.altair_chart(chart, use_container_width=True)
    else:
        st.warning("Select at least one municipality to show the chart.")

prices = fetch_municipal_prices()
show_caption()
show_region_drilldown(prices)
import cbsodata
import pandas as pd
import streamlit as st

TABLE_PRICES_QUARTERLY = "85792ENG"
TABLE_PRICES_MUNICIPAL = "83625ENG"
<<<<<<< HEAD
TABLE_PRICES_QUARTERLY = "85792ENG"
TABLE_PRICES_MUNICIPAL = "83625ENG"
TABLE_DEMOGRAPHICS = "85210ENG"
=======
TABLE_ENERGY_MUNICIPAL = "86159NED"
>>>>>>> main


@st.cache_data(ttl=3600, show_spinner="Fetching CBS quarterly price data…")
def fetch_quarterly_prices() -> pd.DataFrame:
    """Fetch 85792ENG: price index + avg price by province,
    quarterly from 1995."""
    raw = pd.DataFrame(cbsodata.get_data(TABLE_PRICES_QUARTERLY))

    df = raw.rename(
        columns={
            "Regions": "region",
            "Periods": "period",
            "PriceIndexPurchasePrices_1": "price_index",
            "AveragePurchasePrice_7": "avg_price",
            "NumberOfDwellingsSold_4": "n_sales",
        }
    )

    df["region"] = df["region"].str.strip()
    df["period"] = df["period"].str.strip()

    df["year"] = df["period"].str[:4].astype(int)
    quarter_map = {
        "1st quarter": 1,
        "2nd quarter": 2,
        "3rd quarter": 3,
        "4th quarter": 4,
    }
    df["quarter"] = df["period"].str[5:].map(quarter_map)

    quarterly = df[df["quarter"].notna()].copy()
    quarterly["date"] = pd.to_datetime(
        quarterly["year"].astype(str)
        + "-"
        + (quarterly["quarter"] * 3).astype(int).astype(str)
        + "-01"
    )

    return quarterly


@st.cache_data(ttl=3600, show_spinner="Fetching CBS municipal price data…")
def fetch_municipal_prices() -> pd.DataFrame:
    """Fetch 83625ENG: average purchase price by municipality,
    annual from 1995.

    Filters out national, province, and landsdeel aggregates so only
    actual municipalities remain.
    """
    raw = pd.DataFrame(cbsodata.get_data(TABLE_PRICES_MUNICIPAL))

    df = raw.rename(
        columns={
            "Regions": "region",
            "Periods": "period",
            "AveragePurchasePrice_1": "avg_price",
        }
    )

    df["region"] = df["region"].str.strip()
    df["period"] = df["period"].str.strip()
    df["year"] = df["period"].str[:4].astype(int)

    aggregates = df["region"].str.contains(
        r"\(PV\)|\(LD\)", regex=True, na=False
    ) | (df["region"] == "The Netherlands")
    df = df[~aggregates].copy()

    df = df.dropna(subset=["avg_price"])

    return df

<<<<<<< HEAD
@st.cache_data(ttl=3600, show_spinner="Fetching CBS demographic data…")
def fetch_demographics() -> pd.DataFrame:
    """Fetch demographic and housing indicators by municipality"""

    raw = pd.DataFrame(cbsodata.get_data(TABLE_DEMOGRAPHICS))

    df = raw.rename(
        columns={
            "Regions": "region",
            "Periods": "year",

            "AverageDisposableIncome_1": "income",
            "AverageWOZValueOfDwellings_2": "woz_value",

            "TotalDwellings_3": "houses",
            "PrivateHouseholds_4": "households",

            "PopulationDensity_5": "density",

            "HighlyEducatedPopulation_6": "high_education_pct",
            "Population65YearsOrOlder_7": "age65_pct",

            "UrbanisationLevel_8": "urban_index",
        }
    )

    df["region"] = df["region"].str.strip()
    df["year"] = df["year"].str[:4].astype(int)

    return df
=======

@st.cache_data(
    ttl=3600,
    show_spinner="Fetching CBS energy consumption data…",
)
def fetch_energy_consumption() -> pd.DataFrame:
    """Fetch 86159NED: avg gas and electricity use per
    municipality (2024), for total housing stock.

    Returns one row per municipality with columns:
      region, avg_gas, avg_electricity, pct_district_heating
    """
    raw = pd.DataFrame(
        cbsodata.get_data(TABLE_ENERGY_MUNICIPAL)
    )
    raw["SoortRegio_2"] = raw["SoortRegio_2"].str.strip()
    raw["Woningkenmerken"] = (
        raw["Woningkenmerken"].str.strip()
    )

    muni = raw[
        (raw["SoortRegio_2"] == "Gemeente")
        & (raw["Woningkenmerken"] == "Totaal woningen")
    ].copy()

    df = muni.rename(columns={
        "Gemeentenaam_1": "region",
        "GemiddeldAardgasverbruik_4": "avg_gas",
        "GemiddeldeElektriciteitslevering_5": "avg_elec",
        "Stadsverwarming_7": "pct_district_heating",
    })
    df["region"] = df["region"].str.strip()

    return df[
        ["region", "avg_gas", "avg_elec",
         "pct_district_heating"]
    ].reset_index(drop=True)
>>>>>>> main

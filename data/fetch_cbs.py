import cbsodata
import pandas as pd
import streamlit as st

TABLE_PRICES_QUARTERLY = "85792ENG"
TABLE_PRICES_MUNICIPAL = "83625ENG"
TABLE_PRICES_QUARTERLY = "85792ENG"
TABLE_PRICES_MUNICIPAL = "83625ENG"
TABLE_DEMOGRAPHICS = "85210ENG"


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
    annual from 1995."""
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

    return df

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

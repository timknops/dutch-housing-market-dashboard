import io

import pandas as pd
import requests
import streamlit as st

ECB_URL = "https://data-api.ecb.europa.eu/service/data/MIR/M.NL.B.A2C..R.A.2250.EUR.N"

MATURITY_LABELS = {
    "AM": "Cost of borrowing (aggregate)",
    "F": "Variable / up to 1 year",
    "I": "1–5 year fixation",
    "O": "5–10 year fixation",
    "P": "Over 10 year fixation",
}


@st.cache_data(ttl=3600, show_spinner="Fetching ECB mortgage rate data…")
def fetch_mortgage_rates() -> pd.DataFrame:
    """Fetch ECB MIR mortgage rates for NL, monthly, all fixation periods."""
    r = requests.get(ECB_URL, headers={"Accept": "text/csv"}, timeout=30)
    r.raise_for_status()

    raw = pd.read_csv(io.StringIO(r.text))

    df = raw[raw["MATURITY_NOT_IRATE"].isin(MATURITY_LABELS)].copy()
    df = df[["TIME_PERIOD", "OBS_VALUE", "MATURITY_NOT_IRATE"]].rename(
        columns={
            "TIME_PERIOD": "month",
            "OBS_VALUE": "rate",
            "MATURITY_NOT_IRATE": "fixation",
        }
    )
    df["fixation_label"] = df["fixation"].map(MATURITY_LABELS)
    df["date"] = pd.to_datetime(df["month"] + "-01")

    return df.sort_values("date")

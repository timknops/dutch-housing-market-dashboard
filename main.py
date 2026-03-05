import streamlit as st

st.set_page_config(
    page_title="Dutch Housing Market",
    layout="wide",
)

overview = st.Page(
    "pages/market_overview.py",
    title="Market Overview",
)
regional = st.Page(
    "pages/regional_analysis.py",
    title="Regional Analysis",
)
affordability = st.Page(
    "pages/affordability.py",
    title="Affordability",
)
ml_segments = st.Page(
    "pages/ml_clustering.py",
    title="Market Segments (ML)",
)

pg = st.navigation(
    [overview, regional, affordability, ml_segments]
)
pg.run()

# Remaining Work

## Data Layer

- [ ] **CBS key figures fetch** — income, WOZ value, population per municipality. One table per year (e.g. `85163NED`? for 2022, `84799NED`? for 2021). Fetch multiple years and stack into one DataFrame.
- [ ] **Merge pipeline** (`data/process.py`) — join CBS municipal prices with key figures on region + year; join with ECB rates on time period.

## Tab 2: Regional Analysis

- [ ] Scatter plot: income vs house price by municipality
- [ ] Municipality/province selector for drill-down
- [ ] Ranking table: most/least expensive municipalities
- [ ] *(stretch)* Choropleth map colored by avg price (needs GeoJSON from CBS geodata)

## Tab 3: Affordability

- [ ] Price-to-income ratio per municipality
- [ ] Monthly mortgage cost calculator (user inputs price, uses current ECB rate)
- [ ] Most/least affordable municipalities table or heatmap

## Tab 4: ML / Predictions (bonus)

- [ ] **Clustering** — k-means on municipality features (price, income, WOZ, population density) → scatter plot of segments.
- [ ] **Time series forecast** — predict national house price 1–2 years ahead (statsmodels ARIMA or Prophet)
- [ ] **Regression** — predict price from municipality features, show feature importances

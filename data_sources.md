# Data Sources Registry — US Natural Gas Model

> Reference for all data ingestion. Check here before writing any API call or file reader.

---

## Primary Price

| Field | Detail |
|---|---|
| **Series** | Henry Hub Natural Gas Spot Price |
| **Source** | FRED (Federal Reserve Bank of St. Louis) |
| **Series ID** | `MHHNGSP` (monthly) / `DHHNGSP` (daily) |
| **URL** | https://fred.stlouisfed.org/series/DHHNGSP |
| **Frequency** | Daily (business days) |
| **Units** | USD per MMBtu |
| **Coverage** | 1997-01-07 to present |
| **API** | `fredapi` Python library — requires `FRED_API_KEY` |
| **License** | Public domain (FRED open data) |
| **Notes** | Use `DHHNGSP` for daily. Gaps on weekends/holidays — reindex + interpolate. |

---

## Natural Gas Storage

| Field | Detail |
|---|---|
| **Series** | Weekly Natural Gas Storage Report |
| **Source** | EIA (US Energy Information Administration) |
| **Series ID** | `NG.NW2_EPG0_SWO_R48_BCF.W` (Lower 48, weekly) |
| **URL** | https://api.eia.gov/v2/natural-gas/stor/wkly |
| **Frequency** | Weekly (every Thursday, reporting prior week) |
| **Units** | Billion cubic feet (Bcf) |
| **Coverage** | 1994 to present |
| **API** | EIA API v2 — requires `EIA_API_KEY` |
| **License** | Public domain (US government data) |
| **Notes** | The single most market-moving data release in US gas. "Storage surprise" = actual vs analyst consensus. Also pull 5-year average for context. Regional breakdown: East, Midwest, Mountain, Pacific, South Central. |

---

## Natural Gas Consumption (Demand)

| Field | Detail |
|---|---|
| **Series** | Natural Gas Consumption by Sector |
| **Source** | EIA API |
| **Series IDs** | `NG.N3010US2.M` (residential), `NG.N3020US2.M` (commercial), `NG.N3035US2.M` (industrial), `NG.N3045US2.M` (electric power), `NG.N3060US2.M` (pipeline & lease) |
| **URL** | https://api.eia.gov/v2/natural-gas/cons/sum |
| **Frequency** | Monthly |
| **Units** | MMcf (million cubic feet) |
| **Coverage** | 1973 to present |
| **API** | EIA API v2 — requires `EIA_API_KEY` |
| **License** | Public domain |
| **Notes** | Electric power sector (`N3045`) is the power burn component — critical US-specific driver. Residential + commercial = heating demand proxy. |

---

## Power Burn (Gas for Electricity Generation)

| Field | Detail |
|---|---|
| **Series** | Natural Gas Consumed for Electricity Generation |
| **Source** | EIA API |
| **Series ID** | `NG.N3045US2.M` (electric power sector consumption) |
| **URL** | https://api.eia.gov/v2/natural-gas/cons/sum |
| **Frequency** | Monthly |
| **Units** | MMcf |
| **Coverage** | 1973 to present |
| **API** | EIA API v2 — requires `EIA_API_KEY` |
| **License** | Public domain |
| **Notes** | Subset of consumption series above. Summer peak (cooling load) competes with winter heating peak — creates the two-season US demand pattern. |

---

## Crude Oil Price (Cross-Commodity)

| Field | Detail |
|---|---|
| **Series** | WTI Crude Oil Price |
| **Source** | FRED |
| **Series ID** | `DCOILWTICO` |
| **URL** | https://fred.stlouisfed.org/series/DCOILWTICO |
| **Frequency** | Daily (business days) |
| **Units** | USD per barrel |
| **Coverage** | 1986-01-02 to present |
| **API** | `fredapi` — requires `FRED_API_KEY` |
| **License** | Public domain |
| **Notes** | US equivalent of Brent. Reindex + interpolate for weekends/holidays. |

---

## Weather — Temperature

| Field | Detail |
|---|---|
| **Series** | Hourly temperature at key US consumption cities |
| **Source** | Open-Meteo (no API key required) |
| **Archive URL** | https://archive-api.open-meteo.com/v1/archive |
| **Forecast URL** | https://api.open-meteo.com/v1/forecast |
| **Frequency** | Hourly → aggregate to daily mean |
| **Units** | °C |
| **Coverage** | 1940 to present (ERA5); recent days via ECMWF forecast |
| **API** | REST, no key needed |
| **License** | CC BY 4.0 |
| **Cities** | New York (40.71, -74.01), Chicago (41.88, -87.63), Houston (29.76, -95.37), Atlanta (33.75, -84.39), Boston (42.36, -71.06) |
| **Notes** | Average across all 5 cities for a national consumption proxy — same multi-city approach as German project. Northeast + Midwest = heating demand. South = cooling/power burn. |

---

## Weather — Heating & Cooling Degree Days

| Field | Detail |
|---|---|
| **Series** | HDD and CDD (US national and regional) |
| **Source** | EIA API |
| **Series IDs** | `NG.N3010US2.M` region-specific HDD series via EIA |
| **Alt Source** | NOAA Climate Prediction Center — https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/cdus/degree_days/ |
| **Frequency** | Weekly / monthly |
| **Units** | Degree days (base 65°F) |
| **Coverage** | 1990s to present |
| **License** | Public domain |
| **Notes** | HDD base = 65°F (equivalent to German 18°C threshold). EIA publishes HDD-weighted consumption forecasts — useful for model validation. |

---

## LNG Exports

| Field | Detail |
|---|---|
| **Series** | US LNG Exports by Terminal |
| **Source** | EIA API |
| **Series ID** | `NG.N9133US2.M` (total LNG exports) |
| **URL** | https://api.eia.gov/v2/natural-gas/move/lngc |
| **Frequency** | Monthly |
| **Units** | MMcf |
| **Coverage** | 2016 to present (Sabine Pass first exports Feb 2016) |
| **API** | EIA API v2 — requires `EIA_API_KEY` |
| **License** | Public domain |
| **Notes** | Structural demand floor post-2016. Key events: Sabine Pass (2016), Corpus Christi (2019), Freeport LNG outage (Jun–Dec 2022 — bearish supply shock). |

---

## Pipeline Imports

| Field | Detail |
|---|---|
| **Series** | Pipeline Imports from Canada and Mexico |
| **Source** | EIA API |
| **Series IDs** | `NG.N9100CA2.M` (Canada imports), `NG.N9100MX2.M` (Mexico imports) |
| **URL** | https://api.eia.gov/v2/natural-gas/move/ist |
| **Frequency** | Monthly |
| **Units** | MMcf |
| **API** | EIA API v2 — requires `EIA_API_KEY` |
| **License** | Public domain |

---

## Dry Gas Production

| Field | Detail |
|---|---|
| **Series** | US Dry Natural Gas Production |
| **Source** | EIA API |
| **Series ID** | `NG.N9070US2.M` |
| **URL** | https://api.eia.gov/v2/natural-gas/sum/lsum |
| **Frequency** | Monthly |
| **Units** | MMcf |
| **Coverage** | 1973 to present |
| **API** | EIA API v2 — requires `EIA_API_KEY` |
| **License** | Public domain |
| **Notes** | Shale revolution visible post-2008 (Marcellus, Permian associated gas). YoY growth rate used as supply-side pressure feature. |

---

## Electricity Prices (Cross-Commodity)

| Field | Detail |
|---|---|
| **Series** | US Wholesale Electricity Prices |
| **Source** | EIA API |
| **Series ID** | EIA Form 923 / EIA-861 |
| **URL** | https://api.eia.gov/v2/electricity/wholesale-prices |
| **Frequency** | Monthly |
| **Units** | USD/MWh |
| **API** | EIA API v2 — requires `EIA_API_KEY` |
| **License** | Public domain |
| **Notes** | Relevant hubs: PJM (Northeast/Midwest), ERCOT (Texas), MISO. Gas-to-power switching: when power prices rise, gas demand for generation rises. |

---

## API Keys

Stored in `.env` and .gitignore (so its not committed bt accident lol!):
```
EIA_API_KEY=...     # Register at: https://api.eia.gov/registrations
FRED_API_KEY=...    # Register at: https://fred.stlouisfed.org/docs/api/api_key.html
```

Load in code via:
```python
from dotenv import load_dotenv
import os
load_dotenv()
eia_key = os.getenv("EIA_API_KEY")
fred_key = os.getenv("FRED_API_KEY")
```

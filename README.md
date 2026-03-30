# US Natural Gas Consumption Model — Henry Hub

A quantitative research pipeline for modelling and forecasting US natural gas demand, using **Henry Hub** as the primary price benchmark. The project ingests data from public US energy and weather APIs, performs exploratory analysis, engineers demand-relevant features, and builds multiple forecasting models evaluated in a trading context.

---

## Objective

Build a reproducible, end-to-end forecasting pipeline for US natural gas consumption that:

- Ingests and cleans data from EIA, FRED, and Open-Meteo
- Captures the two-season US demand structure (winter heating + summer power burn)
- Evaluates models under a realistic forecast scenario — where only weather is known in advance
- Interprets outputs in terms of market signals, not just academic accuracy

---

## Project Structure

```
NatGasModel_US/
│
├── data/
│   └── raw/                        # All source data (CSV), committed to repo
│       ├── henry_hub_daily.csv     # Henry Hub spot price (FRED: DHHNGSP)
│       ├── wti_daily.csv           # WTI crude oil price (FRED: DCOILWTICO)
│       ├── eia_storage_weekly.csv  # EIA weekly storage, Lower 48 (Bcf)
│       ├── eia_consumption_monthly.csv  # EIA monthly consumption (MMcf)
│       └── temperatures_daily.csv  # 5-city US mean temperature (Open-Meteo)
│
├── diagrams/                       # All plot outputs saved as SVG
├── models/                         # Serialised model artefacts (.pkl)
│
├── notebooks/
│   ├── data_overview/              # One notebook per raw data source
│   ├── data_analysis/              # Cross-variable EDA
│   └── modelling/                  # One notebook per model
│
├── src/
│   ├── data_handling/
│   │   ├── loaders.py              # Fetch + read layer, build_feature_matrix()
│   │   └── __init__.py
│   └── models/
│       └── __init__.py
│
├── fetch_data.py                   # Run once to populate data/raw/
├── data_sources.md                 # Full source registry with API series IDs
├── industry_learnings.md           # Market concepts and terminology reference
├── requirements.txt
└── .env                            # API keys (not committed)
```

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                             │
│                                                                 │
│  FRED API          EIA API v2           Open-Meteo              │
│  (fredapi)         (requests)           (requests, no key)      │
│                                                                 │
│  DHHNGSP           natural-gas/         archive-api +           │
│  Henry Hub         stor/wkly            forecast API            │
│  daily price       cons/sum             5 US cities             │
│                                         ERA5 + ECMWF            │
│  DCOILWTICO                                                      │
│  WTI crude                                                       │
│  daily price                                                     │
└────────────┬───────────────┬──────────────────┬─────────────────┘
             │               │                  │
             ▼               ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    data/raw/  (CSV files)                        │
│                                                                  │
│  henry_hub_daily    eia_storage_weekly    temperatures_daily     │
│  wti_daily          eia_consumption_monthly                      │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│              src/data_handling/loaders.py                        │
│                                                                  │
│  read_*()  functions                                             │
│  ├── Reindex to daily calendar                                   │
│  ├── Interpolate price gaps (weekends/holidays)                  │
│  └── Forward-fill weekly/monthly data to daily                   │
│                                                                  │
│  build_feature_matrix()                                          │
│  ├── Aligns all series to common daily index                     │
│  ├── Computes HDD and CDD (base 65°F) from temperature           │
│  └── Adds weekend binary flag                                    │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Feature Matrix                                 │
│                                                                  │
│   temperature_c  │  hdd  │  cdd  │  henry_hub_price             │
│   wti_price  │  storage_bcf  │  weekend  │  consumption_mmcf    │
│                                           ▲                      │
│                                     TARGET VARIABLE              │
└──────────────────────────────┬──────────────────────────────────┘
                               │
              ┌────────────────┴─────────────────┐
              │                                  │
              ▼                                  ▼
┌─────────────────────────┐       ┌──────────────────────────────┐
│   Full regressors        │       │   Static regressors           │
│   (optimistic scenario)  │       │   (realistic scenario)        │
│                          │       │                               │
│   All actual values      │       │   Prices + storage frozen     │
│   used for X             │       │   at last known value         │
│                          │       │   post train cutoff           │
│                          │       │   (only HDD/CDD known         │
│                          │       │    in advance)                │
└────────────┬─────────────┘       └──────────────┬───────────────┘
             │                                    │
             └──────────────┬─────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                       MODELS                                     │
│                                                                  │
│   Linear Regression → ARX → SARIMAX → XGBoost → NeuralProphet   │
│                                                                  │
│   Evaluated on: MAPE at 14-day, 60-day, 365-day horizons        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Feature Matrix

| Feature            | Type       | Description                                                 |
| ------------------ | ---------- | ----------------------------------------------------------- |
| `hdd`              | Weather    | Heating Degree Days, base 65°F — winter heating proxy       |
| `cdd`              | Weather    | Cooling Degree Days, base 65°F — summer power burn proxy    |
| `henry_hub_price`  | Price      | Daily Henry Hub spot price (USD/MMBtu)                      |
| `wti_price`        | Price      | Daily WTI crude oil spot price (USD/bbl)                    |
| `storage_bcf`      | Structural | EIA weekly working gas in storage, Lower 48 (Bcf)           |
| `weekend`          | Calendar   | 1 = Saturday/Sunday, 0 = weekday                            |
| `temperature_c`    | Reference  | Raw daily mean temp — kept for reference, not a model input |
| `consumption_mmcf` | **Target** | EIA monthly total consumption (MMcf)                        |

### Two Forecast Scenarios

| Scenario              | Description                                                                                          |
| --------------------- | ---------------------------------------------------------------------------------------------------- |
| **Full regressors**   | All actual values used — optimistic upper bound                                                      |
| **Static regressors** | Prices and storage forward-filled after train cutoff — realistic, since only weather is forecastable |

Both scenarios evaluated on every model.

---

## Key Market Context

**Henry Hub** is a physical pipeline junction in Erath, Louisiana. It is the delivery point for NYMEX natural gas futures and the US benchmark price.

**The Thursday EIA storage report** is the dominant weekly price driver. A storage "surprise" (actual vs analyst consensus) routinely moves Henry Hub 3–5% intraday.

**HDD and CDD** replace a simple temperature input because US gas demand has two distinct seasons — winter heating (HDD) and summer power burn (CDD). A single temperature feature cannot capture both.

**Storage vs 5-year average** is the market's primary supply health metric. Entering winter above the 5-year average is bearish; below is bullish.

---

## Setup

```bash
# 1. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add API keys
cp .env.example .env
# Edit .env with your EIA and FRED keys

# 4. Fetch all source data
python fetch_data.py
```

**API keys required:**

- EIA: free at [api.eia.gov/registrations](https://api.eia.gov/registrations)
- FRED: free at [fred.stlouisfed.org](https://fred.stlouisfed.org/docs/api/api_key.html)

---

## Roadmap

- [x] Phase 0 — Project setup
- [x] Phase 1 — Data ingestion layer
- [ ] Phase 2 — Data overview notebooks
- [ ] Phase 3 — Exploratory data analysis
- [ ] Phase 4 — Feature engineering
- [ ] Phase 5 — Modelling
- [ ] Phase 6 — Interpretation & trading context

\*\* AI was used in the making of this project as it is primarily for learning purposes

# US Natural Gas Quantitative Research Pipeline

A full end-to-end quantitative research project modelling US natural gas demand and price dynamics, anchored to **Henry Hub** — the primary US gas price benchmark. The project spans the entire research lifecycle: live API data ingestion, per-series data analysis, cross-variable EDA, feature engineering, and a progression of forecasting models evaluated in a trading context.

Built to replicate the methodology of a professional German natural gas consumption model, adapted for the US market.

---

## What This Project Does

Starting from zero raw data, the pipeline:

1. **Pulls live data from three public APIs** — EIA (US Energy Information Administration), FRED (Federal Reserve Economic Data), and Open-Meteo — with no manual downloads
2. **Analyses each data source in isolation** — understanding seasonality, regime shifts, and market significance before any cross-variable work
3. **Explores relationships between variables** — storage vs price, temperature vs consumption, crude oil spillovers
4. **Engineers demand-relevant features** — converting raw temperature into Heating Degree Days (HDD) and Cooling Degree Days (CDD), computing storage surplus/deficit vs the 5-year average
5. **Builds and compares five forecasting models** — from a simple linear regression baseline up to XGBoost and NeuralProphet
6. **Evaluates models in a realistic trading scenario** — where only weather is known in advance, not future prices or storage

---

## Data Sources (All via API — No Manual Downloads)

| Source | API | What it provides | Series |
|---|---|---|---|
| **FRED** | `fredapi` Python library | Henry Hub daily spot price | `DHHNGSP` |
| **FRED** | `fredapi` Python library | WTI crude oil daily price | `DCOILWTICO` |
| **EIA API v2** | `requests` | Weekly natural gas storage, Lower 48 (Bcf) | `natural-gas/stor/wkly` |
| **EIA API v2** | `requests` | Monthly total gas consumption (MMcf) | `natural-gas/cons/sum` |
| **Open-Meteo** | `requests` (no API key) | Daily temperature, 5 US cities, ERA5 reanalysis back to 2000 | archive-api |

All data is fetched with a single command: `python fetch_data.py`

---

## Project Structure

```
NatGasModel_US/
│
├── data/raw/                           # All source data as CSV (committed)
│   ├── henry_hub_daily.csv             # Henry Hub spot price (daily)
│   ├── wti_daily.csv                   # WTI crude oil price (daily)
│   ├── eia_storage_weekly.csv          # EIA working gas in storage (weekly, Bcf)
│   ├── eia_consumption_monthly.csv     # EIA total consumption (monthly, MMcf)
│   └── temperatures_daily.csv         # 5-city US mean temperature (daily, °C)
│
├── notebooks/
│   ├── data_overview/                  # Phase 2 — one notebook per raw series
│   │   ├── 001_henry_hub_price.ipynb
│   │   ├── 002_wti_crude.ipynb
│   │   ├── 003_eia_storage.ipynb
│   │   ├── 004_consumption.ipynb
│   │   └── 005_temperature.ipynb
│   ├── eda/                            # Phase 3 — cross-variable analysis
│   │   └── 301_price_vs_storage.ipynb
│   └── modelling/                      # Phase 5 — one notebook per model
│
├── src/data_handling/
│   └── loaders.py                      # All fetch + feature engineering logic
│
├── diagram/                            # All chart outputs saved as SVG
├── fetch_data.py                       # One-shot data download script
├── industry_learnings.md               # US gas market concepts & terminology
├── technical_learnings.md             # Python/pandas/plotting reference
└── requirements.txt
```

---

## Data Flow

```
┌──────────────────────────────────────────────────────────────┐
│                      LIVE DATA SOURCES                        │
│                                                              │
│  FRED API           EIA API v2          Open-Meteo           │
│  fredapi library    requests            requests (no key)    │
│                                                              │
│  Henry Hub price    Weekly storage      Daily temperature    │
│  WTI crude price    Monthly consumption ERA5 reanalysis      │
│                     (Lower 48)          5 US cities          │
└──────────┬──────────────────┬───────────────────┬────────────┘
           │                  │                   │
           ▼                  ▼                   ▼
┌──────────────────────────────────────────────────────────────┐
│                  data/raw/  (CSV files)                       │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│               src/data_handling/loaders.py                    │
│                                                              │
│  ├── Reindex all series to full daily calendar               │
│  ├── Interpolate weekend/holiday price gaps                  │
│  ├── Forward-fill weekly/monthly data to daily               │
│  ├── Compute HDD and CDD (base 65°F)                         │
│  └── build_feature_matrix() — single aligned DataFrame       │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                     Feature Matrix                            │
│                                                              │
│  hdd │ cdd │ henry_hub_price │ wti_price │ storage_bcf       │
│  weekend │ temperature_c │ consumption_mmcf (TARGET)         │
└──────────────────────────┬───────────────────────────────────┘
                           │
          ┌────────────────┴─────────────────┐
          ▼                                  ▼
  Full regressors                   Static regressors
  (all actuals — optimistic)        (prices/storage frozen
                                     post-cutoff — realistic)
          │                                  │
          └──────────────┬───────────────────┘
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                        MODELS                                 │
│                                                              │
│  Linear Regression → ARX → SARIMAX → XGBoost → NeuralProphet│
│                                                              │
│  Evaluated: MAPE at 14-day, 60-day, 365-day horizons         │
└──────────────────────────────────────────────────────────────┘
```

---

## Research Phases

### Phase 0 — Project Setup ✅
Repository structure, virtual environment, API key management, `.gitignore`, dependency pinning.

### Phase 1 — Data Ingestion Layer ✅
`src/data_handling/loaders.py` — one fetch function per source, all hitting live APIs. A single `python fetch_data.py` from the project root populates all of `data/raw/`. No manual data wrangling.

### Phase 2 — Data Overview Notebooks ✅ *(in progress)*
One notebook per raw data source. Each series analysed in isolation:
- Full price/volume history with annotated market events
- Distribution analysis
- Seasonality decomposition
- Series-specific market context (e.g. the Thursday EIA storage report, the HDD/CDD base-65°F convention, the shale revolution structural break)

### Phase 3 — Exploratory Data Analysis 🔄 *(in progress)*
Cross-variable analysis — how the series interact:
- Henry Hub price vs storage surplus/deficit (lead/lag, rolling correlation)
- Temperature vs consumption (HDD/CDD elasticity)
- WTI vs Henry Hub (fuel switching, associated gas supply dynamics)
- Correlation matrix across all features

### Phase 4 — Feature Engineering
Transform raw series into model-ready features:
- HDD / CDD from raw temperature (already in loaders)
- Storage surplus/deficit vs 5-year historical average
- Lagged regressors (storage leads price by ~1 week)
- Regime indicators (pre/post shale, injection/withdrawal season)
- `build_feature_matrix()` — single function returning the aligned feature DataFrame

### Phase 5 — Modelling
Five models in increasing complexity, each evaluated in both forecast scenarios:

| Model | Why it's here |
|---|---|
| **Linear Regression** | Interpretable baseline — coefficient magnitudes reveal feature importance |
| **ARX** (AutoRegressive with eXogenous inputs) | Adds price autocorrelation structure |
| **SARIMAX** | Handles the seasonal pattern explicitly |
| **XGBoost** | Captures non-linear interactions between weather, storage, and price |
| **NeuralProphet** | Trend + seasonality decomposition with regressor support |

Evaluation: MAPE at 14-day, 60-day, and 365-day forecast horizons.

### Phase 6 — Interpretation & Trading Context
Translate model outputs into market-relevant language:
- Which features drive the forecast at each horizon?
- When does the model under/over-predict — and why?
- How do storage surprises propagate through the forecast?
- Storage signal trading strategy: does the 1-week storage→price lead observed in EDA survive into the model?

---

## Feature Matrix

| Feature | Type | Description |
|---|---|---|
| `hdd` | Weather | Heating Degree Days, base 65°F — winter heating proxy |
| `cdd` | Weather | Cooling Degree Days, base 65°F — summer power burn proxy |
| `henry_hub_price` | Price | Daily Henry Hub spot price (USD/MMBtu) |
| `wti_price` | Price | Daily WTI crude oil spot price (USD/bbl) |
| `storage_bcf` | Structural | EIA weekly working gas in storage, Lower 48 (Bcf) |
| `weekend` | Calendar | 1 = Saturday/Sunday, 0 = weekday |
| `temperature_c` | Reference | Raw daily mean temp — kept for reference, excluded from model |
| `consumption_mmcf` | **Target** | EIA monthly total consumption (MMcf) |

### Two Forecast Scenarios

| Scenario | Description |
|---|---|
| **Full regressors** | All actual values used — optimistic upper bound on accuracy |
| **Static regressors** | Prices and storage frozen at last known value after train cutoff — realistic, since only weather (HDD/CDD) is forecastable in advance |

---

## Key Market Context

**Henry Hub** is a physical pipeline junction in Erath, Louisiana, where 13 interstate pipelines interconnect. It is the delivery point for NYMEX natural gas futures — the US benchmark price.

**The Thursday EIA storage report** (10:30am ET) is the dominant weekly price catalyst. A storage surprise of 20–30 Bcf routinely moves Henry Hub 3–5% intraday.

**HDD and CDD** replace a simple temperature input because US gas demand has two distinct seasonal peaks — winter heating (Nov–Mar, driven by HDD) and summer power burn (Jun–Sep, driven by CDD). A single temperature feature misses the summer peak entirely.

**Storage vs 5-year average** is the market's primary supply health metric. The EDA found that storage surplus/deficit explains ~24% of Henry Hub price variance on its own, with a 1-week lead — raw storage level explains only ~3%.

---

## Setup

```bash
# 1. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add API keys to .env
cp .env.example .env
# Fill in EIA_API_KEY and FRED_API_KEY

# 4. Fetch all source data (hits FRED, EIA, and Open-Meteo APIs)
python fetch_data.py
```

**Free API keys:**
- EIA: [api.eia.gov/registrations](https://api.eia.gov/registrations)
- FRED: [fred.stlouisfed.org/docs/api/api_key.html](https://fred.stlouisfed.org/docs/api/api_key.html)
- Open-Meteo: no key required

---

*AI was used in the making of this project as it is primarily for learning purposes.*

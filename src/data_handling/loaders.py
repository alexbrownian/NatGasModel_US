"""
src/data_handling/loaders.py

Two-layer ingestion for the US Natural Gas Model.

    Layer 1  fetch_*()             – hit live API, write to data/raw/ as CSV
    Layer 2  read_*()              – read from data/raw/, normalise, return pd.Series
    Assembly build_feature_matrix() – single aligned DataFrame ready for modelling
             get_static_regressors() – forward-fill prices/storage after cutoff
                                       (realistic forecast scenario)
"""

import os
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import requests
from dotenv import load_dotenv
from fredapi import Fred

load_dotenv()

EIA_KEY  = os.getenv("EIA_API_KEY")
FRED_KEY = os.getenv("FRED_API_KEY")
EIA_BASE = "https://api.eia.gov/v2"

# Five US cities weighted toward major consumption regions.
# Northeast + Midwest = heating demand; South = power burn / cooling demand.
CITIES = [
    {"name": "New York", "lat": 40.71, "lon": -74.01},
    {"name": "Chicago",  "lat": 41.88, "lon": -87.63},
    {"name": "Houston",  "lat": 29.76, "lon": -95.37},
    {"name": "Atlanta",  "lat": 33.75, "lon": -84.39},
    {"name": "Boston",   "lat": 42.36, "lon": -71.06},
]


# ── EIA v2 helper ─────────────────────────────────────────────────────────────

def _eia_fetch(route: str, frequency: str, facets: dict,
               data_col: str = "value", start: str = "2000-01-01") -> list:
    """
    Paginated EIA API v2 fetch. Returns list of raw record dicts.

    Args:
        route:     EIA v2 route, e.g. "natural-gas/stor/wkly"
        frequency: "daily" | "weekly" | "monthly"
        facets:    {facet_key: facet_value}, e.g. {"duoarea": "NUS"}
        data_col:  value column to request (almost always "value")
        start:     ISO date string for earliest period to fetch

    Returns:
        List of dicts, each containing at minimum "period" and data_col.

    To discover valid facet values for any route, call:
        GET https://api.eia.gov/v2/{route}/facet/{facet_name}/?api_key={key}
    """
    if not EIA_KEY:
        raise EnvironmentError(
            "EIA_API_KEY not set or expired, check .env file!"
        )

    url     = f"{EIA_BASE}/{route}/data/"
    records = []
    offset  = 0

    while True:
        params = [
            ("api_key",            EIA_KEY),
            ("frequency",          frequency),
            ("data[0]",            data_col),
            ("start",              start),
            ("sort[0][column]",    "period"),
            ("sort[0][direction]", "asc"),
            ("length",             "5000"),
            ("offset",             str(offset)),
        ]
        for k, v in facets.items():
            params.append((f"facets[{k}][]", v))

        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        payload  = resp.json()["response"]
        records.extend(payload["data"])
        total    = int(payload["total"])
        offset  += 5000
        if offset >= total:
            break

    return records


# ── Fetch layer (API -->  data/raw/) ─────────────────────────────────────────────

def fetch_henry_hub_prices(start: str = "2000-01-01") -> None:
    """
    Fetch Henry Hub natural gas daily spot price from FRED (series DHHNGSP). 
    D daily
    HH henry hub
    NGS natural gas spot
    P price
    FRED sources this directly from EIA —  better ai already parsed (fredapi lib wrapper)
    Saves to data/raw/henry_hub_daily.csv.
    """
    if not FRED_KEY:
        raise EnvironmentError("FRED_API_KEY not set. Add it to your .env file.")

    fred = Fred(api_key=FRED_KEY)
    s = fred.get_series("DHHNGSP", observation_start=start)
    s.index.name = "date"
    s.name = "henry_hub_price"
    s.to_frame().to_csv("data/raw/henry_hub_daily.csv")
    print(f"Henry Hub: {len(s)} records → data/raw/henry_hub_daily.csv")


def fetch_wti_prices(start: str = "2000-01-01") -> None:
    """
    Fetch WTI crude oil daily spot price from FRED (series DCOILWTICO).
    D daily
    COIL crude oi
    WTI west texas intermediate
    CO cushing oklahoma - physical delivery points 

    Saves to data/raw/wti_daily.csv.
    """
    if not FRED_KEY:
        raise EnvironmentError("FRED_API_KEY not set. Add it to your .env file.")

    fred = Fred(api_key=FRED_KEY)
    s = fred.get_series("DCOILWTICO", observation_start=start)
    s.index.name = "date"
    s.name = "wti_price"
    s.to_frame().to_csv("data/raw/wti_daily.csv")
    print(f"WTI crude: {len(s)} records → data/raw/wti_daily.csv")


def fetch_eia_storage(start: str = "2000-01-01") -> None:
    """
    Fetch EIA weekly natural gas storage, Lower 48 working gas (Bcf).
    EIA v2 route: natural-gas/stor/wkly

    lower 48 is everything besides Alaska 

    This is the single most market-moving series in US gas — the Thursday
    EIA storage report. "Storage surprise" (actual vs consensus) drives
    Henry Hub intraday moves of 2–5% or more.

    Saves to data/raw/eia_storage_weekly.csv.

    VERIFY facets at: https://api.eia.gov/v2/natural-gas/stor/wkly/facet/duoarea/?api_key={key}
    and:              https://api.eia.gov/v2/natural-gas/stor/wkly/facet/process/?api_key={key}
    """
    records = _eia_fetch(
        route     = "natural-gas/stor/wkly",
        frequency = "weekly",
        facets    = {"duoarea": "R48", "process": "SWO"},  # R48=Lower 48, SWO=total working gas
        data_col  = "value",
        start     = start,
    )
    df = (
        pd.DataFrame(records)[["period", "value"]]
        .rename(columns={"period": "date", "value": "storage_bcf"})
    )
    df["date"]        = pd.to_datetime(df["date"])
    df["storage_bcf"] = pd.to_numeric(df["storage_bcf"], errors="coerce")
    df = df.sort_values("date").set_index("date")
    df.to_csv("data/raw/eia_storage_weekly.csv")
    print(f"EIA storage: {len(df)} weekly records → data/raw/eia_storage_weekly.csv")


def fetch_eia_consumption(start: str = "2001-01-01") -> None:
    """
    Fetch EIA monthly US natural gas consumption, all sectors combined (MMcf) --> million cubic feet , roughly BTU
    EIA v2 route: natural-gas/cons/sum

    Note: EIA consumption data is published monthly with ~2 month lag.
    In build_feature_matrix() it is forward-filled to daily. This is the
    TARGET VARIABLE for all models.

    Saves to data/raw/eia_consumption_monthly.csv.

    VERIFY facets at: https://api.eia.gov/v2/natural-gas/cons/sum/facet/process/?api_key={key}
    """
    records = _eia_fetch(
        route     = "natural-gas/cons/sum",
        frequency = "monthly",
        facets    = {"duoarea": "NUS", "process": "VCS"},  # VCS=volume consumed, sum
        data_col  = "value",
        start     = start,
    )
    df = (
        pd.DataFrame(records)[["period", "value"]]
        .rename(columns={"period": "date", "value": "consumption_mmcf"})
    )
    df["date"]             = pd.to_datetime(df["date"])
    df["consumption_mmcf"] = pd.to_numeric(df["consumption_mmcf"], errors="coerce")
    df = df.sort_values("date").set_index("date")
    df.to_csv("data/raw/eia_consumption_monthly.csv")
    print(f"EIA consumption: {len(df)} monthly records → data/raw/eia_consumption_monthly.csv")


def fetch_temperatures(start: str = "2000-01-01", end: str = None) -> None:
    """
    Fetch daily mean temperature (°C) for 5 US cities via Open-Meteo (no key needed).
    Uses ERA5-Land reanalysis for history; ECMWF IFS forecast endpoint to fill
    the ~5-day gap ERA5 hasn't processed yet. Averages across all 5 cities to
    produce a single national consumption-proxy temperature series.

    Saves to data/raw/temperatures_daily.csv.
    """
    if end is None:
        end = datetime.today().strftime("%Y-%m-%d")

    # ERA5 archive lags ~5 days; fetch history up to 6 days ago to be safe
    era5_cutoff  = (datetime.today() - timedelta(days=6)).strftime("%Y-%m-%d")
    days_missing = (datetime.today() - datetime.strptime(era5_cutoff, "%Y-%m-%d")).days + 1

    city_series = []

    for city in CITIES:
        # ── Historical: ERA5-Land archive ─────────────────────────────────
        r_hist = requests.get(
            "https://archive-api.open-meteo.com/v1/archive",
            params={
                "latitude":   city["lat"],
                "longitude":  city["lon"],
                "start_date": start,
                "end_date":   era5_cutoff,
                "hourly":     "temperature_2m",
                "models":     "era5_land",
                "timezone":   "UTC",
            },
            timeout=60,
        )
        r_hist.raise_for_status()
        hist = pd.DataFrame(r_hist.json()["hourly"])
        hist["time"] = pd.to_datetime(hist["time"])
        hist = hist.set_index("time")["temperature_2m"]

        # ── Recent: ECMWF IFS (covers the ERA5 processing lag) ────────────
        r_recent = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude":      city["lat"],
                "longitude":     city["lon"],
                "hourly":        "temperature_2m",
                "models":        "ecmwf_ifs04",
                "past_days":     days_missing,
                "forecast_days": 1,
                "timezone":      "UTC",
            },
            timeout=30,
        )
        r_recent.raise_for_status()
        recent = pd.DataFrame(r_recent.json()["hourly"])
        recent["time"] = pd.to_datetime(recent["time"])
        recent = recent.set_index("time")["temperature_2m"]

        # ── Combine, deduplicate (keep most recent source), daily mean ─────
        combined = pd.concat([hist, recent])
        combined = combined[~combined.index.duplicated(keep="last")]
        daily    = combined.groupby(pd.Grouper(freq="D")).mean()
        city_series.append(daily.rename(city["name"]))
        print(f"  {city['name']}: {len(daily)} days")

    # Average across all 5 cities → single national temperature proxy
    temps_avg = pd.concat(city_series, axis=1).mean(axis=1).rename("temperature_c")
    temps_avg.index.name = "date"
    temps_avg.to_frame().to_csv("data/raw/temperatures_daily.csv")
    print(f"Temperatures: {len(temps_avg)} daily records → data/raw/temperatures_daily.csv")


def fetch_all(start: str = "2000-01-01") -> None:
    """Fetch all data sources and populate data/raw/. Run once to initialise."""
    os.makedirs("data/raw", exist_ok=True)
    print("── Henry Hub prices ─────────────────────────────────")
    fetch_henry_hub_prices(start)
    print("── WTI crude prices ─────────────────────────────────")
    fetch_wti_prices(start)
    print("── EIA weekly storage ───────────────────────────────")
    fetch_eia_storage(start)
    print("── EIA monthly consumption ──────────────────────────")
    fetch_eia_consumption(start)
    print("── Temperatures (5 US cities, Open-Meteo) ───────────")
    fetch_temperatures(start)
    print("── Done. All sources saved to data/raw/ ─────────────")


# ── Read layer (data/raw/ → pd.Series) ───────────────────────────────────────

def read_henry_hub_prices(file: str = "data/raw/henry_hub_daily.csv") -> pd.Series:
    """
    Read Henry Hub daily spot price. Reindexes to full calendar days and
    interpolates weekends/holidays
    Returns pd.Series named "henry_hub_price".
    """
    df  = pd.read_csv(file, index_col="date", parse_dates=True)
    s   = df["henry_hub_price"].astype(float)
    idx = pd.date_range(start=s.index.min(), end=s.index.max(), freq="D")
    return s.reindex(idx).interpolate(method="time").rename("henry_hub_price")

## these are a bit assumptions but are left for simplicitity
def read_wti_prices(file: str = "data/raw/wti_daily.csv") -> pd.Series:
    """
    Read WTI crude oil daily spot price. Reindexes and interpolates gaps.
    Returns pd.Series named "wti_price".

    ---- we assume no huge geopolitical events during the weekend (trump LOL) ----
    """
    df  = pd.read_csv(file, index_col="date", parse_dates=True)
    s   = df["wti_price"].astype(float)
    idx = pd.date_range(start=s.index.min(), end=s.index.max(), freq="D")
    return s.reindex(idx).interpolate(method="time").rename("wti_price") 
    #interpolate straight line between two surrounding real prices


def read_eia_storage(file: str = "data/raw/eia_storage_weekly.csv") -> pd.Series:
    """
    Read EIA weekly storage levels (Bcf). Forward-fills to daily — storage
    is assumed constant within the week until the next Thursday report. (limitation of EIA data set)
    Returns pd.Series named "storage_bcf".
    """
    df  = pd.read_csv(file, index_col="date", parse_dates=True)
    s   = df["storage_bcf"].astype(float).sort_index()
    idx = pd.date_range(start=s.index.min(), end=s.index.max(), freq="D")
    return s.reindex(idx).ffill().rename("storage_bcf") 
    #ffill last known value from when the EIA releases storages (thursday 10:30 ET)


def read_eia_consumption(file: str = "data/raw/eia_consumption_monthly.csv") -> pd.Series:
    """
    Read EIA monthly total consumption (MMcf). Forward-fills to daily.
    This is the TARGET VARIABLE for all models.
    Returns pd.Series named "consumption_mmcf".
    """
    df  = pd.read_csv(file, index_col="date", parse_dates=True)
    s   = df["consumption_mmcf"].astype(float).sort_index()
    idx = pd.date_range(start=s.index.min(), end=s.index.max(), freq="D")
    return s.reindex(idx).ffill().rename("consumption_mmcf")


def read_temperatures(file: str = "data/raw/temperatures_daily.csv") -> pd.Series:
    """
    Read daily mean temperature (°C, 5-city US average).
    Returns pd.Series named "temperature_c".
    """
    df = pd.read_csv(file, index_col="date", parse_dates=True)
    return df["temperature_c"].astype(float).sort_index().rename("temperature_c")


# ── Feature engineering ───────────────────────────────────────────────────────

def _compute_hdd_cdd(temp_c: pd.Series) -> pd.DataFrame:
    """
    Compute Heating Degree Days (HDD) and Cooling Degree Days (CDD) from
    daily mean temperature in °C using the US standard base of 65°F.

        HDD = max(0, 65 - T_F)   heating demand proxy  (winter)
        CDD = max(0, T_F - 65)   cooling/power burn proxy (summer)

    This is unique to the US gas market
    """
    temp_f = temp_c * 9 / 5 + 32
    hdd    = np.maximum(0.0, 65.0 - temp_f)
    cdd    = np.maximum(0.0, temp_f - 65.0)
    return pd.DataFrame({"hdd": hdd, "cdd": cdd}, index=temp_c.index)


# ── Assembly ──────────────────────────────────────────────────────────────────

def build_feature_matrix() -> pd.DataFrame:
    """
    Assemble the full aligned feature matrix from all local data sources.

    Columns:
        temperature_c     raw daily mean temp (°C) — kept for reference, not a model input
        hdd               heating degree days (base 65°F) — replaces temperature_capped
        cdd               cooling degree days (base 65°F) — captures summer power burn
        henry_hub_price   daily HH spot price (USD/MMBtu)
        wti_price         daily WTI crude (USD/bbl)
        storage_bcf       EIA weekly storage, forward-filled to daily (Bcf)
        weekend           1 = Saturday or Sunday, 0 = weekday
        consumption_mmcf  TARGET: EIA monthly consumption, forward-filled to daily (MMcf)

    Usage:
        df = build_feature_matrix().dropna()
        X  = df.drop(columns=["consumption_mmcf", "temperature_c"])
        y  = df["consumption_mmcf"]
    """
    temperature = read_temperatures()
    hdd_cdd     = _compute_hdd_cdd(temperature)
    henry_hub   = read_henry_hub_prices()
    wti         = read_wti_prices()
    storage     = read_eia_storage()
    consumption = read_eia_consumption()

    df = pd.concat(
        [temperature, hdd_cdd, henry_hub, wti, storage, consumption],
        axis=1,
    )
    df["weekend"] = (df.index.weekday >= 5).astype(float)
    return df.sort_index()


def get_static_regressors(df: pd.DataFrame, cutoff: str) -> pd.DataFrame:
    """
    Return a copy of the feature matrix with all non-weather regressors
    frozen (forward-filled) from the cutoff date onward.

    Simulates the realistic forecast scenario: in practice only weather
    (HDD/CDD) is forecastable; prices and storage are unknown post-cutoff.

    Args:
        df:     Output of build_feature_matrix()
        cutoff: ISO date string e.g. "2021-01-01"

    Returns:
        DataFrame with same shape; price/storage columns frozen post-cutoff.
    """
    weather_cols = {"temperature_c", "hdd", "cdd", "weekend", "consumption_mmcf"}
    price_cols   = [c for c in df.columns if c not in weather_cols]

    static = df.copy()
    static.loc[cutoff:, price_cols] = np.nan
    static[price_cols] = static[price_cols].ffill()
    return static
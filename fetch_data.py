"""
Run once to populate data/raw/ with all source data.
Execute from the project root: python fetch_data.py
"""
import sys
sys.path.insert(0, ".")

from src.data_handling.loaders import (
    fetch_wti_prices, fetch_eia_storage,
    fetch_eia_consumption, fetch_temperatures,
)
import os
os.makedirs("data/raw", exist_ok=True)

fetch_wti_prices(start="2000-01-01")
from src.data_handling.loaders import fetch_all

fetch_all(start="2000-01-01")
fetch_eia_consumption(start="2001-01-01")
fetch_temperatures(start="2000-01-01")

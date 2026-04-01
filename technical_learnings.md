# Technical Learnings — US NatGas Quant Project

> A reference guide of Python, pandas, and tooling concepts learned during this project.
> Add to this as new patterns are encountered.

---

## Python

### Lambda functions

A compact, unnamed function written on one line. Used when a function is short and only needed once.

```python
lambda x: x.rolling(5).mean()

# Equivalent to:
def some_function(x):
    return x.rolling(5).mean()
```

Syntax: `lambda <input> : <what to return>`

Most common uses: `.apply()`, `.transform()`, `.map()`, `sorted()`. The function is called by whatever receives it, not by you directly.

---

## pandas

### Creating a DataFrame from a list of dicts

`pd.DataFrame(records)` where `records` is a list of dicts turns each dict into a row. Column names come from the dict keys.

### Selecting and renaming columns

```python
df[["col_a", "col_b"]].rename(columns={"col_a": "new_name"})
```

### Setting the index

`.set_index("date")` promotes a column to the row label. Enables date-range slicing like `df["2020":"2024"]`.

### Type conversion

```python
pd.to_datetime(df["date"])                        # string → datetime
pd.to_numeric(df["value"], errors="coerce")       # string → float, bad values → NaN
series.astype(float)
```

`errors="coerce"` means bad values become NaN instead of raising an error.

### Resampling (changing frequency)

```python
series.resample("W-FRI").mean()    # daily → weekly, anchored to Friday
series.resample("M").sum()         # daily → monthly sum
```

Frequency anchoring matters — `"W"` defaults to Sunday. Use `"W-FRI"` to match EIA storage dates (Friday).

### Aligning two series with different dates — merge_asof

When two series have close but not identical dates, use `merge_asof` instead of `concat`:

```python
df = pd.merge_asof(
    left.sort_values("date"),
    right.sort_values("date"),
    on="date",
    tolerance=pd.Timedelta(days=3),
    direction="nearest",
)
```

Matches each row in `left` to the nearest row in `right` within the tolerance. Use this when frequencies differ (e.g. daily price resampled to weekly vs EIA weekly storage) — exact index join produces zero rows.

### Rolling calculations

```python
series.rolling(30).mean()           # 30-period rolling mean
series.rolling(30).std()            # 30-period rolling std dev (volatility proxy)
series.rolling(52).corr(other)      # rolling correlation between two series
```

First `n-1` values are NaN — not enough history to fill the window yet.

### Filling gaps — reindex + interpolate

```python
full_idx = pd.date_range(start=series.index.min(), end=series.index.max(), freq="D")
series = series.reindex(full_idx).interpolate(method="time")
```

`reindex` stamps existing values onto the full calendar and inserts NaN for missing dates. `interpolate(method="time")` fills NaN linearly, weighted by actual time distance between surrounding points.

### groupby + transform

`.transform()` applies a function to each group and returns results in the original row positions (same shape as input):

```python
storage_df.groupby("week")["storage_bcf"].transform(
    lambda x: x.rolling(5, min_periods=3).mean()
)
```

This computes a 5-year rolling average per week-of-year, placed back at the correct dates in the original DataFrame.

### Surplus / deficit vs seasonal average

```python
storage_df["week"]        = storage_df.index.isocalendar().week.astype(int)
weekly_mean               = storage_df.groupby("week")["storage_bcf"].mean()
storage_df["avg_bcf"]     = storage_df["week"].map(weekly_mean)
storage_df["surplus_bcf"] = storage_df["storage_bcf"] - storage_df["avg_bcf"]
```

Pattern: extract a time component (week, month) → compute group means → `.map()` back → subtract. Works for any seasonal deviation calculation.

### Useful inspection methods

```python
series.idxmax()                      # index label of the maximum value
series.idxmin()                      # index label of the minimum value
series[series == series.max()]       # row(s) where value equals max
df.tail(5)                           # last 5 rows as DataFrame
series.index[-5:]                    # last 5 index labels
series.describe()                    # count, mean, std, min, quartiles, max
series.isna().sum()                  # count of missing values
```

---

## matplotlib / plotting

### Multiple subplots — axes[0], axes[1]

`plt.subplots(nrows, ncols)` returns a figure and an array of Axes objects:

```python
fig, axes = plt.subplots(2, 1, figsize=(14, 7), sharex=True)
# axes[0] = top panel
# axes[1] = bottom panel
```

Draw on a specific panel explicitly:

```python
axes[0].plot(x, y, color="tab:blue", label="Price")
axes[0].set_ylabel("$/MMBtu")

axes[1].bar(x, z, color="tab:green")
axes[1].set_ylabel("Bcf")
```

`sharex=True` links zoom/pan across panels — use for time series where both panels share the same date range.

### Avoid mixing pandas .plot() with matplotlib .bar() on shared axes

`pandas.Series.plot(ax=axes[0])` installs its own date formatter that conflicts with `axes[1].bar()` on a shared axis — bars render invisibly or at wrong positions.

**Fix:** use pure matplotlib calls for both panels:

```python
axes[0].plot(series.index, series.values, ...)   # not series.plot(ax=axes[0])
axes[1].bar(other.index, other.values, ...)
```

### Dual y-axis chart

```python
fig, ax1 = plt.subplots(figsize=(14, 4))
ax2 = ax1.twinx()

ax1.plot(df.index, df["price"],   color="tab:blue",  label="Price")
ax2.plot(df.index, df["storage"], color="tab:green", label="Storage")

ax1.set_ylabel("$/MMBtu", color="tab:blue")
ax2.set_ylabel("Bcf",     color="tab:green")

# Combine both legends into one
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")
```

### Colouring bars conditionally

```python
# np.where — watch out for NaN (NaN >= 0 is False, so NaN bars get the "false" colour)
color = np.where(series >= 0, "tab:green", "tab:red")

# Safer: list comprehension, and dropna() first
sc = series.dropna()
colors = ["tab:green" if v >= 0 else "tab:red" for v in sc.values]
```

---

## Tooling & Environment

### Notebook project root detection (cross-platform)

Hard-coded absolute paths break on different machines. Use this pattern instead:

```python
from pathlib import Path

project_root = Path.cwd().resolve()
if not (project_root / "data" / "raw").exists():
    for parent in [project_root, *project_root.parents]:
        if (parent / "data" / "raw").exists() and (parent / "notebooks").exists():
            project_root = parent
            break
```

Walks up the directory tree until it finds a folder containing both `data/raw/` and `notebooks/` — the project root fingerprint. Works regardless of where Jupyter starts the kernel.

### NotebookEdit tool — use single quotes

The NotebookEdit tool escapes double quotes to `\"` inside cell source, which Python reads as a line continuation character and errors:

```
SyntaxError: unexpected character after line continuation character
```

**Fix:** use single quotes `'` throughout cells written via NotebookEdit. Functionally identical in Python.

---

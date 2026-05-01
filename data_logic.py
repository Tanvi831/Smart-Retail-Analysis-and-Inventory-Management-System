"""
Member 1 — Data preprocessing, inventory logic,
forecast vs actual calculation, seasonal grouping.

Dataset columns:
  Date, Store ID, Product ID, Category, Region,
  Inventory Level, Units Sold, Units Ordered,
  Demand Forecast, Price, Discount,
  Weather Condition, Holiday/Promotion,
  Competitor Pricing, Seasonality
"""

import pandas as pd
import numpy as np
from pathlib import Path

# ─────────────────────────────────────────────
# 1. LOAD & PREPROCESS
# ─────────────────────────────────────────────

def load_data(filepath: str = "retail_store_inventory.csv") -> pd.DataFrame:
    """Load CSV, fix dtypes, drop bad rows."""
    df = pd.read_csv(filepath)

    # Parse date
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=False, errors="coerce")

    # Drop the one null Date row and one null Competitor Pricing row
    df.dropna(subset=["Date"], inplace=True)

    # Fill missing Competitor Pricing with product median
    df["Competitor Pricing"] = df.groupby("Product ID")["Competitor Pricing"] \
                                  .transform(lambda x: x.fillna(x.median()))

    # Enforce dtypes
    int_cols = ["Inventory Level", "Units Sold", "Units Ordered",
                "Discount", "Holiday/Promotion"]
    for c in int_cols:
        df[c] = df[c].astype(int)

    df["Price"]              = df["Price"].astype(float)
    df["Demand Forecast"]    = df["Demand Forecast"].astype(float)
    df["Competitor Pricing"] = df["Competitor Pricing"].astype(float)

    # Derived columns
    df["Year"]       = df["Date"].dt.year
    df["Month"]      = df["Date"].dt.month
    df["Month Name"] = df["Date"].dt.strftime("%b")
    df["Week"]       = df["Date"].dt.isocalendar().week.astype(int)
    df["Revenue"]    = df["Units Sold"] * df["Price"] * (1 - df["Discount"] / 100)

    # Sort for time-series work
    df.sort_values(["Store ID", "Product ID", "Date"], inplace=True)
    df.reset_index(drop=True, inplace=True)

    return df


# ─────────────────────────────────────────────
# 2. INVENTORY LOGIC
# ─────────────────────────────────────────────

REORDER_FACTOR   = 0.25   # reorder when stock < 25 % of max
CRITICAL_FACTOR  = 0.10   # critical when stock < 10 % of max
OVERSTOCK_FACTOR = 0.85   # overstock when stock > 85 % of max

def add_inventory_flags(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds:
      - Stock Status   : 'Critical' | 'Low' | 'Adequate' | 'Overstock'
      - Reorder Flag   : 1 / 0
      - Days of Stock  : estimated days until stockout
      - Suggested Order: units to bring stock to max level
    """
    df = df.copy()

    max_stock = 500   # dataset max
    reorder_threshold  = max_stock * REORDER_FACTOR     # 125
    critical_threshold = max_stock * CRITICAL_FACTOR    # 50
    overstock_threshold = max_stock * OVERSTOCK_FACTOR  # 425

    def status(level):
        if level <= critical_threshold:
            return "Critical"
        elif level <= reorder_threshold:
            return "Low"
        elif level >= overstock_threshold:
            return "Overstock"
        return "Adequate"

    df["Stock Status"]   = df["Inventory Level"].apply(status)
    df["Reorder Flag"]   = (df["Inventory Level"] <= reorder_threshold).astype(int)

    # Daily burn rate — use 7-day rolling avg of Units Sold per product+store
    df["Avg Daily Sales"] = (
        df.groupby(["Store ID", "Product ID"])["Units Sold"]
          .transform(lambda x: x.rolling(7, min_periods=1).mean())
    )

    # Days of stock = inventory / avg daily sales (avoid div/0)
    df["Days of Stock"] = np.where(
        df["Avg Daily Sales"] > 0,
        (df["Inventory Level"] / df["Avg Daily Sales"]).round(1),
        np.inf
    )

    # Suggested reorder quantity to reach max_stock
    df["Suggested Order"] = np.where(
        df["Reorder Flag"] == 1,
        (max_stock - df["Inventory Level"]).clip(lower=0),
        0
    )

    return df


def get_low_stock_products(df: pd.DataFrame,
                            n: int = 10) -> pd.DataFrame:
    """Return the n most critical products (latest snapshot per product+store)."""
    latest = (
        df.sort_values("Date")
          .groupby(["Store ID", "Product ID"])
          .last()
          .reset_index()
    )
    low = latest[latest["Reorder Flag"] == 1].copy()
    low = low.sort_values("Inventory Level").head(n)
    return low[["Store ID", "Product ID", "Category", "Region",
                "Inventory Level", "Stock Status", "Days of Stock",
                "Suggested Order"]]


# ─────────────────────────────────────────────
# 3. FORECAST VS ACTUAL
# ─────────────────────────────────────────────

def add_forecast_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds per-row:
      - Forecast Error : Demand Forecast - Units Sold
      - Abs Error      : |Forecast Error|
      - MAPE           : absolute percentage error (0-100)
      - Forecast Bias  : positive = over-forecast, negative = under-forecast
    """
    df = df.copy()
    df["Forecast Error"] = df["Demand Forecast"] - df["Units Sold"]
    df["Abs Error"]      = df["Forecast Error"].abs()
    df["MAPE"]           = np.where(
        df["Units Sold"] > 0,
        (df["Abs Error"] / df["Units Sold"] * 100).round(2),
        np.nan
    )
    df["Forecast Bias"]  = df["Forecast Error"].apply(
        lambda e: "Over" if e > 0 else ("Under" if e < 0 else "Exact")
    )
    return df


def forecast_accuracy_summary(df: pd.DataFrame,
                               group_by: str = "Category") -> pd.DataFrame:
    """
    Aggregate MAPE and bias by a grouping column.
    group_by: 'Category' | 'Region' | 'Store ID' | 'Seasonality' | 'Month Name'
    """
    summary = (
        df.groupby(group_by)
          .agg(
              Avg_MAPE    =("MAPE",           "mean"),
              Accuracy_Pct=("MAPE",           lambda x: round(100 - x.mean(), 2)),
              Over_Pct    =("Forecast Bias",  lambda x: round((x=="Over").mean()*100, 1)),
              Under_Pct   =("Forecast Bias",  lambda x: round((x=="Under").mean()*100, 1)),
              Total_Rows  =("Units Sold",     "count"),
          )
          .round(2)
          .reset_index()
          .sort_values("Accuracy_Pct", ascending=False)
    )
    return summary


# ─────────────────────────────────────────────
# 4. SEASONAL GROUPING
# ─────────────────────────────────────────────

SEASON_ORDER = ["Spring", "Summer", "Autumn", "Winter"]

def seasonal_summary(df: pd.DataFrame,
                     metric: str = "Units Sold") -> pd.DataFrame:
    """
    Returns pivot: rows = Season, cols = Category,
    values = sum of `metric`.
    """
    pivot = (
        df.groupby(["Seasonality", "Category"])[metric]
          .sum()
          .unstack(fill_value=0)
    )
    # Enforce season order
    pivot = pivot.reindex(
        [s for s in SEASON_ORDER if s in pivot.index]
    )
    return pivot


def seasonal_kpis(df: pd.DataFrame) -> pd.DataFrame:
    """Per-season totals: revenue, units sold, avg inventory, avg MAPE."""
    return (
        df.groupby("Seasonality")
          .agg(
              Total_Revenue   =("Revenue",         "sum"),
              Total_Units_Sold=("Units Sold",       "sum"),
              Avg_Inventory   =("Inventory Level",  "mean"),
              Avg_MAPE        =("MAPE",             "mean"),
              Promo_Days      =("Holiday/Promotion","sum"),
          )
          .round(2)
          .reindex([s for s in SEASON_ORDER if s in df["Seasonality"].unique()])
          .reset_index()
    )


def monthly_trend(df: pd.DataFrame,
                  metric: str = "Revenue") -> pd.DataFrame:
    """Monthly aggregated metric, sorted chronologically."""
    return (
        df.groupby(["Year", "Month", "Month Name"])[metric]
          .sum()
          .reset_index()
          .sort_values(["Year", "Month"])
          .assign(Period=lambda x: x["Month Name"] + " " + x["Year"].astype(str))
          .reset_index(drop=True)
    )


# ─────────────────────────────────────────────
# 5. CONVENIENCE — run full pipeline
# ─────────────────────────────────────────────

def build_full_dataset(filepath: str = "retail_store_inventory.csv") -> pd.DataFrame:
    """
    One-call function: load → inventory flags → forecast metrics.
    Returns enriched DataFrame used by all other members.
    """
    df = load_data(filepath)
    df = add_inventory_flags(df)
    df = add_forecast_metrics(df)
    return df


# ─────────────────────────────────────────────
# Quick smoke-test (run: python member1_data_logic.py)
# ─────────────────────────────────────────────
if __name__ == "__main__":
    df = build_full_dataset("retail_store_inventory.csv")
    print("Shape:", df.shape)
    print("\nStock status counts:\n", df["Stock Status"].value_counts())
    print("\nSeasonal KPIs:\n", seasonal_kpis(df).to_string(index=False))
    print("\nForecast accuracy by category:\n",
          forecast_accuracy_summary(df).to_string(index=False))
    print("\nLow stock products:\n",
          get_low_stock_products(df).to_string(index=False))

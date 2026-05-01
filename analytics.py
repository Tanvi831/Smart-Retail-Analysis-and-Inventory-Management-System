"""
Member 3 — Analytics & Visualization.

Covers:
  - Sales vs inventory graphs
  - Category analysis
  - Region analysis
  - Seasonal trends
  - Low stock detection & alerts

All functions receive an enriched DataFrame from Member 1's
build_full_dataset() and return Plotly figures ready for st.plotly_chart().
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ── Shared colour palette ──────────────────────────────────────────
PALETTE = {
    "blue":   "#378ADD",
    "teal":   "#1D9E75",
    "amber":  "#EF9F27",
    "coral":  "#D85A30",
    "purple": "#7F77DD",
    "red":    "#E24B4A",
    "green":  "#639922",
    "gray":   "#888780",
}
CAT_COLORS = [PALETTE["blue"], PALETTE["teal"], PALETTE["amber"],
              PALETTE["coral"], PALETTE["purple"]]
REG_COLORS = [PALETTE["blue"], PALETTE["teal"], PALETTE["amber"], PALETTE["coral"]]
SEA_COLORS = [PALETTE["teal"], PALETTE["amber"], PALETTE["coral"], PALETTE["blue"]]

PLOTLY_BASE = dict(
    plot_bgcolor  = "rgba(0,0,0,0)",
    paper_bgcolor = "rgba(0,0,0,0)",
    font          = dict(family="Arial, sans-serif", size=12, color="#444441"),
    margin        = dict(l=10, r=10, t=40, b=10),
    hoverlabel    = dict(bgcolor="white", font_size=12),
)


def _apply_base(fig: go.Figure, title: str = "", height: int = 360) -> go.Figure:
    fig.update_layout(**PLOTLY_BASE, title=dict(text=title, font_size=14),
                      height=height)
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor="rgba(0,0,0,0.06)", zeroline=False)
    return fig


# ─────────────────────────────────────────────────────────────────
# 1.  SALES vs INVENTORY
# ─────────────────────────────────────────────────────────────────

def fig_sales_vs_inventory(df: pd.DataFrame,
                            product_id: str = None,
                            store_id:   str = None,
                            freq:       str = "W") -> go.Figure:
    """
    Dual-axis line chart: Units Sold (bars) + Inventory Level (line).
    freq: 'D' daily | 'W' weekly | 'ME' monthly
    """
    sub = df.copy()
    if product_id: sub = sub[sub["Product ID"] == product_id]
    if store_id:   sub = sub[sub["Store ID"]   == store_id]

    agg = (
        sub.groupby(pd.Grouper(key="Date", freq=freq))
           .agg(units_sold     =("Units Sold",      "sum"),
                inventory_level=("Inventory Level", "mean"),
                revenue        =("Revenue",         "sum"))
           .reset_index()
    )

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(x=agg["Date"], y=agg["units_sold"],
               name="Units sold", marker_color=PALETTE["blue"],
               opacity=0.75),
        secondary_y=False
    )
    fig.add_trace(
        go.Scatter(x=agg["Date"], y=agg["inventory_level"],
                   name="Avg inventory", mode="lines",
                   line=dict(color=PALETTE["amber"], width=2)),
        secondary_y=True
    )
    fig.update_yaxes(title_text="Units sold",      secondary_y=False)
    fig.update_yaxes(title_text="Inventory level", secondary_y=True,
                     showgrid=False)
    fig = _apply_base(fig, "Sales vs inventory level", height=340)
    fig.update_layout(legend=dict(orientation="h", y=-0.2),
                      barmode="overlay")
    return fig


def fig_forecast_vs_actual(df: pd.DataFrame,
                            product_id: str = None,
                            freq:       str = "W") -> go.Figure:
    """
    Line chart: Demand Forecast vs actual Units Sold.
    Shaded area between them shows forecast error.
    """
    sub = df.copy()
    if product_id: sub = sub[sub["Product ID"] == product_id]

    agg = (
        sub.groupby(pd.Grouper(key="Date", freq=freq))
           .agg(actual  =("Units Sold",      "sum"),
                forecast=("Demand Forecast", "sum"),
                mape    =("MAPE",            "mean"))
           .reset_index()
    )

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=pd.concat([agg["Date"], agg["Date"].iloc[::-1]]),
        y=pd.concat([agg["forecast"], agg["actual"].iloc[::-1]]),
        fill="toself", fillcolor="rgba(55,138,221,0.08)",
        line=dict(color="rgba(0,0,0,0)"), showlegend=False,
        name="Error band"
    ))
    fig.add_trace(go.Scatter(
        x=agg["Date"], y=agg["actual"],
        name="Actual sales", line=dict(color=PALETTE["blue"], width=2)
    ))
    fig.add_trace(go.Scatter(
        x=agg["Date"], y=agg["forecast"],
        name="Predicted sales", line=dict(color=PALETTE["coral"], width=2)
    ))
    return _apply_base(fig, "Demand forecast vs actual sales", height=320)


# ─────────────────────────────────────────────────────────────────
# 2.  CATEGORY ANALYSIS
# ─────────────────────────────────────────────────────────────────

def fig_category_revenue(df: pd.DataFrame) -> go.Figure:
    """Horizontal bar — total revenue per category."""
    cat = (
        df.groupby("Category")["Revenue"].sum()
          .sort_values().reset_index()
    )
    fig = go.Figure(go.Bar(
        x=cat["Revenue"], y=cat["Category"],
        orientation="h",
        marker_color=CAT_COLORS[:len(cat)],
        text=cat["Revenue"].apply(lambda v: f"₹{v:,.0f}"),
        textposition="outside"
    ))
    return _apply_base(fig, "Revenue by category", height=280)


def fig_category_units_trend(df: pd.DataFrame, freq: str = "ME") -> go.Figure:
    """Multi-line trend: units sold per category over time."""
    agg = (
        df.groupby(["Category", pd.Grouper(key="Date", freq=freq)])
          ["Units Sold"].sum().reset_index()
    )
    fig = go.Figure()
    for i, cat in enumerate(df["Category"].unique()):
        sub = agg[agg["Category"] == cat]
        fig.add_trace(go.Scatter(
            x=sub["Date"], y=sub["Units Sold"],
            name=cat, mode="lines",
            line=dict(color=CAT_COLORS[i % len(CAT_COLORS)], width=2)
        ))
    fig.update_layout(legend=dict(orientation="h", y=-0.25))
    return _apply_base(fig, "Monthly units sold by category", height=340)


def fig_category_mape(df: pd.DataFrame) -> go.Figure:
    """Bar chart: forecast accuracy (100 - MAPE) per category."""
    acc = (
        df.groupby("Category")["MAPE"].mean()
          .reset_index()
          .assign(Accuracy=lambda x: (100 - x["MAPE"]).round(1))
          .sort_values("Accuracy", ascending=False)
    )
    colors = [PALETTE["teal"] if v >= 85 else
              PALETTE["amber"] if v >= 70 else
              PALETTE["red"] for v in acc["Accuracy"]]
    fig = go.Figure(go.Bar(
        x=acc["Category"], y=acc["Accuracy"],
        marker_color=colors,
        text=acc["Accuracy"].apply(lambda v: f"{v}%"),
        textposition="outside"
    ))
    fig.add_hline(y=85, line_dash="dot", line_color=PALETTE["amber"],
                  annotation_text="85% target")
    fig.update_yaxes(range=[0, 110])
    return _apply_base(fig, "Forecast accuracy (%) by category", height=300)


# ─────────────────────────────────────────────────────────────────
# 3.  REGION ANALYSIS
# ─────────────────────────────────────────────────────────────────

def fig_region_revenue_pie(df: pd.DataFrame) -> go.Figure:
    """Donut chart — revenue share per region."""
    reg = df.groupby("Region")["Revenue"].sum().reset_index()
    fig = go.Figure(go.Pie(
        labels=reg["Region"], values=reg["Revenue"],
        hole=0.5,
        marker_colors=REG_COLORS,
        textinfo="label+percent",
        hovertemplate="Region: %{label}<br>Revenue: ₹%{value:,.0f}<extra></extra>"
    ))
    return _apply_base(fig, "Revenue share by region", height=300)


def fig_region_sales_bar(df: pd.DataFrame) -> go.Figure:
    """Grouped bar — units sold per region per category."""
    agg = df.groupby(["Region", "Category"])["Units Sold"].sum().reset_index()
    fig = go.Figure()
    for i, cat in enumerate(df["Category"].unique()):
        sub = agg[agg["Category"] == cat]
        fig.add_trace(go.Bar(
            x=sub["Region"], y=sub["Units Sold"],
            name=cat, marker_color=CAT_COLORS[i % len(CAT_COLORS)]
        ))
    fig.update_layout(barmode="group",
                      legend=dict(orientation="h", y=-0.25))
    return _apply_base(fig, "Units sold by region & category", height=340)


# ─────────────────────────────────────────────────────────────────
# 4.  SEASONAL TRENDS
# ─────────────────────────────────────────────────────────────────

SEASON_ORDER = ["Spring", "Summer", "Autumn", "Winter"]


def fig_seasonal_revenue(df: pd.DataFrame) -> go.Figure:
    """Bar chart — total revenue by season."""
    sea = (
        df.groupby("Seasonality")["Revenue"].sum()
          .reindex([s for s in SEASON_ORDER if s in df["Seasonality"].unique()])
          .reset_index()
    )
    fig = go.Figure(go.Bar(
        x=sea["Seasonality"], y=sea["Revenue"],
        marker_color=SEA_COLORS[:len(sea)],
        text=sea["Revenue"].apply(lambda v: f"₹{v:,.0f}"),
        textposition="outside"
    ))
    return _apply_base(fig, "Total revenue by season", height=300)


def fig_seasonal_weather_impact(df: pd.DataFrame) -> go.Figure:
    """Grouped bar: avg units sold per weather condition per season."""
    agg = df.groupby(["Seasonality", "Weather Condition"])["Units Sold"].mean().reset_index()
    fig = go.Figure()
    weather_colors = {"Sunny": PALETTE["amber"], "Rainy": PALETTE["blue"],
                      "Cloudy": PALETTE["gray"],  "Snowy": PALETTE["purple"]}
    for wc, col in weather_colors.items():
        sub = agg[agg["Weather Condition"] == wc]
        fig.add_trace(go.Bar(
            x=[s for s in SEASON_ORDER if s in sub["Seasonality"].values],
            y=[sub[sub["Seasonality"] == s]["Units Sold"].values[0]
               if s in sub["Seasonality"].values else 0
               for s in SEASON_ORDER if s in df["Seasonality"].unique()],
            name=wc, marker_color=col
        ))
    fig.update_layout(barmode="group",
                      legend=dict(orientation="h", y=-0.25))
    return _apply_base(fig, "Avg sales by weather & season", height=320)


# ─────────────────────────────────────────────────────────────────
# 5.  LOW STOCK DETECTION
# ─────────────────────────────────────────────────────────────────

LOW_STOCK_THRESHOLD  = 125   # 25% of 500 max
CRIT_STOCK_THRESHOLD = 50    # 10% of 500 max


def get_current_stock_snapshot(df: pd.DataFrame) -> pd.DataFrame:
    """Latest record per Store×Product — used for live stock status."""
    latest = (
        df.sort_values("Date")
          .groupby(["Store ID", "Product ID"])
          .last()
          .reset_index()
    )
    latest["Status Color"] = latest["Stock Status"].map({
        "Critical":  "🔴",
        "Low":       "🟡",
        "Adequate":  "🟢",
        "Overstock": "🔵",
    })
    return latest


def fig_low_stock_bar(df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    """
    Horizontal bar chart of the most under-stocked products (latest snapshot).
    Red bars = critical, amber = low.
    """
    snap = get_current_stock_snapshot(df)
    low  = (
        snap[snap["Stock Status"].isin(["Critical", "Low"])]
        .sort_values("Inventory Level")
        .head(top_n)
    )
    colors = [PALETTE["red"] if s == "Critical" else PALETTE["amber"]
              for s in low["Stock Status"]]
    fig = go.Figure(go.Bar(
        x=low["Inventory Level"],
        y=low["Product ID"] + " · " + low["Store ID"],
        orientation="h",
        marker_color=colors,
        text=low["Inventory Level"].astype(str) + " units",
        textposition="outside",
        customdata=np.stack([low["Category"], low["Days of Stock"].round(1),
                             low["Suggested Order"]], axis=-1),
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Category: %{customdata[0]}<br>"
            "Inventory: %{x} units<br>"
            "Days of stock: %{customdata[1]}<br>"
            "Suggested order: %{customdata[2]}<extra></extra>"
        )
    ))
    fig.add_vline(x=LOW_STOCK_THRESHOLD, line_dash="dot",
                  line_color=PALETTE["amber"],
                  annotation_text="Reorder threshold (125)")
    fig.add_vline(x=CRIT_STOCK_THRESHOLD, line_dash="dot",
                  line_color=PALETTE["red"],
                  annotation_text="Critical (50)")
    return _apply_base(fig, f"Low stock alert — bottom {top_n} products",
                       height=max(280, top_n * 26))


def fig_stock_status_donut(df: pd.DataFrame) -> go.Figure:
    """Donut chart showing proportion of records by stock status."""
    snap   = get_current_stock_snapshot(df)
    counts = snap["Stock Status"].value_counts().reset_index()
    counts.columns = ["Status", "Count"]
    color_map = {"Critical": PALETTE["red"],   "Low":      PALETTE["amber"],
                 "Adequate": PALETTE["teal"],  "Overstock": PALETTE["blue"]}
    fig = go.Figure(go.Pie(
        labels=counts["Status"], values=counts["Count"],
        hole=0.55,
        marker_colors=[color_map.get(s, PALETTE["gray"])
                       for s in counts["Status"]],
        textinfo="label+percent"
    ))
    return _apply_base(fig, "Stock status distribution", height=300)


def get_low_stock_alert_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns a styled DataFrame of low/critical products for display.
    Suitable for st.dataframe() with colour highlighting.
    """
    snap   = get_current_stock_snapshot(df)
    alerts = snap[snap["Reorder Flag"] == 1].copy()
    alerts = alerts[[
        "Status Color", "Store ID", "Product ID", "Category", "Region",
        "Inventory Level", "Stock Status", "Days of Stock",
        "Avg Daily Sales", "Suggested Order"
    ]].sort_values(["Stock Status", "Inventory Level"])
    alerts.columns = [
        " ", "Store", "Product", "Category", "Region",
        "Stock", "Status", "Days Left",
        "Avg Daily Sales", "Suggested Order"
    ]
    alerts["Days Left"]       = alerts["Days Left"].round(1)
    alerts["Avg Daily Sales"] = alerts["Avg Daily Sales"].round(1)
    return alerts.reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────
# 6.  KPI SUMMARY HELPERS  (used by Member 4 for metric cards)
# ─────────────────────────────────────────────────────────────────

def compute_kpis(df: pd.DataFrame) -> dict:
    """Return a dict of headline KPI values for the dashboard."""
    snap      = get_current_stock_snapshot(df)
    total_rev = df["Revenue"].sum()
    prev_rev  = df[df["Date"] < df["Date"].max() - pd.Timedelta(30, "d")]["Revenue"].sum()
    rev_delta = ((total_rev - prev_rev) / prev_rev * 100) if prev_rev else 0

    return {
        "total_revenue":      round(total_rev, 2),
        "revenue_delta_pct":  round(rev_delta, 1),
        "total_units_sold":   int(df["Units Sold"].sum()),
        "reorder_alerts":     int(snap["Reorder Flag"].sum()),
        "critical_products":  int((snap["Stock Status"] == "Critical").sum()),
        "avg_inventory":      round(df["Inventory Level"].mean(), 1),
        "overall_accuracy":   round(100 - df["MAPE"].mean(), 1),
        "total_products":     df["Product ID"].nunique(),
        "total_stores":       df["Store ID"].nunique(),
        "overstock_products": int((snap["Stock Status"] == "Overstock").sum()),
    }

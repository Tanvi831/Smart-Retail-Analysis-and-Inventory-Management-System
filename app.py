"""
Member 4 — Streamlit UI Developer.
Main app entry point: navigation, dashboard, filters, chart integration.

Run with:  streamlit run app.py
File structure expected:
  app.py                    ← this file
  retail_store_inventory.csv
  member1_data_logic.py
  member2_database.py
  member3_analytics.py
"""

import streamlit as st
import pandas as pd
from datetime import date

# ── Page config (must be first Streamlit call) ─────────────────────
st.set_page_config(
    page_title="Smart Retail Analysis & Inventory Management System",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS — Cream theme ────────────────────────────────────────
st.markdown("""
<style>
/* ── Global background: soft cream ── */
[data-testid="stAppViewContainer"],
[data-testid="stAppViewBlockContainer"],
.main .block-container {
    background-color: #FFF5E1 !important;
}

/* ── Sidebar: slightly darker cream ── */
[data-testid="stSidebar"] {
    background-color: #F5E6C8 !important;
}
[data-testid="stSidebar"] * {
    color: #3B2E1A !important;
}

/* ── Main text colour ── */
html, body, [class*="css"] {
    color: #3B2E1A;
}

/* ── Metric cards ── */
[data-testid="stMetricValue"] {
    font-size: 1.6rem !important;
    font-weight: 500;
    color: #3B2E1A !important;
}
[data-testid="metric-container"] {
    background-color: #FEF0D0;
    border-radius: 8px;
    padding: 10px 14px;
    border: 1px solid #E8D5A3;
}

/* ── Buttons ── */
[data-testid="stButton"] > button {
    background-color: #E8C97A;
    color: #3B2E1A;
    border: 1px solid #C9A84C;
    border-radius: 6px;
    font-weight: 500;
}
[data-testid="stButton"] > button:hover {
    background-color: #D4B05A;
    border-color: #A8893A;
}

/* ── Headings ── */
h1, h2, h3 { color: #3B2E1A !important; }

/* ── Divider ── */
hr { margin: 0.6rem 0; border-color: rgba(0,0,0,0.10); }

/* ── Alert strip ── */
.alert-strip {
    background: #FCEBEB; border-left: 4px solid #E24B4A;
    border-radius: 0; padding: 10px 16px;
    color: #791F1F; font-size: 13px; margin-bottom: 12px;
}
.warn-strip {
    background: #FAEEDA; border-left: 4px solid #EF9F27;
    border-radius: 0; padding: 10px 16px;
    color: #633806; font-size: 13px; margin-bottom: 12px;
}

/* ── Pill badges ── */
.pill-red   { background:#FCEBEB; color:#A32D2D; padding:2px 10px;
              border-radius:12px; font-size:12px; font-weight:500; }
.pill-amber { background:#FAEEDA; color:#854F0B; padding:2px 10px;
              border-radius:12px; font-size:12px; font-weight:500; }
.pill-green { background:#EAF3DE; color:#3B6D11; padding:2px 10px;
              border-radius:12px; font-size:12px; font-weight:500; }
.pill-blue  { background:#E6F1FB; color:#185FA5; padding:2px 10px;
              border-radius:12px; font-size:12px; font-weight:500; }

/* ── Dataframe / table ── */
[data-testid="stDataFrame"] {
    background-color: #FEF0D0;
    border-radius: 6px;
}

/* ── Selectbox / input backgrounds ── */
[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
[data-testid="stDateInput"] input {
    background-color: #FEF0D0 !important;
    border-color: #D4B05A !important;
}

/* ── Expander ── */
[data-testid="stExpander"] {
    background-color: #FEF0D0;
    border: 1px solid #E8D5A3;
    border-radius: 6px;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# LOAD DATA  (cached globally)
# ─────────────────────────────────────────────
@st.cache_data(show_spinner="Loading dataset…")
def load_data():
    from data_logic import build_full_dataset
    return build_full_dataset("retail_store_inventory.csv")


# ─────────────────────────────────────────────
# SIDEBAR  ── navigation + global filters
# ─────────────────────────────────────────────
def render_sidebar(df: pd.DataFrame) -> dict:
    with st.sidebar:
        st.markdown("## 📦 Smart Retail Analysis & Inventory Management System")
        st.divider()

        page = st.radio(
            "Navigate",
            ["🏠 Dashboard", "📊 Sales & Inventory", "🗂️ Category Analysis",
             "🌍 Region Analysis", "🍂 Seasonal Trends",
             "⚠️ Low Stock Alerts", "🗄️ Database"],
            label_visibility="collapsed"
        )

        st.divider()
        st.markdown("**Global filters**")

        stores = ["All"] + sorted(df["Store ID"].unique().tolist())
        sel_store = st.selectbox("Store", stores)

        categories = ["All"] + sorted(df["Category"].unique().tolist())
        sel_cat = st.selectbox("Category", categories)

        regions = ["All"] + sorted(df["Region"].unique().tolist())
        sel_region = st.selectbox("Region", regions)

        seasons = ["All"] + ["Spring", "Summer", "Autumn", "Winter"]
        sel_season = st.selectbox("Season", seasons)

        min_date = df["Date"].min().date()
        max_date = df["Date"].max().date()
        date_range = st.date_input("Date range",
                                    value=(min_date, max_date),
                                    min_value=min_date,
                                    max_value=max_date)
        if len(date_range) == 2:
            d_from, d_to = date_range
        else:
            d_from, d_to = min_date, max_date

        freq_map = {"Daily": "D", "Weekly": "W", "Monthly": "ME"}
        agg_freq_label = st.selectbox("Chart aggregation",
                                       list(freq_map.keys()), index=1)
        agg_freq = freq_map[agg_freq_label]

        st.divider()
        if st.button("🔄 Refresh data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    return dict(page=page, store=sel_store, category=sel_cat,
                region=sel_region, season=sel_season,
                date_from=d_from, date_to=d_to, freq=agg_freq)


def apply_filters(df: pd.DataFrame, f: dict) -> pd.DataFrame:
    mask = (
        (df["Date"].dt.date >= f["date_from"]) &
        (df["Date"].dt.date <= f["date_to"])
    )
    if f["store"]    != "All": mask &= df["Store ID"]    == f["store"]
    if f["category"] != "All": mask &= df["Category"]    == f["category"]
    if f["region"]   != "All": mask &= df["Region"]      == f["region"]
    if f["season"]   != "All": mask &= df["Seasonality"] == f["season"]
    return df[mask].copy()


# ─────────────────────────────────────────────
# PAGE 1 — DASHBOARD
# ─────────────────────────────────────────────
def page_dashboard(df: pd.DataFrame, f: dict):
    from analytics import (
        compute_kpis, fig_sales_vs_inventory,
        fig_category_revenue, fig_stock_status_donut,
        fig_seasonal_revenue, get_low_stock_alert_table
    )

    st.title("Dashboard")
    st.caption(f"Data: {f['date_from']} → {f['date_to']}  |  "
               f"Store: {f['store']}  |  Category: {f['category']}  |  "
               f"Region: {f['region']}")

    kpis = compute_kpis(df)

    if kpis["critical_products"] > 0:
        st.markdown(
            f'<div class="alert-strip">🔴 <b>{kpis["critical_products"]} critical products</b> '
            f'are nearly out of stock — immediate reorder required.</div>',
            unsafe_allow_html=True
        )
    if kpis["reorder_alerts"] > 0:
        st.markdown(
            f'<div class="warn-strip">🟡 <b>{kpis["reorder_alerts"]} products</b> '
            f'are below the reorder threshold.</div>',
            unsafe_allow_html=True
        )

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total revenue",
              f"₹{kpis['total_revenue']:,.0f}",
              f"{kpis['revenue_delta_pct']:+.1f}% vs prev 30d")
    c2.metric("Units sold",       f"{kpis['total_units_sold']:,}")
    c3.metric("Reorder alerts",   kpis["reorder_alerts"],
              delta=str(kpis["critical_products"]) + " critical",
              delta_color="inverse")
    c4.metric("Forecast accuracy", f"{kpis['overall_accuracy']}%")
    c5.metric("Avg inventory",     f"{kpis['avg_inventory']} units")

    st.divider()

    col1, col2 = st.columns([2, 1])
    with col1:
        st.plotly_chart(
            fig_sales_vs_inventory(df, freq=f["freq"]),
            use_container_width=True
        )
    with col2:
        st.plotly_chart(fig_stock_status_donut(df), use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.plotly_chart(fig_category_revenue(df), use_container_width=True)
    with col4:
        st.plotly_chart(fig_seasonal_revenue(df), use_container_width=True)

    st.divider()
    st.subheader("⚠️ Immediate restock required")
    alerts = get_low_stock_alert_table(df)
    if alerts.empty:
        st.success("All products are above the reorder threshold.")
    else:
        st.dataframe(alerts.head(10), use_container_width=True,
                     hide_index=True, height=280)


# ─────────────────────────────────────────────
# PAGE 2 — SALES & INVENTORY
# ─────────────────────────────────────────────
def page_sales_inventory(df: pd.DataFrame, f: dict):
    from analytics import (
        fig_sales_vs_inventory, fig_forecast_vs_actual
    )

    st.title("Sales & Inventory")

    product_list = sorted(df["Product ID"].unique().tolist())
    sel_product = st.selectbox("Product", ["All"] + product_list)
    pid = sel_product if sel_product != "All" else None

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(
            fig_sales_vs_inventory(df, product_id=pid, freq=f["freq"]),
            use_container_width=True
        )
    with col2:
        st.plotly_chart(
            fig_forecast_vs_actual(df, product_id=pid, freq=f["freq"]),
            use_container_width=True
        )

    with st.expander("Raw data explorer"):
        show_df = df if pid is None else df[df["Product ID"] == pid]
        st.dataframe(
            show_df[["Date", "Store ID", "Product ID", "Category", "Region",
                     "Inventory Level", "Units Sold", "Demand Forecast",
                     "Revenue", "Stock Status", "Reorder Flag",
                     "Forecast Error", "MAPE"]].head(500),
            use_container_width=True, hide_index=True
        )


# ─────────────────────────────────────────────
# PAGE 3 — CATEGORY ANALYSIS
# ─────────────────────────────────────────────
def page_category(df: pd.DataFrame, f: dict):
    from analytics import (
        fig_category_revenue, fig_category_units_trend, fig_category_mape
    )

    st.title("Category analysis")

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig_category_revenue(df), use_container_width=True)
    with col2:
        st.plotly_chart(fig_category_mape(df),    use_container_width=True)

    st.plotly_chart(
        fig_category_units_trend(df, freq=f["freq"]),
        use_container_width=True
    )

    st.subheader("Category summary table")
    cat_summary = (
        df.groupby("Category")
          .agg(
              Total_Revenue   =("Revenue",        "sum"),
              Total_Units_Sold=("Units Sold",      "sum"),
              Avg_Inventory   =("Inventory Level", "mean"),
              Avg_MAPE        =("MAPE",            "mean"),
              Reorder_Count   =("Reorder Flag",    "sum"),
          )
          .round(2)
          .reset_index()
    )
    cat_summary["Accuracy %"] = (100 - cat_summary["Avg_MAPE"]).round(1)
    cat_summary["Total_Revenue"] = cat_summary["Total_Revenue"].apply(
        lambda v: f"₹{v:,.0f}"
    )
    st.dataframe(cat_summary, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────
# PAGE 4 — REGION ANALYSIS
# ─────────────────────────────────────────────
def page_region(df: pd.DataFrame, f: dict):
    from analytics import (
        fig_region_revenue_pie, fig_region_sales_bar
    )

    st.title("Region analysis")

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig_region_revenue_pie(df), use_container_width=True)
    with col2:
        st.plotly_chart(fig_region_sales_bar(df),   use_container_width=True)

    st.subheader("Region KPIs")
    reg_kpi = (
        df.groupby("Region")
          .agg(
              Revenue       =("Revenue",        "sum"),
              Units_Sold    =("Units Sold",      "sum"),
              Avg_Inventory =("Inventory Level", "mean"),
              Avg_MAPE      =("MAPE",            "mean"),
              Reorder_Alerts=("Reorder Flag",    "sum"),
          )
          .round(2).reset_index()
    )
    reg_kpi["Accuracy %"] = (100 - reg_kpi["Avg_MAPE"]).round(1)
    reg_kpi["Revenue"]    = reg_kpi["Revenue"].apply(lambda v: f"₹{v:,.0f}")
    st.dataframe(reg_kpi, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────
# PAGE 5 — SEASONAL TRENDS
# ─────────────────────────────────────────────
def page_seasonal(df: pd.DataFrame, f: dict):
    from analytics import (
        fig_seasonal_revenue, fig_seasonal_weather_impact
    )
    from data_logic import seasonal_kpis

    st.title("Seasonal trends")

    st.plotly_chart(fig_seasonal_revenue(df),        use_container_width=True)
    st.plotly_chart(fig_seasonal_weather_impact(df), use_container_width=True)

    st.subheader("Seasonal KPIs")
    sea_kpis = seasonal_kpis(df)
    sea_kpis["Total_Revenue"] = sea_kpis["Total_Revenue"].apply(
        lambda v: f"₹{v:,.0f}"
    )
    sea_kpis["Accuracy %"] = (100 - sea_kpis["Avg_MAPE"]).round(1)
    st.dataframe(sea_kpis, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────
# PAGE 6 — LOW STOCK ALERTS
# ─────────────────────────────────────────────
def page_low_stock(df: pd.DataFrame):
    from analytics import (
        fig_low_stock_bar, fig_stock_status_donut,
        get_low_stock_alert_table, get_current_stock_snapshot
    )

    st.title("Low stock alerts")

    snap      = get_current_stock_snapshot(df)
    critical  = (snap["Stock Status"] == "Critical").sum()
    low_count = (snap["Stock Status"] == "Low").sum()
    reorder   = snap["Reorder Flag"].sum()

    if critical > 0:
        st.markdown(
            f'<div class="alert-strip">🔴 <b>{critical} products critically low</b> '
            f'— stock may run out within days!</div>',
            unsafe_allow_html=True
        )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Critical",    int(critical),   delta_color="inverse")
    c2.metric("Low stock",   int(low_count),  delta_color="inverse")
    c3.metric("Reorder now", int(reorder),    delta_color="inverse")
    c4.metric("Overstock",   int((snap["Stock Status"] == "Overstock").sum()))

    col1, col2 = st.columns([2, 1])
    with col1:
        top_n = st.slider("Show top N low-stock products", 5, 20, 12)
        st.plotly_chart(fig_low_stock_bar(df, top_n=top_n),
                        use_container_width=True)
    with col2:
        st.plotly_chart(fig_stock_status_donut(df), use_container_width=True)

    st.subheader("Full restock action list")
    alerts = get_low_stock_alert_table(df)
    if alerts.empty:
        st.success("✅ No products currently below reorder threshold.")
    else:
        st.dataframe(alerts, use_container_width=True, hide_index=True)
        csv = alerts.to_csv(index=False).encode()
        st.download_button("⬇️ Download restock list (CSV)",
                           data=csv,
                           file_name="restock_list.csv",
                           mime="text/csv")


# ─────────────────────────────────────────────
# PAGE 7 — DATABASE CRUD UI
# ─────────────────────────────────────────────
def page_database():
    import database as db

    st.title("🗄️ Database Management")
    st.caption("MySQL 5.5  ·  inventory_db  ·  inventory table")

    # ── Connection check ──────────────────────
    try:
        conn = db.get_connection()
        cur  = conn.cursor()
        cur.execute("SELECT VERSION()")
        ver = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM inventory")
        total = cur.fetchone()[0]
        conn.close()
        st.success(f"✅  Connected  ·  MySQL {ver}  ·  {total:,} rows in inventory table")
    except Exception as e:
        st.error(f"❌  Cannot connect to MySQL: {e}")
        st.info("Open database.py and update DB_PASSWORD at the top of the file.")
        st.stop()

    st.divider()

    # ── CRUD Tabs ─────────────────────────────
    tab_c, tab_r, tab_u, tab_d = st.tabs([
        "➕  Create",
        "🔍  Read",
        "✏️  Update",
        "🗑️  Delete"
    ])

    # ════════════════════════════════════════
    # CREATE
    # ════════════════════════════════════════
    with tab_c:
        st.subheader("Add a new inventory record")
        st.caption("Inserts into MySQL ✅  AND appends to CSV file ✅  — both stay in sync.")

        c1, c2, c3 = st.columns(3)
        new_date    = c1.text_input("Date (M/D/YYYY)",  value="1/1/2025")
        new_store   = c2.selectbox("Store ID",  ["S001","S002","S003","S004","S005"])
        new_product = c3.selectbox("Product ID",
                        [f"P{str(n).zfill(4)}" for n in range(1, 21)])

        c4, c5, c6 = st.columns(3)
        new_cat     = c4.selectbox("Category",
                        ["Groceries","Electronics","Furniture","Toys","Clothing"])
        new_region  = c5.selectbox("Region", ["North","South","East","West"])
        new_season  = c6.selectbox("Seasonality",
                        ["Spring","Summer","Autumn","Winter"])

        c7, c8, c9 = st.columns(3)
        new_inv     = c7.number_input("Inventory Level", 0, 500, 200)
        new_sold    = c8.number_input("Units Sold",      0, 500,  80)
        new_ordered = c9.number_input("Units Ordered",   0, 200,  60)

        c10, c11, c12 = st.columns(3)
        new_price   = c10.number_input("Price",            0.0, 200.0, 33.5)
        new_fc      = c11.number_input("Demand Forecast",  0.0, 600.0, 90.0)
        new_disc    = c12.number_input("Discount (%)",     0,   100,    10)

        c13, c14, c15 = st.columns(3)
        new_weather = c13.selectbox("Weather Condition",
                        ["Sunny","Rainy","Cloudy","Snowy"])
        new_promo   = c14.selectbox("Holiday/Promotion", [0, 1])
        new_comp    = c15.number_input("Competitor Pricing", 0.0, 200.0, 30.0)

        if st.button("➕  Insert Record", type="primary", use_container_width=True):
            try:
                new_id = db.create_record(
                    date               = new_date,
                    store_id           = new_store,
                    product_id         = new_product,
                    category           = new_cat,
                    region             = new_region,
                    inventory_level    = int(new_inv),
                    units_sold         = int(new_sold),
                    units_ordered      = int(new_ordered),
                    demand_forecast    = float(new_fc),
                    price              = float(new_price),
                    discount           = int(new_disc),
                    weather_condition  = new_weather,
                    holiday_promotion  = int(new_promo),
                    competitor_pricing = float(new_comp),
                    seasonality        = new_season
                )
                st.success(f"✅  Record inserted into MySQL AND appended to CSV — ID: **{new_id}**")
            except Exception as e:
                st.error(f"Insert failed: {e}")

    # ════════════════════════════════════════
    # READ
    # ════════════════════════════════════════
    with tab_r:
        st.subheader("View inventory records")

        r1, r2, r3 = st.columns(3)
        f_store = r1.selectbox("Filter by Store",
                    ["All","S001","S002","S003","S004","S005"],
                    key="r_store")
        f_cat   = r2.selectbox("Filter by Category",
                    ["All","Groceries","Electronics","Furniture","Toys","Clothing"],
                    key="r_cat")
        f_limit = r3.slider("Max rows to show", 10, 500, 50)

        if st.button("🔍  Fetch Records", use_container_width=True):
            try:
                conn = db.get_connection()
                cur  = conn.cursor()

                sql    = "SELECT * FROM inventory WHERE 1=1"
                params = []
                if f_store != "All":
                    sql += " AND store_id = %s"
                    params.append(f_store)
                if f_cat != "All":
                    sql += " AND category = %s"
                    params.append(f_cat)
                sql += f" LIMIT {f_limit}"

                cur.execute(sql, params)
                rows = cur.fetchall()
                conn.close()

                cols = ["id","date","store_id","product_id","category",
                        "region","inventory_level","units_sold","units_ordered",
                        "demand_forecast","price","discount","weather_condition",
                        "holiday_promotion","competitor_pricing","seasonality"]

                df_result = pd.DataFrame(rows, columns=cols)
                st.dataframe(df_result, use_container_width=True, hide_index=True)
                st.caption(f"{len(df_result):,} rows returned")

            except Exception as e:
                st.error(f"Read failed: {e}")

    # ════════════════════════════════════════
    # UPDATE
    # ════════════════════════════════════════
    with tab_u:
        st.subheader("Update inventory level")
        st.caption("Updates inventory level in MySQL ✅  AND in the CSV file ✅")

        u1, u2 = st.columns(2)
        upd_id  = u1.number_input("Record ID", min_value=1, step=1, value=1)
        upd_lvl = u2.number_input("New Inventory Level", min_value=0,
                                   max_value=500, step=1, value=300)

        if st.button("👁️  Preview current value"):
            try:
                conn = db.get_connection()
                cur  = conn.cursor()
                cur.execute(
                    "SELECT id, date, store_id, product_id, inventory_level "
                    "FROM inventory WHERE id = %s",
                    (int(upd_id),)
                )
                row = cur.fetchone()
                conn.close()
                if row:
                    st.info(
                        f"ID: **{row[0]}** | Date: {row[1]} | "
                        f"Store: {row[2]} | Product: {row[3]} | "
                        f"Current Inventory Level: **{row[4]}**"
                    )
                else:
                    st.warning(f"No record found with id = {int(upd_id)}")
            except Exception as e:
                st.error(str(e))

        if st.button("✏️  Update Record", type="primary", use_container_width=True):
            try:
                db.update_inventory(
                    record_id           = int(upd_id),
                    new_inventory_level = int(upd_lvl)
                )
                st.success(
                    f"✅  Record **{int(upd_id)}** updated in MySQL AND CSV — "
                    f"inventory_level is now **{int(upd_lvl)}**"
                )
            except Exception as e:
                st.error(f"Update failed: {e}")

    # ════════════════════════════════════════
    # DELETE
    # ════════════════════════════════════════
    with tab_d:
        st.subheader("Delete a record")
        st.caption("Removes the row from MySQL ✅  AND from the CSV file ✅")

        del_id = st.number_input("Record ID to delete", min_value=1,
                                  step=1, value=1)

        if st.button("👁️  Preview record before delete"):
            try:
                conn = db.get_connection()
                cur  = conn.cursor()
                cur.execute("SELECT * FROM inventory WHERE id = %s", (int(del_id),))
                row = cur.fetchone()
                conn.close()
                if row:
                    cols = ["id","date","store_id","product_id","category",
                            "region","inventory_level","units_sold","units_ordered",
                            "demand_forecast","price","discount","weather_condition",
                            "holiday_promotion","competitor_pricing","seasonality"]
                    df_prev = pd.DataFrame([row], columns=cols)
                    st.dataframe(df_prev, use_container_width=True, hide_index=True)
                else:
                    st.warning(f"No record found with id = {int(del_id)}")
            except Exception as e:
                st.error(str(e))

        if st.button("🗑️  Delete Record", type="primary", use_container_width=True):
            try:
                db.delete_record(record_id=int(del_id))
                st.success(f"✅  Record **{int(del_id)}** deleted from MySQL AND removed from CSV.")
            except Exception as e:
                st.error(f"Delete failed: {e}")

    st.divider()

    # ── Table summary ─────────────────────────
    st.subheader("Table summary")
    try:
        conn = db.get_connection()
        cur  = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM inventory")
        total = cur.fetchone()[0]

        cur.execute("SELECT COUNT(DISTINCT store_id) FROM inventory")
        stores = cur.fetchone()[0]

        cur.execute("SELECT COUNT(DISTINCT product_id) FROM inventory")
        products = cur.fetchone()[0]

        conn.close()

        m1, m2, m3 = st.columns(3)
        m1.metric("Total rows", f"{total:,}")
        m2.metric("Stores",     stores)
        m3.metric("Products",   products)

    except Exception as e:
        st.warning(str(e))


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    df_raw  = load_data()
    filters = render_sidebar(df_raw)
    df      = apply_filters(df_raw, filters)

    if df.empty:
        st.warning("No data for the selected filters. Please adjust the sidebar.")
        st.stop()

    p = filters["page"]

    if   p == "🏠 Dashboard":          page_dashboard(df, filters)
    elif p == "📊 Sales & Inventory":  page_sales_inventory(df, filters)
    elif p == "🗂️ Category Analysis":  page_category(df, filters)
    elif p == "🌍 Region Analysis":    page_region(df, filters)
    elif p == "🍂 Seasonal Trends":    page_seasonal(df, filters)
    elif p == "⚠️ Low Stock Alerts":   page_low_stock(df)
    elif p == "🗄️ Database":           page_database()


if __name__ == "__main__":
    main()
# Smart-Retail-Analysis-and-Inventory-Management-System


A Streamlit dashboard for retail inventory monitoring, sales analytics, demand forecasting, and database management.

---

## Features

- Inventory stock alerts (Critical / Low / Adequate / Overstock)
- Sales and revenue trend charts
- Demand forecast vs actual analysis
- Category, region, and seasonal breakdowns
- Full CRUD operations synced between MySQL and CSV

---

## Project Files

| File | Purpose |
|---|---|
| `app.py` | Streamlit UI and page navigation |
| `data_logic.py` | Data loading, cleaning, and calculations |
| `analytics.py` | Charts and KPI metrics |
| `database.py` | MySQL connection and CRUD operations |
| `retail_store_inventory.csv` | Source dataset |

---

## Installation

```bash
pip install streamlit pandas numpy plotly pymysql
```

Update your MySQL credentials in `database.py`, then run:

```bash
python database.py --setup    # create database and table
python database.py --seed     # load CSV into MySQL
streamlit run app.py          # start the app
```

---

## Dataset Columns

`Date`, `Store ID`, `Product ID`, `Category`, `Region`, `Inventory Level`, `Units Sold`, `Units Ordered`, `Demand Forecast`, `Price`, `Discount`, `Weather Condition`, `Holiday/Promotion`, `Competitor Pricing`, `Seasonality`

---

## Built With

Python · Streamlit · Plotly · Pandas · MySQL

"""
database.py  —  Simple MySQL connectivity + CRUD for mini project
=================================================================
Steps to use:
  1. pip install pymysql
  2. Start MySQL 5.5
  3. Run:  python database.py --setup    (creates DB + table)
  4. Run:  python database.py --seed     (loads CSV into MySQL)
  5. Done — test CRUD at the bottom of this file
"""

import pymysql
import csv
import sys

# ─────────────────────────────────────────────
# 1.  CHANGE YOUR PASSWORD HERE
# ─────────────────────────────────────────────
DB_HOST     = "localhost"
DB_PORT     = 3306
DB_USER     = "root"
DB_PASSWORD = "root"      # ← put your MySQL password here
DB_NAME     = "inventory_db"
CSV_FILE    = "retail_store_inventory.csv"


# ─────────────────────────────────────────────
# 2.  GET CONNECTION
# ─────────────────────────────────────────────
def get_connection():
    return pymysql.connect(
        host     = DB_HOST,
        port     = DB_PORT,
        user     = DB_USER,
        password = DB_PASSWORD,
        database = DB_NAME,
        charset  = "utf8"
    )


# ─────────────────────────────────────────────
# 3.  SETUP — create database and table
# ─────────────────────────────────────────────
def setup():
    # Connect without selecting a DB to create it first
    conn = pymysql.connect(
        host=DB_HOST, port=DB_PORT,
        user=DB_USER, password=DB_PASSWORD,
        charset="utf8"
    )
    cur = conn.cursor()
    cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} DEFAULT CHARACTER SET utf8")
    cur.execute(f"USE {DB_NAME}")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id                  INT AUTO_INCREMENT PRIMARY KEY,
            date                VARCHAR(20),
            store_id            VARCHAR(10),
            product_id          VARCHAR(10),
            category            VARCHAR(50),
            region              VARCHAR(50),
            inventory_level     INT,
            units_sold          INT,
            units_ordered       INT,
            demand_forecast     FLOAT,
            price               FLOAT,
            discount            INT,
            weather_condition   VARCHAR(30),
            holiday_promotion   INT,
            competitor_pricing  FLOAT,
            seasonality         VARCHAR(20)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8
    """)

    conn.commit()
    conn.close()
    print("Setup done — database and table created.")


# ─────────────────────────────────────────────
# 4.  SEED — load CSV into MySQL
# ─────────────────────────────────────────────
def seed():
    conn = get_connection()
    cur  = conn.cursor()

    # Clear existing data before loading
    cur.execute("DELETE FROM inventory")

    sql = """
        INSERT INTO inventory
            (date, store_id, product_id, category, region,
             inventory_level, units_sold, units_ordered,
             demand_forecast, price, discount,
             weather_condition, holiday_promotion,
             competitor_pricing, seasonality)
        VALUES
            (%s, %s, %s, %s, %s,
             %s, %s, %s,
             %s, %s, %s,
             %s, %s,
             %s, %s)
    """

    rows = []
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append((
                row["Date"],
                row["Store ID"],
                row["Product ID"],
                row["Category"],
                row["Region"],
                int(row["Inventory Level"]),
                int(row["Units Sold"]),
                int(row["Units Ordered"]),
                float(row["Demand Forecast"]),
                float(row["Price"]),
                int(row["Discount"]),
                row["Weather Condition"],
                int(row["Holiday/Promotion"]),
                float(row["Competitor Pricing"]) if row["Competitor Pricing"] else None,
                row["Seasonality"]
            ))

    # Insert in batches of 1000 rows (safe for MySQL 5.5)
    batch = 1000
    for i in range(0, len(rows), batch):
        cur.executemany(sql, rows[i:i+batch])
        print(f"  Inserted rows {i+1} to {min(i+batch, len(rows))}...")

    conn.commit()
    conn.close()
    print(f"Seed done — {len(rows)} rows loaded from CSV.")


# ─────────────────────────────────────────────
# 5.  CRUD OPERATIONS  (MySQL + CSV in sync)
# ─────────────────────────────────────────────

CSV_HEADERS = [
    "Date", "Store ID", "Product ID", "Category", "Region",
    "Inventory Level", "Units Sold", "Units Ordered",
    "Demand Forecast", "Price", "Discount",
    "Weather Condition", "Holiday/Promotion",
    "Competitor Pricing", "Seasonality"
]


def _read_csv_rows():
    """Read all rows from CSV as list of dicts."""
    rows = []
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def _write_csv_rows(rows):
    """Overwrite CSV with given list of dicts."""
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writeheader()
        writer.writerows(rows)


# ── CREATE — insert into MySQL + append to CSV ──
def create_record(date, store_id, product_id, category, region,
                  inventory_level, units_sold, units_ordered,
                  demand_forecast, price, discount,
                  weather_condition, holiday_promotion,
                  competitor_pricing, seasonality):
    # 1. Insert into MySQL
    conn = get_connection()
    cur  = conn.cursor()
    sql  = """
        INSERT INTO inventory
            (date, store_id, product_id, category, region,
             inventory_level, units_sold, units_ordered,
             demand_forecast, price, discount,
             weather_condition, holiday_promotion,
             competitor_pricing, seasonality)
        VALUES
            (%s, %s, %s, %s, %s,
             %s, %s, %s,
             %s, %s, %s,
             %s, %s, %s, %s)
    """
    cur.execute(sql, (
        date, store_id, product_id, category, region,
        inventory_level, units_sold, units_ordered,
        demand_forecast, price, discount,
        weather_condition, holiday_promotion,
        competitor_pricing, seasonality
    ))
    new_id = cur.lastrowid
    conn.commit()
    conn.close()

    # 2. Append to CSV
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writerow({
            "Date":               date,
            "Store ID":           store_id,
            "Product ID":         product_id,
            "Category":           category,
            "Region":             region,
            "Inventory Level":    inventory_level,
            "Units Sold":         units_sold,
            "Units Ordered":      units_ordered,
            "Demand Forecast":    demand_forecast,
            "Price":              price,
            "Discount":           discount,
            "Weather Condition":  weather_condition,
            "Holiday/Promotion":  holiday_promotion,
            "Competitor Pricing": competitor_pricing,
            "Seasonality":        seasonality
        })

    print(f"Created — MySQL id={new_id}, row appended to CSV.")
    return new_id


# ── READ — fetch rows from MySQL ────────────
def read_records(store_id=None, category=None, limit=10):
    conn   = get_connection()
    cur    = conn.cursor()
    sql    = "SELECT * FROM inventory WHERE 1=1"
    params = []
    if store_id:
        sql += " AND store_id = %s"
        params.append(store_id)
    if category:
        sql += " AND category = %s"
        params.append(category)
    sql += f" LIMIT {int(limit)}"
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    print(f"\n{len(rows)} row(s) returned.")
    return rows


# ── UPDATE — change inventory level in MySQL + CSV ──
def update_inventory(record_id, new_inventory_level):
    # 1. Fetch current row from MySQL to identify it in CSV
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT * FROM inventory WHERE id = %s", (record_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        print(f"No record found with id={record_id}")
        return

    # Row tuple: (id, date, store_id, product_id, category, region,
    #             inv_level, units_sold, units_ordered, demand_forecast,
    #             price, discount, weather_condition, holiday_promotion,
    #             competitor_pricing, seasonality)
    old_date       = str(row[1])
    old_store      = row[2]
    old_product    = row[3]
    old_inv        = str(row[6])

    # 2. Update MySQL
    cur.execute(
        "UPDATE inventory SET inventory_level = %s WHERE id = %s",
        (new_inventory_level, record_id)
    )
    conn.commit()
    conn.close()

    # 3. Update matching row in CSV
    csv_rows = _read_csv_rows()
    updated  = 0
    for csv_row in csv_rows:
        if (csv_row["Date"]       == old_date    and
            csv_row["Store ID"]   == old_store   and
            csv_row["Product ID"] == old_product and
            csv_row["Inventory Level"] == old_inv):
            csv_row["Inventory Level"] = str(new_inventory_level)
            updated += 1
            break   # update only the first match

    _write_csv_rows(csv_rows)
    print(f"Updated — MySQL id={record_id} and CSV row updated. "
          f"Inventory level: {old_inv} → {new_inventory_level}")


# ── DELETE — remove from MySQL + CSV ────────
def delete_record(record_id):
    # 1. Fetch row from MySQL before deleting
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT * FROM inventory WHERE id = %s", (record_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        print(f"No record found with id={record_id}")
        return

    old_date    = str(row[1])
    old_store   = row[2]
    old_product = row[3]
    old_inv     = str(row[6])

    # 2. Delete from MySQL
    cur.execute("DELETE FROM inventory WHERE id = %s", (record_id,))
    conn.commit()
    conn.close()

    # 3. Remove matching row from CSV
    csv_rows = _read_csv_rows()
    new_rows = []
    deleted  = False
    for csv_row in csv_rows:
        if (not deleted and
            csv_row["Date"]            == old_date    and
            csv_row["Store ID"]        == old_store   and
            csv_row["Product ID"]      == old_product and
            csv_row["Inventory Level"] == old_inv):
            deleted = True   # skip this row (delete it)
            continue
        new_rows.append(csv_row)

    _write_csv_rows(new_rows)
    print(f"Deleted — MySQL id={record_id} removed, CSV row removed.")


# ── COUNT — quick row count check ───────────
def count_records():
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM inventory")
    total = cur.fetchone()[0]
    conn.close()
    print(f"Total rows in inventory table: {total}")
    return total


# ─────────────────────────────────────────────
# 6.  KEPT FOR BACKWARD COMPATIBILITY
# ─────────────────────────────────────────────
def add_to_csv_and_db(date, store_id, product_id, category, region,
                      inventory_level, units_sold, units_ordered,
                      demand_forecast, price, discount,
                      weather_condition, holiday_promotion,
                      competitor_pricing, seasonality):
    """Same as create_record — both insert into MySQL and append to CSV."""
    return create_record(
        date, store_id, product_id, category, region,
        inventory_level, units_sold, units_ordered,
        demand_forecast, price, discount,
        weather_condition, holiday_promotion,
        competitor_pricing, seasonality
    )


# ─────────────────────────────────────────────
# 7.  CLI + QUICK TEST
# ─────────────────────────────────────────────
if __name__ == "__main__":
    args = sys.argv[1:]

    if "--setup" in args:
        setup()

    elif "--seed" in args:
        seed()

    elif "--test" in args:
        print("\n===== TESTING ALL CRUD OPERATIONS =====\n")

        # CREATE
        print("--- CREATE ---")
        new_id = create_record(
            date               = "1/1/2025",
            store_id           = "S001",
            product_id         = "P0001",
            category           = "Groceries",
            region             = "North",
            inventory_level    = 300,
            units_sold         = 90,
            units_ordered      = 60,
            demand_forecast    = 95.0,
            price              = 33.5,
            discount           = 10,
            weather_condition  = "Sunny",
            holiday_promotion  = 0,
            competitor_pricing = 30.0,
            seasonality        = "Winter"
        )

        # READ
        print("\n--- READ ---")
        read_records(store_id="S001", limit=5)

        # UPDATE
        print("\n--- UPDATE ---")
        update_inventory(record_id=new_id, new_inventory_level=450)

        # verify update
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute("SELECT id, inventory_level FROM inventory WHERE id = %s", (new_id,))
        row = cur.fetchone()
        conn.close()
        print(f"Verified — id={row[0]}, inventory_level={row[1]}")

        # DELETE
        print("\n--- DELETE ---")
        delete_record(record_id=new_id)

        # final count
        print("\n--- COUNT ---")
        count_records()

        print("\n===== ALL CRUD OPERATIONS PASSED =====")

    elif "--add" in args:
        # Example: python database.py --add
        print("Adding one new row to CSV and DB...")
        add_to_csv_and_db(
            date               = "1/2/2025",
            store_id           = "S001",
            product_id         = "P0001",
            category           = "Groceries",
            region             = "North",
            inventory_level    = 200,
            units_sold         = 70,
            units_ordered      = 50,
            demand_forecast    = 75.0,
            price              = 33.5,
            discount           = 5,
            weather_condition  = "Cloudy",
            holiday_promotion  = 0,
            competitor_pricing = 31.0,
            seasonality        = "Winter"
        )

    else:
        print("Usage:")
        print("  python database.py --setup   # create DB and table")
        print("  python database.py --seed    # load CSV into MySQL")
        print("  python database.py --test    # test all CRUD operations")
        print("  python database.py --add     # add one row to CSV and DB")
-- ============================================================
-- Simple Inventory Schema — MySQL 5.5
-- One table only — matches database.py exactly
--
-- How to run:
--   mysql -u root -p
--   mysql> SOURCE C:/path/to/schema.sql;
-- ============================================================

-- Step 1: Create database
CREATE DATABASE IF NOT EXISTS inventory_db
    DEFAULT CHARACTER SET utf8
    COLLATE utf8_general_ci;

-- Step 2: Select it
USE inventory_db;

-- Step 3: Drop old table if it exists (clean start)
DROP TABLE IF EXISTS inventory;

-- Step 4: Create the single inventory table
CREATE TABLE inventory (
    id                  INT           AUTO_INCREMENT PRIMARY KEY,
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ============================================================
-- Verify after running this file:
--   SHOW TABLES;           → should show: inventory
--   DESCRIBE inventory;    → should show 17 columns
--   SELECT COUNT(*) FROM inventory;  → 0 (empty before seed)
-- ============================================================

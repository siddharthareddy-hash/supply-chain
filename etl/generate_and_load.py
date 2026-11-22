import os, random
from datetime import date, timedelta
from decimal import Decimal
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values

load_dotenv()
DB = dict(host="localhost", port=5432, dbname="supply_chain",
          user=os.getenv("POSTGRES_USER", "etl_user"),
          password=os.getenv("POSTGRES_PASSWORD"))
random.seed(42)

SUPPLIERS = [(f"SUP-{i:03d}", f"Supplier {i}",
              random.choice(["China","Vietnam","Germany","India","Mexico"]),
              round(random.uniform(2.5, 4.9), 2)) for i in range(1, 11)]
PRODUCTS = [(f"SKU-{i:04d}", f"Product {i}",
             random.choice(["Electronics","Machinery","Textiles","Automotive"]),
             round(random.uniform(0.5, 250.0), 3),
             round(random.uniform(50, 5000), 2)) for i in range(1, 26)]

WAREHOUSES = [
    ("WH-01", "Port of Los Angeles Warehouse", "Los Angeles", "USA",         "North America", 33.770100, -118.265000),
    ("WH-02", "Rotterdam Distribution Center", "Rotterdam",   "Netherlands", "Europe",        51.924400,   4.477700),
    ("WH-03", "Singapore Logistics Hub",       "Singapore",   "Singapore",   "Asia",           1.264400, 103.991500),
    ("WH-04", "Hamburg Freight Terminal",      "Hamburg",     "Germany",     "Europe",        53.544400,   9.977000),
    ("WH-05", "Shanghai Bonded Warehouse",     "Shanghai",    "China",       "Asia",          31.230400, 121.473700),
]

ROUTES = [
    ("RT-SEA-01",  "WH-01", "Los Angeles", "USA",         "SEA",  3, 12500),
    ("RT-RAIL-01", "WH-02", "Rotterdam",   "Netherlands", "RAIL", 21,  3200),
    ("RT-AIR-01",  "WH-03", "Frankfurt",   "Germany",     "AIR",   9,  1800),
]

MODE_RISK = {"AIR": 0.10, "RAIL": 0.20, "SEA": 0.35, "ROAD": 0.25}


def main():
    conn = psycopg2.connect(**DB)
    cur = conn.cursor()

    cur.execute("TRUNCATE TABLE Fact_Shipment, DQ_Quarantine, Dim_Supplier, "
                "Dim_Product, Dim_Route, Dim_Warehouse RESTART IDENTITY CASCADE")
    conn.commit()

    for wid, name, city, country, region, lat, lon in WAREHOUSES:
        cur.execute("""INSERT INTO Dim_Warehouse (Warehouse_ID, Warehouse_Name, City,
                       Country, Region, Latitude, Longitude)
                       VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                    (wid, name, city, country, region, lat, lon))
    for sid, name, country, rel in SUPPLIERS:
        cur.execute("""INSERT INTO Dim_Supplier (Supplier_ID, Supplier_Name, Country,
                       Reliability_Score, Valid_From) VALUES (%s,%s,%s,%s,%s)""",
                    (sid, name, country, rel, date(2024, 1, 1)))
    for sku, name, cat, wgt, val in PRODUCTS:
        cur.execute("""INSERT INTO Dim_Product (Product_ID, Product_Name, Category,
                       Unit_Weight_Kg, Unit_Value_USD) VALUES (%s,%s,%s,%s,%s)""",
                    (sku, name, cat, wgt, val))

    for rid, whid, dest_port, dest_country, mode, std_days, base_cost in ROUTES:
        cur.execute("""INSERT INTO Dim_Route (Origin_Warehouse_Key, Route_ID, Destination_Port,
                       Destination_Country, Transport_Mode, Standard_Duration_Days,
                       Base_Cost_USD, Valid_From)
                       SELECT Warehouse_Key, %s, %s, %s, %s, %s, %s, %s
                       FROM Dim_Warehouse WHERE Warehouse_ID = %s""",
                    (rid, dest_port, dest_country, mode, std_days, base_cost,
                     date(2024, 1, 1), whid))
    conn.commit()

    cur.execute("SELECT Supplier_Key FROM Dim_Supplier")
    supplier_keys = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT Product_Key FROM Dim_Product")
    product_keys = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT Route_Key, Standard_Duration_Days, Base_Cost_USD, Transport_Mode "
                "FROM Dim_Route WHERE Is_Current")
    routes = cur.fetchall()
    cur.execute("SELECT Warehouse_Key FROM Dim_Warehouse")
    warehouse_keys = [r[0] for r in cur.fetchall()]

    SUPPLIER_RISK = {k: 0.25 * (4.9 - rel) / 2.4
                     for k, (_, _, _, rel) in zip(supplier_keys, SUPPLIERS)}

    shipments, quarantine, n = [], [], 0
    for day in range(365):
        d = date(2024, 1, 1) + timedelta(days=day)
        for _ in range(random.randint(2, 8)):
            n += 1
            shipment_id = f"SHP-{d:%Y%m%d}-{n:06d}"
            route_key, std_days, base_cost, mode = random.choice(routes)
            sup_key = random.choice(supplier_keys)
            season_risk = 0.10 if d.month in (11, 12, 1) else 0.0
            p_delay = min(0.8, MODE_RISK[mode] + SUPPLIER_RISK[sup_key] + season_risk)
            delay = int(random.expovariate(1 / 3)) if random.random() < p_delay else 0
            transit = std_days + delay
 
            qty = random.randint(10, 500)
            cost = round(float(base_cost) * random.uniform(0.8, 1.3), 2)
            customs = round(Decimal(random.uniform(0, 900)), 2)
            damaged = random.random() < 0.03
            row = (shipment_id, int(d.strftime("%Y%m%d")), random.choice(supplier_keys),
                   random.choice(warehouse_keys), random.choice(product_keys), route_key,
                   qty, cost, transit, delay, customs, damaged, std_days, d)
            if d > date.today():
                quarantine.append(("synthetic", str(row), "Future date"))
            else:
                shipments.append(row)

    execute_values(cur, """INSERT INTO Fact_Shipment (Shipment_ID, Date_Key, Supplier_Key,
        Warehouse_Key, Product_Key, Route_Key, Quantity_Shipped, Shipping_Cost_USD,
        Actual_Transit_Days, Delay_Days, Customs_Fee_USD, Damage_Flag,
        Avg_Standard_Duration_Days, Shipped_Date) VALUES %s""", shipments, page_size=500)

    for src, row, reason in quarantine:
        cur.execute("INSERT INTO DQ_Quarantine (Source_Table, Rejected_Row, Failure_Reason) VALUES (%s,%s,%s)",
                    (src, row, reason))

    conn.commit()
    print(f"Loaded {len(shipments)} shipments, quarantined {len(quarantine)} rows.")

if __name__ == "__main__":
    main()

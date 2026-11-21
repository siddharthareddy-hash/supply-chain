"""
Mock data generator for the Supply Chain Intelligence System.
Generates dimensions + 12 months of shipments with INJECTED signal:
  - 3 chronic-delay routes
  - Q4 seasonal delay spikes
  - ~3% anomalous shipments (cost / transit outliers)
  - a small % of dirty rows (to exercise the DQ gate)
"""
import numpy as np
import pandas as pd
from faker import Faker
from pathlib import Path

fake = Faker()
fake.seed_instance(42)
rng = np.random.default_rng(42)

OUT = Path(__file__).resolve().parents[2] / "data"
OUT.mkdir(parents=True, exist_ok=True)

N_SUPPLIERS = 25
N_WAREHOUSES = 8
N_PRODUCTS = 60
N_ROUTES = 20
N_SHIPMENTS = 60_000

# ----------------------------------------------------------------------
# 1. Dimensions
# ----------------------------------------------------------------------
warehouses = pd.DataFrame([
    {
        "Warehouse_ID":   f"WH{i:03d}",
        "Warehouse_Name": f"{fake.city()} DC",
        "City":           fake.city(),
        "Country":        fake.country_code(),
        "Region":         rng.choice(["NA", "EU", "APAC", "LATAM", "MEA"]),
        "Latitude":       round(fake.latitude(), 6),
        "Longitude":      round(fake.longitude(), 6),
    }
    for i in range(N_WAREHOUSES)
])

suppliers = pd.DataFrame([
    {
        "Supplier_ID":       f"SUP{i:04d}",
        "Supplier_Name":     fake.company(),
        "Country":           fake.country_code(),
        "Reliability_Score": round(float(np.clip(rng.beta(6, 2) * 5, 0, 5)), 2),
    }
    for i in range(N_SUPPLIERS)
])

products = pd.DataFrame([
    {
        "Product_ID":     f"P{i:05d}",
        "Product_Name":   f"{fake.word().title()} {fake.word().title()}",
        "Category":       rng.choice(["Electronics", "Machinery", "Textiles",
                                      "Chemicals", "Food"]),
        "Unit_Weight_KG": round(float(rng.lognormal(1.5, 1.0)), 3),
        "Unit_Value_USD": round(float(rng.lognormal(4.0, 1.2)), 2),
    }
    for i in range(N_PRODUCTS)
])

MODE_STD = {"AIR": 3, "SEA": 21, "RAIL": 12, "ROAD": 5}
MODE_COST = {"AIR": 4000, "SEA": 1500, "RAIL": 2200, "ROAD": 900}
CHRONIC_DELAY_ROUTES = {3, 7, 15}  # injected signal

route_rows = []
for i in range(N_ROUTES):
    mode = rng.choice(["AIR", "SEA", "RAIL", "ROAD"], p=[0.2, 0.4, 0.2, 0.2])
    route_rows.append({
        "Route_ID":               f"RT{i:03d}",
        "Origin_Warehouse_ID":    rng.choice(warehouses.Warehouse_ID),
        "Destination_Port":       fake.city(),
        "Destination_Country":    fake.country_code(),
        "Transport_Mode":         mode,
        "Standard_Duration_Days": MODE_STD[mode] + int(rng.integers(0, 4)),
        "Base_Cost_USD":          round(MODE_COST[mode] * rng.uniform(0.8, 1.3), 2),
        # internal column used ONLY by the generator; dropped before saving
        "_delay_mean":            2.5 if i in CHRONIC_DELAY_ROUTES else 0.2,
    })
routes = pd.DataFrame(route_rows)

# ----------------------------------------------------------------------
# 2. Fact: shipments over 12 months
# ----------------------------------------------------------------------
dates = pd.date_range("2024-01-01", "2024-12-31", freq="D")

ship = pd.DataFrame({
    "Shipment_ID":  [f"SH{i:06d}" for i in range(N_SHIPMENTS)],
    "Shipped_Date": rng.choice(dates, N_SHIPMENTS),
})
ship["Shipped_Date"] = pd.to_datetime(ship["Shipped_Date"])

ship["Supplier_ID"]      = rng.choice(suppliers.Supplier_ID, N_SHIPMENTS)
ship["Product_ID"]       = rng.choice(products.Product_ID, N_SHIPMENTS)
ship["Route_ID"]         = rng.choice(routes.Route_ID, N_SHIPMENTS)
ship["Warehouse_ID"]     = rng.choice(warehouses.Warehouse_ID, N_SHIPMENTS)
ship["Quantity_Shipped"] = rng.integers(10, 5000, N_SHIPMENTS)

ship = (
    ship
    .merge(routes, on="Route_ID")
    .merge(products, on="Product_ID")
    .merge(suppliers[["Supplier_ID", "Reliability_Score"]], on="Supplier_ID")
)

# --- transit time = standard + exponential delay + Q4 seasonal spike ---
month = ship["Shipped_Date"].dt.month
seasonal = np.where(month.isin([10, 11, 12]), 1.5, 0.0)

delay = np.maximum(
    0.0,
    rng.exponential(ship["_delay_mean"].to_numpy() + seasonal),
)
ship["Actual_Transit_Days"] = (
    ship["Standard_Duration_Days"] + delay
).round().clip(lower=1).astype(int)

# --- cost: base + weight component * lognormal noise ---
weight_total = ship["Quantity_Shipped"] * ship["Unit_Weight_KG"]
cost = (
    ship["Base_Cost_USD"]
    * (1 + 0.0004 * weight_total)
    * rng.lognormal(0, 0.15, N_SHIPMENTS)
)

# --- injected anomalies (~3%): 2-4x cost; (~1%): 2x transit ---
anom_mask = rng.random(N_SHIPMENTS) < 0.03
cost = cost * np.where(anom_mask, rng.uniform(2.0, 4.0, N_SHIPMENTS), 1.0)

transit_bump = rng.random(N_SHIPMENTS) < 0.01
ship.loc[transit_bump, "Actual_Transit_Days"] = (
    ship.loc[transit_bump, "Actual_Transit_Days"] * 2
).clip(upper=120).astype(int)

ship["Delay_Days"] = (
    ship["Actual_Transit_Days"] - ship["Standard_Duration_Days"]
).clip(lower=0)

ship["Shipping_Cost_USD"]        = cost.round(2)
ship["Customs_Clearance_Hours"]  = rng.gamma(2.0, 6.0, N_SHIPMENTS).round(1)
ship["Damage_Flag"]              = rng.random(N_SHIPMENTS) < 0.015
ship["Avg_Standard_Duration_Days"] = ship["Standard_Duration_Days"]

# ----------------------------------------------------------------------
# 3. Dirty rows (to exercise the DQ gate downstream)
# ----------------------------------------------------------------------
dirty_idx = rng.choice(N_SHIPMENTS, size=150, replace50], "Quantity_Shipped"] = -1
ship.loc[dirty_idx[50:100], "Shipping_Cost_USD"] = -99.0
ship.loc[dirty_idx[100:], "Actual_Transit_Days"] = 0

# ----------------------------------------------------------------------
# 4. Save - ERP dump style
# ----------------------------------------------------------------------
ship = ship.drop(columns=["_delay_mean"])
warehouses.to_csv(OUT / "warehouses.csv", index=False)
suppliers.to_csv(OUT / "suppliers.csv", index=False)
products.to_csv(OUT / "products.csv",(columns=["_delay_mean"]).to_csv(OUT / "routes.csv", index=False)
ship.to_csv(OUT / "shipments.csv", index=False, date_format="%Y-%m-%d")

print(f"Generated {len(ship):,} shipments "
      f"({int(anom_mask.sum())} anomalous, 150 dirty rows)")
print(f"Files written to: {OUT}")

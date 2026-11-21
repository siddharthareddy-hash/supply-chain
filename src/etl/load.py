import json
import pandas as pd
from sqlalchemy import create_engine, text
from src.config import get_connection_string

SHIPMENT_COLS = [
    "Shipment_ID", "Date_Key", "Supplier_Key", "Warehouse_Key",
    "Product_Key", "hipped", "Shipping_Cost_USD",
    "Actual_Transit_Days", "Delay_Days", "Customs_Clearance_Hours",
    "Damage_Flag", "Avg_Standard_Duration_Days", "Shipped_Date",
]


def load_dimensions(engine, data_dir):
    """Load dims; suppliers/routes as SCD2 current rows (upsert on natural key)."""
    for table, file, key in [
        ("Dim_Warehouse", "warehouses.csv", "Warehouse_ID"),
        ("Dim_Product",   "products.csv",   "Product_ID"),
        ("Dim_Supplier",  "suppliers.csv",  "Supplier_ID"),
        ("Dim_Route",     "routes.csv",     "Route_ID"),
    ]:
        df = pd.read_csv(data_dir / file)
        df.to_sql(f"_stg_{table}", engine, if_exists="        if table in ("Dim_Supplier", "Dim_Route"):
            # SCD2: expire changed current rows, insert new versions
            with engine.begin() as conn:
                conn.execute(text(f"""
                    UPDATE {table} t
                    SET Is_Current = FALSE,
                        Valid_To   = CURRENT_DATE - 1
                    FROM _stg_{table} s
                    WHERE t.{key} = s.{key}
                      AND t.Is_Current = TRUE
                      AND (t.Reliability_Score IS DISTINCT FROM s.Reliability_Score
                           OR t.Standard_Duration_Days IS DISTINCT FROM s.Standard_Duration_Days
                           OR t.Base_Cost_USD IS DISTINCT FROM s.Base_Cost_USD);
                """))
                conn.execute(text(f"""
                    INSERT INTO {table} ({key}, Supplier_Name, Country, Reliability_Score,
                                         Origin_Warehouse_Key, Destination_Port,
                                         Destination_Country, Transport_Mode,
                                         Standard_Duration_Days, Base_Cost_USD,
                                         Valid_From, Is_Current)
                    SELECT s.{key}, s.Supplier_Name, s.Country, s.Reliability_Score,
                           w.Warehouse_Key, s.Destination_Port, s.Destination_Country,
                           s.Transport_Mode, s.Standard_Duration_Days, s.Base_Cost_USD,
                           CURRENT_DATE, TRUE
                    FROM _stg_{table} s
                    LEFT JOIN Dim_Warehouse w ON w.Warehouse_ID = s.Origin_Warehouse_ID
                    LEFT JOIN {table} cur
                           ON cur.{key} = s.{key} AND cur.Is_Current = TRUE
                    WHERE cur.{key} IS NULL;      -- only brand-new rows here
                """))
        else:
            df.to_sql(table, engine, if_exists="append", index=False)


def load_shipments(engine, df: pd.DataFrame, data_dir):
    """Key-lookup + idempotent upsert into partitioned Fact_Shipment."""
    dim_date = pd.read

> ⚠️ The response reached the length limit. Reply **continue** to get the rest.
    dim_date = pd.read_sql(
        "SELECT Date_Key, Full_Date FROM Dim_Date", engine
    )
    dim_date["Full_Date"] = pd.to_datetime(dim_date["Full_Date"])

    key_maps = {
        "Supplier_Key":  ("Dim_Supplier",  "Supplier_ID",  True),   # True = Is_Current only
        "Warehouse_Key": ("Dim_Warehouse", "Warehouse_ID", False),
        "Product_Key":   ("Dim_Product",   "Product_ID",   False),
        "Route_Key":     ("Dim_Route",     "Route_ID",     True),
    }
    for key_col, (table, nat_key, current_only) in key_maps.items():
        q = f"SELECT {nat_key}, {key_col} FROM {table}"
        if current_only:
            q += " WHERE Is_Current = TRUE"
        mapping = pd.read_sql(q, engine)
        df = df.merge(mapping, on=nat_key, how="inner")   # inner: drop orphans

    df["Date_Key"] = (
        df["Shipped_Date"].dt.strftime("%Y%m%d").astype(int)
    )

    fact = df[SHIPMENT_COLS].copy()

    # Idempotent upsert: staging → anti-join → insert only new rows
    fact.to_sql("_stg_fact_shipment", engine, if_exists="replace", index=False)
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO Fact_Shipment (
                Shipment_ID, Date_Key, Supplier_Key, Warehouse_Key,
                Product_Key, Route_Key, Quantity_Shipped, Shipping_Cost_USD,
                Actual_Transit_Days, Delay_Days, Customs_Clearance_Hours,
                Damage_Flag, Avg_Standard_Duration_Days, Shipped_Date)
            SELECT s.Shipment_ID, s.Date_Key, s.Supplier_Key, s.Warehouse_Key,
                   s.Product_Key, s.Route_Key, s.Quantity_Shipped, s.Shipping_Cost_USD,
                   s.Actual_Transit_Days, s.Delay_Days, s.Customs_Clearance_Hours,
                   s.Damage_Flag, s.Avg_Standard_Duration_Days, s.Shipped_Date
            FROM _stg_fact_shipment s
            LEFT JOIN Fact_Shipment f
                   ON f.Shipment_ID = s.Shipment_ID
                  AND f.Shipped_Date = s.Shipped_Date
            WHERE f.Shipment_ID IS NULL;
        """))
        conn.execute(text("DROP TABLE IF EXISTS _stg_fact_shipment;"))

    return len(fact)


def quarantine(engine, bad_df: pd.DataFrame, source_table: str):
    """Write rejected rows to DQ_Quarantine as JSONB."""
    if bad_df.empty:
        return
    rows = [
        {
            "source_table": source_table,
            "rejected_row": json.dumps(row, default=str),
            "failure_reason": row.get("Failure_Reason", "unknown"),
        }
        for row in bad_df.to_dict(orient="records")
    ]
    with engine.begin() as conn:
        conn.execute(
            text("""INSERT INTO DQ_Quarantine (Source_Table, Rejected_Row, Failure_Reason)
                    VALUES (:source_table, CAST(:rejected_row AS JSONB), :failure_reason)"""),
            rows,
        )

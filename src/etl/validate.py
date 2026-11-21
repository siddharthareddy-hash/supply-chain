import pandera as pa
from pandera import Column, Check
import pandas as pd

shipment_schema = pa.DataFrameSchema(
    {
        "Shipment_ID":         Column(str, pa.Check.str_matches(r"^SH\d{6}$"), unique=True),
        "Shipped_Date":        Column(pa.DateTime),
        "Supplier_ID":         Column(str, pa.Check.str_matches(r"^SUP\d{4}$")),
        "Product_ID":          Column(str, pa.Check.str_matches(r"^P\d{5}$")),
        "Route_ID":            Column(str, pa.Check.str_matches(r"^RT\d{3}$")),
        "Warehouse_ID":        Column(str, pa.Check.str_matches(r"^WH\d{3}$")),
        "Quantity_Shipped":    Column(int,   Check.gt(0)),
        "Shipping_Cost_USD":   Column(float, Check.ge(0)),
        "Actual_Transit_Days": Column(int,   Check.gt(0)),
        "Delay_Days":          Column(int,   Check.ge(0)),
        "Customs_Clearance_Hours": Column(float, Check.ge(0)),
        "Damage_Flag":         Column(bool),
    },
    strict=False,      # allow extra generator columns; loader selects what it needs
    coerce=True,
)


def validate_shipments(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Returns (valid_df, quarantined_df). Quarantined rows get a failure reason."""
    try:
        return shipment_schema.validate(df, lazy=False), pd.DataFrame()
    except pa.errors.SchemaError as exc:
        # Fallback: row-level check to isolate bad rows
        valid_rows, bad_rows = [], []
        for idx, row in df.iterrows():
            try:
                shipment_schema.validate(row.to_frame().T)
                valid_rows.append(row)
            except pa.errors.SchemaError:
                row["Failure_Reason"] = str(exc)[:500]
                bad_rows.append(row)
        return pd.DataFrame(valid_rows), pd.DataFrame(bad_rows)

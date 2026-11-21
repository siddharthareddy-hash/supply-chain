from pathlib import Path
import pandas as pd


def read_shipments(data_dir: Path) -> pd.DataFrame:
    df = pd.read_csv(data_dir / "shipments.csv", parse_dates=["Shipped_Date"])
    return df

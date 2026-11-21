import argparse
from pathlib import Path

from sqlalchemy import create_engine, text

from src.config import get_connection_string
from src.etl.extract import read_shipments
from src.etl.validate import validate_shipments
from src.etl.load import load_dimensions, load_shipments, quarantine


def run(data_dir: Path) -> dict:
    engine = create_engine(get_connection_string())

    # 0. DDL (idempotent)
    for sql_file in ["01_create_dimensions.sql", "02_create_facts.sql"]:
        with open(Path("sql") / sql_file) as f:
            with engine.begin() as conn:
                conn.execute(text(f.read()))

    # 1. Dimensions
    load_dimensions(engine, data_dir)

    # 2. Extract → validate (DQ gate) → load
    raw = read_shipments(data_dir)
    valid, bad = validate_shipments(raw)
    n_loaded = load_shipments(engine, valid, data_dir)
    quarantine(engine, bad, "Fact_Shipment")

    return {
        "rows_in": len(raw),
        "rows_valid": len(valid),
        "rows_quarantined": len(bad),
        "rows_loaded": n_loaded,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data", type=Path)
    args = parser.parse_args()
    stats = run(args.data_dir)
    print("Pipeline complete:", stats)

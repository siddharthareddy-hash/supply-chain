# Supply Chain Intelligence

A data engineering + analytics project analyzing shipment reliability
across transport modes, suppliers, and time — built on a Postgres star schema.

## Stack
- **PostgreSQL** — star schema (`Fact_Shipment` + dimension tables, SCD2 on routes)
- **Python** — ETL (`etl/generate_and_load.py`, seeded synthetic data, ~1,850 shipments)
- **Streamlit + Plotly** — interactive dashboard
- **python-dotenv + psycopg2** — secure DB connectivity

## Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# .env file:
#   POSTGRES_USER=etl_user
#   POSTGRES_PASSWORD=...
python etl/generate_and_load.py
streamlit run dashboard/app.py

import os
import pandas as pd
import plotly.express as px
import streamlit as st
import psycopg2
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Supply Chain Intel", layout="wide")
st.title("📦 Supply Chain Intelligence Dashboard")


@st.cache_data(ttl=600)
def load_query(query: str) -> pd.DataFrame:
    conn = psycopg2.connect(
        host="localhost", port=5432, dbname="supply_chain",
        user=os.getenv("POSTGRES_USER", "etl_user"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )
    try:
        return pd.read_sql(query, conn)
    finally:
        conn.close()


MODE_RELIABILITY = """
SELECT r.Transport_Mode AS mode,
       COUNT(*) AS shipments,
       ROUND(100.0 * AVG((f.Delay_Days > 0)::int), 1) AS pct_delayed,
       ROUND(AVG(f.Delay_Days)::numeric, 2) AS avg_delay_days,
       ROUND(AVG(f.Shipping_Cost_Usd)::numeric, 2) AS avg_ship_cost,
       ROUND(AVG(f.Customs_Fee_Usd)::numeric, 2) AS avg_customs_fee
FROM Fact_Shipment f
JOIN Dim_Route r ON r.Route_Key = f.Route_Key AND r.Is_Current
GROUP BY 1 ORDER BY pct_delayed DESC
"""

SUPPLIER_MATRIX = """
SELECT s.Supplier_Name AS supplier, r.Transport_Mode AS mode,
       COUNT(*) AS shipments,
       ROUND(100.0 * AVG((f.Delay_Days > 0)::int), 1) AS pct_delayed,
       ROUND(AVG(f.Delay_Days)::numeric, 2) AS avg_delay_days
FROM Fact_Shipment f
JOIN Dim_Route r ON r.Route_Key = f.Route_Key AND r.Is_Current
JOIN Dim_Supplier s ON s.Supplier_Key = f.Supplier_Key
GROUP BY 1, 2 HAVING COUNT(*) >= 20
"""

MONTHLY_TREND = """
SELECT DATE_TRUNC('month', f.Shipped_Date)::date AS month,
       r.Transport_Mode AS mode,
       COUNT(*) AS shipments,
       ROUND(100.0 * AVG((f.Delay_Days > 0)::int), 1) AS pct_delayed
FROM Fact_Shipment f
JOIN Dim_Route r ON r.Route_Key = f.Route_Key AND r.Is_Current
GROUP BY 1, 2 ORDER BY 1, 2
"""

# ---- KPI row ----
totals = load_query("""
SELECT COUNT(*) AS shipments,
       ROUND(100.0 * AVG((Delay_Days > 0)::int), 1) AS pct_delayed,
       ROUND(AVG(Delay_Days)::numeric, 2) AS avg_delay,
       ROUND(SUM(Shipping_Cost_Usd + Customs_Fee_Usd)::numeric, 0) AS total_logistics_cost
FROM Fact_Shipment
""").iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Shipments", f"{totals.shipments:,}")
c2.metric("Delayed", f"{totals.pct_delayed}%")
c3.metric("Avg Delay (days)", f"{totals.avg_delay}")
c4.metric("Logistics Cost", f"${float(totals.total_logistics_cost):,.0f}")

# ---- Mode reliability ----
st.subheader("Reliability by Transport Mode")
modes = load_query(MODE_RELIABILITY)
col1, col2 = st.columns(2)
with col1:
    fig = px.bar(modes, x="mode", y="pct_delayed", color="mode",
                 title="% of Shipments Delayed", text_auto=True)
    st.plotly_chart(fig, use_container_width=True)
with col2:
    fig = px.bar(modes, x="mode", y="avg_delay_days", color="mode",
                 title="Avg Delay (days)", text_auto=True)
    st.plotly_chart(fig, use_container_width=True)
st.dataframe(modes, use_container_width=True)

# ---- Monthly trend ----
st.subheader("Delay Rate Over Time")
trend = load_query(MONTHLY_TREND)
fig = px.line(trend, x="month", y="pct_delayed", color="mode", markers=True,
              title="Monthly % Delayed by Mode")
st.plotly_chart(fig, use_container_width=True)

# ---- Supplier × Mode ----
st.subheader("Supplier × Mode Delay Matrix (min 20 shipments)")
matrix = load_query(SUPPLIER_MATRIX)
pivot = matrix.pivot(index="supplier", columns="mode", values="pct_delayed")
fig = px.imshow(pivot, text_auto=True, color_continuous_scale="OrRd",
                title="Delay % Heatmap (red = worse)")
st.plotly_chart(fig, use_container_width=True)

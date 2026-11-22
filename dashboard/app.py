import os
import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

st.set_page_config(page_title="Supply Chain Intel", layout="wide")
st.title("📦 Supply Chain Intelligence Dashboard")

@st.cache_data(ttl=300)
def load_view(view_name):
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "supply_chain"),
        user=os.getenv("POSTGRES_USER", "etl_user"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )
    df = pd.read_sql(f"SELECT * FROM {view_name}", conn)
    conn.close()
    return df

routes    = load_view("v_route_performance")
warehouse = load_view("v_warehouse_cost")
trend     = load_view("v_monthly_delay_trend")
damage    = load_view("v_damage_analysis")

# KPI row
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Shipments", f"{routes.shipments.sum():,}")
c2.metric("Avg On-Time %", f"{(routes.on_time_pct * routes.shipments).sum() / routes.shipments.sum():.1f}%")
c3.metric("Avg Delay (days)", f"{trend.avg_delay.mean():.2f}")
c4.metric("Overall Damage Rate", f"{damage.damaged.sum() / damage.shipments.sum() * 100:.2f}%")

st.subheader("Route Performance")
st.dataframe(routes, use_container_width=True)
fig = px.bar(routes, x="transport_mode", y="on_time_pct",
             color="transport_mode", text="on_time_pct",
             title="On-Time % by Transport Mode")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Monthly Delay Trend")
fig2 = px.line(trend, x="month_name", y="avg_delay",
               color="transport_mode", markers=True,
               title="Avg Delay Days by Mode")
st.plotly_chart(fig2, use_container_width=True)

st.subheader("Cost per KG by Warehouse / Category")
fig3 = px.bar(warehouse.sort_values("cost_per_kg", ascending=False).head(15),
              x="warehouse_name", y="cost_per_kg", color="category",
              barmode="group", title="Cost per KG (top 15)")
st.plotly_chart(fig3, use_container_width=True)

st.subheader("Damage Rate by Supplier / Warehouse")
fig4 = px.scatter(damage, x="reliability_score", y="damage_rate_pct",
                  size="shipments", color="region", hover_name="supplier_name",
                  title="Reliability Score vs Damage Rate")
st.plotly_chart(fig4, use_container_width=True)

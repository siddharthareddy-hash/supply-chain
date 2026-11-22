import os
import pandas as pd
import psycopg2
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import joblib
from dotenv import load_dotenv

load_dotenv()

engine = create_engine(
    f"postgresql://{os.environ['PG_USER']}:{os.environ['PG_PASSWORD']}"
    f"@{os.environ['PG_HOST']}:{os.environ['PG_PORT']}/{os.environ['PG_DB']}"
)

QUERY = """
SELECT f.shipment_id,
       r.transport_mode,
       r.destination_country,
       w.region           AS warehouse_region,
       s.reliability_score,
       p.category         AS product_category,
       p.unit_weight_kg,
       f.quantity_shipped,
       f.shipping_cost_usd,
       f.avg_standard_duration_days,
       EXTRACT(MONTH FROM f.shipped_date)  AS ship_month,
       EXTRACT(DOW   FROM f.shipped_date)  AS ship_dow,
       (f.delay_days > 0) AS is_delayed
FROM fact_shipment f
JOIN dim_route     r ON r.route_key     = f.route_key
JOIN dim_warehouse w ON w.warehouse_key = f.warehouse_key
JOIN dim_supplier  s ON s.supplier_key  = f.supplier_key
JOIN dim_product   p ON p.product_key   = f.product_key
WHERE f.shipped_date < '2024-10-01'          -- hold out the last ~3 months
"""

df = pd.read_sql(QUERY, engine)
print(f"Rows: {len(df)}, delay rate: {df.is_delayed.mean():.1%}")

cat_cols = ["transport_mode", "destination_country", "warehouse_region", "product_category"]
num_cols = ["reliability_score", "unit_weight_kg", "quantity_shipped",
            "shipping_cost_usd", "avg_standard_duration_days", "ship_month", "ship_dow"]

X, y = df[cat_cols + num_cols], df["is_delayed"]

preprocess = ColumnTransformer([
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols),
    ("num", "passthrough", num_cols),
])

model = Pipeline([
    ("prep", preprocess),
    ("clf", RandomForestClassifier(n_estimators=300, min_samples_leaf=5,
                                   class_weight="balanced", random_state=42)),
])

X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25,
                                          stratify=y, random_state=42)
model.fit(X_tr, y_tr)

proba = model.predict_proba(X_te)[:, 1]
print(classification_report(y_te, model.predict(X_te)))
print(f"ROC-AUC: {roc_auc_score(y_te, proba):.3f}")

os.makedirs("ml/artifacts", exist_ok=True)
joblib.dump(model, "ml/artifacts/delay_classifier.joblib")
print("Saved ml/artifacts/delay_classifier.joblib")

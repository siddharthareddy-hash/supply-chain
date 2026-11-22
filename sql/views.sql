-- 1. Route performance: on-time %, avg delay, cost
CREATE OR REPLACE VIEW v_route_performance AS
SELECT r.route_id,
       r.transport_mode,
       r.destination_country,
       COUNT(*)                                          AS shipments,
       ROUND(100.0 * COUNT(*) FILTER (WHERE f.delay_days = 0)
             / COUNT(*), 1)                              AS on_time_pct,
       ROUND(AVG(f.delay_days)::numeric, 2)              AS avg_delay_days,
       ROUND(AVG(f.shipping_cost_usd)::numeric, 2)       AS avg_ship_cost,
       ROUND(AVG(f.customs_fee_usd)::numeric, 2)         AS avg_customs_fee
FROM fact_shipment f
JOIN dim_route r ON f.route_key = r.route_key
GROUP BY r.route_id, r.transport_mode, r.destination_country;

-- 2. Cost efficiency by warehouse & product category
CREATE OR REPLACE VIEW v_warehouse_cost AS
SELECT w.warehouse_id,
       w.warehouse_name,
       w.region,
       p.category,
       COUNT(*)                                            AS shipments,
       SUM(f.quantity_shipped)                             AS units_shipped,
       ROUND(SUM(f.shipping_cost_usd)::numeric, 2)         AS total_ship_cost,
       ROUND((SUM(f.shipping_cost_usd)
              / NULLIF(SUM(f.quantity_shipped * p.unit_weight_kg), 0)
              )::numeric, 4)                               AS cost_per_kg
FROM fact_shipment f
JOIN dim_warehouse w ON f.warehouse_key = w.warehouse_key
JOIN dim_product  p ON f.product_key  = p.product_key
GROUP BY w.warehouse_id, w.warehouse_name, w.region, p.category;

-- 3. Monthly delay trend by transport mode
CREATE OR REPLACE VIEW v_monthly_delay_trend AS
SELECT d.year, d.month, d.month_name,
       r.transport_mode,
       COUNT(*)                                            AS shipments,
       ROUND(AVG(f.delay_days)::numeric, 2)                AS avg_delay,
       ROUND(100.0 * COUNT(*) FILTER (WHERE f.delay_days > 0)
             / COUNT(*), 1)                                AS delayed_pct
FROM fact_shipment f
JOIN dim_date d ON f.date_key = d.date_key
JOIN dim_route r ON f.route_key = r.route_key
GROUP BY d.year, d.month, d.month_name, r.transport_mode;

-- 4. Damage rate by supplier & warehouse
CREATE OR REPLACE VIEW v_damage_analysis AS
SELECT s.supplier_id, s.supplier_name, s.reliability_score,
       w.warehouse_id, w.region,
       COUNT(*)                                            AS shipments,
       COUNT(*) FILTER (WHERE f.damage_flag)               AS damaged,
       ROUND(100.0 * COUNT(*) FILTER (WHERE f.damage_flag)
             / COUNT(*), 2)                                AS damage_rate_pct
FROM fact_shipment f
JOIN dim_supplier  s ON f.supplier_key  = s.supplier_key
JOIN dim_warehouse w ON f.warehouse_key = w.warehouse_key
GROUP BY s.supplier_id, s.supplier_name, s.reliability_score, w.warehouse_id, w.region;

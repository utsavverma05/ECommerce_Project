-- ============================================================
-- 06_seller_decile.sql
-- Decision: Performance tiering — enforce SLA on bottom decile;
--           give preferential routing to top decile.
-- Note: SQLite doesn't have NTILE; Python handles decile binning.
--       This query returns per-seller OTD for Python post-processing.
-- ============================================================

SELECT
    oi.seller_id,
    s.seller_state,
    COUNT(DISTINCT o.order_id)                                   AS total_orders,
    SUM(CASE
        WHEN o.order_delivered_customer_date <= o.order_estimated_delivery_date
        THEN 1 ELSE 0 END)                                       AS on_time,
    ROUND(100.0 * SUM(CASE
        WHEN o.order_delivered_customer_date <= o.order_estimated_delivery_date
        THEN 1 ELSE 0 END) / COUNT(DISTINCT o.order_id), 2)     AS otd_pct,
    ROUND(SUM(oi.price + oi.freight_value), 2)                   AS total_revenue
FROM orders o
JOIN order_items oi ON o.order_id  = oi.order_id
JOIN sellers     s  ON oi.seller_id = s.seller_id
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL
GROUP BY 1, 2
HAVING COUNT(DISTINCT o.order_id) >= 20   -- min volume threshold for stability
ORDER BY otd_pct DESC;

-- ============================================================
-- 02_otd_by_node.sql
-- Decision: Which fulfillment nodes to flag for performance review.
-- Unit: seller_state = warehouse node proxy
-- ============================================================

SELECT
    s.seller_state                                               AS node,
    STRFTIME('%Y-%m', o.order_purchase_timestamp)                AS month,
    COUNT(DISTINCT o.order_id)                                   AS total_orders,
    SUM(CASE
        WHEN o.order_delivered_customer_date <= o.order_estimated_delivery_date
        THEN 1 ELSE 0 END)                                       AS on_time,
    ROUND(100.0 * SUM(CASE
        WHEN o.order_delivered_customer_date <= o.order_estimated_delivery_date
        THEN 1 ELSE 0 END) / COUNT(DISTINCT o.order_id), 2)     AS otd_pct,
    ROUND(AVG(
        JULIANDAY(o.order_delivered_customer_date) -
        JULIANDAY(o.order_estimated_delivery_date)
    ), 2)                                                        AS avg_delay_days
FROM orders o
JOIN order_items oi ON o.order_id  = oi.order_id
JOIN sellers     s  ON oi.seller_id = s.seller_id
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL
GROUP BY 1, 2
ORDER BY 1, 2;

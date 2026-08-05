
SELECT
    s.seller_state                                          AS node,
    COUNT(DISTINCT o.order_id)                              AS total_orders,
    SUM(CASE
        WHEN o.order_status IN ('cancelled','unavailable')
          OR o.order_delivered_customer_date IS NULL
        THEN 1 ELSE 0 END)                                  AS rto_orders,
    ROUND(100.0 * SUM(CASE
        WHEN o.order_status IN ('cancelled','unavailable')
          OR o.order_delivered_customer_date IS NULL
        THEN 1 ELSE 0 END) / COUNT(DISTINCT o.order_id), 2) AS rto_rate_pct,
    ROUND(AVG(oi.price + oi.freight_value), 2)              AS avg_order_value,
    ROUND(SUM(CASE
        WHEN o.order_status IN ('cancelled','unavailable')
          OR o.order_delivered_customer_date IS NULL
        THEN oi.price + oi.freight_value ELSE 0 END), 2)   AS revenue_at_risk
FROM orders o
JOIN order_items oi ON o.order_id  = oi.order_id
JOIN sellers     s  ON oi.seller_id = s.seller_id
GROUP BY 1
ORDER BY rto_rate_pct DESC;

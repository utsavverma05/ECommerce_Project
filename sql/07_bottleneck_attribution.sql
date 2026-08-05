
SELECT
    s.seller_state                                          AS node,
    COUNT(DISTINCT o.order_id)                              AS orders,
    ROUND(AVG(
        JULIANDAY(o.order_delivered_carrier_date) -
        JULIANDAY(o.order_approved_at)
    ), 2)                                                   AS avg_processing_days,
    ROUND(AVG(
        JULIANDAY(o.order_delivered_customer_date) -
        JULIANDAY(o.order_delivered_carrier_date)
    ), 2)                                                   AS avg_transit_days,
    ROUND(AVG(
        JULIANDAY(o.order_delivered_customer_date) -
        JULIANDAY(o.order_approved_at)
    ), 2)                                                   AS avg_total_days,
    ROUND(100.0 * AVG(
        JULIANDAY(o.order_delivered_carrier_date) -
        JULIANDAY(o.order_approved_at)
    ) / AVG(
        JULIANDAY(o.order_delivered_customer_date) -
        JULIANDAY(o.order_approved_at)
    ), 1)                                                   AS processing_pct_of_total
FROM orders o
JOIN order_items oi ON o.order_id  = oi.order_id
JOIN sellers     s  ON oi.seller_id = s.seller_id
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL
  AND o.order_delivered_carrier_date  IS NOT NULL
  AND o.order_approved_at             IS NOT NULL
GROUP BY 1
ORDER BY avg_total_days DESC;

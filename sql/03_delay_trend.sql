
SELECT
    STRFTIME('%Y-%m', order_purchase_timestamp)          AS month,
    COUNT(order_id)                                       AS orders,
    ROUND(AVG(
        JULIANDAY(order_delivered_customer_date) -
        JULIANDAY(order_estimated_delivery_date)
    ), 2)                                                 AS avg_delay_days,
    ROUND(AVG(
        JULIANDAY(order_delivered_carrier_date) -
        JULIANDAY(order_approved_at)
    ), 2)                                                 AS avg_processing_days,
    ROUND(AVG(
        JULIANDAY(order_delivered_customer_date) -
        JULIANDAY(order_delivered_carrier_date)
    ), 2)                                                 AS avg_transit_days,
    ROUND(100.0 * SUM(CASE
        WHEN order_delivered_customer_date <= order_estimated_delivery_date
        THEN 1 ELSE 0 END) / COUNT(order_id), 2)         AS otd_pct
FROM orders
WHERE order_status = 'delivered'
  AND order_delivered_customer_date IS NOT NULL
GROUP BY 1
ORDER BY 1;

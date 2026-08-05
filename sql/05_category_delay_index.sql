-- ============================================================
-- 05_category_delay_index.sql
-- Decision: Which categories to reposition closer to demand nodes.
-- Delay index = order_count × avg_positive_delay (volume-weighted burden).
-- ============================================================

SELECT
    p.product_category_name                                 AS category,
    COUNT(DISTINCT o.order_id)                              AS order_count,
    ROUND(AVG(
        JULIANDAY(o.order_delivered_customer_date) -
        JULIANDAY(o.order_estimated_delivery_date)
    ), 2)                                                   AS avg_delay_days,
    ROUND(AVG(oi.price), 2)                                 AS avg_price,
    ROUND(
        COUNT(DISTINCT o.order_id) *
        MAX(0, AVG(
            JULIANDAY(o.order_delivered_customer_date) -
            JULIANDAY(o.order_estimated_delivery_date)
        )), 1
    )                                                       AS delay_index
FROM orders o
JOIN order_items oi ON o.order_id  = oi.order_id
JOIN products    p  ON oi.product_id = p.product_id
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL
GROUP BY 1
ORDER BY delay_index DESC;

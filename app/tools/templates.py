SQL_USERS_VOLUME = """
SELECT
  traffic_source,
  COUNT(1) AS users,
  MIN(created_at) AS first_user,
  MAX(created_at) AS last_user
FROM `bigquery-public-data.thelook_ecommerce.users`
WHERE DATE(created_at) BETWEEN CAST(@start_date AS DATE) AND CAST(@end_date AS DATE)
  AND (@traffic_source IS NULL OR traffic_source = @traffic_source)
GROUP BY traffic_source
ORDER BY users DESC
"""

SQL_CHANNEL_PERFORMANCE = """
WITH users_in_period AS (
  SELECT
    id AS user_id,
    traffic_source
  FROM `bigquery-public-data.thelook_ecommerce.users`
  WHERE DATE(created_at) BETWEEN CAST(@start_date AS DATE) AND CAST(@end_date AS DATE)
),
orders_in_period AS (
  SELECT
    o.order_id,
    o.user_id,
    o.created_at
  FROM `bigquery-public-data.thelook_ecommerce.orders` o
  WHERE DATE(o.created_at) BETWEEN CAST(@start_date AS DATE) AND CAST(@end_date AS DATE)
    AND o.status IN ('Complete', 'Shipped', 'Delivered')
),
revenue_by_order AS (
  SELECT
    oi.order_id,
    SUM(oi.sale_price) AS revenue
  FROM `bigquery-public-data.thelook_ecommerce.order_items` oi
  WHERE oi.order_id IN (SELECT order_id FROM orders_in_period)
  GROUP BY oi.order_id
)
SELECT
  u.traffic_source AS channel,
  COUNT(DISTINCT u.user_id) AS users,
  COUNT(DISTINCT o.order_id) AS orders,
  COALESCE(SUM(r.revenue), 0) AS revenue,
  SAFE_DIVIDE(COUNT(DISTINCT o.order_id), COUNT(DISTINCT u.user_id)) AS conversion_rate,
  SAFE_DIVIDE(COALESCE(SUM(r.revenue), 0), NULLIF(COUNT(DISTINCT o.order_id), 0)) AS aov
FROM users_in_period u
LEFT JOIN orders_in_period o
  ON o.user_id = u.user_id
LEFT JOIN revenue_by_order r
  ON r.order_id = o.order_id
GROUP BY u.traffic_source
ORDER BY revenue DESC
"""

def get_template(name: str) -> str:
    templates = {
        "users_volume": SQL_USERS_VOLUME,
        "channel_performance": SQL_CHANNEL_PERFORMANCE,
    }
    return templates[name]
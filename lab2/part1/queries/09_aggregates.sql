SELECT COUNT(*)            AS services_total,
       COUNT(cost)         AS with_cost,
       SUM(cost)           AS cost_sum,
       ROUND(AVG(cost), 2) AS cost_avg,
       MIN(cost)           AS cost_min,
       MAX(cost)           AS cost_max
FROM services
WHERE end_date IS NOT NULL;

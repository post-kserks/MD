SELECT work_type,
       COUNT(*)  AS services,
       SUM(cost) AS cost_sum
FROM services
GROUP BY work_type
HAVING COUNT(*) > 3
ORDER BY services DESC;

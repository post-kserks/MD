SELECT m.device_type AS category,
       COUNT(*)      AS computers
FROM computers c
INNER JOIN models m ON m.id_model = c.id_model
WHERE c.status <> 'списан'
GROUP BY m.device_type
HAVING COUNT(*) > 5
ORDER BY computers DESC;

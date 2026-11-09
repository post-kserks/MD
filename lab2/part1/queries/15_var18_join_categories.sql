SELECT c.inv_number,
       m.device_type                   AS category,
       m.manufacturer || ' ' || m.name AS model,
       c.status
FROM computers c
INNER JOIN models m ON m.id_model = c.id_model
ORDER BY m.device_type, c.inv_number;

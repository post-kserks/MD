SELECT inv_number, hostname, status
FROM computers
WHERE id_model IN (SELECT id_model FROM models WHERE device_type = 'ноутбук')
ORDER BY inv_number;

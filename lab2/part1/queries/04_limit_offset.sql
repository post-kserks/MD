SELECT id_service, inv_number, work_type, start_date, cost
FROM services
WHERE cost IS NOT NULL
ORDER BY cost DESC, id_service
LIMIT 5 OFFSET 5;

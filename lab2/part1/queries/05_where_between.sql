SELECT inv_number, commission_date, warranty_end, status
FROM computers
WHERE commission_date BETWEEN '2023-01-01' AND '2024-12-31'
  AND status <> 'списан'
ORDER BY commission_date;

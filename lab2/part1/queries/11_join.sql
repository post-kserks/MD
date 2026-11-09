SELECT c.inv_number,
       m.manufacturer || ' ' || m.name AS model,
       r.building || ', ' || r.number  AS room,
       e.surname || ' ' || e.name       AS employee,
       c.status
FROM computers c
INNER JOIN models m ON m.id_model = c.id_model
INNER JOIN rooms r ON r.id_room = c.id_room
LEFT JOIN assignments a ON a.inv_number = c.inv_number AND a.return_date IS NULL
LEFT JOIN employees e ON e.tab_number = a.tab_number
WHERE c.status <> 'списан'
ORDER BY c.inv_number;

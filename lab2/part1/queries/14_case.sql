SELECT inv_number,
       warranty_end,
       CASE
           WHEN warranty_end IS NULL THEN 'без гарантии'
           WHEN warranty_end < date('now') THEN 'истекла'
           WHEN warranty_end <= date('now', '+180 days') THEN 'истекает в течение полугода'
           ELSE 'действует'
       END AS warranty_state
FROM computers
WHERE status <> 'списан'
ORDER BY warranty_end IS NULL, warranty_end DESC;

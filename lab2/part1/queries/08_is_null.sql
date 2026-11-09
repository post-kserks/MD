SELECT tab_number, surname, name, phone, email
FROM employees
WHERE email IS NULL OR phone IS NULL
ORDER BY surname;

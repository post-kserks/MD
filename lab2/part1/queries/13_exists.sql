SELECT p.name, p.version, p.license_type, p.license_count
FROM programs p
WHERE NOT EXISTS (SELECT 1 FROM software_installs i WHERE i.id_program = p.id_program)
ORDER BY p.name;

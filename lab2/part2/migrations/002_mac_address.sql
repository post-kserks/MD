ALTER TABLE computers ADD COLUMN mac_address TEXT
    CHECK (mac_address IS NULL OR mac_address GLOB
           '[0-9A-F][0-9A-F]:[0-9A-F][0-9A-F]:[0-9A-F][0-9A-F]:[0-9A-F][0-9A-F]:[0-9A-F][0-9A-F]:[0-9A-F][0-9A-F]');

CREATE UNIQUE INDEX ux_computers_mac ON computers (mac_address);

UPDATE computers
SET mac_address = printf('00:1A:2B:00:%02X:%02X',
                         CAST(substr(inv_number, 4) AS INTEGER) / 256,
                         CAST(substr(inv_number, 4) AS INTEGER) % 256)
WHERE hostname IS NOT NULL;

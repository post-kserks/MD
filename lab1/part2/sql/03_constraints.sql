PRAGMA foreign_keys = OFF;
BEGIN TRANSACTION;

CREATE TABLE departments_new (
    id_department INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL UNIQUE CHECK (length(trim(name)) > 0)
);
INSERT INTO departments_new (id_department, name)
SELECT id_department, name FROM departments;
DROP TABLE departments;
ALTER TABLE departments_new RENAME TO departments;

CREATE TABLE rooms_new (
    id_room   INTEGER PRIMARY KEY AUTOINCREMENT,
    building  TEXT    NOT NULL CHECK (length(trim(building)) > 0),
    number    TEXT    NOT NULL CHECK (length(trim(number)) > 0),
    floor     INTEGER NOT NULL CHECK (floor BETWEEN -3 AND 50),
    room_type TEXT    NOT NULL DEFAULT 'кабинет'
                      CHECK (room_type IN ('кабинет', 'серверная', 'склад')),
    UNIQUE (building, number)
);
INSERT INTO rooms_new (id_room, building, number, floor, room_type)
SELECT id_room, building, number, floor, room_type FROM rooms;
DROP TABLE rooms;
ALTER TABLE rooms_new RENAME TO rooms;

CREATE TABLE models_new (
    id_model     INTEGER PRIMARY KEY AUTOINCREMENT,
    manufacturer TEXT    NOT NULL CHECK (length(trim(manufacturer)) > 0),
    name         TEXT    NOT NULL CHECK (length(trim(name)) > 0),
    device_type  TEXT    NOT NULL DEFAULT 'настольный ПК'
                         CHECK (device_type IN ('настольный ПК', 'моноблок', 'ноутбук', 'сервер')),
    UNIQUE (manufacturer, name)
);
INSERT INTO models_new (id_model, manufacturer, name, device_type)
SELECT id_model, manufacturer, name, device_type FROM models;
DROP TABLE models;
ALTER TABLE models_new RENAME TO models;

CREATE TABLE employees_new (
    tab_number     TEXT    NOT NULL PRIMARY KEY
                           CHECK (length(tab_number) = 6 AND tab_number NOT GLOB '*[^0-9]*'),
    surname        TEXT    NOT NULL CHECK (length(trim(surname)) > 0),
    name           TEXT    NOT NULL CHECK (length(trim(name)) > 0),
    patronymic     TEXT,
    position       TEXT    NOT NULL CHECK (length(trim(position)) > 0),
    phone          TEXT    CHECK (phone IS NULL OR phone NOT GLOB '*[^0-9+() -]*'),
    email          TEXT    UNIQUE CHECK (email IS NULL OR email LIKE '_%@_%._%'),
    dismissal_date TEXT    CHECK (dismissal_date IS NULL OR dismissal_date IS date(dismissal_date)),
    id_department  INTEGER NOT NULL
                           REFERENCES departments (id_department)
                           ON UPDATE CASCADE ON DELETE RESTRICT
);
INSERT INTO employees_new (tab_number, surname, name, patronymic, position, phone,
                           email, dismissal_date, id_department)
SELECT tab_number, surname, name, patronymic, position, phone,
       email, dismissal_date, id_department FROM employees;
DROP TABLE employees;
ALTER TABLE employees_new RENAME TO employees;

CREATE TABLE computers_new (
    inv_number      TEXT    NOT NULL PRIMARY KEY
                            CHECK (inv_number GLOB 'ПК-[0-9][0-9][0-9][0-9][0-9]'),
    serial_number   TEXT    NOT NULL UNIQUE CHECK (length(trim(serial_number)) > 0),
    hostname        TEXT    UNIQUE
                            CHECK (hostname IS NULL OR (length(hostname) BETWEEN 1 AND 15
                                   AND hostname NOT GLOB '*[^A-Za-z0-9-]*')),
    commission_date TEXT    NOT NULL DEFAULT (date('now'))
                            CHECK (commission_date IS date(commission_date)),
    warranty_end    TEXT    CHECK (warranty_end IS NULL OR (warranty_end IS date(warranty_end)
                                   AND warranty_end >= commission_date)),
    status          TEXT    NOT NULL DEFAULT 'в резерве'
                            CHECK (status IN ('в эксплуатации', 'в резерве', 'в ремонте', 'списан')),
    writeoff_date   TEXT    CHECK (writeoff_date IS NULL OR (writeoff_date IS date(writeoff_date)
                                   AND writeoff_date >= commission_date)),
    id_model        INTEGER NOT NULL
                            REFERENCES models (id_model) ON UPDATE CASCADE ON DELETE RESTRICT,
    id_room         INTEGER NOT NULL
                            REFERENCES rooms (id_room) ON UPDATE CASCADE ON DELETE RESTRICT,

    CHECK ((status = 'списан') = (writeoff_date IS NOT NULL))
);
INSERT INTO computers_new (inv_number, serial_number, hostname, commission_date, warranty_end,
                           status, writeoff_date, id_model, id_room)
SELECT inv_number, serial_number, hostname, commission_date, warranty_end,
       status, writeoff_date, id_model, id_room FROM computers;
DROP TABLE computers;
ALTER TABLE computers_new RENAME TO computers;

CREATE TABLE components_new (
    id_component   INTEGER PRIMARY KEY AUTOINCREMENT,
    component_type TEXT    NOT NULL
                           CHECK (component_type IN ('процессор', 'оперативная память', 'накопитель',
                                                     'видеокарта', 'материнская плата', 'блок питания')),
    manufacturer   TEXT    NOT NULL,
    model          TEXT    NOT NULL,
    serial_number  TEXT    UNIQUE,
    param_value    REAL    CHECK (param_value IS NULL OR param_value > 0),
    unit           TEXT    CHECK (unit IS NULL OR unit IN ('ГБ', 'ТБ', 'ГГц', 'Вт')),

    inv_number     TEXT    REFERENCES computers (inv_number)
                           ON UPDATE CASCADE ON DELETE SET NULL,

    CHECK ((param_value IS NULL) = (unit IS NULL))
);
INSERT INTO components_new (id_component, component_type, manufacturer, model, serial_number,
                            param_value, unit, inv_number)
SELECT id_component, component_type, manufacturer, model, serial_number,
       param_value, unit, inv_number FROM components;
DROP TABLE components;
ALTER TABLE components_new RENAME TO components;

CREATE TABLE programs_new (
    id_program    INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL CHECK (length(trim(name)) > 0),
    version       TEXT    NOT NULL,
    developer     TEXT    NOT NULL,
    license_type  TEXT    NOT NULL DEFAULT 'бесплатная'
                          CHECK (license_type IN ('бесплатная', 'коммерческая', 'подписка')),
    license_count INTEGER CHECK (license_count IS NULL OR license_count > 0),
    UNIQUE (name, version),

    CHECK ((license_type = 'бесплатная') = (license_count IS NULL))
);
INSERT INTO programs_new (id_program, name, version, developer, license_type, license_count)
SELECT id_program, name, version, developer, license_type, license_count FROM programs;
DROP TABLE programs;
ALTER TABLE programs_new RENAME TO programs;

CREATE TABLE assignments_new (
    id_assignment INTEGER PRIMARY KEY AUTOINCREMENT,
    tab_number    TEXT    NOT NULL
                          REFERENCES employees (tab_number) ON UPDATE CASCADE ON DELETE RESTRICT,
    inv_number    TEXT    NOT NULL
                          REFERENCES computers (inv_number) ON UPDATE CASCADE ON DELETE CASCADE,
    issue_date    TEXT    NOT NULL DEFAULT (date('now')) CHECK (issue_date IS date(issue_date)),
    return_date   TEXT    CHECK (return_date IS NULL OR (return_date IS date(return_date)
                                 AND return_date >= issue_date)),
    doc_number    TEXT
);
INSERT INTO assignments_new (id_assignment, tab_number, inv_number, issue_date, return_date, doc_number)
SELECT id_assignment, tab_number, inv_number, issue_date, return_date, doc_number FROM assignments;
DROP TABLE assignments;
ALTER TABLE assignments_new RENAME TO assignments;

CREATE TABLE software_installs_new (
    inv_number   TEXT    NOT NULL
                         REFERENCES computers (inv_number) ON UPDATE CASCADE ON DELETE CASCADE,
    id_program   INTEGER NOT NULL
                         REFERENCES programs (id_program) ON UPDATE CASCADE ON DELETE CASCADE,
    install_date TEXT    NOT NULL DEFAULT (date('now')) CHECK (install_date IS date(install_date)),

    PRIMARY KEY (inv_number, id_program)
);
INSERT INTO software_installs_new (inv_number, id_program, install_date)
SELECT inv_number, id_program, install_date FROM software_installs;
DROP TABLE software_installs;
ALTER TABLE software_installs_new RENAME TO software_installs;

CREATE TABLE services_new (
    id_service          INTEGER PRIMARY KEY AUTOINCREMENT,
    inv_number          TEXT    NOT NULL
                                REFERENCES computers (inv_number) ON UPDATE CASCADE ON DELETE CASCADE,
    work_type           TEXT    NOT NULL DEFAULT 'ремонт'
                                CHECK (work_type IN ('ремонт', 'модернизация', 'профилактика', 'диагностика')),
    start_date          TEXT    NOT NULL DEFAULT (date('now')) CHECK (start_date IS date(start_date)),
    end_date            TEXT    CHECK (end_date IS NULL OR (end_date IS date(end_date)
                                       AND end_date >= start_date)),
    fault_description   TEXT,
    works_done          TEXT,
    cost                REAL    CHECK (cost IS NULL OR cost >= 0),
    executor_tab_number TEXT    REFERENCES employees (tab_number) ON UPDATE CASCADE ON DELETE RESTRICT,
    service_org         TEXT    CHECK (service_org IS NULL OR length(trim(service_org)) > 0),

    CHECK ((executor_tab_number IS NULL) <> (service_org IS NULL))
);
INSERT INTO services_new (id_service, inv_number, work_type, start_date, end_date, fault_description,
                          works_done, cost, executor_tab_number, service_org)
SELECT id_service, inv_number, work_type, start_date, end_date, fault_description,
       works_done, cost, executor_tab_number, service_org FROM services;
DROP TABLE services;
ALTER TABLE services_new RENAME TO services;

CREATE UNIQUE INDEX ux_assignments_active ON assignments (inv_number) WHERE return_date IS NULL;

CREATE UNIQUE INDEX ux_services_open ON services (inv_number) WHERE end_date IS NULL;

CREATE INDEX ix_employees_department ON employees (id_department);
CREATE INDEX ix_computers_model ON computers (id_model);
CREATE INDEX ix_computers_room ON computers (id_room);
CREATE INDEX ix_components_computer ON components (inv_number);
CREATE INDEX ix_assignments_employee ON assignments (tab_number);
CREATE INDEX ix_assignments_computer ON assignments (inv_number);
CREATE INDEX ix_installs_program ON software_installs (id_program);
CREATE INDEX ix_services_computer ON services (inv_number);
CREATE INDEX ix_services_executor ON services (executor_tab_number);

COMMIT;
PRAGMA foreign_keys = ON;
PRAGMA foreign_key_check;

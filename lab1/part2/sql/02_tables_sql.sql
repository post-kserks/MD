CREATE TABLE employees (
    tab_number     TEXT PRIMARY KEY,
    surname        TEXT,
    name           TEXT,
    patronymic     TEXT,
    position       TEXT,
    phone          TEXT,
    email          TEXT,
    dismissal_date TEXT,
    id_department  INTEGER
);

CREATE TABLE computers (
    inv_number      TEXT PRIMARY KEY,
    serial_number   TEXT,
    hostname        TEXT,
    commission_date TEXT,
    warranty_end    TEXT,
    status          TEXT,
    writeoff_date   TEXT,
    id_model        INTEGER,
    id_room         INTEGER
);

CREATE TABLE components (
    id_component   INTEGER PRIMARY KEY AUTOINCREMENT,
    component_type TEXT,
    manufacturer   TEXT,
    model          TEXT,
    serial_number  TEXT,
    param_value    REAL,
    unit           TEXT,
    inv_number     TEXT
);

CREATE TABLE programs (
    id_program    INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT,
    version       TEXT,
    developer     TEXT,
    license_type  TEXT,
    license_count INTEGER
);

CREATE TABLE assignments (
    id_assignment INTEGER PRIMARY KEY AUTOINCREMENT,
    tab_number    TEXT,
    inv_number    TEXT,
    issue_date    TEXT,
    return_date   TEXT,
    doc_number    TEXT
);

CREATE TABLE software_installs (
    inv_number   TEXT,
    id_program   INTEGER,
    install_date TEXT,
    PRIMARY KEY (inv_number, id_program)
);

CREATE TABLE services (
    id_service          INTEGER PRIMARY KEY AUTOINCREMENT,
    inv_number          TEXT,
    work_type           TEXT,
    start_date          TEXT,
    end_date            TEXT,
    fault_description   TEXT,
    works_done          TEXT,
    cost                REAL,
    executor_tab_number TEXT,
    service_org         TEXT
);

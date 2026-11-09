CREATE TABLE departments (
    id_department INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT
);

CREATE TABLE rooms (
    id_room   INTEGER PRIMARY KEY AUTOINCREMENT,
    building  TEXT,
    number    TEXT,
    floor     INTEGER,
    room_type TEXT
);

CREATE TABLE models (
    id_model     INTEGER PRIMARY KEY AUTOINCREMENT,
    manufacturer TEXT,
    name         TEXT,
    device_type  TEXT
);

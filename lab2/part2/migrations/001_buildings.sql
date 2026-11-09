CREATE TABLE buildings (
    id_building INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE CHECK (length(trim(name)) > 0),
    address     TEXT
);

INSERT INTO buildings (name)
SELECT DISTINCT building FROM rooms ORDER BY building;

UPDATE buildings SET address = 'г. Москва, ул. Бауманская, д. 10'
WHERE name = 'Главный корпус';
UPDATE buildings SET address = 'г. Москва, ул. Бауманская, д. 10, стр. 2'
WHERE name = 'Корпус Б';

CREATE TABLE rooms_new (
    id_room     INTEGER PRIMARY KEY AUTOINCREMENT,
    id_building INTEGER NOT NULL
                        REFERENCES buildings (id_building) ON UPDATE CASCADE ON DELETE RESTRICT,
    number      TEXT    NOT NULL CHECK (length(trim(number)) > 0),
    floor       INTEGER NOT NULL CHECK (floor BETWEEN -3 AND 50),
    room_type   TEXT    NOT NULL DEFAULT 'кабинет'
                        CHECK (room_type IN ('кабинет', 'серверная', 'склад')),
    UNIQUE (id_building, number)
);

INSERT INTO rooms_new (id_room, id_building, number, floor, room_type)
SELECT r.id_room, b.id_building, r.number, r.floor, r.room_type
FROM rooms r
JOIN buildings b ON b.name = r.building;

DROP TABLE rooms;
ALTER TABLE rooms_new RENAME TO rooms;
CREATE INDEX ix_rooms_building ON rooms (id_building);

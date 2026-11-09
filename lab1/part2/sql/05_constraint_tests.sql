PRAGMA foreign_keys = ON;
BEGIN TRANSACTION;

SELECT 'T01 | NOT NULL | Сотрудник без фамилии | ожидается: ошибка' AS test;
INSERT INTO employees (tab_number, name, position, id_department) VALUES ('700701', 'Иван', 'Логист', 7);

SELECT 'T02 | NOT NULL | Компьютер без серийного номера | ожидается: ошибка' AS test;
INSERT INTO computers (inv_number, id_model, id_room) VALUES ('ПК-00100', 1, 8);

SELECT 'T03 | NOT NULL | Текстовый первичный ключ равен NULL | ожидается: ошибка' AS test;
INSERT INTO computers (inv_number, serial_number, id_model, id_room) VALUES (NULL, 'TEST-NULL-PK', 1, 8);

SELECT 'T04 | UNIQUE | Повтор серийного номера компьютера | ожидается: ошибка' AS test;
INSERT INTO computers (inv_number, serial_number, id_model, id_room) SELECT 'ПК-00100', serial_number, 1, 8 FROM computers WHERE inv_number = 'ПК-00002';

SELECT 'T05 | UNIQUE | Повтор пары «здание + номер» помещения | ожидается: ошибка' AS test;
INSERT INTO rooms (building, number, floor) VALUES ('Главный корпус', '101', 1);

SELECT 'T06 | UNIQUE | Повтор e-mail сотрудника | ожидается: ошибка' AS test;
INSERT INTO employees (tab_number, surname, name, position, email, id_department) VALUES ('700701', 'Иванов', 'Иван', 'Логист', 'm.ivanova@firma.ru', 7);

SELECT 'T07 | UNIQUE (частичный индекс) | Второе действующее закрепление компьютера (БО1) | ожидается: ошибка' AS test;
INSERT INTO assignments (tab_number, inv_number, issue_date) VALUES ('200205', 'ПК-00002', '2026-11-09');

SELECT 'T08 | PRIMARY KEY (составной) | Повторная установка программы на компьютер | ожидается: ошибка' AS test;
INSERT INTO software_installs (inv_number, id_program, install_date) VALUES ('ПК-00002', 1, '2026-11-09');

SELECT 'T09 | DEFAULT | Помещение без типа получает «кабинет» | ожидается: успех' AS test;
INSERT INTO rooms (building, number, floor) VALUES ('Корпус Б', '120', 1);
SELECT room_type FROM rooms WHERE building = 'Корпус Б' AND number = '120';

SELECT 'T10 | DEFAULT | Новый компьютер: состояние и дата ввода по умолчанию | ожидается: успех' AS test;
INSERT INTO computers (inv_number, serial_number, id_model, id_room) VALUES ('ПК-00100', 'TEST-DEFAULT', 1, 10);
SELECT status, commission_date = date('now') AS today FROM computers WHERE inv_number = 'ПК-00100';

SELECT 'T11 | CHECK | Недопустимое состояние компьютера | ожидается: ошибка' AS test;
UPDATE computers SET status = 'сломан' WHERE inv_number = 'ПК-00002';

SELECT 'T12 | CHECK | Инвентарный номер не по формату «ПК-NNNNN» | ожидается: ошибка' AS test;
INSERT INTO computers (inv_number, serial_number, id_model, id_room) VALUES ('PC-1', 'TEST-FORMAT', 1, 8);

SELECT 'T13 | CHECK | Этаж вне диапазона −3…50 | ожидается: ошибка' AS test;
INSERT INTO rooms (building, number, floor) VALUES ('Корпус Б', '999', 99);

SELECT 'T14 | CHECK | Дата возврата раньше даты выдачи | ожидается: ошибка' AS test;
UPDATE assignments SET return_date = '2000-01-01' WHERE inv_number = 'ПК-00002' AND return_date IS NULL;

SELECT 'T15 | CHECK | «Списан» без даты списания (БО5) | ожидается: ошибка' AS test;
UPDATE computers SET status = 'списан' WHERE inv_number = 'ПК-00004';

SELECT 'T16 | CHECK | У обслуживания два исполнителя сразу (БО7) | ожидается: ошибка' AS test;
INSERT INTO services (inv_number, executor_tab_number, service_org) VALUES ('ПК-00002', '400402', 'ООО «СервисПлюс»');

SELECT 'T17 | CHECK | Платная программа без количества лицензий (БО9) | ожидается: ошибка' AS test;
INSERT INTO programs (name, version, developer, license_type) VALUES ('Kompas-3D', 'v22', 'АСКОН', 'коммерческая');

SELECT 'T18 | CHECK | Отрицательная стоимость обслуживания | ожидается: ошибка' AS test;
UPDATE services SET cost = -100 WHERE id_service = 1;

SELECT 'T19 | CHECK | Дата в неверном формате | ожидается: ошибка' AS test;
UPDATE computers SET warranty_end = '31.12.2027' WHERE inv_number = 'ПК-00002';

SELECT 'T20 | FOREIGN KEY | Сотрудник в несуществующем отделе | ожидается: ошибка' AS test;
INSERT INTO employees (tab_number, surname, name, position, id_department) VALUES ('700701', 'Иванов', 'Иван', 'Логист', 99);

SELECT 'T21 | FOREIGN KEY, ON DELETE RESTRICT | Удаление отдела, в котором есть сотрудники | ожидается: ошибка' AS test;
DELETE FROM departments WHERE id_department = 1;

SELECT 'T22 | FOREIGN KEY, ON DELETE RESTRICT | Удаление сотрудника с историей закреплений | ожидается: ошибка' AS test;
DELETE FROM employees WHERE tab_number = '400402';

SELECT 'T23 | FOREIGN KEY, ON DELETE RESTRICT | Удаление модели без компьютеров | ожидается: успех' AS test;
DELETE FROM models WHERE id_model = 11;
SELECT COUNT(*) AS models_left FROM models;

SELECT 'T24 | ON UPDATE CASCADE | Смена инвентарного номера ПК-00007 → ПК-09999 | ожидается: успех' AS test;
UPDATE computers SET inv_number = 'ПК-09999' WHERE inv_number = 'ПК-00007';
SELECT (SELECT COUNT(*) FROM assignments WHERE inv_number = 'ПК-09999') AS assignments, (SELECT COUNT(*) FROM software_installs WHERE inv_number = 'ПК-09999') AS installs, (SELECT COUNT(*) FROM services WHERE inv_number = 'ПК-09999') AS services, (SELECT COUNT(*) FROM components WHERE inv_number = 'ПК-09999') AS components, (SELECT COUNT(*) FROM assignments WHERE inv_number = 'ПК-00007') AS old_refs;

SELECT 'T25 | ON UPDATE CASCADE | Смена кода ИТ-отдела 4 → 40 | ожидается: успех' AS test;
UPDATE departments SET id_department = 40 WHERE id_department = 4;
SELECT (SELECT COUNT(*) FROM employees WHERE id_department = 40) AS moved, (SELECT COUNT(*) FROM employees WHERE id_department = 4) AS left_old;

SELECT 'T26 | ON DELETE CASCADE / SET NULL | Удаление компьютера ПК-00012 | ожидается: успех' AS test;
DELETE FROM computers WHERE inv_number = 'ПК-00012';
SELECT (SELECT COUNT(*) FROM assignments WHERE inv_number = 'ПК-00012') AS assignments, (SELECT COUNT(*) FROM services WHERE inv_number = 'ПК-00012') AS services, (SELECT COUNT(*) FROM software_installs WHERE inv_number = 'ПК-00012') AS installs, (SELECT COUNT(*) FROM components WHERE inv_number IS NULL) AS on_stock;

SELECT 'T27 | ON DELETE CASCADE | Удаление программы Adobe Photoshop | ожидается: успех' AS test;
DELETE FROM programs WHERE id_program = 5;
SELECT COUNT(*) AS photoshop_installs FROM software_installs WHERE id_program = 5;

ROLLBACK;

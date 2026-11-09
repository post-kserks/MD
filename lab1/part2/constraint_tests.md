| № | Ограничение | Проверка | Ожидалось | Результат SQLite |
| --- | --- | --- | --- | --- |
| T01 | NOT NULL | Сотрудник без фамилии | ошибка | ✔ NOT NULL constraint failed: employees.surname |
| T02 | NOT NULL | Компьютер без серийного номера | ошибка | ✔ NOT NULL constraint failed: computers.serial_number |
| T03 | NOT NULL | Текстовый первичный ключ равен NULL | ошибка | ✔ NOT NULL constraint failed: computers.inv_number |
| T04 | UNIQUE | Повтор серийного номера компьютера | ошибка | ✔ UNIQUE constraint failed: computers.serial_number |
| T05 | UNIQUE | Повтор пары «здание + номер» помещения | ошибка | ✔ UNIQUE constraint failed: rooms.building, rooms.number |
| T06 | UNIQUE | Повтор e-mail сотрудника | ошибка | ✔ UNIQUE constraint failed: employees.email |
| T07 | UNIQUE (частичный индекс) | Второе действующее закрепление компьютера (БО1) | ошибка | ✔ UNIQUE constraint failed: assignments.inv_number |
| T08 | PRIMARY KEY (составной) | Повторная установка программы на компьютер | ошибка | ✔ UNIQUE constraint failed: software_installs.inv_number, software_installs.id_program |
| T09 | DEFAULT | Помещение без типа получает «кабинет» | успех | ✔ выполнено; room_type=кабинет |
| T10 | DEFAULT | Новый компьютер: состояние и дата ввода по умолчанию | успех | ✔ выполнено; status=в резерве, today=1 |
| T11 | CHECK | Недопустимое состояние компьютера | ошибка | ✔ CHECK constraint failed: status IN ('в эксплуатации', 'в резерве', 'в ремонте', 'списан') |
| T12 | CHECK | Инвентарный номер не по формату «ПК-NNNNN» | ошибка | ✔ CHECK constraint failed: inv_number GLOB 'ПК-[0-9][0-9][0-9][0-9][0-9]' |
| T13 | CHECK | Этаж вне диапазона −3…50 | ошибка | ✔ CHECK constraint failed: floor BETWEEN -3 AND 50 |
| T14 | CHECK | Дата возврата раньше даты выдачи | ошибка | ✔ CHECK constraint failed: return_date IS NULL OR (return_date IS date(return_date) AND return_date >= issue_date) |
| T15 | CHECK | «Списан» без даты списания (БО5) | ошибка | ✔ CHECK constraint failed: (status = 'списан') = (writeoff_date IS NOT NULL) |
| T16 | CHECK | У обслуживания два исполнителя сразу (БО7) | ошибка | ✔ CHECK constraint failed: (executor_tab_number IS NULL) <> (service_org IS NULL) |
| T17 | CHECK | Платная программа без количества лицензий (БО9) | ошибка | ✔ CHECK constraint failed: (license_type = 'бесплатная') = (license_count IS NULL) |
| T18 | CHECK | Отрицательная стоимость обслуживания | ошибка | ✔ CHECK constraint failed: cost IS NULL OR cost >= 0 |
| T19 | CHECK | Дата в неверном формате | ошибка | ✔ CHECK constraint failed: warranty_end IS NULL OR (warranty_end IS date(warranty_end) AND warranty_end >= commission_date) |
| T20 | FOREIGN KEY | Сотрудник в несуществующем отделе | ошибка | ✔ FOREIGN KEY constraint failed |
| T21 | FOREIGN KEY, ON DELETE RESTRICT | Удаление отдела, в котором есть сотрудники | ошибка | ✔ FOREIGN KEY constraint failed |
| T22 | FOREIGN KEY, ON DELETE RESTRICT | Удаление сотрудника с историей закреплений | ошибка | ✔ FOREIGN KEY constraint failed |
| T23 | FOREIGN KEY, ON DELETE RESTRICT | Удаление модели без компьютеров | успех | ✔ выполнено; models_left=10 |
| T24 | ON UPDATE CASCADE | Смена инвентарного номера ПК-00007 → ПК-09999 | успех | ✔ выполнено; assignments=2, installs=6, services=1, components=4, old_refs=0 |
| T25 | ON UPDATE CASCADE | Смена кода ИТ-отдела 4 → 40 | успех | ✔ выполнено; moved=3, left_old=0 |
| T26 | ON DELETE CASCADE / SET NULL | Удаление компьютера ПК-00012 | успех | ✔ выполнено; assignments=0, services=0, installs=0, on_stock=13 |
| T27 | ON DELETE CASCADE | Удаление программы Adobe Photoshop | успех | ✔ выполнено; photoshop_installs=0 |

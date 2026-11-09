import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "db" / "computers.db"

TESTS = [
    ("NOT NULL", "Сотрудник без фамилии", "error", [
        "INSERT INTO employees (tab_number, name, position, id_department) "
        "VALUES ('700701', 'Иван', 'Логист', 7)"], None),
    ("NOT NULL", "Компьютер без серийного номера", "error", [
        "INSERT INTO computers (inv_number, id_model, id_room) VALUES ('ПК-00100', 1, 8)"], None),
    ("NOT NULL", "Текстовый первичный ключ равен NULL", "error", [
        "INSERT INTO computers (inv_number, serial_number, id_model, id_room) "
        "VALUES (NULL, 'TEST-NULL-PK', 1, 8)"], None),
    ("UNIQUE", "Повтор серийного номера компьютера", "error", [
        "INSERT INTO computers (inv_number, serial_number, id_model, id_room) "
        "SELECT 'ПК-00100', serial_number, 1, 8 FROM computers WHERE inv_number = 'ПК-00002'"], None),
    ("UNIQUE", "Повтор пары «здание + номер» помещения", "error", [
        "INSERT INTO rooms (building, number, floor) VALUES ('Главный корпус', '101', 1)"], None),
    ("UNIQUE", "Повтор e-mail сотрудника", "error", [
        "INSERT INTO employees (tab_number, surname, name, position, email, id_department) "
        "VALUES ('700701', 'Иванов', 'Иван', 'Логист', 'm.ivanova@firma.ru', 7)"], None),
    ("UNIQUE (частичный индекс)", "Второе действующее закрепление компьютера (БО1)", "error", [
        "INSERT INTO assignments (tab_number, inv_number, issue_date) "
        "VALUES ('200205', 'ПК-00002', '2026-11-09')"], None),
    ("PRIMARY KEY (составной)", "Повторная установка программы на компьютер", "error", [
        "INSERT INTO software_installs (inv_number, id_program, install_date) "
        "VALUES ('ПК-00002', 1, '2026-11-09')"], None),
    ("DEFAULT", "Помещение без типа получает «кабинет»", "ok", [
        "INSERT INTO rooms (building, number, floor) VALUES ('Корпус Б', '120', 1)"],
        "SELECT room_type FROM rooms WHERE building = 'Корпус Б' AND number = '120'"),
    ("DEFAULT", "Новый компьютер: состояние и дата ввода по умолчанию", "ok", [
        "INSERT INTO computers (inv_number, serial_number, id_model, id_room) "
        "VALUES ('ПК-00100', 'TEST-DEFAULT', 1, 10)"],
        "SELECT status, commission_date = date('now') AS today FROM computers "
        "WHERE inv_number = 'ПК-00100'"),
    ("CHECK", "Недопустимое состояние компьютера", "error", [
        "UPDATE computers SET status = 'сломан' WHERE inv_number = 'ПК-00002'"], None),
    ("CHECK", "Инвентарный номер не по формату «ПК-NNNNN»", "error", [
        "INSERT INTO computers (inv_number, serial_number, id_model, id_room) "
        "VALUES ('PC-1', 'TEST-FORMAT', 1, 8)"], None),
    ("CHECK", "Этаж вне диапазона −3…50", "error", [
        "INSERT INTO rooms (building, number, floor) VALUES ('Корпус Б', '999', 99)"], None),
    ("CHECK", "Дата возврата раньше даты выдачи", "error", [
        "UPDATE assignments SET return_date = '2000-01-01' WHERE inv_number = 'ПК-00002' "
        "AND return_date IS NULL"], None),
    ("CHECK", "«Списан» без даты списания (БО5)", "error", [
        "UPDATE computers SET status = 'списан' WHERE inv_number = 'ПК-00004'"], None),
    ("CHECK", "У обслуживания два исполнителя сразу (БО7)", "error", [
        "INSERT INTO services (inv_number, executor_tab_number, service_org) "
        "VALUES ('ПК-00002', '400402', 'ООО «СервисПлюс»')"], None),
    ("CHECK", "Платная программа без количества лицензий (БО9)", "error", [
        "INSERT INTO programs (name, version, developer, license_type) "
        "VALUES ('Kompas-3D', 'v22', 'АСКОН', 'коммерческая')"], None),
    ("CHECK", "Отрицательная стоимость обслуживания", "error", [
        "UPDATE services SET cost = -100 WHERE id_service = 1"], None),
    ("CHECK", "Дата в неверном формате", "error", [
        "UPDATE computers SET warranty_end = '31.12.2027' WHERE inv_number = 'ПК-00002'"], None),
    ("FOREIGN KEY", "Сотрудник в несуществующем отделе", "error", [
        "INSERT INTO employees (tab_number, surname, name, position, id_department) "
        "VALUES ('700701', 'Иванов', 'Иван', 'Логист', 99)"], None),
    ("FOREIGN KEY, ON DELETE RESTRICT", "Удаление отдела, в котором есть сотрудники", "error", [
        "DELETE FROM departments WHERE id_department = 1"], None),
    ("FOREIGN KEY, ON DELETE RESTRICT", "Удаление сотрудника с историей закреплений", "error", [
        "DELETE FROM employees WHERE tab_number = '400402'"], None),
    ("FOREIGN KEY, ON DELETE RESTRICT", "Удаление модели без компьютеров", "ok", [
        "DELETE FROM models WHERE id_model = 11"],
        "SELECT COUNT(*) AS models_left FROM models"),
    ("ON UPDATE CASCADE", "Смена инвентарного номера ПК-00007 → ПК-09999", "ok", [
        "UPDATE computers SET inv_number = 'ПК-09999' WHERE inv_number = 'ПК-00007'"],
        "SELECT (SELECT COUNT(*) FROM assignments WHERE inv_number = 'ПК-09999') AS assignments, "
        "(SELECT COUNT(*) FROM software_installs WHERE inv_number = 'ПК-09999') AS installs, "
        "(SELECT COUNT(*) FROM services WHERE inv_number = 'ПК-09999') AS services, "
        "(SELECT COUNT(*) FROM components WHERE inv_number = 'ПК-09999') AS components, "
        "(SELECT COUNT(*) FROM assignments WHERE inv_number = 'ПК-00007') AS old_refs"),
    ("ON UPDATE CASCADE", "Смена кода ИТ-отдела 4 → 40", "ok", [
        "UPDATE departments SET id_department = 40 WHERE id_department = 4"],
        "SELECT (SELECT COUNT(*) FROM employees WHERE id_department = 40) AS moved, "
        "(SELECT COUNT(*) FROM employees WHERE id_department = 4) AS left_old"),
    ("ON DELETE CASCADE / SET NULL", "Удаление компьютера ПК-00012", "ok", [
        "DELETE FROM computers WHERE inv_number = 'ПК-00012'"],
        "SELECT (SELECT COUNT(*) FROM assignments WHERE inv_number = 'ПК-00012') AS assignments, "
        "(SELECT COUNT(*) FROM services WHERE inv_number = 'ПК-00012') AS services, "
        "(SELECT COUNT(*) FROM software_installs WHERE inv_number = 'ПК-00012') AS installs, "
        "(SELECT COUNT(*) FROM components WHERE inv_number IS NULL) AS on_stock"),
    ("ON DELETE CASCADE", "Удаление программы Adobe Photoshop", "ok", [
        "DELETE FROM programs WHERE id_program = 5"],
        "SELECT COUNT(*) AS photoshop_installs FROM software_installs WHERE id_program = 5"),
]


def fmt_rows(cur):
    cols = [d[0] for d in cur.description]
    return "; ".join(", ".join(f"{c}={v}" for c, v in zip(cols, row)) for row in cur.fetchall())


def run():
    con = sqlite3.connect(DB, isolation_level=None)
    con.execute("PRAGMA foreign_keys = ON")
    results = []
    for n, (kind, title, expect, stmts, check) in enumerate(TESTS, 1):
        con.execute("SAVEPOINT t")
        try:
            for s in stmts:
                con.execute(s)
            got = "ok"
            message = "выполнено"
            if check:
                message += "; " + fmt_rows(con.execute(check))
        except sqlite3.Error as e:
            got = "error"
            message = str(e)
        finally:
            con.execute("ROLLBACK TO t")
            con.execute("RELEASE t")
        results.append((n, kind, title, stmts, check, expect, got, message))
    con.close()
    return results


def write_sql(results, path):
    blocks = []
    for n, kind, title, stmts, check, expect, _, _ in results:
        label = f"T{n:02d} | {kind} | {title} | ожидается: {'ошибка' if expect == 'error' else 'успех'}"
        body = [f"SELECT '{label}' AS test;"] + [s + ";" for s in stmts]
        if check:
            body.append(check + ";")
        blocks.append("\n".join(body))
    path.write_text("PRAGMA foreign_keys = ON;\nBEGIN TRANSACTION;\n\n" + "\n\n".join(blocks)
                    + "\n\nROLLBACK;\n", encoding="utf-8")


def write_md(results, path):
    lines = ["| № | Ограничение | Проверка | Ожидалось | Результат SQLite |",
             "| --- | --- | --- | --- | --- |"]
    for n, kind, title, _, _, expect, got, message in results:
        verdict = "✔" if expect == got else "✘"
        exp = "ошибка" if expect == "error" else "успех"
        text = " ".join(message.split()).replace("|", "/")
        lines.append(f"| T{n:02d} | {kind} | {title} | {exp} | {verdict} {text} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    res = run()
    write_sql(res, ROOT / "sql" / "05_constraint_tests.sql")
    write_md(res, ROOT / "constraint_tests.md")
    bad = [r for r in res if r[5] != r[6]]
    for n, kind, title, _, _, expect, got, message in res:
        print(f"T{n:02d} {'OK ' if expect == got else 'BAD'} {title}: {message}")
    sys.exit(1 if bad else 0)

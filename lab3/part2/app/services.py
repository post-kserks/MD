import re
from datetime import date

from db import Database

STATUSES = ("в эксплуатации", "в резерве", "в ремонте", "списан")
WORK_TYPES = ("ремонт", "модернизация", "профилактика", "диагностика")
INV_RE = re.compile(r"^ПК-\d{5}$")
HOST_RE = re.compile(r"^[A-Za-z0-9-]{1,15}$")


class ValidationError(Exception):
    def __init__(self, errors):
        self.errors = errors
        super().__init__("; ".join(errors.values()))


def clean(value):
    if value is None:
        return None
    value = str(value).strip()
    return value or None


class Checker:
    def __init__(self, data):
        self.data = {k: clean(v) for k, v in data.items()}
        self.errors = {}

    def get(self, key):
        return self.data.get(key)

    def fail(self, key, message):
        self.errors.setdefault(key, message)

    def required(self, key, label):
        if self.get(key) is None:
            self.fail(key, f"Заполните поле «{label}»")
        return self.get(key)

    def date(self, key, label, required=True):
        value = self.required(key, label) if required else self.get(key)
        if value is None:
            return None
        try:
            date.fromisoformat(value)
        except ValueError:
            self.fail(key, f"«{label}»: дата в формате ГГГГ-ММ-ДД")
            return None
        if value > date.today().isoformat():
            self.fail(key, f"«{label}» не может быть в будущем")
        return value

    def number(self, key, label, minimum=0.0):
        value = self.get(key)
        if value is None:
            return None
        try:
            number = float(value.replace(",", "."))
        except ValueError:
            self.fail(key, f"«{label}»: введите число")
            return None
        if number < minimum:
            self.fail(key, f"«{label}» не может быть меньше {minimum:g}")
        return number

    def done(self):
        if self.errors:
            raise ValidationError(self.errors)


class Accounting:
    def __init__(self, db: Database):
        self.db = db

    def models(self):
        return self.db.rows("SELECT id_model, manufacturer || ' ' || name || ' · ' || device_type "
                            "FROM models ORDER BY manufacturer, name")

    def rooms(self, *types):
        sql = ("SELECT r.id_room, b.name || ', ' || r.number || ' (' || r.room_type || ')' "
               "FROM rooms r JOIN buildings b USING (id_building)")
        if types:
            sql += f" WHERE r.room_type IN ({', '.join('?' for _ in types)})"
        return self.db.rows(sql + " ORDER BY b.name, r.number", types)

    def computers(self, where="1 = 1", params=()):
        return self.db.rows(
            "SELECT c.inv_number, c.inv_number || ' · ' || m.manufacturer || ' ' || m.name || ' · ' || c.status "
            f"FROM computers c JOIN models m USING (id_model) WHERE {where} ORDER BY c.inv_number", params)

    def reserve_computers(self):
        return self.computers("c.status = 'в резерве'")

    def serviceable_computers(self):
        return self.computers("c.status IN ('в эксплуатации', 'в резерве') AND NOT EXISTS "
                              "(SELECT 1 FROM services s WHERE s.inv_number = c.inv_number AND s.end_date IS NULL)")

    def writeoff_candidates(self):
        return self.computers("c.status IN ('в эксплуатации', 'в резерве')")

    def active_computers(self):
        return self.computers("c.status <> 'списан'")

    def employees(self, it_only=False):
        sql = ("SELECT e.tab_number, e.surname || ' ' || e.name || COALESCE(' ' || e.patronymic, '') "
               "|| ' · ' || d.name FROM employees e JOIN departments d USING (id_department) "
               "WHERE e.dismissal_date IS NULL")
        if it_only:
            sql += " AND d.name = 'ИТ-отдел'"
        return self.db.rows(sql + " ORDER BY e.surname, e.name")

    def active_assignments(self):
        return self.db.rows(
            "SELECT a.id_assignment, a.inv_number || ' · ' || e.surname || ' ' || substr(e.name, 1, 1) || '. · с ' "
            "|| a.issue_date FROM assignments a JOIN employees e USING (tab_number) "
            "JOIN computers c USING (inv_number) WHERE a.return_date IS NULL AND c.status = 'в эксплуатации' "
            "ORDER BY a.inv_number")

    def open_services(self):
        return self.db.rows("SELECT id_service, inv_number || ' · ' || work_type || ' · с ' || start_date "
                            "FROM services WHERE end_date IS NULL ORDER BY start_date")

    def programs(self):
        return self.db.rows("SELECT id_program, name || ' ' || version || ' · ' || license_type FROM programs "
                            "ORDER BY name")

    def stats(self):
        counts = dict(self.db.rows("SELECT status, COUNT(*) FROM computers GROUP BY status"))
        return {s: counts.get(s, 0) for s in STATUSES}

    def expiring_warranty(self, days=180):
        return self.db.rows(
            "SELECT c.inv_number, m.manufacturer || ' ' || m.name, c.warranty_end FROM computers c "
            "JOIN models m USING (id_model) WHERE c.status <> 'списан' AND c.warranty_end "
            "BETWEEN date('now') AND date('now', ?) ORDER BY c.warranty_end", (f"+{days} days",))

    def open_services_table(self):
        return self.db.rows(
            "SELECT s.inv_number, s.work_type, s.start_date, COALESCE(e.surname || ' ' || substr(e.name, 1, 1) "
            "|| '.', s.service_org) FROM services s LEFT JOIN employees e ON e.tab_number = s.executor_tab_number "
            "WHERE s.end_date IS NULL ORDER BY s.start_date")

    def _computer(self, inv):
        rows = self.db.rows("SELECT status, commission_date, id_room FROM computers WHERE inv_number = ?", (inv,))
        return rows[0] if rows else None

    def _room_type(self, id_room):
        return self.db.value("SELECT room_type FROM rooms WHERE id_room = ?", (id_room,))

    def register_computer(self, data):
        c = Checker(data)
        inv = c.required("inv_number", "Инвентарный номер")
        if inv and not INV_RE.match(inv):
            c.fail("inv_number", "Инвентарный номер — в формате ПК-NNNNN")
        elif inv and self._computer(inv):
            c.fail("inv_number", f"Компьютер {inv} уже есть в базе")
        serial = c.required("serial_number", "Серийный номер")
        if serial and self.db.value("SELECT 1 FROM computers WHERE serial_number = ?", (serial,)):
            c.fail("serial_number", "Компьютер с таким серийным номером уже есть")
        model = c.required("id_model", "Модель")
        room = c.required("id_room", "Помещение")
        if room and self._room_type(room) != "склад":
            c.fail("id_room", "Новый компьютер ставится на склад (состояние «в резерве»)")
        commission = c.date("commission_date", "Дата ввода")
        warranty = c.get("warranty_end")
        if warranty:
            try:
                date.fromisoformat(warranty)
                if commission and warranty < commission:
                    c.fail("warranty_end", "Гарантия не может закончиться раньше даты ввода")
            except ValueError:
                c.fail("warranty_end", "«Гарантия до»: дата в формате ГГГГ-ММ-ДД")
        host = c.get("hostname")
        if host and not HOST_RE.match(host):
            c.fail("hostname", "Сетевое имя: латиница, цифры и дефис, до 15 символов")
        elif host and self.db.value("SELECT 1 FROM computers WHERE hostname = ?", (host,)):
            c.fail("hostname", "Такое сетевое имя уже занято")
        c.done()
        with self.db.transaction() as con:
            con.execute("INSERT INTO computers (inv_number, serial_number, hostname, commission_date, warranty_end, "
                        "status, id_model, id_room) VALUES (?, ?, ?, ?, ?, 'в резерве', ?, ?)",
                        (inv, serial, host, commission, warranty, int(model), int(room)))
        return f"Компьютер {inv} поставлен на учёт в состоянии «в резерве»"

    def assign_computer(self, data):
        c = Checker(data)
        inv = c.required("inv_number", "Компьютер")
        comp = self._computer(inv) if inv else None
        if inv and not comp:
            c.fail("inv_number", "Компьютер не найден")
        elif comp and comp[0] != "в резерве":
            c.fail("inv_number", f"Выдать можно только компьютер в резерве (сейчас — «{comp[0]}»)")
        elif inv and self.db.value("SELECT 1 FROM assignments WHERE inv_number = ? AND return_date IS NULL", (inv,)):
            c.fail("inv_number", "У компьютера уже есть действующее закрепление")
        tab = c.required("tab_number", "Сотрудник")
        if tab:
            dismissed = self.db.rows("SELECT dismissal_date FROM employees WHERE tab_number = ?", (tab,))
            if not dismissed:
                c.fail("tab_number", "Сотрудник не найден")
            elif dismissed[0][0]:
                c.fail("tab_number", "Нельзя выдать компьютер уволенному сотруднику")
        issued = c.date("issue_date", "Дата выдачи")
        if issued and comp and issued < comp[1]:
            c.fail("issue_date", f"Дата выдачи раньше даты ввода компьютера ({comp[1]})")
        room = c.required("id_room", "Помещение")
        if room and self._room_type(room) == "склад":
            c.fail("id_room", "Выданный компьютер переносится в кабинет или серверную")
        c.done()
        with self.db.transaction() as con:
            con.execute("INSERT INTO assignments (tab_number, inv_number, issue_date, doc_number) VALUES (?, ?, ?, ?)",
                        (tab, inv, issued, c.get("doc_number")))
            con.execute("UPDATE computers SET status = 'в эксплуатации', id_room = ? WHERE inv_number = ?",
                        (int(room), inv))
        return f"Компьютер {inv} выдан, состояние — «в эксплуатации»"

    def return_computer(self, data):
        c = Checker(data)
        aid = c.required("id_assignment", "Закрепление")
        row = self.db.rows("SELECT a.inv_number, a.issue_date, c.status FROM assignments a JOIN computers c "
                           "USING (inv_number) WHERE a.id_assignment = ? AND a.return_date IS NULL", (aid,)) if aid else []
        if aid and not row:
            c.fail("id_assignment", "Действующее закрепление не найдено")
        elif row and row[0][2] != "в эксплуатации":
            c.fail("id_assignment", "Сначала завершите обслуживание компьютера")
        returned = c.date("return_date", "Дата возврата")
        if returned and row and returned < row[0][1]:
            c.fail("return_date", f"Дата возврата раньше даты выдачи ({row[0][1]})")
        room = c.required("id_room", "Склад")
        if room and self._room_type(room) != "склад":
            c.fail("id_room", "Возвращённый компьютер помещается на склад")
        c.done()
        inv = row[0][0]
        with self.db.transaction() as con:
            con.execute("UPDATE assignments SET return_date = ? WHERE id_assignment = ?", (returned, int(aid)))
            con.execute("UPDATE computers SET status = 'в резерве', id_room = ? WHERE inv_number = ?", (int(room), inv))
        return f"Компьютер {inv} возвращён на склад, состояние — «в резерве»"

    def open_service(self, data):
        c = Checker(data)
        inv = c.required("inv_number", "Компьютер")
        comp = self._computer(inv) if inv else None
        if inv and not comp:
            c.fail("inv_number", "Компьютер не найден")
        elif comp and comp[0] not in ("в эксплуатации", "в резерве"):
            c.fail("inv_number", f"Компьютер в состоянии «{comp[0]}» нельзя передать в обслуживание")
        work = c.required("work_type", "Вид работ")
        if work and work not in WORK_TYPES:
            c.fail("work_type", "Выберите вид работ из списка")
        start = c.date("start_date", "Дата начала")
        if start and comp and start < comp[1]:
            c.fail("start_date", f"Дата начала раньше даты ввода компьютера ({comp[1]})")
        executor, org = c.get("executor_tab_number"), c.get("service_org")
        if bool(executor) == bool(org):
            c.fail("executor_tab_number", "Укажите ровно одного исполнителя: сотрудника или сервисную организацию")
        c.done()
        with self.db.transaction() as con:
            con.execute("INSERT INTO services (inv_number, work_type, start_date, fault_description, "
                        "executor_tab_number, service_org) VALUES (?, ?, ?, ?, ?, ?)",
                        (inv, work, start, c.get("fault_description"), executor, org))
            con.execute("UPDATE computers SET status = 'в ремонте' WHERE inv_number = ?", (inv,))
        return f"Обслуживание компьютера {inv} открыто, состояние — «в ремонте»"

    def close_service(self, data):
        c = Checker(data)
        sid = c.required("id_service", "Обслуживание")
        row = self.db.rows("SELECT inv_number, start_date FROM services WHERE id_service = ? AND end_date IS NULL",
                           (sid,)) if sid else []
        if sid and not row:
            c.fail("id_service", "Незавершённое обслуживание не найдено")
        end = c.date("end_date", "Дата окончания")
        if end and row and end < row[0][1]:
            c.fail("end_date", f"Дата окончания раньше даты начала ({row[0][1]})")
        c.required("works_done", "Выполненные работы")
        cost = c.number("cost", "Стоимость")
        c.done()
        inv = row[0][0]
        in_use = self.db.value(
            "SELECT EXISTS (SELECT 1 FROM assignments WHERE inv_number = ? AND return_date IS NULL) "
            "OR (SELECT r.room_type FROM computers c JOIN rooms r USING (id_room) WHERE c.inv_number = ?) = 'серверная'",
            (inv, inv))
        status = "в эксплуатации" if in_use else "в резерве"
        with self.db.transaction() as con:
            con.execute("UPDATE services SET end_date = ?, works_done = ?, cost = ? WHERE id_service = ?",
                        (end, c.get("works_done"), cost, int(sid)))
            con.execute("UPDATE computers SET status = ? WHERE inv_number = ?", (status, inv))
        return f"Обслуживание завершено, компьютер {inv} — «{status}»"

    def write_off(self, data):
        c = Checker(data)
        inv = c.required("inv_number", "Компьютер")
        comp = self._computer(inv) if inv else None
        if inv and not comp:
            c.fail("inv_number", "Компьютер не найден")
        elif comp and comp[0] == "списан":
            c.fail("inv_number", "Компьютер уже списан")
        elif comp and comp[0] == "в ремонте":
            c.fail("inv_number", "Сначала завершите обслуживание компьютера")
        wo = c.date("writeoff_date", "Дата списания")
        if wo and comp and wo < comp[1]:
            c.fail("writeoff_date", f"Дата списания раньше даты ввода ({comp[1]})")
        last_issue = self.db.value("SELECT MAX(issue_date) FROM assignments WHERE inv_number = ?", (inv,)) if inv else None
        if wo and last_issue and wo < last_issue:
            c.fail("writeoff_date", f"Дата списания раньше последней выдачи ({last_issue})")
        c.done()
        with self.db.transaction() as con:
            con.execute("UPDATE assignments SET return_date = ? WHERE inv_number = ? AND return_date IS NULL", (wo, inv))
            if c.get("components_to_stock"):
                con.execute("UPDATE components SET inv_number = NULL WHERE inv_number = ?", (inv,))
            con.execute("DELETE FROM software_installs WHERE inv_number = ?", (inv,))
            con.execute("UPDATE computers SET status = 'списан', writeoff_date = ? WHERE inv_number = ?", (wo, inv))
        return f"Компьютер {inv} списан"

    def install_program(self, data):
        c = Checker(data)
        inv = c.required("inv_number", "Компьютер")
        comp = self._computer(inv) if inv else None
        if comp and comp[0] == "списан":
            c.fail("inv_number", "Нельзя установить программу на списанный компьютер")
        pid = c.required("id_program", "Программа")
        prog = self.db.rows("SELECT license_type, license_count, name FROM programs WHERE id_program = ?",
                            (pid,)) if pid else []
        if pid and not prog:
            c.fail("id_program", "Программа не найдена")
        if inv and pid and self.db.value("SELECT 1 FROM software_installs WHERE inv_number = ? AND id_program = ?",
                                         (inv, pid)):
            c.fail("id_program", "Программа уже установлена на этот компьютер")
        if prog and prog[0][0] != "бесплатная":
            used = self.db.value("SELECT COUNT(*) FROM software_installs WHERE id_program = ?", (pid,))
            if used >= prog[0][1]:
                c.fail("id_program", f"Все лицензии заняты: {used} из {prog[0][1]}")
        installed = c.date("install_date", "Дата установки")
        c.done()
        with self.db.transaction() as con:
            con.execute("INSERT INTO software_installs (inv_number, id_program, install_date) VALUES (?, ?, ?)",
                        (inv, int(pid), installed))
        return f"Программа «{prog[0][2]}» установлена на {inv}"

import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk

from db import DatabaseError
from services import WORK_TYPES, ValidationError
from theme import C
from widgets import LookupCombo, Message


def today():
    return date.today().isoformat()


def in_years(n):
    d = date.today()
    try:
        return d.replace(year=d.year + n).isoformat()
    except ValueError:
        return d.replace(year=d.year + n, day=28).isoformat()


def operation_specs(acc):
    return {
        "register": ("Постановка компьютера на учёт", acc.register_computer, [
            ("inv_number", "Инвентарный номер", "entry", True, acc_next_inv(acc)),
            ("serial_number", "Серийный номер", "entry", True, None),
            ("id_model", "Модель", acc.models, True, None),
            ("id_room", "Помещение (склад)", lambda: acc.rooms("склад"), True, None),
            ("commission_date", "Дата ввода (ГГГГ-ММ-ДД)", "entry", True, today()),
            ("warranty_end", "Гарантия до", "entry", False, in_years(3)),
            ("hostname", "Сетевое имя", "entry", False, None),
        ]),
        "assign": ("Выдача компьютера сотруднику", acc.assign_computer, [
            ("inv_number", "Компьютер (в резерве)", acc.reserve_computers, True, None),
            ("tab_number", "Сотрудник", acc.employees, True, None),
            ("issue_date", "Дата выдачи", "entry", True, today()),
            ("doc_number", "Номер распоряжения", "entry", False, None),
            ("id_room", "Переместить в помещение", lambda: acc.rooms("кабинет", "серверная"), True, None),
        ]),
        "return": ("Возврат компьютера на склад", acc.return_computer, [
            ("id_assignment", "Действующее закрепление", acc.active_assignments, True, None),
            ("return_date", "Дата возврата", "entry", True, today()),
            ("id_room", "Склад", lambda: acc.rooms("склад"), True, None),
        ]),
        "service_open": ("Регистрация обслуживания", acc.open_service, [
            ("inv_number", "Компьютер", acc.serviceable_computers, True, None),
            ("work_type", "Вид работ", lambda: [(w, w) for w in WORK_TYPES], True, "ремонт"),
            ("start_date", "Дата начала", "entry", True, today()),
            ("fault_description", "Описание неисправности", "entry", False, None),
            ("executor_tab_number", "Исполнитель — сотрудник ИТ", lambda: acc.employees(it_only=True), False, None),
            ("service_org", "или сервисная организация", "entry", False, None),
        ]),
        "service_close": ("Завершение обслуживания", acc.close_service, [
            ("id_service", "Незавершённое обслуживание", acc.open_services, True, None),
            ("end_date", "Дата окончания", "entry", True, today()),
            ("works_done", "Выполненные работы", "entry", True, None),
            ("cost", "Стоимость, руб.", "entry", False, None),
        ]),
        "writeoff": ("Списание компьютера", acc.write_off, [
            ("inv_number", "Компьютер", acc.writeoff_candidates, True, None),
            ("writeoff_date", "Дата списания", "entry", True, today()),
            ("components_to_stock", "Снять комплектующие на склад", "check", False, "1"),
        ]),
        "install": ("Установка программы", acc.install_program, [
            ("inv_number", "Компьютер", acc.active_computers, True, None),
            ("id_program", "Программа", acc.programs, True, None),
            ("install_date", "Дата установки", "entry", True, today()),
        ]),
    }


def acc_next_inv(acc):
    last = acc.db.value("SELECT MAX(inv_number) FROM computers WHERE inv_number GLOB 'ПК-[0-9]*'")
    n = int(last[3:]) + 1 if last else 1
    return f"ПК-{n:05d}"


class FormDialog(tk.Toplevel):
    def __init__(self, master, F, title, width=560):
        super().__init__(master)
        self.F = F
        self.title(title)
        self.configure(bg=C["surface"])
        self.transient(master)
        self.resizable(False, False)
        self.body = ttk.Frame(self, style="Card.TFrame", padding=24)
        self.body.pack(fill="both", expand=True)
        ttk.Label(self.body, text=title, style="H2.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 14))
        self.body.columnconfigure(0, weight=1, minsize=width)
        self.widgets, self.errors, self.row = {}, {}, 1
        self.message = Message(self.body)
        self.bind("<Escape>", lambda e: self.destroy())

    def add_field(self, key, label, kind, required, default):
        ttk.Label(self.body, text=label + (" *" if required else ""), style="Field.TLabel").grid(
            row=self.row, column=0, sticky="w")
        if kind == "entry":
            w = ttk.Entry(self.body)
            if default is not None:
                w.insert(0, default)
        elif kind == "check":
            var = tk.StringVar(value=default or "")
            w = ttk.Checkbutton(self.body, variable=var, onvalue="1", offvalue="", text="да")
            w.var = var
        elif kind == "text":
            w = tk.Text(self.body, height=3, font=self.F["body"], relief="solid", borderwidth=1)
            if default:
                w.insert("1.0", default)
        else:
            w = LookupCombo(self.body, kind(), optional=not required)
            if default is not None:
                w.set_key(default)
        w.grid(row=self.row + 1, column=0, sticky="ew", pady=(4, 0))
        err = ttk.Label(self.body, text="", style="Error.TLabel")
        err.grid(row=self.row + 2, column=0, sticky="w", pady=(2, 8))
        self.widgets[key], self.errors[key] = w, err
        self.row += 3

    def value(self, key):
        w = self.widgets[key]
        if isinstance(w, LookupCombo):
            return w.get_key()
        if isinstance(w, ttk.Checkbutton):
            return w.var.get()
        if isinstance(w, tk.Text):
            return w.get("1.0", "end").strip()
        return w.get()

    def values(self):
        return {k: self.value(k) for k in self.widgets}

    def show_errors(self, errors):
        for key, label in self.errors.items():
            label.configure(text=errors.get(key, ""))
            w = self.widgets[key]
            if isinstance(w, LookupCombo):
                w.configure(style="Bad.TCombobox" if key in errors else "TCombobox")
            elif isinstance(w, ttk.Entry):
                w.configure(style="Bad.TEntry" if key in errors else "TEntry")
        other = [m for k, m in errors.items() if k not in self.errors]
        if other:
            self.message.show("danger", "; ".join(other))

    def add_buttons(self, ok_text, ok_command):
        self.message.grid(row=self.row, column=0, sticky="ew", pady=(4, 8))
        bar = ttk.Frame(self.body, style="Card.TFrame")
        bar.grid(row=self.row + 1, column=0, sticky="e", pady=(8, 0))
        ttk.Button(bar, text="Отмена", command=self.destroy).pack(side="left", padx=(0, 8))
        ttk.Button(bar, text=ok_text, style="Primary.TButton", command=ok_command).pack(side="left")
        self.bind("<Return>", lambda e: ok_command())

    def open_modal(self):
        self.update_idletasks()
        m = self.master.winfo_toplevel()
        x = m.winfo_rootx() + (m.winfo_width() - self.winfo_width()) // 2
        y = m.winfo_rooty() + max(40, (m.winfo_height() - self.winfo_height()) // 3)
        self.geometry(f"+{max(0, x)}+{max(0, y)}")
        self.grab_set()
        first = next(iter(self.widgets.values()), None)
        if first is not None:
            first.focus_set()


class OperationDialog(FormDialog):
    def __init__(self, master, F, spec, on_done):
        title, action, fields = spec
        super().__init__(master, F, title)
        self.action, self.on_done = action, on_done
        for key, label, kind, required, default in fields:
            self.add_field(key, label, kind, required, default)
        self.add_buttons("Сохранить", self.submit)
        self.open_modal()

    def submit(self):
        self.message.clear()
        try:
            text = self.action(self.values())
        except ValidationError as e:
            self.show_errors(e.errors)
            return
        except DatabaseError as e:
            self.show_errors({})
            self.message.show("danger", f"Ошибка базы данных: {e}")
            return
        self.destroy()
        self.on_done(text)


class RecordDialog(FormDialog):
    def __init__(self, master, F, db, table, row, on_done):
        self.db, self.table, self.row_data, self.on_done = db, table, row, on_done
        mode = "Изменение записи" if row else "Новая запись"
        super().__init__(master, F, f"{mode}: {table}")
        self.cols = db.columns(table)
        self.pk = db.primary_key(table)
        fks = {fk["column"]: fk for fk in db.foreign_keys(table)}
        auto = len(self.pk) == 1 and next(c for c in self.cols if c["name"] == self.pk[0])["type"] == "INTEGER"
        for c in self.cols:
            name = c["name"]
            if row is None and auto and name == self.pk[0]:
                continue
            required = (c["notnull"] or c["pk"]) and c["default"] is None
            hint = f" ({c['type'].lower()})" if c["type"] else ""
            if name in fks:
                items = self._lookup(fks[name])
                self.add_field(name, f"{name} → {fks[name]['table']}", lambda items=items: items, required,
                               row.get(name) if row else None)
            else:
                value = row.get(name) if row else None
                self.add_field(name, name + hint, "entry", required, None if value is None else str(value))
        self.add_buttons("Сохранить", self.submit)
        self.open_modal()

    def _lookup(self, fk):
        cols = self.db.columns(fk["table"])
        label = next((c["name"] for c in cols if c["type"] == "TEXT" and c["name"] != fk["ref"]), fk["ref"])
        return [(k, f"{k} · {v}") for k, v in self.db.rows(
            f'SELECT "{fk["ref"]}", "{label}" FROM "{fk["table"]}" ORDER BY 1')]

    def submit(self):
        self.message.clear()
        values = {}
        types = {c["name"]: c["type"] for c in self.cols}
        for k in self.widgets:
            v = self.value(k)
            v = None if v in ("", None) else v
            if v is not None and types.get(k) in ("INTEGER", "REAL") and isinstance(v, str):
                try:
                    v = int(v) if types[k] == "INTEGER" else float(v.replace(",", "."))
                except ValueError:
                    self.show_errors({k: f"Ожидается число ({types[k].lower()})"})
                    return
            values[k] = v
        try:
            if self.row_data is None:
                self.db.insert(self.table, values)
                text = f"Запись добавлена в {self.table}"
            else:
                pk = {k: self.row_data[k] for k in self.pk}
                self.db.update(self.table, pk, values)
                text = f"Запись в {self.table} изменена"
        except DatabaseError as e:
            self.show_errors({})
            self.message.show("danger", f"СУБД отклонила изменение: {e}")
            return
        self.destroy()
        self.on_done(text)


ON_DELETE = {"CASCADE": "будут удалены", "SET NULL": "потеряют ссылку (NULL)", "RESTRICT": "запрещают удаление",
             "NO ACTION": "запрещают удаление"}


def confirm_delete(master, db, table, row):
    pk = {k: row[k] for k in db.primary_key(table)}
    deps = db.dependents(table, pk)
    lines = [f"Удалить запись {', '.join(f'{k} = {v}' for k, v in pk.items())} из таблицы {table}?"]
    for t, n, action in deps:
        lines.append(f"• связанные записи в {t}: {n} — {ON_DELETE.get(action, action)}")
    lines.append("Отменить действие будет нельзя.")
    if not messagebox.askyesno("Подтверждение удаления", "\n".join(lines), icon="warning", parent=master):
        return None
    try:
        db.delete(table, pk)
    except DatabaseError as e:
        messagebox.showerror("Удаление невозможно", f"СУБД отклонила удаление:\n{e}", parent=master)
        return None
    return f"Запись удалена из {table}"

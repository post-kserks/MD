import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, ttk

from db import DatabaseError
from dialogs import RecordDialog, confirm_delete
from io_ops import export_table, import_table
from queries import catalog, param_names
from theme import C
from widgets import Card, DataTable, LookupCombo, Message, scrolled_text

TABLE_TITLES = {
    "computers": "Компьютеры", "employees": "Сотрудники", "assignments": "Закрепления",
    "services": "Обслуживание", "departments": "Отделы", "rooms": "Помещения", "buildings": "Здания",
    "models": "Модели", "programs": "Программы", "components": "Комплектующие",
    "software_installs": "Установки ПО",
}


class View(ttk.Frame):
    title = ""
    crumbs = ""

    def __init__(self, app):
        super().__init__(app.content, padding=(24, 16))
        self.app, self.F = app, app.F

    @property
    def db(self):
        return self.app.db

    def refresh(self):
        pass


class Dashboard(View):
    title, crumbs = "Главная", "Учёт ПК / Главная"
    CARDS = [("В эксплуатации", "в эксплуатации", "success"), ("В резерве", "в резерве", "info"),
             ("В ремонте", "в ремонте", "warning"), ("Списано", "списан", "danger")]

    def __init__(self, app):
        super().__init__(app)
        row = ttk.Frame(self)
        row.pack(fill="x")
        self.values = {}
        for i, (title, key, kind) in enumerate(self.CARDS):
            card = ttk.Frame(row, style="Card.TFrame", padding=(18, 12))
            card.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 12, 0))
            row.columnconfigure(i, weight=1)
            ttk.Label(card, text=title, style="CardMuted.TLabel").pack(anchor="w")
            self.values[key] = ttk.Label(card, text="—", style=f"Stat{kind}.TLabel")
            self.values[key].pack(anchor="w")
        actions = Card(self, "Быстрые действия", self.F)
        actions.pack(fill="x", pady=16)
        rows = [[("＋ Поставить на учёт", "register", "Primary.TButton"), ("Выдать компьютер", "assign", "TButton"),
                 ("Принять возврат", "return", "TButton")],
                [("Зарегистрировать обслуживание", "service_open", "TButton"),
                 ("Завершить обслуживание", "service_close", "TButton"), ("Списать компьютер", "writeoff", "TButton")]]
        for i, buttons in enumerate(rows):
            bar = ttk.Frame(actions, style="Inner.TFrame")
            bar.pack(anchor="w", pady=(0 if i == 0 else 8, 0))
            for text, op, style in buttons:
                ttk.Button(bar, text=text, style=style, command=lambda o=op: app.operation(o)).pack(side="left", padx=(0, 8))
        bottom = ttk.Frame(self)
        bottom.pack(fill="both", expand=True)
        bottom.columnconfigure(0, weight=1, uniform="half")
        bottom.columnconfigure(1, weight=1, uniform="half")
        bottom.rowconfigure(0, weight=1)
        left = Card(bottom, "Истекает гарантия (полгода)", self.F)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.warranty = DataTable(left, height=8, style="Inner.TFrame", fit=True)
        self.warranty.pack(fill="both", expand=True)
        right = Card(bottom, "Незавершённые обслуживания", self.F)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        self.services = DataTable(right, height=8, style="Inner.TFrame", fit=True)
        self.services.pack(fill="both", expand=True)

    def refresh(self):
        if not self.db.is_open:
            return
        stats = self.app.acc.stats()
        for key, label in self.values.items():
            label.configure(text=str(stats.get(key, 0)))
        self.warranty.load(["Инв. №", "Модель", "Гарантия до"], self.app.acc.expiring_warranty())
        self.services.load(["Инв. №", "Вид работ", "С", "Исполнитель"], self.app.acc.open_services_table())


class TablesView(View):
    title, crumbs = "Просмотр данных", "Учёт ПК / Данные"
    STATUS_ALL = "все состояния"

    def __init__(self, app):
        super().__init__(app)
        bar = ttk.Frame(self)
        bar.pack(fill="x", pady=(0, 12))
        ttk.Button(bar, text="⟳", width=3, command=self.refresh).pack(side="right")
        ttk.Button(bar, text="Удалить", command=self.delete).pack(side="right", padx=(0, 8))
        ttk.Button(bar, text="Изменить", command=self.edit).pack(side="right", padx=(0, 8))
        ttk.Button(bar, text="＋ Добавить", style="Primary.TButton", command=self.add).pack(side="right", padx=(0, 8))
        self.table_box = ttk.Combobox(bar, state="readonly", width=17)
        self.table_box.pack(side="left", padx=(0, 12))
        self.table_box.bind("<<ComboboxSelected>>", lambda e: self.set_table(self.table_box.get().split(" — ")[0]))
        ttk.Label(bar, text="Поиск").pack(side="left")
        self.search = ttk.Entry(bar, width=15)
        self.search.pack(side="left", padx=(6, 16))
        self.search.bind("<KeyRelease>", lambda e: self.apply_filter())
        self.status_box = ttk.Combobox(bar, state="readonly", width=14,
                                       values=[self.STATUS_ALL, "в эксплуатации", "в резерве", "в ремонте", "списан"])
        self.status_box.set(self.STATUS_ALL)
        self.status_box.bind("<<ComboboxSelected>>", lambda e: self.refresh())
        self.grid_table = DataTable(self, height=18, on_open=lambda row: self.edit())
        self.grid_table.pack(fill="both", expand=True)
        self.info = ttk.Label(self, text="", style="Muted.TLabel")
        self.info.pack(anchor="w", pady=(8, 0))
        self.table = "computers"

    def set_table(self, table):
        self.table = table
        self.search.delete(0, "end")
        self.grid_table.filter_text = ""
        self.refresh()

    def refresh(self):
        if not self.db.is_open:
            return
        tables = self.db.tables()
        self.table_box["values"] = [f"{t} — {TABLE_TITLES.get(t, t)}" for t in tables]
        if self.table not in tables:
            self.table = tables[0]
        self.table_box.set(f"{self.table} — {TABLE_TITLES.get(self.table, self.table)}")
        if self.table == "computers":
            self.status_box.pack(side="left", after=self.search, padx=(0, 8))
        else:
            self.status_box.pack_forget()
        sql, params = f'SELECT * FROM "{self.table}"', ()
        if self.table == "computers" and self.status_box.get() != self.STATUS_ALL:
            sql, params = sql + " WHERE status = ?", (self.status_box.get(),)
        try:
            res = self.db.run(sql, params)
        except DatabaseError as e:
            self.app.notify("danger", str(e))
            return
        self.grid_table.load(res.columns, res.rows)
        self.apply_filter()
        self.app.set_title(f"Данные: {TABLE_TITLES.get(self.table, self.table).lower()}",
                           f"Учёт ПК / Данные / {self.table}")

    def apply_filter(self):
        self.grid_table.set_filter(self.search.get())
        sort = f" · сортировка: {self.grid_table.sort_col}" if self.grid_table.sort_col else ""
        self.info.configure(text=f"{self.grid_table.count_text()}{sort} · щелчок по заголовку — сортировка, "
                                 f"двойной щелчок по строке — изменить")

    def add(self):
        RecordDialog(self, self.F, self.db, self.table, None, self.after_change)

    def edit(self):
        row = self.grid_table.selected()
        if row is None:
            self.app.notify("warning", "Выберите строку в таблице")
            return
        RecordDialog(self, self.F, self.db, self.table, row, self.after_change)

    def delete(self):
        row = self.grid_table.selected()
        if row is None:
            self.app.notify("warning", "Выберите строку в таблице")
            return
        text = confirm_delete(self, self.db, self.table, row)
        if text:
            self.after_change(text)

    def after_change(self, text):
        self.app.notify("success", text)
        self.refresh()


class SqlView(View):
    title, crumbs = "SQL-запросы", "Учёт ПК / SQL-запросы"

    def __init__(self, app):
        super().__init__(app)
        frame, self.editor = scrolled_text(self, self.F, height=9)
        frame.pack(fill="x")
        self.editor.insert("1.0", "SELECT m.device_type AS category, COUNT(*) AS computers\nFROM computers c\n"
                                  "JOIN models m ON m.id_model = c.id_model\nWHERE c.status <> 'списан'\n"
                                  "GROUP BY m.device_type\nHAVING COUNT(*) > 5\nORDER BY computers DESC;")
        for seq in ("<Control-Return>", "<Command-Return>"):
            self.editor.bind(seq, lambda e: (self.execute(), "break")[1])
        bar = ttk.Frame(self)
        bar.pack(fill="x", pady=10)
        ttk.Button(bar, text="▶ Выполнить (Ctrl+Enter)", style="Primary.TButton", command=self.execute).pack(side="left")
        ttk.Button(bar, text="Очистить", command=lambda: self.editor.delete("1.0", "end")).pack(side="left", padx=8)
        self.status = ttk.Label(bar, text="", style="Muted.TLabel")
        self.status.pack(side="right")
        self.message = Message(self, empty_style="TLabel")
        self.message.pack(fill="x")
        self.result = DataTable(self, height=14)
        self.result.pack(fill="both", expand=True, pady=(8, 0))

    def refresh(self):
        self.editor.focus_set()

    def load_sql(self, sql):
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", sql)

    def execute(self):
        sql = self.editor.get("sel.first", "sel.last") if self.editor.tag_ranges("sel") else self.editor.get("1.0", "end")
        sql = sql.strip()
        if not sql:
            return
        self.message.clear()
        try:
            res = self.db.run(sql)
        except DatabaseError as e:
            self.message.show("danger", f"Ошибка: {e}")
            self.status.configure(text="запрос не выполнен")
            return
        if res.is_select:
            self.result.load(res.columns, res.rows)
            self.status.configure(text=f"Готово: {len(res.rows)} строк за {res.elapsed_ms:.0f} мс")
        else:
            changed = "скрипт выполнен" if res.script else f"изменено строк: {res.rowcount}"
            self.message.show("success", f"Выполнено, {changed}")
            self.status.configure(text=f"{res.elapsed_ms:.0f} мс")
            self.app.data_changed()


class QueriesView(View):
    title, crumbs = "Готовые запросы", "Учёт ПК / Готовые запросы"

    def __init__(self, app):
        super().__init__(app)
        self.items = catalog()
        left = Card(self, "Запросы ЛР2", self.F)
        left.pack(side="left", fill="y", padx=(0, 16))
        self.listbox = tk.Listbox(left, width=38, height=22, font=self.F["body"], activestyle="none",
                                  relief="flat", highlightthickness=0, bg=C["surface"], fg=C["text"],
                                  selectbackground=C["selected"], selectforeground=C["text"], exportselection=False)
        for title, _, _ in self.items:
            self.listbox.insert("end", title)
        self.listbox.pack(fill="y", expand=True)
        self.listbox.bind("<<ListboxSelect>>", lambda e: self.select())
        self.listbox.bind("<Double-1>", lambda e: self.run())
        right = ttk.Frame(self)
        right.pack(side="left", fill="both", expand=True)
        top = Card(right)
        top.pack(fill="x")
        self.heading = ttk.Label(top, text="", style="H2.TLabel", wraplength=480)
        self.heading.pack(anchor="w")
        frame, self.sql = scrolled_text(top, self.F, height=7)
        frame.pack(fill="x", pady=8)
        self.params = ttk.Frame(top, style="Inner.TFrame")
        self.params.pack(fill="x")
        bar = ttk.Frame(top, style="Inner.TFrame")
        bar.pack(fill="x", pady=(8, 0))
        ttk.Button(bar, text="▶ Выполнить", style="Primary.TButton", command=self.run).pack(side="left")
        ttk.Button(bar, text="Открыть в SQL-консоли", command=self.to_console).pack(side="left", padx=8)
        self.status = ttk.Label(bar, text="", style="CardMuted.TLabel")
        self.status.pack(side="right")
        self.message = Message(right, empty_style="TLabel")
        self.message.pack(fill="x", pady=(8, 0))
        self.result = DataTable(right, height=12)
        self.result.pack(fill="both", expand=True, pady=(8, 0))
        self.param_entries = {}
        self.listbox.selection_set(len(self.items) - 3)
        self.select()

    def refresh(self):
        if not self.result.rows:
            self.run()

    def current(self):
        sel = self.listbox.curselection()
        return self.items[sel[0]] if sel else None

    def select(self):
        item = self.current()
        if not item:
            return
        title, sql, params = item
        self.heading.configure(text=title)
        self.sql.configure(state="normal")
        self.sql.delete("1.0", "end")
        self.sql.insert("1.0", sql)
        self.sql.configure(state="disabled")
        for w in self.params.winfo_children():
            w.destroy()
        self.param_entries = {}
        for i, (name, (label, default)) in enumerate(params.items()):
            ttk.Label(self.params, text=f"{label} (:{name})", style="Field.TLabel").grid(row=0, column=2 * i, padx=(0, 6))
            e = ttk.Entry(self.params, width=14)
            e.insert(0, default)
            e.grid(row=0, column=2 * i + 1, padx=(0, 16))
            self.param_entries[name] = e

    def run(self):
        item = self.current()
        if not item or not self.db.is_open:
            return
        _, sql, _ = item
        values = {n: self.param_entries[n].get() for n in param_names(sql)}
        values = {k: (int(v) if v.isdigit() else v) for k, v in values.items()}
        self.message.clear()
        try:
            res = self.db.run(sql, values)
        except DatabaseError as e:
            self.message.show("danger", f"Ошибка: {e}")
            return
        self.result.load(res.columns, res.rows)
        self.status.configure(text=f"{len(res.rows)} строк · {res.elapsed_ms:.0f} мс")

    def to_console(self):
        item = self.current()
        if item:
            self.app.show("sql")
            self.app.views["sql"].load_sql(item[1])


class ImportExportView(View):
    title, crumbs = "Импорт и экспорт", "Учёт ПК / Импорт и экспорт"

    def __init__(self, app):
        super().__init__(app)
        left = Card(self, "Параметры операции", self.F)
        left.pack(side="left", fill="y", padx=(0, 16))
        self.op = tk.StringVar(value="export")
        self.fmt = tk.StringVar(value="csv")
        ttk.Label(left, text="Операция", style="Field.TLabel").pack(anchor="w")
        row = ttk.Frame(left, style="Inner.TFrame")
        row.pack(anchor="w", pady=(4, 10))
        ttk.Radiobutton(row, text="Экспорт из базы в файл", variable=self.op, value="export",
                        command=self.suggest).pack(side="left")
        ttk.Radiobutton(row, text="Импорт из файла в базу", variable=self.op, value="import",
                        command=self.suggest).pack(side="left", padx=12)
        ttk.Label(left, text="Формат", style="Field.TLabel").pack(anchor="w")
        row = ttk.Frame(left, style="Inner.TFrame")
        row.pack(anchor="w", pady=(4, 10))
        for f in ("csv", "json"):
            ttk.Radiobutton(row, text=f.upper(), variable=self.fmt, value=f, command=self.suggest).pack(side="left", padx=(0, 12))
        ttk.Label(left, text="Таблица *", style="Field.TLabel").pack(anchor="w")
        self.table = LookupCombo(left, width=40)
        self.table.pack(anchor="w", fill="x", pady=(4, 10))
        self.table.bind("<<ComboboxSelected>>", lambda e: self.suggest())
        ttk.Label(left, text="Файл *", style="Field.TLabel").pack(anchor="w")
        row = ttk.Frame(left, style="Inner.TFrame")
        row.pack(fill="x", pady=(4, 10))
        self.path = ttk.Entry(row, width=36)
        self.path.pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="Обзор…", command=self.browse).pack(side="left", padx=(8, 0))
        ttk.Label(left, text="Разделитель CSV", style="Field.TLabel").pack(anchor="w")
        self.delim = ttk.Combobox(left, state="readonly", width=16, values=["запятая ( , )", "точка с запятой ( ; )"])
        self.delim.set("запятая ( , )")
        self.delim.pack(anchor="w", pady=(4, 10))
        self.header = tk.StringVar(value="1")
        self.skip = tk.StringVar(value="")
        ttk.Checkbutton(left, text="Первая строка — заголовки столбцов", variable=self.header,
                        onvalue="1", offvalue="").pack(anchor="w")
        ttk.Checkbutton(left, text="Пропускать существующие записи (импорт)", variable=self.skip,
                        onvalue="1", offvalue="").pack(anchor="w", pady=(4, 12))
        ttk.Button(left, text="Начать", style="Primary.TButton", command=self.start).pack(anchor="e")
        right = Card(self, "Ход выполнения", self.F)
        right.pack(side="left", fill="both", expand=True)
        self.progress = ttk.Progressbar(right, mode="determinate", maximum=100)
        self.progress.pack(fill="x")
        self.message = Message(right)
        self.message.pack(fill="x", pady=10)
        ttk.Label(right, text="Журнал", style="Field.TLabel").pack(anchor="w")
        frame, self.log = scrolled_text(right, self.F, height=14, wrap="word")
        frame.pack(fill="both", expand=True, pady=(4, 0))
        self.log.configure(state="disabled")

    def refresh(self):
        if self.db.is_open:
            current = self.table.get_key()
            self.table.set_items([(t, f"{t} — {TABLE_TITLES.get(t, t)}") for t in self.db.tables()])
            self.table.set_key(current or "computers")
            self.suggest()

    def suggest(self):
        table = self.table.get_key()
        if table and self.op.get() == "export":
            base = Path(self.app.db.path).parent if self.app.db.path else Path.cwd()
            self.path.delete(0, "end")
            self.path.insert(0, str(base / "export" / f"{table}.{self.fmt.get()}"))

    def browse(self):
        ext = self.fmt.get()
        types = [(ext.upper(), f"*.{ext}"), ("Все файлы", "*")]
        if self.op.get() == "export":
            path = filedialog.asksaveasfilename(parent=self, defaultextension=f".{ext}", filetypes=types,
                                                initialfile=f"{self.table.get_key() or 'table'}.{ext}")
        else:
            path = filedialog.askopenfilename(parent=self, filetypes=types)
        if path:
            self.path.delete(0, "end")
            self.path.insert(0, path)

    def write_log(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", f"{datetime.now():%H:%M:%S}  {text}\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def start(self):
        table, path, fmt = self.table.get_key(), self.path.get().strip(), self.fmt.get()
        delimiter = ";" if "точка" in self.delim.get() else ","
        self.message.clear()
        self.progress["value"] = 0
        if not table or not path:
            self.message.show("warning", "Выберите таблицу и файл")
            return
        try:
            if self.op.get() == "export":
                Path(path).parent.mkdir(parents=True, exist_ok=True)
                n = export_table(self.db, table, path, fmt, delimiter, bool(self.header.get()))
                text = f"Экспорт завершён: {n} строк → {Path(path).name}"
            else:
                total, added = import_table(self.db, table, path, fmt, delimiter, bool(self.header.get()),
                                            bool(self.skip.get()))
                text = f"Импорт завершён: в файле {total} строк, добавлено {added}"
                self.app.data_changed()
        except (DatabaseError, ValueError, OSError) as e:
            kind = "импорт отменён, изменения откатаны" if self.op.get() == "import" else "экспорт не выполнен"
            self.message.show("danger", f"Ошибка, {kind}: {e}")
            self.write_log(f"{self.op.get()} {table} ({fmt}): ошибка — {e}")
            return
        self.progress["value"] = 100
        self.message.show("success", text)
        self.write_log(f"{self.op.get()} {table} ({fmt}): {text}")

import sqlite3
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import theme
from db import Database, DatabaseError
from dialogs import OperationDialog, operation_specs
from services import Accounting
from views import Dashboard, ImportExportView, QueriesView, SqlView, TablesView

DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "computers.db"

NAV = [
    ("Работа", None, None),
    ("⌂  Главная", "dashboard", None),
    ("▤  Компьютеры", "tables", "computers"),
    ("☺  Сотрудники", "tables", "employees"),
    ("⇄  Закрепления", "tables", "assignments"),
    ("✎  Обслуживание", "tables", "services"),
    ("≡  Справочники", "tables", "departments"),
    ("Данные", None, None),
    ("›  SQL-запросы", "sql", None),
    ("★  Готовые запросы", "queries", None),
    ("⇅  Импорт и экспорт", "io", None),
]


class App(tk.Tk):
    def __init__(self, db_path=None):
        super().__init__()
        self.title("Учёт ПК — АС учёта компьютеров фирмы")
        self.geometry("1280x800")
        self.minsize(1024, 640)
        self.F = theme.setup(self)
        self.db = Database()
        self.acc = Accounting(self.db)
        self.build_menu()
        self.build_layout()
        self.views = {"dashboard": Dashboard(self), "tables": TablesView(self), "sql": SqlView(self),
                      "queries": QueriesView(self), "io": ImportExportView(self)}
        self.current = None
        self.protocol("WM_DELETE_WINDOW", self.quit_app)
        self.open_db(db_path or DEFAULT_DB, quiet=db_path is None)
        self.show("dashboard")

    def build_menu(self):
        m = tk.Menu(self)
        file = tk.Menu(m, tearoff=False)
        file.add_command(label="Открыть базу…", command=self.ask_open)
        file.add_command(label="Закрыть базу", command=self.close_db)
        file.add_command(label="Резервная копия…", command=self.backup)
        file.add_separator()
        file.add_command(label="Выход", command=self.quit_app)
        m.add_cascade(label="Файл", menu=file)
        data = tk.Menu(m, tearoff=False)
        for label, table in [("Компьютеры", "computers"), ("Сотрудники", "employees"), ("Закрепления", "assignments"),
                             ("Обслуживание", "services"), ("Комплектующие", "components"),
                             ("Программы", "programs"), ("Справочники", "departments")]:
            data.add_command(label=label, command=lambda t=table: self.show("tables", t))
        data.add_separator()
        data.add_command(label="Добавить запись", command=lambda: self.table_action("add"))
        data.add_command(label="Изменить запись", command=lambda: self.table_action("edit"))
        data.add_command(label="Удалить запись", command=lambda: self.table_action("delete"))
        m.add_cascade(label="Данные", menu=data)
        ops = tk.Menu(m, tearoff=False)
        for label, op in [("Поставить компьютер на учёт…", "register"), ("Выдать компьютер сотруднику…", "assign"),
                          ("Принять возврат компьютера…", "return"), (None, None),
                          ("Зарегистрировать обслуживание…", "service_open"),
                          ("Завершить обслуживание…", "service_close"), (None, None),
                          ("Установить программу…", "install"), ("Списать компьютер…", "writeoff")]:
            if label is None:
                ops.add_separator()
            else:
                ops.add_command(label=label, command=lambda o=op: self.operation(o))
        m.add_cascade(label="Операции", menu=ops)
        q = tk.Menu(m, tearoff=False)
        q.add_command(label="SQL-консоль", command=lambda: self.show("sql"))
        q.add_command(label="Готовые запросы", command=lambda: self.show("queries"))
        m.add_cascade(label="Запросы", menu=q)
        io = tk.Menu(m, tearoff=False)
        io.add_command(label="Экспорт данных…", command=lambda: self.show_io("export"))
        io.add_command(label="Импорт данных…", command=lambda: self.show_io("import"))
        m.add_cascade(label="Импорт/экспорт", menu=io)
        hlp = tk.Menu(m, tearoff=False)
        hlp.add_command(label="О программе", command=lambda: messagebox.showinfo(
            "О программе", "Учёт ПК — АС учёта компьютеров, используемых фирмой.\n"
                           "ЛР3 (часть 2), дисциплина «Модели данных».\nPython, Tkinter, SQLite.", parent=self))
        m.add_cascade(label="Справка", menu=hlp)
        self.config(menu=m)

    def build_layout(self):
        side = ttk.Frame(self, style="Sidebar.TFrame", width=220)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)
        ttk.Label(side, text="Учёт ПК", style="Brand.TLabel").pack(anchor="w", padx=20, pady=(20, 0))
        ttk.Label(side, text="АС учёта компьютеров", style="Sidebar.TLabel").pack(anchor="w", padx=20, pady=(0, 16))
        self.nav_buttons = []
        for label, view, arg in NAV:
            if view is None:
                ttk.Label(side, text=label.upper(), style="Sidebar.TLabel").pack(anchor="w", padx=20, pady=(12, 4))
                continue
            b = ttk.Button(side, text=label, style="Nav.TButton", command=lambda v=view, a=arg: self.show(v, a))
            b.pack(fill="x", padx=10, pady=1)
            self.nav_buttons.append((b, view, arg))
        self.db_label = ttk.Label(side, text="", style="Sidebar.TLabel", wraplength=190)
        self.db_label.pack(side="bottom", anchor="w", padx=20, pady=16)
        main = ttk.Frame(self)
        main.pack(side="left", fill="both", expand=True)
        top = ttk.Frame(main, style="Top.TFrame", padding=(24, 10))
        top.pack(fill="x")
        self.crumbs = ttk.Label(top, text="", style="Crumb.TLabel")
        self.crumbs.pack(anchor="w")
        self.heading = ttk.Label(top, text="", style="Title.TLabel")
        self.heading.pack(anchor="w")
        self.content = ttk.Frame(main)
        self.content.pack(fill="both", expand=True)
        self.statusbar = ttk.Label(main, text="", style="Muted.TLabel", padding=(24, 6))
        self.statusbar.pack(fill="x", side="bottom")

    def set_title(self, title, crumbs):
        self.heading.configure(text=title)
        self.crumbs.configure(text=crumbs)

    def show(self, name, arg=None):
        if self.current is not None:
            self.current.pack_forget()
        view = self.views[name]
        self.current = view
        view.pack(fill="both", expand=True)
        self.set_title(view.title, view.crumbs)
        for b, v, a in self.nav_buttons:
            active = v == name and (a is None or a == arg or (name == "tables" and arg is None and a == view.table))
            b.configure(style="NavActive.TButton" if active else "Nav.TButton")
        if not self.db.is_open:
            self.notify("warning", "База данных не открыта: Файл → Открыть базу…")
            return
        if name == "tables" and arg:
            view.set_table(arg)
        else:
            view.refresh()

    def show_io(self, op):
        self.show("io")
        self.views["io"].op.set(op)
        self.views["io"].suggest()

    def table_action(self, action):
        if self.current is not self.views["tables"]:
            self.show("tables", "computers")
        getattr(self.views["tables"], action)()

    def notify(self, kind, text):
        colors = {"success": theme.C["success"], "danger": theme.C["danger"], "warning": theme.C["warning"],
                  "info": theme.C["muted"]}
        self.statusbar.configure(text=text, foreground=colors.get(kind, theme.C["muted"]))

    def operation(self, op):
        if not self.db.is_open:
            messagebox.showwarning("Нет базы", "Сначала откройте базу данных", parent=self)
            return
        try:
            spec = operation_specs(self.acc)[op]
        except DatabaseError as e:
            messagebox.showerror("Ошибка базы данных", str(e), parent=self)
            return
        OperationDialog(self, self.F, spec, self.operation_done)

    def operation_done(self, text):
        self.notify("success", text)
        messagebox.showinfo("Готово", text, parent=self)
        self.data_changed()

    def data_changed(self):
        if self.current is not None and self.current is not self.views["sql"]:
            self.current.refresh()

    def open_db(self, path, quiet=False):
        try:
            self.db.open(path)
        except DatabaseError as e:
            self.db_label.configure(text="база не открыта")
            if not quiet:
                messagebox.showerror("Ошибка подключения", str(e), parent=self)
            self.notify("danger", str(e))
            return False
        version = self.db.value("PRAGMA user_version")
        self.db_label.configure(text=f"{Path(path).name} · схема v{version}")
        self.notify("success", f"Подключена база {path}")
        return True

    def ask_open(self):
        path = filedialog.askopenfilename(parent=self, title="Открыть базу данных SQLite",
                                          filetypes=[("SQLite", "*.db *.sqlite *.sqlite3"), ("Все файлы", "*")])
        if path and self.open_db(path):
            self.show("dashboard")

    def close_db(self):
        self.db.close()
        self.db_label.configure(text="база не открыта")
        for view in self.views.values():
            for child in view.winfo_children():
                if hasattr(child, "load"):
                    child.load([], [])
        self.notify("info", "База данных закрыта")

    def backup(self):
        if not self.db.is_open:
            return
        path = filedialog.asksaveasfilename(parent=self, defaultextension=".db",
                                            initialfile=f"{self.db.path.stem}_backup.db")
        if not path:
            return
        dst = sqlite3.connect(path)
        try:
            self.db.con.backup(dst)
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка", f"Не удалось создать копию: {e}", parent=self)
            return
        finally:
            dst.close()
        self.notify("success", f"Резервная копия сохранена: {path}")

    def quit_app(self):
        self.db.close()
        self.destroy()


def main():
    App(sys.argv[1] if len(sys.argv) > 1 else None).mainloop()


if __name__ == "__main__":
    main()

import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from dialogs import OperationDialog, RecordDialog, operation_specs  # noqa: E402
from main import App  # noqa: E402


def pump(app, n=3):
    for _ in range(n):
        app.update_idletasks()
        app.update()


def main():
    tmp = Path(tempfile.mkdtemp())
    db = tmp / "computers.db"
    shutil.copy2(ROOT / "data" / "computers.db", db)
    app = App(str(db))
    pump(app)
    checks = []
    for name, arg in [("dashboard", None), ("tables", "computers"), ("tables", "employees"), ("tables", "services"),
                      ("sql", None), ("queries", None), ("io", None)]:
        app.show(name, arg)
        pump(app)
        checks.append(f"экран {name}{'/' + arg if arg else ''}: ok")
    dash = app.views["dashboard"]
    checks.append(f"главная: {[dash.values[k].cget('text') for k in dash.values]}")
    tv = app.views["tables"]
    app.show("tables", "computers")
    tv.status_box.set("в резерве")
    tv.refresh()
    checks.append(f"фильтр «в резерве»: {len(tv.grid_table.shown)} строк")
    tv.search.insert(0, "lenovo")
    tv.apply_filter()
    tv.grid_table.sort_by("commission_date")
    checks.append(f"поиск и сортировка: {tv.info.cget('text')[:40]}")
    for op, spec in operation_specs(app.acc).items():
        dlg = OperationDialog(app, app.F, spec, lambda t: None)
        pump(app)
        for key in dlg.widgets:
            w = dlg.widgets[key]
            if hasattr(w, "set_key"):
                w.set("")
        dlg.submit()
        errs = [k for k, lbl in dlg.errors.items() if lbl.cget("text")]
        checks.append(f"форма {op}: пустая отправка → ошибки в полях {errs}")
        dlg.destroy()
    for table in app.db.tables():
        res = app.db.run(f'SELECT * FROM "{table}" LIMIT 1')
        dlg = RecordDialog(app, app.F, app.db, table, dict(zip(res.columns, res.rows[0])), lambda t: None)
        pump(app)
        dlg.destroy()
    checks.append(f"карточки записей всех {len(app.db.tables())} таблиц: ok")
    sql = app.views["sql"]
    app.show("sql")
    sql.execute()
    checks.append(f"SQL: {sql.status.cget('text')}")
    sql.load_sql("SELECT nope FROM computers")
    sql.execute()
    checks.append(f"SQL с ошибкой: {sql.message.cget('text')}")
    qv = app.views["queries"]
    app.show("queries")
    qv.run()
    checks.append(f"готовый запрос: {qv.heading.cget('text')} → {qv.status.cget('text')}")
    io = app.views["io"]
    app.show("io")
    io.path.delete(0, "end")
    io.path.insert(0, str(tmp / "computers.csv"))
    io.start()
    checks.append(f"экспорт: {io.message.cget('text')}")
    io.op.set("import")
    io.start()
    checks.append(f"повторный импорт без пропуска: {io.message.cget('text')[:70]}")
    app.quit_app()
    shutil.rmtree(tmp)
    print("\n".join(checks))


if __name__ == "__main__":
    main()

import shutil
import sqlite3
import sys
from datetime import date
from pathlib import Path

from validate_rules import validate

ROOT = Path(__file__).resolve().parent.parent
SQL = ROOT / "sql"
DB = ROOT / "db" / "computers.db"
STEPS = ["01_tables_gui.sql", "02_tables_sql.sql", "03_constraints.sql", "04_seed.sql"]
TABLES = ["departments", "rooms", "models", "employees", "computers", "components",
          "programs", "assignments", "software_installs", "services"]


def export_schema(con, path):
    rows = con.execute(
        "SELECT type, name, sql FROM sqlite_master "
        "WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    order = {name: i for i, name in enumerate(TABLES)}
    tables = sorted((r for r in rows if r[0] == "table"), key=lambda r: order.get(r[1], 99))
    indexes = sorted((r for r in rows if r[0] == "index"), key=lambda r: r[1])
    path.write_text("\n\n".join(r[2] + ";" for r in tables + indexes) + "\n", encoding="utf-8")


def build():
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    for name in STEPS:
        con.executescript((SQL / name).read_text(encoding="utf-8"))
        print("выполнен", name)
    con.execute("PRAGMA foreign_keys = ON")
    fk = con.execute("PRAGMA foreign_key_check").fetchall()
    integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
    print("foreign_key_check:", "нарушений нет" if not fk else fk)
    print("integrity_check:", integrity)
    for t in TABLES:
        print(f"  {t:18} {con.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]:4} строк")
    export_schema(con, ROOT / "schema_export.sql")
    con.close()

    backup = ROOT / "backup" / f"computers_{date.today():%Y-%m-%d}.db"
    shutil.copy2(DB, backup)
    print("резервная копия:", backup.relative_to(ROOT))
    return bool(fk) or integrity != "ok"


if __name__ == "__main__":
    broken = build()
    print("\nПроверка бизнес-правил:")
    sys.exit(1 if broken or validate() else 0)

import argparse
import sqlite3
import sys
import tempfile
from pathlib import Path

import dbio


def empty_copy(src_con, path):
    ddl = [r[0] for r in src_con.execute(
        "SELECT sql FROM sqlite_master WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%' "
        "ORDER BY type = 'index'")]
    con = sqlite3.connect(path)
    con.executescript(";\n".join(ddl) + ";")
    con.execute("PRAGMA foreign_keys = ON")
    return con


def rows(con, table):
    return sorted(con.execute(f'SELECT * FROM "{table}"').fetchall(), key=repr)


def check(fmt, folder, src_con):
    ok = True
    with tempfile.TemporaryDirectory() as tmp:
        dst = empty_copy(src_con, Path(tmp) / "roundtrip.db")
        for t in dbio.tables(src_con):
            f = folder / f"{t}.{fmt}"
            fields, data = dbio.read_csv(f) if fmt == "csv" else dbio.read_json(f)
            dbio.insert_rows(dst, t, fields, data)
            same = rows(src_con, t) == rows(dst, t)
            types = dbio.type_mismatches(dst, t)
            ok &= same and not types
            note = "совпадает" if same else "РАСХОЖДЕНИЕ"
            print(f"  {t:18} {len(data):4} строк, {note}" + (f"; типы: {types}" if types else ""))
        dst.close()
    return ok


def main():
    p = argparse.ArgumentParser(description="Проверка: экспорт → импорт в пустую копию схемы → сравнение")
    p.add_argument("--db", default=dbio.DB)
    a = p.parse_args()
    src = dbio.connect(a.db)
    result = True
    for fmt in ("csv", "json"):
        print(f"{fmt.upper()}:")
        result &= check(fmt, dbio.HERE / "export" / fmt, src)
    src.close()
    print("итог:", "данные восстановлены без потерь" if result else "есть расхождения")
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()

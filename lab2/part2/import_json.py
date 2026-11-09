import argparse
import sys

import dbio


def main():
    p = argparse.ArgumentParser(description="Импорт JSON-файла (массив объектов) в таблицу SQLite")
    p.add_argument("file")
    p.add_argument("--table", required=True)
    p.add_argument("--db", default=dbio.DB)
    p.add_argument("--skip-existing", action="store_true",
                   help="пропускать строки, конфликтующие по ключу или UNIQUE")
    a = p.parse_args()
    try:
        con = dbio.connect(a.db)
        fields, rows = dbio.read_json(a.file)
        before, after = dbio.insert_rows(con, a.table, fields, rows, a.skip_existing)
    except (OSError, ValueError, dbio.sqlite3.Error) as e:
        sys.exit(f"ошибка импорта, изменения отменены: {e}")
    print(f"{a.table}: в файле {len(rows)} строк, было {before}, стало {after}, добавлено {after - before}")
    for problem in dbio.type_mismatches(con, a.table):
        print("  несоответствие типов:", problem)


if __name__ == "__main__":
    main()

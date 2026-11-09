import argparse
import sys
from pathlib import Path

import dbio


def main():
    p = argparse.ArgumentParser(description="Экспорт таблиц SQLite в CSV")
    p.add_argument("tables", nargs="*", help="таблицы (по умолчанию — все)")
    p.add_argument("--db", default=dbio.DB)
    p.add_argument("--out", default=dbio.HERE / "export" / "csv")
    p.add_argument("--delimiter", default=",")
    p.add_argument("--bom", action="store_true", help="UTF-8 с BOM (для Excel)")
    a = p.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    try:
        con = dbio.connect(a.db)
        for t in a.tables or dbio.tables(con):
            n = dbio.export_csv(con, t, out / f"{t}.csv", a.delimiter, a.bom)
            print(f"{t:18} {n:4} строк → {out / (t + '.csv')}")
    except (OSError, ValueError, dbio.sqlite3.Error) as e:
        sys.exit(f"ошибка экспорта: {e}")


if __name__ == "__main__":
    main()

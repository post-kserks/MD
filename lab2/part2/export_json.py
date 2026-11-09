import argparse
import sys
from pathlib import Path

import dbio


def main():
    p = argparse.ArgumentParser(description="Экспорт таблиц SQLite в JSON")
    p.add_argument("tables", nargs="*", help="таблицы (по умолчанию — все)")
    p.add_argument("--db", default=dbio.DB)
    p.add_argument("--out", default=dbio.HERE / "export" / "json")
    a = p.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    try:
        con = dbio.connect(a.db)
        for t in a.tables or dbio.tables(con):
            n = dbio.export_json(con, t, out / f"{t}.json")
            print(f"{t:18} {n:4} строк → {out / (t + '.json')}")
    except (OSError, ValueError, dbio.sqlite3.Error) as e:
        sys.exit(f"ошибка экспорта: {e}")


if __name__ == "__main__":
    main()

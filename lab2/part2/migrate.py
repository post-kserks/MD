import argparse
import sqlite3
import sys
from pathlib import Path

import dbio
from backup import make_backup
from restore import restore

MIGRATIONS = dbio.HERE / "migrations"


def available():
    out = []
    for path in sorted(MIGRATIONS.glob("*.sql")):
        out.append((int(path.name.split("_", 1)[0]), path))
    return out


def version(con):
    return con.execute("PRAGMA user_version").fetchone()[0]


def apply(con, number, path):
    script = ("PRAGMA foreign_keys = OFF;\nBEGIN;\n" + path.read_text(encoding="utf-8")
              + f"\nPRAGMA user_version = {number};\nCOMMIT;\nPRAGMA foreign_keys = ON;\n")
    try:
        con.executescript(script)
    except sqlite3.Error:
        if con.in_transaction:
            con.rollback()
        con.execute("PRAGMA foreign_keys = ON")
        raise
    bad = con.execute("PRAGMA foreign_key_check").fetchall()
    if bad:
        raise RuntimeError(f"после миграции {path.name} нарушены внешние ключи: {bad[:5]}")


def migrate(db=dbio.DB, target=None):
    con = dbio.connect(db)
    current = version(con)
    todo = [(n, p) for n, p in available() if n > current and (target is None or n <= target)]
    if not todo:
        con.close()
        return current, [], None
    backup, _ = make_backup(db)
    done = []
    try:
        for n, p in todo:
            apply(con, n, p)
            done.append(p.name)
    except (sqlite3.Error, RuntimeError):
        con.close()
        restore(backup, db)
        raise
    current = version(con)
    con.close()
    return current, done, backup


def main():
    p = argparse.ArgumentParser(description="Миграции структуры базы (версия хранится в PRAGMA user_version)")
    p.add_argument("--db", default=dbio.DB)
    p.add_argument("--to", type=int, help="целевая версия (по умолчанию — последняя)")
    p.add_argument("--list", action="store_true")
    a = p.parse_args()
    con = dbio.connect(a.db)
    cur = version(con)
    con.close()
    if a.list:
        for n, path in available():
            print(f"{'✔' if n <= cur else ' '} {path.name}")
        print("текущая версия:", cur)
        return
    try:
        new, done, backup = migrate(a.db, a.to)
    except (sqlite3.Error, RuntimeError, OSError) as e:
        sys.exit(f"миграция не выполнена, база восстановлена из копии: {e}")
    if not done:
        print(f"база уже в версии {new}, применять нечего")
        return
    print("резервная копия перед миграцией:", Path(backup).name)
    for name in done:
        print("применена", name)
    print("версия схемы:", new)


if __name__ == "__main__":
    main()

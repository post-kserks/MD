import argparse
import shutil
import sqlite3
import sys
from pathlib import Path

import dbio
from backup import BACKUP_DIR, list_backups


def restore(backup, db=dbio.DB):
    backup, db = Path(backup), Path(db)
    check = sqlite3.connect(f"file:{backup}?mode=ro", uri=True)
    try:
        status = check.execute("PRAGMA integrity_check").fetchone()[0]
    finally:
        check.close()
    if status != "ok":
        raise RuntimeError(f"копия {backup.name} повреждена: {status}")
    safety = None
    if db.exists():
        safety = db.with_name(db.stem + "_before_restore.db")
        shutil.copy2(db, safety)
    src, dst = sqlite3.connect(backup), sqlite3.connect(db)
    try:
        src.backup(dst)
    finally:
        src.close()
        dst.close()
    return safety


def main():
    p = argparse.ArgumentParser(description="Восстановление базы SQLite из резервной копии")
    p.add_argument("backup", nargs="?", help="файл копии (по умолчанию — последняя)")
    p.add_argument("--db", default=dbio.DB)
    p.add_argument("--dir", default=BACKUP_DIR)
    p.add_argument("--list", action="store_true", help="показать доступные копии")
    a = p.parse_args()
    copies = list_backups(a.dir, Path(a.db).stem)
    if a.list:
        for c in copies:
            print(c.name)
        return
    if not a.backup and not copies:
        sys.exit("резервных копий нет")
    src = Path(a.backup) if a.backup else copies[-1]
    try:
        safety = restore(src, a.db)
    except (OSError, RuntimeError, sqlite3.Error) as e:
        sys.exit(f"ошибка восстановления: {e}")
    print(f"база восстановлена из {src.name}")
    if safety:
        print(f"предыдущее состояние сохранено в {safety.name}")


if __name__ == "__main__":
    main()

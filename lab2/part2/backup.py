import argparse
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import dbio

BACKUP_DIR = dbio.HERE / "backups"


def make_backup(db=dbio.DB, backup_dir=BACKUP_DIR, keep=10):
    db, backup_dir = Path(db), Path(backup_dir)
    if not db.exists():
        raise FileNotFoundError(f"нет файла базы данных: {db}")
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    dst = backup_dir / f"{db.stem}_{stamp}.db"
    n = 1
    while dst.exists():
        dst = backup_dir / f"{db.stem}_{stamp}_{n}.db"
        n += 1
    src_con, dst_con = sqlite3.connect(db), sqlite3.connect(dst)
    try:
        src_con.backup(dst_con)
        status = dst_con.execute("PRAGMA integrity_check").fetchone()[0]
    finally:
        src_con.close()
        dst_con.close()
    if status != "ok":
        dst.unlink()
        raise RuntimeError(f"копия повреждена: {status}")
    removed = rotate(backup_dir, db.stem, keep)
    return dst, removed


def list_backups(backup_dir=BACKUP_DIR, stem="computers"):
    return sorted(Path(backup_dir).glob(f"{stem}_*.db"))


def rotate(backup_dir, stem, keep):
    copies = list_backups(backup_dir, stem)
    old = copies[:-keep] if keep > 0 else []
    for path in old:
        path.unlink()
    return old


def main():
    p = argparse.ArgumentParser(description="Резервная копия базы SQLite с датой и временем в имени")
    p.add_argument("--db", default=dbio.DB)
    p.add_argument("--dir", default=BACKUP_DIR)
    p.add_argument("--keep", type=int, default=10, help="сколько последних копий хранить")
    a = p.parse_args()
    try:
        dst, removed = make_backup(a.db, a.dir, a.keep)
    except (OSError, RuntimeError, sqlite3.Error) as e:
        sys.exit(f"ошибка резервного копирования: {e}")
    print("создана копия:", dst)
    for path in removed:
        print("удалена устаревшая копия:", path.name)


if __name__ == "__main__":
    main()

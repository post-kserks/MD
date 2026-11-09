import shutil
import sqlite3
import tempfile
from pathlib import Path

import dbio
from backup import make_backup
from restore import restore


def counts(db):
    con = sqlite3.connect(db)
    try:
        return {t: dbio.count(con, t) for t in dbio.tables(con)}
    finally:
        con.close()


def main():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        db = tmp / "computers.db"
        shutil.copy2(dbio.DB, db)
        before = counts(db)
        backup, _ = make_backup(db, tmp / "backups")
        print("1. создана копия:", backup.name)
        con = sqlite3.connect(db)
        con.execute("PRAGMA foreign_keys = ON")
        with con:
            con.execute("DELETE FROM services")
            con.execute("DELETE FROM software_installs")
        con.close()
        damaged = counts(db)
        print(f"2. «авария»: services {before['services']} → {damaged['services']}, "
              f"software_installs {before['software_installs']} → {damaged['software_installs']}")
        restore(backup, db)
        after = counts(db)
        print(f"3. восстановлено: services {after['services']}, software_installs {after['software_installs']}")
        con = sqlite3.connect(db)
        status = con.execute("PRAGMA integrity_check").fetchone()[0]
        con.close()
        print("4. integrity_check:", status, "| все таблицы совпадают с исходными:", after == before)


if __name__ == "__main__":
    main()

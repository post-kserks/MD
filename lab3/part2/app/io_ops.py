import csv
import json
from pathlib import Path

from db import Database, DatabaseError


def export_table(db: Database, table, path, fmt, delimiter=",", header=True):
    res = db.run(f'SELECT * FROM "{table}"')
    path = Path(path)
    if fmt == "csv":
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, delimiter=delimiter)
            if header:
                w.writerow(res.columns)
            for row in res.rows:
                w.writerow(["" if v is None else v for v in row])
    elif fmt == "json":
        with open(path, "w", encoding="utf-8") as f:
            json.dump([dict(zip(res.columns, r)) for r in res.rows], f, ensure_ascii=False, indent=2)
    else:
        raise ValueError(f"неизвестный формат: {fmt}")
    return len(res.rows)


def read_file(db: Database, table, path, fmt, delimiter=",", header=True):
    path = Path(path)
    if fmt == "csv":
        with open(path, newline="", encoding="utf-8-sig") as f:
            if header:
                reader = csv.DictReader(f, delimiter=delimiter)
                fields = list(reader.fieldnames or [])
                rows = [{k: (None if v == "" else v) for k, v in r.items()} for r in reader]
            else:
                fields = [c["name"] for c in db.columns(table)]
                rows = [dict(zip(fields, [None if v == "" else v for v in r])) for r in csv.reader(f, delimiter=delimiter)]
    elif fmt == "json":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list) or not all(isinstance(x, dict) for x in data):
            raise ValueError("ожидается JSON-массив объектов")
        fields = []
        for obj in data:
            fields += [k for k in obj if k not in fields]
        rows = data
    else:
        raise ValueError(f"неизвестный формат: {fmt}")
    return fields, rows


def import_table(db: Database, table, path, fmt, delimiter=",", header=True, skip_existing=False):
    fields, rows = read_file(db, table, path, fmt, delimiter, header)
    known = {c["name"] for c in db.columns(table)}
    unknown = [f for f in fields if f not in known]
    if unknown:
        raise ValueError(f"в таблице {table} нет столбцов: {', '.join(unknown)}")
    if not fields:
        raise ValueError("в файле нет столбцов")
    before = db.value(f'SELECT COUNT(*) FROM "{table}"')
    names = ", ".join(f'"{f}"' for f in fields)
    marks = ", ".join("?" for _ in fields)
    tail = " ON CONFLICT DO NOTHING" if skip_existing else ""
    with db.transaction() as con:
        con.executemany(f'INSERT INTO "{table}" ({names}) VALUES ({marks}){tail}',
                        [[r.get(f) for f in fields] for r in rows])
    after = db.value(f'SELECT COUNT(*) FROM "{table}"')
    return len(rows), after - before


__all__ = ["export_table", "import_table", "read_file", "DatabaseError"]

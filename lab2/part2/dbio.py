import csv
import json
import sqlite3
from pathlib import Path

HERE = Path(__file__).resolve().parent
DB = HERE / "db" / "computers.db"
ORDER = ["buildings", "departments", "rooms", "models", "employees", "computers", "components",
         "programs", "assignments", "software_installs", "services"]


def connect(path=DB):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"нет файла базы данных: {path}")
    con = sqlite3.connect(path)
    con.execute("PRAGMA foreign_keys = ON")
    return con


def tables(con):
    names = [r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'")]
    return sorted(names, key=lambda n: ORDER.index(n) if n in ORDER else len(ORDER))


def columns(con, table):
    return [r[1] for r in con.execute(f'PRAGMA table_info("{table}")')]


def declared_types(con, table):
    return {r[1]: r[2].upper() for r in con.execute(f'PRAGMA table_info("{table}")')}


def require_table(con, table):
    if table not in tables(con):
        raise ValueError(f"в базе нет таблицы {table}")


def count(con, table):
    return con.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]


def export_csv(con, table, path, delimiter=",", bom=False):
    require_table(con, table)
    cur = con.execute(f'SELECT * FROM "{table}"')
    cols = [d[0] for d in cur.description]
    n = 0
    with open(path, "w", newline="", encoding="utf-8-sig" if bom else "utf-8") as f:
        w = csv.writer(f, delimiter=delimiter)
        w.writerow(cols)
        for row in cur:
            w.writerow(["" if v is None else v for v in row])
            n += 1
    return n


def read_csv(path, delimiter=","):
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        rows = [{k: (None if v == "" else v) for k, v in row.items()} for row in reader]
        return list(reader.fieldnames or []), rows


def export_json(con, table, path):
    require_table(con, table)
    cur = con.execute(f'SELECT * FROM "{table}"')
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, r)) for r in cur]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    return len(rows)


def read_json(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list) or not all(isinstance(x, dict) for x in data):
        raise ValueError("ожидается JSON-массив объектов")
    fields = []
    for obj in data:
        for k in obj:
            if k not in fields:
                fields.append(k)
    return fields, data


def insert_rows(con, table, fields, rows, skip_existing=False):
    require_table(con, table)
    cols = columns(con, table)
    unknown = [f for f in fields if f not in cols]
    if unknown:
        raise ValueError(f"в таблице {table} нет столбцов: {', '.join(unknown)}")
    if not fields:
        raise ValueError("в файле нет столбцов")
    before = count(con, table)
    names = ", ".join(f'"{f}"' for f in fields)
    marks = ", ".join("?" for _ in fields)
    tail = " ON CONFLICT DO NOTHING" if skip_existing else ""
    sql = f'INSERT INTO "{table}" ({names}) VALUES ({marks}){tail}'
    with con:
        con.executemany(sql, [[row.get(f) for f in fields] for row in rows])
    return before, count(con, table)


def type_mismatches(con, table):
    affinity = {"INTEGER": {"integer"}, "REAL": {"real", "integer"}, "TEXT": {"text"}}
    problems = []
    for col, decl in declared_types(con, table).items():
        allowed = affinity.get(decl)
        if not allowed:
            continue
        for t, n in con.execute(f'SELECT typeof("{col}"), COUNT(*) FROM "{table}" '
                                f'WHERE "{col}" IS NOT NULL GROUP BY 1'):
            if t not in allowed:
                problems.append(f"{col}: {n} знач. типа {t} при объявленном {decl}")
    return problems

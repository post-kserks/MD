import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


class DatabaseError(Exception):
    pass


@dataclass
class Result:
    columns: List[str] = field(default_factory=list)
    rows: List[tuple] = field(default_factory=list)
    rowcount: int = 0
    elapsed_ms: float = 0.0
    script: bool = False

    @property
    def is_select(self):
        return bool(self.columns)


class Database:
    def __init__(self):
        self.con: Optional[sqlite3.Connection] = None
        self.path: Optional[Path] = None

    @property
    def is_open(self):
        return self.con is not None

    def open(self, path):
        path = Path(path)
        if not path.exists():
            raise DatabaseError(f"Файл базы данных не найден: {path}")
        try:
            con = sqlite3.connect(path)
            con.execute("PRAGMA foreign_keys = ON")
            con.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()
        except sqlite3.Error as e:
            raise DatabaseError(f"Не удалось открыть базу данных {path.name}: {e}") from e
        self.close()
        self.con, self.path = con, path

    def close(self):
        if self.con is not None:
            self.con.close()
        self.con, self.path = None, None

    def _require(self):
        if self.con is None:
            raise DatabaseError("База данных не открыта")
        return self.con

    def run(self, sql, params=()):
        con = self._require()
        start = time.perf_counter()
        try:
            cur = con.execute(sql, params)
            if cur.description:
                cols = [d[0] for d in cur.description]
                rows = cur.fetchall()
                return Result(cols, rows, len(rows), (time.perf_counter() - start) * 1000)
            con.commit()
            return Result([], [], cur.rowcount, (time.perf_counter() - start) * 1000)
        except (sqlite3.ProgrammingError, sqlite3.Warning) as e:
            if "one statement" not in str(e):
                raise DatabaseError(str(e)) from e
            try:
                con.executescript(sql)
            except sqlite3.Error as e2:
                if con.in_transaction:
                    con.rollback()
                raise DatabaseError(str(e2)) from e2
            return Result([], [], -1, (time.perf_counter() - start) * 1000, script=True)
        except sqlite3.Error as e:
            if con.in_transaction:
                con.rollback()
            raise DatabaseError(str(e)) from e

    def rows(self, sql, params=()):
        try:
            return self._require().execute(sql, params).fetchall()
        except sqlite3.Error as e:
            raise DatabaseError(str(e)) from e

    def value(self, sql, params=()):
        row = self.rows(sql, params)
        return row[0][0] if row else None

    @contextmanager
    def transaction(self):
        con = self._require()
        try:
            yield con
            con.commit()
        except sqlite3.Error as e:
            con.rollback()
            raise DatabaseError(str(e)) from e
        except Exception:
            con.rollback()
            raise

    def tables(self):
        return [r[0] for r in self.rows(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]

    def columns(self, table):
        self._check_table(table)
        return [{"name": r[1], "type": (r[2] or "").upper(), "notnull": bool(r[3]),
                 "default": r[4], "pk": r[5]} for r in self.rows(f'PRAGMA table_info("{table}")')]

    def primary_key(self, table):
        cols = [c for c in self.columns(table) if c["pk"]]
        return [c["name"] for c in sorted(cols, key=lambda c: c["pk"])]

    def foreign_keys(self, table):
        self._check_table(table)
        return [{"column": r[3], "table": r[2], "ref": r[4]} for r in self.rows(f'PRAGMA foreign_key_list("{table}")')]

    def referencing(self, table):
        out = []
        for t in self.tables():
            for r in self.rows(f'PRAGMA foreign_key_list("{t}")'):
                if r[2] == table:
                    out.append({"table": t, "column": r[3], "ref": r[4], "on_delete": r[6]})
        return out

    def dependents(self, table, pk_values):
        out = []
        for ref in self.referencing(table):
            value = pk_values.get(ref["ref"])
            if value is None:
                continue
            n = self.value(f'SELECT COUNT(*) FROM "{ref["table"]}" WHERE "{ref["column"]}" = ?', (value,))
            if n:
                out.append((ref["table"], n, ref["on_delete"]))
        return out

    def insert(self, table, values):
        self._check_table(table)
        values = {k: v for k, v in values.items() if v is not None}
        if not values:
            self.run(f'INSERT INTO "{table}" DEFAULT VALUES')
            return
        names = ", ".join(f'"{k}"' for k in values)
        marks = ", ".join("?" for _ in values)
        self.run(f'INSERT INTO "{table}" ({names}) VALUES ({marks})', tuple(values.values()))

    def update(self, table, pk, values):
        self._check_table(table)
        sets = ", ".join(f'"{k}" = ?' for k in values)
        where = " AND ".join(f'"{k}" = ?' for k in pk)
        res = self.run(f'UPDATE "{table}" SET {sets} WHERE {where}', tuple(values.values()) + tuple(pk.values()))
        return res.rowcount

    def delete(self, table, pk):
        self._check_table(table)
        where = " AND ".join(f'"{k}" = ?' for k in pk)
        return self.run(f'DELETE FROM "{table}" WHERE {where}', tuple(pk.values())).rowcount

    def _check_table(self, table):
        if table not in self.tables():
            raise DatabaseError(f"В базе нет таблицы {table}")

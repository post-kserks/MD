# ЛР1, часть 2 — база данных SQLite

## Пересобрать базу

```bash
cd lab1/part2/scripts
python3 seed.py
python3 build_db.py
python3 check_constraints.py
python3 schema_diagram.py
```

`build_db.py` создаёт `db/computers.db` из `sql/01–04`, проверяет внешние ключи и бизнес-правила, экспортирует `schema_export.sql` и кладёт копию в `backup/`.

## Что сделать вручную в DBeaver (скриншоты для отчёта)

Скриншоты сохранить в `img/` под указанными именами, затем пересобрать отчёт:

```bash
python3 tools/build_docx.py lab1/part2/report.md
```

| Файл | Что снять |
| --- | --- |
| `img/dbeaver_connection.png` | «Новое соединение → SQLite», путь к `db/computers.db`, вкладка свойств драйвера с `foreign_keys = true` |
| `img/dbeaver_table_designer.png` | таблица `rooms` в визуальном конструкторе (вкладка «Колонки») |
| `img/dbeaver_sql_editor.png` | SQL-редактор с выполненным `sql/02_tables_sql.sql` |
| `img/dbeaver_er.png` | ПКМ по базе → «Просмотр диаграммы» |

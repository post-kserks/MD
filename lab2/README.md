# ЛР2 — запросы, импорт и экспорт

## Часть 1 — SELECT-запросы (вариант 18)

```bash
cd lab2/part1
python3 run_queries.py
```

Запросы лежат в `part1/queries/`, по одному в файле. Результаты пишутся в `part1/results.md`. База — `lab1/part2/db/computers.db`, открывается только на чтение.

## Часть 2 — импорт/экспорт, миграции, резервные копии

Работа идёт с копией базы `part2/db/computers.db`. После миграций схема в версии 2: добавлены таблица `buildings` и столбец `computers.mac_address`.

```bash
cd lab2/part2
python3 export_csv.py
python3 export_json.py
python3 verify_roundtrip.py
python3 import_csv.py data/new_programs.csv --table programs
python3 import_json.py data/new_components.json --table components --skip-existing
python3 migrate.py --list
python3 backup.py --keep 10
python3 restore.py --list
python3 check_backup_restore.py
```

## Скриншоты DBeaver для отчётов

Сохранить в `img/` соответствующей части и пересобрать отчёт: `python3 tools/build_docx.py lab2/part1/report.md lab2/part2/report.md`.

| Файл | Что снять |
| --- | --- |
| `part1/img/dbeaver_query.png` | SQL-редактор с запросом `16_var18_categories_over_n.sql` и результатом |
| `part2/img/dbeaver_export_csv.png` | мастер «Экспорт данных», шаг настроек CSV |
| `part2/img/dbeaver_import_csv.png` | мастер «Импорт данных», шаг сопоставления столбцов для `data/new_programs.csv` |
| `part2/img/dbeaver_export_json.png` | мастер «Экспорт данных», формат JSON |
| `part2/img/dbeaver_import_json.png` | мастер «Импорт данных» с источником JSON для `data/new_components.json` |

Импорт CSV и JSON в DBeaver выполнять на копии базы (например, `backups/` → открыть копию), чтобы не задвоить данные, уже загруженные скриптами. Если в вашей версии DBeaver в мастере импорта нет источника JSON, поправьте раздел 6.1 отчёта: импорт JSON тогда выполняется только скриптом `import_json.py`.

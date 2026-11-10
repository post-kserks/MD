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

## Скриншоты DBeaver в отчётах

Сняты в DBeaver 26.2 и лежат в `part1/img/` и `part2/img/`. Чтобы заменить их своими, сохраните снимки под теми же именами и пересоберите отчёты: `python3 tools/build_docx.py lab2/part1/report.md lab2/part2/report.md`.

| Файл | Что на снимке |
| --- | --- |
| `part1/img/dbeaver_query.png` | SQL-редактор с запросом `16_var18_categories_over_n.sql` и результатом |
| `part2/img/dbeaver_export_csv.png` | мастер «Export Data», настройки формата CSV |
| `part2/img/dbeaver_import_csv.png` | мастер «Import Data», сопоставление столбцов для `data/new_programs.csv` |
| `part2/img/dbeaver_export_json.png` | мастер «Export Data», настройки формата JSON |
| `part2/img/dbeaver_import_json.png` | мастер «Import Data»: в Community-версии источники только CSV и Table, импорта JSON нет |

# ЛР3 — дизайн интерфейса и приложение

## Часть 1 — макеты и прототип

```bash
cd lab3/part1/design
python3 screens.py
```

Скрипт формирует `wireframes/*.svg`, `mockups/*.svg`, `design_system.svg` и `prototype/index.html`. Прототип — один самостоятельный файл, открывается в любом браузере. PNG-версии экранов лежат рядом с SVG и вставлены в отчёт.

### Figma

Файл «Учёт ПК — ИУ5 ЛР3» создан в аккаунте Figma: 8 фреймов экранов, фрейм «Компоненты дизайн-системы» и прототип из 41 перехода со стартовой точкой «01 Главная». Скриншоты лежат в `part1/img/figma_*.png`.

Как воспроизвести:

1. Вставить в Figma `design/figma/all_screens.svg` (Edit → Paste после копирования файла в Finder) и разгруппировать (Object → Ungroup Selection). Получатся 8 фреймов с именами экранов. В этом SVG шрифт заменён на Inter: шрифты Arial из исходных SVG Figma не отображает.
2. Plugins → Development → Import plugin from manifest → `design/figma/manifest.json`, затем запустить «MD prototype builder». Плагин добавит области переходов, связи прототипа, стартовую точку и компоненты.

## Часть 2 — приложение на Tkinter

```bash
cd lab3/part2
python3 app/main.py
```

Нужен Python 3.9+ с Tk 8.6 или новее (проверено на Python 3.12 / Tk 9.0). Системный `/usr/bin/python3` в macOS идёт с Tk 8.5 — на нём окно зависает; подойдёт Python с python.org или `uv python install 3.12`.

Тесты:

```bash
python3 -m unittest discover -s tests
python3 tests/smoke_ui.py
```

### Скриншоты приложения для отчёта

Запустить приложение, сделать снимки окна (Cmd+Shift+4, затем пробел и щелчок по окну) и сохранить в `part2/img/`:

| Файл | Что снять |
| --- | --- |
| `app_dashboard.png` | главный экран |
| `app_sql.png` | SQL-запросы с выполненным запросом |
| `app_tables.png` | «Компьютеры» с сортировкой по столбцу |
| `app_queries.png` | «Готовые запросы», вариант 18 с N = 5 |
| `app_import_export.png` | экспорт таблицы в CSV с сообщением об успехе |
| `app_form_errors.png` | «Операции → Поставить на учёт», нажать «Сохранить» с пустыми полями |
| `app_assign.png` | «Операции → Выдать компьютер» с заполненными полями |

Пересобрать отчёты: `python3 tools/build_docx.py lab3/part1/report.md lab3/part2/report.md`.

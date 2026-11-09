import re
from pathlib import Path

LR2_DIR = Path(__file__).resolve().parents[3] / "lab2" / "part1" / "queries"

TITLES = {
    "01_select_all": "Все компьютеры",
    "02_select_columns": "Сотрудники: ФИО, должность, телефон",
    "03_order_by": "Компьютеры от новых к старым",
    "04_limit_offset": "Обслуживания: вторая страница по стоимости",
    "05_where_between": "Введены в 2023–2024 годах",
    "06_in_subquery": "Ноутбуки (IN с подзапросом)",
    "07_like": "Сотрудники на «К» (LIKE)",
    "08_is_null": "Сотрудники без e-mail или телефона",
    "09_aggregates": "Статистика стоимости обслуживаний",
    "10_group_having": "Виды работ, выполнявшиеся больше трёх раз",
    "11_join": "Компьютеры, помещения и сотрудники (JOIN)",
    "12_distinct": "Типы и производители комплектующих",
    "13_exists": "Неустановленные программы (NOT EXISTS)",
    "14_case": "Состояние гарантии (CASE)",
    "15_var18_join_categories": "Вариант 18: компьютеры и их категории",
    "16_var18_categories_over_n": "Вариант 18: категории, где больше N компьютеров",
}

PARAMS = {
    "16_var18_categories_over_n": ("HAVING COUNT(*) > 5", "HAVING COUNT(*) > :n", {"n": ("N", "5")}),
}

SCHEMA_V2 = {
    "11_join": [
        ("r.building || ', ' || r.number", "b.name || ', ' || r.number"),
        ("INNER JOIN rooms r ON r.id_room = c.id_room",
         "INNER JOIN rooms r ON r.id_room = c.id_room\nINNER JOIN buildings b ON b.id_building = r.id_building"),
    ],
}

EXTRA = [
    ("Свободные лицензии платных программ",
     "SELECT p.name, p.version, p.license_count AS licenses, COUNT(i.inv_number) AS used,\n"
     "       p.license_count - COUNT(i.inv_number) AS free\n"
     "FROM programs p\nLEFT JOIN software_installs i USING (id_program)\n"
     "WHERE p.license_type <> 'бесплатная'\nGROUP BY p.id_program\nORDER BY free;", {}),
    ("Затраты на обслуживание по отделам за период",
     "SELECT d.name AS department, COUNT(*) AS services, SUM(s.cost) AS cost\n"
     "FROM services s\nJOIN assignments a ON a.inv_number = s.inv_number\n"
     "     AND a.issue_date <= s.start_date AND COALESCE(a.return_date, '9999') >= s.start_date\n"
     "JOIN employees e USING (tab_number)\nJOIN departments d USING (id_department)\n"
     "WHERE s.start_date BETWEEN :date_from AND :date_to\nGROUP BY d.id_department\nORDER BY cost DESC;",
     {"date_from": ("С", "2025-01-01"), "date_to": ("По", "2026-12-31")}),
]


def catalog():
    items = []
    if LR2_DIR.exists():
        for path in sorted(LR2_DIR.glob("*.sql")):
            sql = path.read_text(encoding="utf-8").strip()
            params = {}
            for old, new in SCHEMA_V2.get(path.stem, []):
                sql = sql.replace(old, new)
            if path.stem in PARAMS:
                old, new, params = PARAMS[path.stem]
                sql = sql.replace(old, new)
            items.append((f"{path.stem[:2]}. {TITLES.get(path.stem, path.stem)}", sql, params))
    for i, (title, sql, params) in enumerate(EXTRA, len(items) + 1):
        items.append((f"{i:02d}. {title}", sql, params))
    return items


def param_names(sql):
    return re.findall(r":([a-z_]+)", sql)

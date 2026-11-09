import sqlite3
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
DB = HERE.parent.parent / "lab1" / "part2" / "db" / "computers.db"
MAX_ROWS = 12
SHOW_ALL = {"14_case"}

TASKS = {
    "01_select_all": ("Все записи таблицы", "Выбрать все записи из таблицы компьютеров."),
    "02_select_columns": ("Отдельные столбцы", "Выбрать ФИО, должность и телефон сотрудников."),
    "03_order_by": ("Сортировка", "Компьютеры от новых к старым; при одинаковой дате — по инвентарному номеру."),
    "04_limit_offset": ("LIMIT и OFFSET", "Вторая «страница» (записи 6–10) обслуживаний по убыванию стоимости."),
    "05_where_between": ("WHERE и BETWEEN", "Действующие компьютеры, введённые в эксплуатацию в 2023–2024 годах."),
    "06_in_subquery": ("IN с подзапросом", "Компьютеры, модель которых относится к типу «ноутбук»."),
    "07_like": ("LIKE", "Сотрудники, фамилия которых начинается на «К»."),
    "08_is_null": ("IS NULL", "Сотрудники, у которых не указан e-mail или телефон."),
    "09_aggregates": ("Агрегатные функции", "Количество, сумма, средняя, минимальная и максимальная стоимость завершённых обслуживаний."),
    "10_group_having": ("GROUP BY и HAVING", "Виды работ, выполнявшиеся больше трёх раз, с суммой затрат."),
    "11_join": ("INNER JOIN и LEFT JOIN", "Действующие компьютеры с моделью, помещением и сотрудником, за которым компьютер закреплён сейчас."),
    "12_distinct": ("DISTINCT", "Уникальные сочетания «тип комплектующего — производитель»."),
    "13_exists": ("EXISTS", "Программы, которые не установлены ни на одном компьютере."),
    "14_case": ("CASE", "Состояние гарантии каждого действующего компьютера."),
    "15_var18_join_categories": ("Вариант 18, задание 1",
                                 "Получить список объектов и их категорий, используя соединение таблиц: компьютеры и их тип устройства (категория задаётся моделью)."),
    "16_var18_categories_over_n": ("Вариант 18, задание 2",
                                   "Найти категории, в которых количество объектов превышает заданное значение: типы устройств, в которых больше 5 несписанных компьютеров."),
}


def md_cell(v):
    if v is None:
        return "NULL"
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    return str(v).replace("|", "\\|")


def run():
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    out = [f"Запросы выполнены {date.today():%d.%m.%Y} над базой `lab1/part2/db/computers.db`.", ""]
    for path in sorted((HERE / "queries").glob("*.sql")):
        title, task = TASKS[path.stem]
        sql = path.read_text(encoding="utf-8").strip()
        cur = con.execute(sql)
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
        num = path.stem[:2]
        out += [f"### Запрос {num}. {title}", "", f"**Задание.** {task}", "",
                f"Файл: `queries/{path.name}`", "", "```sql", sql, "```", "",
                "| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
        limit = len(rows) if path.stem in SHOW_ALL else MAX_ROWS
        for r in rows[:limit]:
            out.append("| " + " | ".join(md_cell(v) for v in r) + " |")
        out.append("")
        if len(rows) > limit:
            out.append(f"Показаны первые {limit} из {len(rows)} строк.")
        else:
            out.append(f"Строк в результате: {len(rows)}.")
        out.append("")
        print(f"{path.name:36} {len(rows):3} строк")
    con.close()
    (HERE / "results.md").write_text("\n".join(out), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(run())

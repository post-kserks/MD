import json
import sqlite3
from pathlib import Path

from ui_kit import PALETTE, SIDEBAR_W, TYPE, Frame, H, W, text_width

HERE = Path(__file__).resolve().parent
DB = HERE.parents[2] / "lab2" / "part2" / "db" / "computers.db"
X0 = SIDEBAR_W + 24
CW = W - SIDEBAR_W - 48

NAV = [
    (None, "", "Работа", None),
    ("dashboard", "⌂", "Главная", "dashboard"),
    ("computers", "▤", "Компьютеры", "computers"),
    ("employees", "☺", "Сотрудники", None),
    ("assignments", "⇄", "Закрепления", None),
    ("services", "✎", "Обслуживание", None),
    ("refs", "≡", "Справочники", None),
    (None, "", "Данные", None),
    ("sql", "›", "SQL-запросы", "sql"),
    ("queries", "★", "Готовые запросы", "queries"),
    ("import_export", "⇅", "Импорт и экспорт", "import_export"),
]

TITLES = {
    "dashboard": "Главная",
    "computers": "Просмотр данных: компьютеры",
    "computer_form": "Постановка компьютера на учёт",
    "assign_form": "Выдача компьютера сотруднику",
    "sql": "SQL-запросы",
    "queries": "Готовые запросы",
    "import_export": "Импорт и экспорт",
    "delete_confirm": "Подтверждение удаления",
}


def q(sql, *args):
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        return [tuple("NULL" if v is None else v for v in r) for r in con.execute(sql, args)]
    finally:
        con.close()


def base(name, wire, crumbs, active=None):
    f = Frame(name, wire)
    f.sidebar(active or name, NAV)
    f.topbar(TITLES[name], crumbs, "computers.db · 30 компьютеров")
    return f


def dashboard(wire):
    f = base("dashboard", wire, "Учёт ПК / Главная")
    stats = dict(q("SELECT status, COUNT(*) FROM computers GROUP BY status"))
    cards = [("В эксплуатации", "в эксплуатации", "success"), ("В резерве", "в резерве", "info"),
             ("В ремонте", "в ремонте", "warning"), ("Списано", "списан", "danger")]
    cw = (CW - 3 * 16) / 4
    for i, (title, key, kind) in enumerate(cards):
        f.card(X0 + i * (cw + 16), 80, cw, 100, title, str(stats.get(key, 0)), kind, "по данным базы")
    f.panel(X0, 196, CW, 92, "Быстрые действия")
    x = X0 + 18
    for label, kind, target in [("＋ Поставить на учёт", "primary", "computer_form"),
                                ("Выдать компьютер", "secondary", "assign_form"),
                                ("Зарегистрировать обслуживание", "secondary", None),
                                ("Списать компьютер", "secondary", None)]:
        x += f.button(x, 246, label, kind, target=target) + 12
    half = (CW - 16) / 2
    f.panel(X0, 304, half, 470, "Гарантия истекает в ближайшие полгода")
    rows = q("SELECT inv_number, m.manufacturer || ' ' || m.name, warranty_end FROM computers c "
             "JOIN models m USING (id_model) WHERE status <> 'списан' AND warranty_end IS NOT NULL "
             "ORDER BY warranty_end DESC LIMIT 8")
    f.table(X0 + 16, 364, [("Инв. №", 100), ("Модель", 228), ("Гарантия до", half - 360)], rows)
    f.panel(X0 + half + 16, 304, half, 470, "Незавершённые обслуживания")
    rows = q("SELECT inv_number, work_type, start_date, COALESCE(e.surname, service_org) FROM services s "
             "LEFT JOIN employees e ON e.tab_number = s.executor_tab_number WHERE end_date IS NULL")
    f.table(X0 + half + 32, 364, [("Инв. №", 96), ("Вид", 100), ("С", 100), ("Исполнитель", half - 328)], rows)
    return f


COMPUTER_ROWS = """
SELECT c.inv_number, m.manufacturer || ' ' || m.name, m.device_type,
       b.name || ', ' || r.number, COALESCE(e.surname || ' ' || substr(e.name, 1, 1) || '.', '—'),
       c.commission_date, c.status
FROM computers c
JOIN models m USING (id_model)
JOIN rooms r USING (id_room)
JOIN buildings b USING (id_building)
LEFT JOIN assignments a ON a.inv_number = c.inv_number AND a.return_date IS NULL
LEFT JOIN employees e ON e.tab_number = a.tab_number
ORDER BY c.inv_number LIMIT 16
"""

COMPUTER_COLS = [("Инв. №", 96), ("Модель", 226), ("Тип", 116), ("Помещение", 176),
                 ("Сотрудник", 140), ("Ввод", 104), ("Состояние", 154)]


def computers_body(f, selected=None):
    f.field(X0, 84, 300, "Поиск", placeholder="инв. номер, сетевое имя, модель…")
    f.field(X0 + 316, 84, 170, "Состояние", "все", combo=True)
    f.field(X0 + 502, 84, 160, "Тип устройства", "все", combo=True)
    bx = W - 24
    for label, kind, target in reversed([("＋ Добавить", "primary", "computer_form"), ("Изменить", "secondary", None),
                                         ("Удалить", "secondary", "delete_confirm"), ("⟳", "secondary", None)]):
        bw = int(text_width(label, TYPE["body"]) + 32)
        bx -= bw
        f.button(bx, 92, label, kind, w=bw, target=target)
        bx -= 8
    f.table(X0, 146, COMPUTER_COLS, q(COMPUTER_ROWS), selected=selected, sort=0, status_col=6)
    f.text(X0, 168 + 34 + 30 * 16, "Показано 1–16 из 30 · сортировка по инв. номеру · двойной щелчок — карточка компьютера",
           size=TYPE["small"], color="muted")
    f.text(W - 24, 168 + 34 + 30 * 16, "‹  1  2  ›", size=TYPE["body"], color="primary", anchor="end", bold=True)


def computers(wire):
    f = base("computers", wire, "Учёт ПК / Компьютеры")
    computers_body(f, selected=11)
    return f


def computer_form(wire):
    f = base("computer_form", wire, "Учёт ПК / Компьютеры / Новый", active="computers")
    f.panel(X0, 80, 640, 560, "Карточка компьютера")
    x1, x2, y = X0 + 24, X0 + 336, 150
    f.field(x1, y, 280, "Инвентарный номер", "ПК-00031", required=True, focused=True)
    f.field(x2, y, 280, "Серийный номер", "LE-A8XP2TZZ", required=True,
            error="Компьютер с таким серийным номером уже есть")
    f.field(x1, y + 90, 592, "Модель", "Lenovo ThinkCentre M70q Gen 3 · настольный ПК", required=True, combo=True)
    f.field(x1, y + 170, 280, "Помещение", "Корпус Б, Б-01 (склад)", required=True, combo=True)
    f.field(x2, y + 170, 280, "Сетевое имя", placeholder="например, BUH-05")
    f.field(x1, y + 250, 280, "Дата ввода в эксплуатацию", "2026-11-09", required=True)
    f.field(x2, y + 250, 280, "Гарантия до", "2029-11-09")
    f.field(x1, y + 330, 280, "Состояние", "в резерве", combo=True)
    f.text(x1, y + 400, "* — обязательные поля", size=TYPE["small"], color="muted")
    f.button(X0 + 640 - 24 - 120, 586, "Сохранить", "primary", w=120, target="computers")
    f.button(X0 + 640 - 24 - 120 - 12 - 100, 586, "Отмена", "secondary", w=100, target="computers")
    f.panel(X0 + 660, 80, CW - 660, 300, "Подсказки")
    for i, s in enumerate(["Инвентарный номер — в формате ПК-NNNNN.",
                           "Новый компьютер ставится на учёт",
                           "в состоянии «в резерве» на складе.",
                           "Серийный номер и сетевое имя",
                           "должны быть уникальными.",
                           "Даты — в формате ГГГГ-ММ-ДД;",
                           "гарантия не раньше даты ввода."]):
        f.text(X0 + 678, 150 + i * 24, s, size=TYPE["small"] + 1)
    return f


def assign_form(wire):
    f = base("assign_form", wire, "Учёт ПК / Закрепления / Выдача", active="assignments")
    f.panel(X0, 80, 640, 470, "Выдача компьютера")
    x1, x2, y = X0 + 24, X0 + 336, 150
    f.field(x1, y, 592, "Компьютер (только в резерве)", "ПК-00004 · Lenovo ThinkCentre M70q Gen 3", required=True, combo=True)
    f.field(x1, y + 80, 592, "Сотрудник", "Петрова Анна Викторовна · Бухгалтерия", required=True, combo=True)
    f.field(x1, y + 160, 280, "Дата выдачи", "2026-11-09", required=True)
    f.field(x2, y + 160, 280, "Номер распоряжения", "Р-2026-040")
    f.field(x1, y + 240, 592, "Переместить в помещение", "Главный корпус, 101 (кабинет)", required=True, combo=True)
    f.button(X0 + 640 - 24 - 120, 496, "Выдать", "primary", w=120, target="dashboard")
    f.button(X0 + 640 - 24 - 120 - 12 - 100, 496, "Отмена", "secondary", w=100, target="dashboard")
    f.panel(X0 + 660, 80, CW - 660, 230, "Проверки перед выдачей")
    for i, s in enumerate(["✓ компьютер в состоянии «в резерве»",
                           "✓ сотрудник не уволен",
                           "✓ у компьютера нет действующего закрепления",
                           "✓ дата выдачи не раньше даты ввода"]):
        f.text(X0 + 678, 150 + i * 30, s, size=TYPE["body"], color="success")
    f.message(X0, 570, 640, "success", "Компьютер ПК-00004 выдан", "Закреплён за Петровой А. В., состояние — «в эксплуатации», помещение — Главный корпус, 101")
    return f


VAR18 = """SELECT m.device_type AS category,
       COUNT(*)      AS computers
FROM computers c
JOIN models m ON m.id_model = c.id_model
WHERE c.status <> 'списан'
GROUP BY m.device_type
HAVING COUNT(*) > 5
ORDER BY computers DESC;"""


def sql(wire):
    f = base("sql", wire, "Учёт ПК / SQL-запросы")
    f.panel(X0, 80, CW, 250)
    f.rect(X0 + 1, 81, 40, 248, "bg", None, rx=0)
    for i, line in enumerate(VAR18.splitlines()):
        f.text(X0 + 30, 108 + i * 20, str(i + 1), size=TYPE["mono"], color="muted", anchor="end", mono=True)
        f.text(X0 + 54, 108 + i * 20, line, size=TYPE["mono"] + 1, mono=True)
    f.button(X0, 346, "▶ Выполнить  Ctrl+Enter", "primary")
    f.button(X0 + 226, 346, "Очистить", "secondary")
    f.button(X0 + 334, 346, "История ▾", "ghost")
    f.text(W - 24, 368, "Готово: 2 строки за 3 мс", size=TYPE["small"] + 1, color="success", anchor="end", bold=True)
    rows = q(VAR18)
    f.table(X0, 400, [("category", 300), ("computers", 200)], rows)
    f.message(X0, 520, CW, "danger", "Пример ошибки: no such column: device",
              "Текст ошибки SQLite показывается здесь, таблица результатов не очищается")
    return f


QUERY_LIST = ["Все компьютеры", "Компьютеры по дате ввода", "Ноутбуки (IN с подзапросом)",
              "Сотрудники без e-mail или телефона", "Статистика обслуживаний", "Виды работ > 3 раз",
              "Компьютеры и сотрудники (JOIN)", "Неустановленные программы", "Состояние гарантии (CASE)",
              "Компьютеры и их категории (вар. 18)", "Категории, где больше N (вар. 18)"]


def queries(wire):
    f = base("queries", wire, "Учёт ПК / Готовые запросы")
    f.panel(X0, 80, 330, H - 104, "Запросы ЛР2")
    for i, name in enumerate(QUERY_LIST):
        y = 140 + i * 40
        if i == len(QUERY_LIST) - 1:
            f.rect(X0 + 10, y - 22, 310, 34, "selected", None, rx=6)
        f.text(X0 + 22, y, f"{i + 1:02d}  {name}", size=TYPE["body"], bold=i == len(QUERY_LIST) - 1)
    rx = X0 + 346
    rw = CW - 346
    f.panel(rx, 80, rw, 196, "Категории, где больше N компьютеров")
    f.text(rx + 18, 150, "Типы устройств, в которых больше N несписанных компьютеров.", size=TYPE["body"])
    f.text(rx + 18, 172, "Вариант 18, задание 2 · GROUP BY + HAVING", size=TYPE["small"] + 1, color="muted")
    f.field(rx + 18, 200, 120, "N", "5", required=True)
    f.button(rx + 156, 208, "▶ Выполнить", "primary")
    f.button(rx + 286, 208, "Показать SQL", "ghost", target="sql")
    f.table(rx, 300, [("category", 300), ("computers", 200)], q(VAR18))
    f.text(rx, 420, "2 строки · запрос выполнен над computers.db", size=TYPE["small"], color="muted")
    return f


def import_export(wire):
    f = base("import_export", wire, "Учёт ПК / Импорт и экспорт")
    f.panel(X0, 80, 560, 520, "Параметры операции")
    x = X0 + 24
    f.text(x, 150, "Операция", bold=True, size=TYPE["small"] + 1)
    f.radio(x, 176, "Экспорт из базы в файл", True)
    f.radio(x + 230, 176, "Импорт из файла в базу")
    f.text(x, 216, "Формат", bold=True, size=TYPE["small"] + 1)
    f.radio(x, 242, "CSV", True)
    f.radio(x + 100, 242, "JSON")
    f.field(x, 278, 512, "Таблица", "computers — компьютеры (30 строк)", required=True, combo=True)
    f.field(x, 352, 400, "Файл", "export/csv/computers.csv", required=True)
    f.button(x + 412, 360, "Обзор…", "secondary", w=100)
    f.field(x, 426, 160, "Разделитель", "запятая ( , )", combo=True)
    f.field(x + 176, 426, 160, "Кодировка", "UTF-8", combo=True)
    f.checkbox(x, 502, "Первая строка — заголовки столбцов", True)
    f.checkbox(x, 530, "Пропускать существующие записи (импорт)")
    f.button(X0 + 560 - 24 - 160, 548, "Начать экспорт", "primary", w=160)
    rx, rw = X0 + 576, CW - 576
    f.panel(rx, 80, rw, 520, "Ход выполнения")
    f.rect(rx + 18, 146, rw - 36, 12, "bg", "border", rx=6)
    f.rect(rx + 18, 146, rw - 36, 12, "success", None, rx=6)
    f.text(rx + 18, 180, "100 % · 30 из 30 строк", size=TYPE["small"] + 1, color="muted")
    f.message(rx + 18, 200, rw - 36, "success", "Экспорт завершён", "30 строк → export/csv/computers.csv")
    f.message(rx + 18, 274, rw - 36, "danger", "Импорт отменён, изменения откатаны",
              "UNIQUE constraint failed: programs.name, programs.version")
    f.text(rx + 18, 366, "Журнал", bold=True, size=TYPE["small"] + 1)
    for i, s in enumerate(["23:42:33  экспорт computers → CSV: 30 строк",
                           "23:41:10  импорт new_programs.csv → programs: +2",
                           "23:41:12  импорт bad_programs.csv: ошибка, откат"]):
        f.text(rx + 18, 392 + i * 22, s, size=TYPE["mono"], mono=True, color="muted")
    return f


def delete_confirm(wire):
    f = base("delete_confirm", wire, "Учёт ПК / Компьютеры", active="computers")
    computers_body(f, selected=11)
    f.hotspots.clear()
    f.modal(520, 230, "Удалить компьютер ПК-00012?",
            ["Будут удалены: 1 закрепление, 1 обслуживание, 6 установок ПО.",
             "3 комплектующих будут перенесены на склад.",
             "Отменить действие будет нельзя."],
            [("Отмена", "secondary", "computers"), ("Удалить", "danger", "computers")], kind="danger")
    return f


SCREENS = [dashboard, computers, computer_form, assign_form, sql, queries, import_export, delete_confirm]


def design_system():
    f = Frame("design_system")
    f.text(40, 50, "Дизайн-система «Учёт ПК»", size=TYPE["h1"] + 2, bold=True)
    f.text(40, 76, "Цвета, шрифты и компоненты, общие для всех экранов и для приложения на Tkinter (ЛР3, часть 2)",
           size=TYPE["body"], color="muted")
    f.text(40, 118, "Палитра", size=TYPE["h2"], bold=True)
    swatches = ["primary", "primary_dark", "primary_light", "bg", "surface", "border", "text", "muted", "sidebar",
                "success", "info", "warning", "danger", "selected"]
    for i, key in enumerate(swatches):
        x = 40 + (i % 7) * 170
        y = 136 + (i // 7) * 90
        f.rect(x, y, 150, 44, PALETTE[key], "border", rx=6)
        f.text(x, y + 62, key, size=TYPE["small"] + 1, bold=True)
        f.text(x, y + 78, PALETTE[key], size=TYPE["small"], color="muted")
    f.text(40, 348, "Типографика (Arial / Helvetica; моноширинный — Menlo / Consolas)", size=TYPE["h2"], bold=True)
    f.text(40, 384, "Заголовок экрана — 22 px, полужирный", size=TYPE["h1"], bold=True)
    f.text(40, 412, "Заголовок панели — 16 px, полужирный", size=TYPE["h2"], bold=True)
    f.text(40, 436, "Основной текст, значения в таблицах — 13 px", size=TYPE["body"])
    f.text(40, 458, "Подписи, подсказки, строка состояния — 11 px", size=TYPE["small"], color="muted")
    f.text(40, 480, "SELECT * FROM computers;  — код SQL, 12 px", size=TYPE["mono"], mono=True)
    f.text(640, 348, "Кнопки", size=TYPE["h2"], bold=True)
    x = 640
    for label, kind, dis in [("Основная", "primary", False), ("Вторичная", "secondary", False),
                             ("Опасная", "danger", False), ("Ссылка", "ghost", False), ("Недоступна", "primary", True)]:
        x += f.button(x, 366, label, kind, disabled=dis) + 10
    f.text(640, 436, "Статусы компьютера", size=TYPE["h2"], bold=True)
    x = 640
    for s, kind in [("в эксплуатации", "success"), ("в резерве", "info"), ("в ремонте", "warning"), ("списан", "danger")]:
        f.badge(x, 450, s, kind)
        x += text_width(s, TYPE["small"]) + 30
    f.text(40, 530, "Поля ввода", size=TYPE["h2"], bold=True)
    f.field(40, 556, 260, "Обычное", placeholder="подсказка")
    f.field(320, 556, 260, "В фокусе", "ПК-00031", focused=True)
    f.field(40, 636, 260, "Ошибка", "PC-1", required=True, error="Формат: ПК-NNNNN")
    f.field(320, 636, 260, "Выпадающий список", "в резерве", combo=True)
    f.checkbox(40, 744, "Флажок", True)
    f.radio(160, 744, "Переключатель", True)
    f.text(640, 530, "Таблица и сообщения", size=TYPE["h2"], bold=True)
    f.table(640, 546, [("Инв. №", 100), ("Модель", 220), ("Состояние", 200)],
            [("ПК-00002", "Dell OptiPlex 7090", "в эксплуатации"), ("ПК-00006", "HP ProDesk 400 G7", "в ремонте"),
             ("ПК-00026", "Lenovo ThinkCentre M70q", "в резерве")], selected=1, status_col=2)
    f.message(640, 696, 290, "success", "Успех", "операция выполнена")
    f.message(946, 696, 290, "danger", "Ошибка", "текст ошибки SQLite")
    return f


def prototype(names):
    links = {}
    images = {"wire": {}, "mock": {}}
    for fn in SCREENS:
        fr = fn(False)
        links[fr.title] = [list(h) for h in fr.hotspots]
        images["mock"][fr.title] = fr.svg()
        images["wire"][fr.title] = fn(True).svg()
    nav = "".join(f'<button data-s="{n}">{TITLES[n]}</button>' for n in names)
    return f"""<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Прототип «Учёт ПК»</title>
<style>
:root {{ --primary: {PALETTE['primary']}; --bg: {PALETTE['bg']}; --text: {PALETTE['text']}; }}
body {{ margin: 0; font-family: Arial, Helvetica, sans-serif; background: #2b3442; color: #fff; }}
header {{ display: flex; flex-wrap: wrap; gap: 6px; align-items: center; padding: 10px 16px; }}
header b {{ margin-right: 12px; }}
header button {{ border: 0; border-radius: 6px; padding: 6px 10px; background: #3b4657; color: #fff; cursor: pointer; }}
header button.on {{ background: var(--primary); }}
#mode {{ margin-left: auto; }}
main {{ display: flex; justify-content: center; padding: 0 16px 24px; }}
.stage {{ position: relative; width: min(100%, 1280px); aspect-ratio: 1280 / 800; }}
.stage img {{ width: 100%; height: 100%; display: block; border-radius: 6px; box-shadow: 0 8px 30px #0006; }}
.hot {{ position: absolute; cursor: pointer; border-radius: 6px; }}
.hint .hot {{ outline: 2px dashed #ffcf4d; background: #ffcf4d22; }}
</style></head>
<body>
<header><b>Прототип «Учёт ПК»</b>{nav}
<button id="hint">Показать кликабельные области</button><button id="mode">Режим: mockup</button></header>
<main><div class="stage" id="stage"><img id="img" alt=""></div></main>
<script>
const LINKS = {json.dumps(links, ensure_ascii=False)};
const IMAGES = {json.dumps(images, ensure_ascii=False)};
let screen = "dashboard", wire = false;
const stage = document.getElementById("stage"), img = document.getElementById("img");
function show(name) {{
  screen = name;
  img.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(IMAGES[wire ? "wire" : "mock"][name]);
  img.alt = name;
  stage.querySelectorAll(".hot").forEach(e => e.remove());
  for (const [x, y, w, h, target] of LINKS[name] || []) {{
    const a = document.createElement("div");
    a.className = "hot";
    a.title = "→ " + target;
    Object.assign(a.style, {{left: x / 12.8 + "%", top: y / 8 + "%", width: w / 12.8 + "%", height: h / 8 + "%"}});
    a.onclick = () => show(target);
    stage.appendChild(a);
  }}
  document.querySelectorAll("header button[data-s]").forEach(b => b.classList.toggle("on", b.dataset.s === name));
}}
document.querySelectorAll("header button[data-s]").forEach(b => b.onclick = () => show(b.dataset.s));
document.getElementById("hint").onclick = () => document.body.classList.toggle("hint");
document.getElementById("mode").onclick = e => {{ wire = !wire; e.target.textContent = "Режим: " + (wire ? "wireframe" : "mockup"); show(screen); }};
show(screen);
</script></body></html>
"""


def main():
    for folder, wire in (("wireframes", True), ("mockups", False)):
        out = HERE / folder
        out.mkdir(exist_ok=True)
        for i, fn in enumerate(SCREENS, 1):
            fr = fn(wire)
            (out / f"{fr.title}.svg").write_text(fr.svg(), encoding="utf-8")
    (HERE / "design_system.svg").write_text(design_system().svg(), encoding="utf-8")
    (HERE / "prototype").mkdir(exist_ok=True)
    names = [fn(False).title for fn in SCREENS]
    (HERE / "prototype" / "index.html").write_text(prototype(names), encoding="utf-8")
    print("экранов:", len(SCREENS), "→ wireframes/, mockups/, design_system.svg, prototype/index.html")


if __name__ == "__main__":
    main()

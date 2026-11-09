"""Генерирует инфологическую модель в нотации Чена: ../img/er_chen.svg.

Запуск: python3 er_chen.py
Позиции подобраны вручную; чтобы сдвинуть элемент, правьте координаты ниже.
"""
import math
from pathlib import Path

W, H = 3150, 1960
FONT = "Arial, Helvetica, sans-serif"
BOLD = 'font-weight="bold" font-family="Arial-BoldMT, Arial, Helvetica, sans-serif"'

# Сущности: имя -> (x, y, ассоциативная?)
ENTITIES = {
    "ОТДЕЛ": (230, 330, False),
    "СОТРУДНИК": (820, 330, False),
    "ЗАКРЕПЛЕНИЕ": (1470, 330, True),
    "ОБСЛУЖИВАНИЕ": (820, 1010, False),
    "КОМПЬЮТЕР": (1470, 1010, False),
    "УСТАНОВКА_ПО": (2130, 1010, True),
    "ПРОГРАММА": (2740, 1010, False),
    "МОДЕЛЬ": (820, 1660, False),
    "ПОМЕЩЕНИЕ": (1470, 1660, False),
    "КОМПЛЕКТУЮЩЕЕ": (2130, 1660, False),
}

# Связи-ромбы: (имя, тип, сущность A, карт. A, обяз. A, сущность B, карт. B, обяз. B)
# Тип пишется в порядке A:B, где A — левая или верхняя сущность на схеме.
# Кардинальность пишется у сущности: «М» у той, чьих экземпляров много.
RELATIONS = [
    ("РАБОТАЕТ_В", "1:М", "ОТДЕЛ", "1", False, "СОТРУДНИК", "М", True),
    ("ВЫПОЛНЯЕТ", "1:М", "СОТРУДНИК", "1", False, "ОБСЛУЖИВАНИЕ", "М", False),
    ("ПРОВОДИТСЯ_ДЛЯ", "М:1", "ОБСЛУЖИВАНИЕ", "М", True, "КОМПЬЮТЕР", "1", False),
    ("ИМЕЕТ_МОДЕЛЬ", "М:1", "КОМПЬЮТЕР", "М", True, "МОДЕЛЬ", "1", False),
    ("НАХОДИТСЯ_В", "М:1", "КОМПЬЮТЕР", "М", True, "ПОМЕЩЕНИЕ", "1", False),
    ("СОДЕРЖИТ", "1:М", "КОМПЬЮТЕР", "1", False, "КОМПЛЕКТУЮЩЕЕ", "М", False),
]

# Метки кардинальности, которые нужно поставить по другую сторону линии: (связь, сущность)
LABEL_FLIP = {("ИМЕЕТ_МОДЕЛЬ", "КОМПЬЮТЕР")}

# Ассоциативные сущности — связи М:М с собственными атрибутами:
# имя -> (тип, смещение подписи типа (dx, dy), [(сущность, карт., обяз.), ...])
ASSOC_LINKS = {
    "ЗАКРЕПЛЕНИЕ": ("М:М", (-75, 62), [("СОТРУДНИК", "М", False), ("КОМПЬЮТЕР", "М", False)]),
    "УСТАНОВКА_ПО": ("М:М", (0, -48), [("КОМПЬЮТЕР", "М", False), ("ПРОГРАММА", "М", False)]),
}



def P(angle, r):
    """Смещение атрибута в полярных координатах (угол в градусах, против часовой от оси X)."""
    a = math.radians(angle)
    return round(r * math.cos(a)), round(-r * math.sin(a))


# Атрибуты: сущность -> [(имя, dx, dy, идентификатор?)]
ATTRS = {
    "ОТДЕЛ": [
        ("код_отдела", -20, -130, True),
        ("название", -20, 130, False),
    ],
    "СОТРУДНИК": [
        ("табельный_номер", -300, -130, True),
        ("фамилия", -170, -220, False),
        ("имя", 0, -250, False),
        ("отчество", 170, -220, False),
        ("должность", 300, -130, False),
        ("телефон", -260, 130, False),
        ("эл_почта", -290, 230, False),
        ("дата_увольнения", 250, 160, False),
    ],
    "ЗАКРЕПЛЕНИЕ": [
        ("номер_закрепления", 0, -170, True),
        ("дата_выдачи", 290, -110, False),
        ("дата_возврата", 330, 0, False),
        ("номер_документа", 290, 115, False),
    ],
    "ОБСЛУЖИВАНИЕ": [
        ("номер_обслуживания", *P(125, 330), True),
        ("вид_работ", *P(145, 440), False),
        ("дата_начала", *P(163, 340), False),
        ("сервисная_организация", *P(182, 450), False),
        ("дата_окончания", *P(200, 340), False),
        ("стоимость", *P(220, 450), False),
        ("выполненные_работы", *P(243, 360), False),
        ("описание_неисправности", *P(268, 400), False),
    ],
    "КОМПЬЮТЕР": [
        ("инвентарный_номер", *P(160, 300), True),
        ("серийный_номер", *P(140, 300), False),
        ("сетевое_имя", *P(120, 330), False),
        ("дата_ввода", *P(63, 500), False),
        ("дата_окончания_гарантии", *P(45, 520), False),
        ("состояние", *P(30, 540), False),
        ("дата_списания", *P(17, 560), False),
    ],
    "УСТАНОВКА_ПО": [
        ("дата_установки", 0, 140, False),
    ],
    "ПРОГРАММА": [
        ("код_программы", -90, -190, True),
        ("наименование", 150, -150, False),
        ("версия", 250, -50, False),
        ("разработчик", 250, 60, False),
        ("тип_лицензии", 150, 160, False),
        ("количество_лицензий", -90, 200, False),
    ],
    "МОДЕЛЬ": [
        ("код_модели", -330, -70, True),
        ("производитель", -340, 50, False),
        ("наименование", -200, 150, False),
        ("тип_устройства", 70, 160, False),
    ],
    "ПОМЕЩЕНИЕ": [
        ("код_помещения", -250, 80, True),
        ("здание", -170, 180, False),
        ("номер", 0, 220, False),
        ("этаж", 170, 180, False),
        ("тип_помещения", 230, 80, False),
    ],
    "КОМПЛЕКТУЮЩЕЕ": [
        ("код_комплектующего", 380, -170, True),
        ("тип_комплектующего", 430, -60, False),
        ("производитель", 430, 50, False),
        ("модель", 380, 160, False),
        ("серийный_номер", 190, 230, False),
        ("значение_параметра", -60, 230, False),
        ("единица_измерения", -310, 200, False),
    ],
}

ENT_H = 60
ATTR_H = 46
REL_W, REL_H = 210, 90


def text_w(s, size):
    return len(s) * size * 0.6


def ent_w(name):
    # у ассоциативной сущности внутри ромб — нужен запас по ширине
    extra = 110 if ENTITIES[name][2] else 40
    return max(190, text_w(name, 18) + extra)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;")


def clip_rect(cx, cy, w, h, tx, ty):
    """Точка на границе прямоугольника (cx, cy, w, h) по направлению к (tx, ty)."""
    dx, dy = tx - cx, ty - cy
    if dx == 0 and dy == 0:
        return cx, cy
    sx = (w / 2) / abs(dx) if dx else float("inf")
    sy = (h / 2) / abs(dy) if dy else float("inf")
    s = min(sx, sy)
    return cx + dx * s, cy + dy * s


def clip_diamond(cx, cy, w, h, tx, ty):
    dx, dy = tx - cx, ty - cy
    s = 1 / (abs(dx) / (w / 2) + abs(dy) / (h / 2))
    return cx + dx * s, cy + dy * s


def clip_ellipse(cx, cy, rx, ry, tx, ty):
    dx, dy = tx - cx, ty - cy
    s = 1 / ((dx / rx) ** 2 + (dy / ry) ** 2) ** 0.5
    return cx + dx * s, cy + dy * s


def arrow_head(x, y, ux, uy, double=False):
    """Наконечник с вершиной в (x, y) по направлению (ux, uy); двойной — для стороны «М»."""
    L, Wd = 18, 7
    heads = []
    for back in ((0, 14) if double else (0,)):
        tx, ty = x - ux * back, y - uy * back
        bx, by = tx - ux * L, ty - uy * L
        heads.append(
            f'<polygon points="{tx:.1f},{ty:.1f} {bx - uy * Wd:.1f},{by + ux * Wd:.1f} {bx + uy * Wd:.1f},{by - ux * Wd:.1f}" fill="#000"/>'
        )
    return "".join(heads)


def line(x1, y1, x2, y2, double=False):
    if not double:
        return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#000" stroke-width="1.6"/>'
    # двойная линия — обязательное участие
    dx, dy = x2 - x1, y2 - y1
    ln = (dx * dx + dy * dy) ** 0.5
    nx, ny = -dy / ln * 3.2, dx / ln * 3.2
    return "".join(
        f'<line x1="{x1 + k * nx:.1f}" y1="{y1 + k * ny:.1f}" x2="{x2 + k * nx:.1f}" y2="{y2 + k * ny:.1f}" stroke="#000" stroke-width="1.4"/>'
        for k in (-1, 1)
    )


def main():
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">',
        f'<rect width="{W}" height="{H}" fill="#fff"/>',
    ]
    lines, shapes = [], []

    # атрибуты
    for ent, attrs in ATTRS.items():
        ex, ey, _ = ENTITIES[ent]
        ew = ent_w(ent)
        for name, dx, dy, key in attrs:
            ax, ay = ex + dx, ey + dy
            rx = text_w(name, 15) / 2 + 18
            ry = ATTR_H / 2
            p1 = clip_rect(ex, ey, ew, ENT_H, ax, ay)
            p2 = clip_ellipse(ax, ay, rx, ry, ex, ey)
            lines.append(line(*p1, *p2))
            shapes.append(
                f'<ellipse cx="{ax}" cy="{ay}" rx="{rx:.1f}" ry="{ry}" fill="#fff" stroke="#000" stroke-width="1.4"/>'
            )
            deco = ' text-decoration="underline"' if key else ""
            weight = ' font-weight="bold" font-family="Arial-BoldMT, Arial, Helvetica, sans-serif"' if key else ""
            shapes.append(
                f'<text x="{ax}" y="{ay + 5}" font-size="15" text-anchor="middle"{deco}{weight}>{esc(name)}</text>'
            )
            if key:  # подчёркивание рисуем явно: не все рендеры поддерживают text-decoration
                tw = text_w(name, 15) * 0.97
                shapes.append(
                    f'<line x1="{ax - tw / 2:.1f}" y1="{ay + 8}" x2="{ax + tw / 2:.1f}" y2="{ay + 8}" stroke="#000" stroke-width="1.2"/>'
                )

    def link(start, ename, card, mand, flip=False):
        """Линия от связи к сущности со стрелкой и меткой кардинальности у сущности."""
        ex, ey, _ = ENTITIES[ename]
        tip = clip_rect(ex, ey, ent_w(ename), ENT_H, *start)
        lines.append(line(*start, *tip, double=mand))
        dx, dy = tip[0] - start[0], tip[1] - start[1]
        ln = (dx * dx + dy * dy) ** 0.5
        ux, uy = dx / ln, dy / ln
        shapes.append(arrow_head(*tip, ux, uy, double=(card == "М")))
        # метка: отступаем от сущности назад вдоль линии и в сторону
        side = -1 if flip else 1
        lx = tip[0] - ux * 50 - uy * 20 * side
        ly = tip[1] - uy * 50 + ux * 20 * side
        shapes.append(f'<text x="{lx:.1f}" y="{ly + 8:.1f}" font-size="22" {BOLD} text-anchor="middle">{card}</text>')

    # связи-ромбы
    for name, kind, a, ca, ma, b, cb, mb in RELATIONS:
        ax, ay, _ = ENTITIES[a]
        bx, by, _ = ENTITIES[b]
        rx, ry = (ax + bx) / 2, (ay + by) / 2
        rw = max(REL_W, text_w(name, 14) + 70)
        for ename, card, mand in ((a, ca, ma), (b, cb, mb)):
            ex, ey, _ = ENTITIES[ename]
            link(clip_diamond(rx, ry, rw, REL_H, ex, ey), ename, card, mand, (name, ename) in LABEL_FLIP)
        pts = f"{rx},{ry - REL_H / 2} {rx + rw / 2},{ry} {rx},{ry + REL_H / 2} {rx - rw / 2},{ry}"
        shapes.append(f'<polygon points="{pts}" fill="#fff" stroke="#000" stroke-width="1.6"/>')
        shapes.append(f'<text x="{rx}" y="{ry - 3}" font-size="14" text-anchor="middle" {BOLD}>{esc(name)}</text>')
        shapes.append(f'<text x="{rx}" y="{ry + 20}" font-size="17" text-anchor="middle" {BOLD}>{kind}</text>')

    # ассоциативные сущности: стрелки к связываемым сущностям
    for name, (kind, (tdx, tdy), targets) in ASSOC_LINKS.items():
        x, y, _ = ENTITIES[name]
        for ename, card, mand in targets:
            ex, ey, _ = ENTITIES[ename]
            link(clip_rect(x, y, ent_w(name), ENT_H, ex, ey), ename, card, mand)
        shapes.append(f'<text x="{x + tdx}" y="{y + tdy}" font-size="17" text-anchor="middle" {BOLD}>{kind}</text>')

    # сущности
    for name, (x, y, assoc) in ENTITIES.items():
        w = ent_w(name)
        shapes.append(
            f'<rect x="{x - w / 2:.1f}" y="{y - ENT_H / 2}" width="{w:.1f}" height="{ENT_H}" fill="#fff" stroke="#000" stroke-width="2.2"/>'
        )
        if assoc:
            pts = f"{x},{y - ENT_H / 2 + 4} {x + w / 2 - 6},{y} {x},{y + ENT_H / 2 - 4} {x - w / 2 + 6},{y}"
            shapes.append(f'<polygon points="{pts}" fill="none" stroke="#000" stroke-width="1.2"/>')
        shapes.append(
            f'<text x="{x}" y="{y + 6}" font-size="18" font-weight="bold" font-family="Arial-BoldMT, Arial, Helvetica, sans-serif" text-anchor="middle">{esc(name)}</text>'
        )

    # легенда
    lx, ly = 2330, 50
    legend = [
        f'<rect x="{lx}" y="{ly}" width="740" height="500" fill="#fff" stroke="#000" stroke-width="1.2"/>',
        f'<text x="{lx + 20}" y="{ly + 34}" font-size="18" {BOLD}>Обозначения</text>',
        f'<rect x="{lx + 20}" y="{ly + 55}" width="110" height="36" fill="#fff" stroke="#000" stroke-width="2"/>',
        f'<text x="{lx + 150}" y="{ly + 79}" font-size="15">сущность</text>',
        f'<rect x="{lx + 20}" y="{ly + 105}" width="110" height="36" fill="#fff" stroke="#000" stroke-width="2"/>',
        f'<polygon points="{lx + 75},{ly + 108} {lx + 126},{ly + 123} {lx + 75},{ly + 138} {lx + 24},{ly + 123}" fill="none" stroke="#000"/>',
        f'<text x="{lx + 150}" y="{ly + 129}" font-size="15">ассоциативная сущность (связь М:М с атрибутами)</text>',
        f'<polygon points="{lx + 75},{ly + 152} {lx + 130},{ly + 177} {lx + 75},{ly + 202} {lx + 20},{ly + 177}" fill="#fff" stroke="#000"/>',
        f'<text x="{lx + 75}" y="{ly + 183}" font-size="13" text-anchor="middle" {BOLD}>1:М</text>',
        f'<text x="{lx + 150}" y="{ly + 183}" font-size="15">связь; под именем — тип связи (1:М, М:1, М:М)</text>',
        f'<ellipse cx="{lx + 75}" cy="{ly + 232}" rx="55" ry="18" fill="#fff" stroke="#000"/>',
        f'<text x="{lx + 75}" y="{ly + 237}" font-size="14" text-anchor="middle" {BOLD}>id</text>',
        f'<line x1="{lx + 66}" y1="{ly + 240}" x2="{lx + 84}" y2="{ly + 240}" stroke="#000"/>',
        f'<text x="{lx + 150}" y="{ly + 238}" font-size="15">атрибут (подчёркнут — идентификатор)</text>',
        line(lx + 20, ly + 285, lx + 130, ly + 285),
        arrow_head(lx + 130, ly + 285, 1, 0),
        f'<text x="{lx + 105}" y="{ly + 275}" font-size="17" {BOLD}>1</text>',
        f'<text x="{lx + 150}" y="{ly + 291}" font-size="15">стрелка к сущности со стороны «один»</text>',
        line(lx + 20, ly + 335, lx + 130, ly + 335),
        arrow_head(lx + 130, ly + 335, 1, 0, double=True),
        f'<text x="{lx + 90}" y="{ly + 325}" font-size="17" {BOLD}>М</text>',
        f'<text x="{lx + 150}" y="{ly + 341}" font-size="15">двойная стрелка к сущности со стороны «много»</text>',
        line(lx + 20, ly + 385, lx + 130, ly + 385, double=True),
        f'<text x="{lx + 150}" y="{ly + 391}" font-size="15">двойная линия — обязательное участие сущности</text>',
        line(lx + 20, ly + 435, lx + 130, ly + 435),
        f'<text x="{lx + 150}" y="{ly + 441}" font-size="15">одинарная линия — необязательное участие</text>',
        f'<text x="{lx + 20}" y="{ly + 482}" font-size="14">Идентификатор УСТАНОВКИ_ПО составной: (инвентарный_номер, код_программы)</text>',
    ]

    out += lines + shapes + legend + ["</svg>"]
    dst = Path(__file__).resolve().parent.parent / "img" / "er_chen.svg"
    dst.write_text("\n".join(out), encoding="utf-8")
    print(dst)


if __name__ == "__main__":
    main()

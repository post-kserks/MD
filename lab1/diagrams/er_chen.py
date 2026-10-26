"""Генерирует инфологическую модель в нотации Чена: ../img/er_chen.svg.

Запуск: python3 er_chen.py
Позиции подобраны вручную; чтобы сдвинуть элемент, правьте координаты ниже.
"""
import math
from pathlib import Path

W, H = 3150, 1960
FONT = "Arial, Helvetica, sans-serif"

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

# Связи: (имя, сущность A, карт. A, обяз. A, сущность B, карт. B, обяз. B)
# Кардинальность пишется у сущности: «М» у той, чьих экземпляров много.
RELATIONS = [
    ("РАБОТАЕТ_В", "СОТРУДНИК", "М", True, "ОТДЕЛ", "1", False),
    ("ПОЛУЧАЕТ", "СОТРУДНИК", "1", False, "ЗАКРЕПЛЕНИЕ", "М", True),
    ("КАСАЕТСЯ", "ЗАКРЕПЛЕНИЕ", "М", True, "КОМПЬЮТЕР", "1", False),
    ("ВЫПОЛНЯЕТ", "СОТРУДНИК", "1", False, "ОБСЛУЖИВАНИЕ", "М", False),
    ("ПРОВОДИТСЯ_ДЛЯ", "ОБСЛУЖИВАНИЕ", "М", True, "КОМПЬЮТЕР", "1", False),
    ("ВЫПОЛНЕНА_НА", "УСТАНОВКА_ПО", "М", True, "КОМПЬЮТЕР", "1", False),
    ("ФИКСИРУЕТ", "УСТАНОВКА_ПО", "М", True, "ПРОГРАММА", "1", False),
    ("ИМЕЕТ_МОДЕЛЬ", "КОМПЬЮТЕР", "М", True, "МОДЕЛЬ", "1", False),
    ("НАХОДИТСЯ_В", "КОМПЬЮТЕР", "М", True, "ПОМЕЩЕНИЕ", "1", False),
    ("СОДЕРЖИТ", "КОМПЬЮТЕР", "1", False, "КОМПЛЕКТУЮЩЕЕ", "М", False),
]



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

    # связи
    for name, a, ca, ma, b, cb, mb in RELATIONS:
        ax, ay, _ = ENTITIES[a]
        bx, by, _ = ENTITIES[b]
        rx, ry = (ax + bx) / 2, (ay + by) / 2
        rw = max(REL_W, text_w(name, 14) + 70)
        for ex, ey, ename, card, mand in ((ax, ay, a, ca, ma), (bx, by, b, cb, mb)):
            p1 = clip_rect(ex, ey, ent_w(ename), ENT_H, rx, ry)
            p2 = clip_diamond(rx, ry, rw, REL_H, ex, ey)
            lines.append(line(*p1, *p2, double=mand))
            # метка кардинальности: чуть в стороне от линии у сущности
            dx, dy = p2[0] - p1[0], p2[1] - p1[1]
            ln = (dx * dx + dy * dy) ** 0.5
            ux, uy = dx / ln, dy / ln
            lx = p1[0] + ux * 26 - uy * 16
            ly = p1[1] + uy * 26 + ux * 16
            shapes.append(
                f'<text x="{lx:.1f}" y="{ly + 7:.1f}" font-size="20" font-weight="bold" font-family="Arial-BoldMT, Arial, Helvetica, sans-serif" text-anchor="middle">{card}</text>'
            )
        pts = f"{rx},{ry - REL_H / 2} {rx + rw / 2},{ry} {rx},{ry + REL_H / 2} {rx - rw / 2},{ry}"
        shapes.append(f'<polygon points="{pts}" fill="#fff" stroke="#000" stroke-width="1.6"/>')
        shapes.append(
            f'<text x="{rx}" y="{ry + 5}" font-size="14" text-anchor="middle" font-weight="bold" font-family="Arial-BoldMT, Arial, Helvetica, sans-serif">{esc(name)}</text>'
        )

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
    lx, ly = 2330, 60
    legend = [
        f'<rect x="{lx}" y="{ly}" width="720" height="350" fill="#fff" stroke="#000" stroke-width="1.2"/>',
        f'<text x="{lx + 20}" y="{ly + 34}" font-size="18" font-weight="bold" font-family="Arial-BoldMT, Arial, Helvetica, sans-serif">Обозначения</text>',
        f'<rect x="{lx + 20}" y="{ly + 55}" width="110" height="36" fill="#fff" stroke="#000" stroke-width="2"/>',
        f'<text x="{lx + 150}" y="{ly + 79}" font-size="15">сущность</text>',
        f'<rect x="{lx + 20}" y="{ly + 105}" width="110" height="36" fill="#fff" stroke="#000" stroke-width="2"/>',
        f'<polygon points="{lx + 75},{ly + 108} {lx + 126},{ly + 123} {lx + 75},{ly + 138} {lx + 24},{ly + 123}" fill="none" stroke="#000"/>',
        f'<text x="{lx + 150}" y="{ly + 129}" font-size="15">ассоциативная сущность (связь М:М)</text>',
        f'<polygon points="{lx + 75},{ly + 155} {lx + 130},{ly + 175} {lx + 75},{ly + 195} {lx + 20},{ly + 175}" fill="#fff" stroke="#000"/>',
        f'<text x="{lx + 150}" y="{ly + 181}" font-size="15">связь</text>',
        f'<ellipse cx="{lx + 75}" cy="{ly + 225}" rx="55" ry="18" fill="#fff" stroke="#000"/>',
        f'<text x="{lx + 75}" y="{ly + 230}" font-size="14" text-anchor="middle" font-weight="bold" font-family="Arial-BoldMT, Arial, Helvetica, sans-serif">id</text>',
        f'<line x1="{lx + 66}" y1="{ly + 233}" x2="{lx + 84}" y2="{ly + 233}" stroke="#000"/>',
        f'<text x="{lx + 150}" y="{ly + 231}" font-size="15">атрибут (подчёркнут — идентификатор)</text>',
        line(lx + 20, ly + 270, lx + 130, ly + 270, double=True),
        f'<text x="{lx + 150}" y="{ly + 276}" font-size="15">обязательное участие сущности в связи</text>',
        line(lx + 20, ly + 310, lx + 130, ly + 310),
        f'<text x="{lx + 150}" y="{ly + 316}" font-size="15">необязательное участие; 1 / М — кардинальность</text>',
    ]

    out += lines + shapes + legend + ["</svg>"]
    dst = Path(__file__).resolve().parent.parent / "img" / "er_chen.svg"
    dst.write_text("\n".join(out), encoding="utf-8")
    print(dst)


if __name__ == "__main__":
    main()

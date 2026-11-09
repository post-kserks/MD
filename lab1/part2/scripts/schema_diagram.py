import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "db" / "computers.db"
OUT = ROOT / "img" / "schema.svg"

W, H = 2140, 1130
BOX_W, HEAD, ROW = 330, 36, 23
FONT = "Arial, Helvetica, sans-serif"
BOLD = 'font-weight="bold" font-family="Arial-BoldMT, Arial, Helvetica, sans-serif"'

POS = {
    "departments": (40, 40),
    "employees": (470, 40),
    "assignments": (900, 40),
    "services": (470, 450),
    "computers": (900, 450),
    "software_installs": (1330, 450),
    "programs": (1760, 450),
    "models": (470, 880),
    "rooms": (900, 880),
    "components": (1330, 880),
}

TITLES = {
    "departments": "ОТДЕЛ", "employees": "СОТРУДНИК", "assignments": "ЗАКРЕПЛЕНИЕ",
    "services": "ОБСЛУЖИВАНИЕ", "computers": "КОМПЬЮТЕР", "software_installs": "УСТАНОВКА_ПО",
    "programs": "ПРОГРАММА", "models": "МОДЕЛЬ", "rooms": "ПОМЕЩЕНИЕ", "components": "КОМПЛЕКТУЮЩЕЕ",
}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;")


def box_rect(table, ncols):
    x, y = POS[table]
    return x, y, BOX_W, HEAD + ROW * ncols


def clip(rect, tx, ty):
    x, y, w, h = rect
    cx, cy = x + w / 2, y + h / 2
    dx, dy = tx - cx, ty - cy
    sx = (w / 2) / abs(dx) if dx else float("inf")
    sy = (h / 2) / abs(dy) if dy else float("inf")
    s = min(sx, sy)
    return cx + dx * s, cy + dy * s


def main():
    con = sqlite3.connect(DB)
    info, fks = {}, []
    for t in POS:
        cols = con.execute(f"PRAGMA table_info({t})").fetchall()
        fk_cols = {r[3] for r in con.execute(f"PRAGMA foreign_key_list({t})")}
        uniq = set()
        for idx in con.execute(f"PRAGMA index_list({t})"):
            if idx[2] and idx[3] == "u" and not idx[4]:
                names = [r[2] for r in con.execute(f"PRAGMA index_info({idx[1]})")]
                if len(names) == 1:
                    uniq.add(names[0])
        info[t] = [(c[1], c[2], c[3], c[5], c[1] in fk_cols, c[1] in uniq) for c in cols]
        for r in con.execute(f"PRAGMA foreign_key_list({t})"):
            fks.append((t, r[2], r[3], r[5], r[6]))
    con.close()

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">',
           f'<rect width="{W}" height="{H}" fill="#fff"/>']
    rects = {t: box_rect(t, len(info[t])) for t in POS}

    for child, parent, col, on_upd, on_del in fks:
        c, p = rects[child], rects[parent]
        pc = (p[0] + p[2] / 2, p[1] + p[3] / 2)
        cc = (c[0] + c[2] / 2, c[1] + c[3] / 2)
        a = clip(c, *pc)
        b = clip(p, *cc)
        out.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="#333" stroke-width="1.6"/>')
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = (dx * dx + dy * dy) ** 0.5
        ux, uy = dx / ln, dy / ln
        nx, ny = -uy, ux
        base = (a[0] + ux * 16, a[1] + uy * 16)
        for k in (-1, 0, 1):
            out.append(f'<line x1="{base[0]:.1f}" y1="{base[1]:.1f}" x2="{a[0] + nx * 9 * k:.1f}" '
                       f'y2="{a[1] + ny * 9 * k:.1f}" stroke="#333" stroke-width="1.6"/>')
        bar = (b[0] - ux * 12, b[1] - uy * 12)
        out.append(f'<line x1="{bar[0] + nx * 9:.1f}" y1="{bar[1] + ny * 9:.1f}" x2="{bar[0] - nx * 9:.1f}" '
                   f'y2="{bar[1] - ny * 9:.1f}" stroke="#333" stroke-width="1.6"/>')
        mx, my = (a[0] + b[0]) / 2 + nx * 14, (a[1] + b[1]) / 2 + ny * 14
        rule = on_del
        out.append(f'<text x="{mx:.1f}" y="{my + 4:.1f}" font-size="12" text-anchor="middle" fill="#444">{esc(rule)}</text>')

    for t, cols in info.items():
        x, y, w, h = rects[t]
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#fff" stroke="#000" stroke-width="1.6"/>')
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{HEAD}" fill="#e8eef7" stroke="#000" stroke-width="1.6"/>')
        out.append(f'<text x="{x + 12}" y="{y + 24}" font-size="16" {BOLD}>{t}</text>')
        out.append(f'<text x="{x + w - 12}" y="{y + 24}" font-size="12" text-anchor="end" fill="#555">{TITLES[t]}</text>')
        for i, (name, ctype, notnull, pk, fk, un) in enumerate(cols):
            ry = y + HEAD + ROW * i + 16
            tags = []
            if pk:
                tags.append("PK")
            if fk:
                tags.append("FK")
            if un:
                tags.append("U")
            if notnull and not pk:
                tags.append("NN")
            weight = f" {BOLD}" if pk else ""
            out.append(f'<text x="{x + 12}" y="{ry}" font-size="14"{weight}>{esc(name)}</text>')
            out.append(f'<text x="{x + 200}" y="{ry}" font-size="13" fill="#555">{ctype}</text>')
            out.append(f'<text x="{x + w - 10}" y="{ry}" font-size="12" text-anchor="end" fill="#1a4f9c">{" ".join(tags)}</text>')

    lx, ly = 1760, 40
    out += [
        f'<rect x="{lx}" y="{ly}" width="330" height="190" fill="#fff" stroke="#000"/>',
        f'<text x="{lx + 14}" y="{ly + 28}" font-size="15" {BOLD}>Обозначения</text>',
        f'<text x="{lx + 14}" y="{ly + 54}" font-size="13">PK — первичный ключ, FK — внешний ключ</text>',
        f'<text x="{lx + 14}" y="{ly + 76}" font-size="13">U — уникальный, NN — NOT NULL</text>',
        f'<line x1="{lx + 14}" y1="{ly + 110}" x2="{lx + 110}" y2="{ly + 110}" stroke="#333" stroke-width="1.6"/>',
        f'<line x1="{lx + 30}" y1="{ly + 110}" x2="{lx + 14}" y2="{ly + 101}" stroke="#333" stroke-width="1.6"/>',
        f'<line x1="{lx + 30}" y1="{ly + 110}" x2="{lx + 14}" y2="{ly + 119}" stroke="#333" stroke-width="1.6"/>',
        f'<line x1="{lx + 98}" y1="{ly + 101}" x2="{lx + 98}" y2="{ly + 119}" stroke="#333" stroke-width="1.6"/>',
        f'<text x="{lx + 122}" y="{ly + 115}" font-size="13">«много» — «один»</text>',
        f'<text x="{lx + 14}" y="{ly + 146}" font-size="13">на линии — действие ON DELETE</text>',
        f'<text x="{lx + 14}" y="{ly + 166}" font-size="13">(у всех FK — ON UPDATE CASCADE)</text>',
    ]
    out.append("</svg>")
    OUT.write_text("\n".join(out), encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()

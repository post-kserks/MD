from xml.sax.saxutils import escape

FONT = "Arial, Helvetica, sans-serif"
MONO = "Menlo, Consolas, monospace"

PALETTE = {
    "primary": "#2F5D9E",
    "primary_dark": "#234A80",
    "primary_light": "#E8EEF7",
    "bg": "#F5F7FA",
    "surface": "#FFFFFF",
    "border": "#D5DBE3",
    "text": "#1F2933",
    "muted": "#6B7785",
    "sidebar": "#1F2A3A",
    "sidebar_text": "#C9D3E0",
    "success": "#2E7D4F",
    "success_bg": "#E3F2E8",
    "warning": "#B7791F",
    "warning_bg": "#FBF0DC",
    "info": "#3D6FB6",
    "info_bg": "#E4EDF9",
    "danger": "#C0392B",
    "danger_bg": "#FBE5E2",
    "row_alt": "#F9FAFC",
    "selected": "#DCE7F7",
    "overlay": "#1F2933",
}

WIRE = {
    "primary": "#7A7A7A",
    "primary_dark": "#5A5A5A",
    "primary_light": "#EEEEEE",
    "bg": "#FFFFFF",
    "surface": "#FFFFFF",
    "border": "#9A9A9A",
    "text": "#333333",
    "muted": "#8A8A8A",
    "sidebar": "#E6E6E6",
    "sidebar_text": "#444444",
    "success": "#555555",
    "success_bg": "#FFFFFF",
    "warning": "#555555",
    "warning_bg": "#FFFFFF",
    "info": "#555555",
    "info_bg": "#FFFFFF",
    "danger": "#555555",
    "danger_bg": "#FFFFFF",
    "row_alt": "#FFFFFF",
    "selected": "#E6E6E6",
    "overlay": "#000000",
}

STATUS_KIND = {
    "в эксплуатации": "success",
    "в резерве": "info",
    "в ремонте": "warning",
    "списан": "danger",
}

TYPE = {"h1": 22, "h2": 16, "body": 13, "small": 11, "mono": 12}

W, H = 1280, 800
SIDEBAR_W = 220
TOPBAR_H = 56


def text_width(s, size):
    return len(s) * size * 0.56


class Frame:
    def __init__(self, title, wire=False):
        self.title = title
        self.wire = wire
        self.c = WIRE if wire else PALETTE
        self.items = []
        self.hotspots = []

    def color(self, key):
        return self.c[key]

    def rect(self, x, y, w, h, fill="surface", stroke=None, rx=4, sw=1, opacity=None, dash=False):
        f = self.c.get(fill, fill)
        s = self.c.get(stroke, stroke) if stroke else "none"
        extra = f' fill-opacity="{opacity}"' if opacity is not None else ""
        extra += ' stroke-dasharray="5 4"' if dash else ""
        self.items.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{f}" '
                          f'stroke="{s}" stroke-width="{sw}"{extra}/>')

    def line(self, x1, y1, x2, y2, color="border", sw=1):
        self.items.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{self.c.get(color, color)}" stroke-width="{sw}"/>')

    def text(self, x, y, s, size=None, color="text", bold=False, anchor="start", mono=False):
        size = size or TYPE["body"]
        weight = ' font-weight="bold" font-family="Arial-BoldMT, Arial, Helvetica, sans-serif"' if bold else ""
        family = f' font-family="{MONO}"' if mono else ""
        self.items.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{self.c.get(color, color)}" '
                          f'text-anchor="{anchor}"{weight}{family}>{escape(str(s))}</text>')

    def circle(self, cx, cy, r, fill="surface", stroke="border", sw=1):
        self.items.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{self.c.get(fill, fill)}" '
                          f'stroke="{self.c.get(stroke, stroke)}" stroke-width="{sw}"/>')

    def link(self, x, y, w, h, target):
        self.hotspots.append((x, y, w, h, target))

    def svg(self):
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
                f'font-family="{FONT}">')
        return "\n".join([head, f'<rect width="{W}" height="{H}" fill="{self.c["bg"]}"/>'] + self.items + ["</svg>"])

    def button(self, x, y, label, kind="primary", w=None, disabled=False, target=None):
        w = w or int(text_width(label, TYPE["body"]) + 32)
        if self.wire:
            self.rect(x, y, w, 34, "surface", "border", rx=4, sw=1.5)
            self.text(x + w / 2, y + 22, label, color="text", anchor="middle", bold=kind == "primary")
        else:
            styles = {
                "primary": ("primary", None, "#FFFFFF"),
                "secondary": ("surface", "border", "text"),
                "danger": ("danger", None, "#FFFFFF"),
                "ghost": ("bg", None, "primary"),
            }
            fill, stroke, fg = styles[kind]
            if disabled:
                fill, stroke, fg = "bg", "border", "muted"
            self.rect(x, y, w, 34, fill, stroke, rx=6)
            self.text(x + w / 2, y + 22, label, color=fg, anchor="middle", bold=kind in ("primary", "danger"))
        if target:
            self.link(x, y, w, 34, target)
        return w

    def field(self, x, y, w, label, value="", placeholder="", required=False, error=None, combo=False,
              focused=False, h=34):
        self.text(x, y, label + (" *" if required else ""), size=TYPE["small"] + 1, color="text", bold=True)
        stroke = "danger" if error else ("primary" if focused else "border")
        self.rect(x, y + 8, w, h, "surface", stroke, rx=5, sw=2 if (error or focused) else 1)
        if value:
            self.text(x + 10, y + 8 + h / 2 + 5, value)
        elif placeholder:
            self.text(x + 10, y + 8 + h / 2 + 5, placeholder, color="muted")
        if combo:
            self.text(x + w - 18, y + 8 + h / 2 + 5, "▾", color="muted", anchor="middle")
        if error:
            self.text(x, y + h + 24, error, size=TYPE["small"], color="danger")

    def badge(self, x, y, label, kind):
        w = text_width(label, TYPE["small"]) + 18
        if self.wire:
            self.rect(x, y, w, 20, "surface", "border", rx=10)
            self.text(x + w / 2, y + 14, label, size=TYPE["small"], color="text", anchor="middle")
        else:
            self.rect(x, y, w, 20, f"{kind}_bg", None, rx=10)
            self.text(x + w / 2, y + 14, label, size=TYPE["small"], color=kind, anchor="middle", bold=True)

    def table(self, x, y, cols, rows, selected=None, sort=None, status_col=None, row_h=30, header_h=34):
        w = sum(c[1] for c in cols)
        self.rect(x, y, w, header_h + row_h * len(rows), "surface", "border", rx=6)
        self.rect(x + 1, y + 1, w - 2, header_h - 1, "primary_light", None, rx=5)
        cx = x
        for i, (name, cw) in enumerate(cols):
            label = name + (" ▾" if sort == i else "")
            self.text(cx + 10, y + 22, label, size=TYPE["small"] + 1, bold=True)
            cx += cw
        for r, row in enumerate(rows):
            ry = y + header_h + r * row_h
            if r == selected:
                self.rect(x + 1, ry, w - 2, row_h, "selected", None, rx=0)
            elif r % 2:
                self.rect(x + 1, ry, w - 2, row_h, "row_alt", None, rx=0)
            self.line(x, ry, x + w, ry)
            cx = x
            for i, (val, (_, cw)) in enumerate(zip(row, cols)):
                if i == status_col and val in STATUS_KIND:
                    self.badge(cx + 8, ry + 5, val, STATUS_KIND[val])
                else:
                    shown = str(val)
                    max_chars = int(cw / (TYPE["body"] * 0.56)) - 1
                    if len(shown) > max_chars:
                        shown = shown[: max_chars - 1] + "…"
                    self.text(cx + 10, ry + 20, shown, color="text" if val != "NULL" else "muted")
                cx += cw
        return w

    def sidebar(self, active, items):
        self.rect(0, 0, SIDEBAR_W, H, "sidebar", None, rx=0)
        if self.wire:
            self.line(SIDEBAR_W, 0, SIDEBAR_W, H, "border")
        self.rect(20, 18, 34, 34, "primary", None, rx=8)
        self.text(37, 41, "ПК", size=13, color="#FFFFFF" if not self.wire else "surface", anchor="middle", bold=True)
        self.text(64, 32, "Учёт ПК", size=15, color="sidebar_text" if self.wire else "#FFFFFF", bold=True)
        self.text(64, 48, "АС учёта компьютеров", size=10, color="sidebar_text")
        y = 84
        for key, icon, label, target in items:
            if key is None:
                self.text(20, y + 14, label.upper(), size=10, color="sidebar_text", bold=True)
                y += 26
                continue
            if key == active:
                self.rect(10, y, SIDEBAR_W - 20, 34, "primary", None, rx=6)
                fg = "#FFFFFF" if not self.wire else "surface"
            else:
                fg = "sidebar_text"
            self.text(26, y + 22, icon, size=13, color=fg, anchor="middle")
            self.text(44, y + 22, label, size=13, color=fg, bold=key == active)
            if target:
                self.link(10, y, SIDEBAR_W - 20, 34, target)
            y += 38
        self.text(20, H - 22, "computers.db · схема v2", size=10, color="sidebar_text")

    def topbar(self, title, crumbs, right=None):
        self.rect(SIDEBAR_W, 0, W - SIDEBAR_W, TOPBAR_H, "surface", None, rx=0)
        self.line(SIDEBAR_W, TOPBAR_H, W, TOPBAR_H)
        self.text(SIDEBAR_W + 24, 24, crumbs, size=TYPE["small"], color="muted")
        self.text(SIDEBAR_W + 24, 44, title, size=TYPE["h2"] + 2, bold=True)
        if right:
            self.text(W - 24, 34, right, size=TYPE["small"], color="muted", anchor="end")

    def card(self, x, y, w, h, title, value, kind="primary", note=""):
        self.rect(x, y, w, h, "surface", "border", rx=8)
        if not self.wire:
            self.rect(x, y, 5, h, kind, None, rx=2)
        self.text(x + 18, y + 26, title, size=TYPE["small"] + 1, color="muted")
        self.text(x + 18, y + 62, value, size=30, color=kind if not self.wire else "text", bold=True)
        if note:
            self.text(x + 18, y + h - 14, note, size=TYPE["small"], color="muted")

    def panel(self, x, y, w, h, title=None):
        self.rect(x, y, w, h, "surface", "border", rx=8)
        if title:
            self.text(x + 18, y + 28, title, size=TYPE["h2"], bold=True)
            self.line(x, y + 44, x + w, y + 44)

    def radio(self, x, y, label, checked=False):
        self.circle(x + 8, y - 4, 8, "surface", "primary" if checked else "border", 1.5)
        if checked:
            self.circle(x + 8, y - 4, 4, "primary", "primary")
        self.text(x + 24, y + 1, label)

    def checkbox(self, x, y, label, checked=False):
        self.rect(x, y - 12, 16, 16, "primary" if checked and not self.wire else "surface",
                  "primary" if checked else "border", rx=3, sw=1.5)
        if checked:
            self.text(x + 8, y + 1, "✓", size=12, color="#FFFFFF" if not self.wire else "text", anchor="middle", bold=True)
        self.text(x + 24, y + 1, label)

    def message(self, x, y, w, kind, title, body):
        h = 58
        self.rect(x, y, w, h, f"{kind}_bg", kind, rx=6)
        icon = {"success": "✓", "danger": "!", "warning": "!", "info": "i"}[kind]
        self.circle(x + 22, y + 29, 11, kind, kind)
        self.text(x + 22, y + 34, icon, size=13, color="#FFFFFF" if not self.wire else "surface", anchor="middle", bold=True)
        self.text(x + 44, y + 24, title, bold=True, color=kind if not self.wire else "text")
        self.text(x + 44, y + 44, body, size=TYPE["small"] + 1, color="text")

    def modal(self, w, h, title, lines, buttons, kind=None):
        self.rect(0, 0, W, H, "overlay", None, rx=0, opacity=0.45)
        x, y = (W - w) / 2, (H - h) / 2
        self.rect(x, y, w, h, "surface", "border", rx=10)
        if kind and not self.wire:
            self.rect(x, y, w, 6, kind, None, rx=3)
        self.text(x + 24, y + 40, title, size=TYPE["h2"] + 1, bold=True)
        for i, s in enumerate(lines):
            self.text(x + 24, y + 74 + i * 22, s)
        bx = x + w - 24
        for label, k, target in reversed(buttons):
            bw = int(text_width(label, TYPE["body"]) + 32)
            bx -= bw
            self.button(bx, y + h - 54, label, k, w=bw, target=target)
            bx -= 10

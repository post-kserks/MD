import tkinter as tk
from tkinter import ttk

from theme import C, STATUS_TAG, style_tree


def sort_key(value):
    if value is None:
        return (2, "")
    if isinstance(value, (int, float)):
        return (0, value)
    return (1, str(value).lower())


class DataTable(ttk.Frame):
    def __init__(self, parent, height=12, on_open=None, style=None):
        super().__init__(parent, style=style or "TFrame")
        self.tree = ttk.Treeview(self, show="headings", height=height, selectmode="browse")
        ys = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        xs = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=ys.set, xscrollcommand=xs.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        ys.grid(row=0, column=1, sticky="ns")
        xs.grid(row=1, column=0, sticky="ew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        style_tree(self.tree)
        self.columns, self.rows, self.shown = [], [], []
        self.sort_col, self.sort_desc = None, False
        self.filter_text = ""
        self.on_open = on_open
        if on_open:
            self.tree.bind("<Double-1>", lambda e: self.selected() and on_open(self.selected()))

    def load(self, columns, rows):
        self.columns, self.rows = list(columns), list(rows)
        if self.sort_col not in self.columns:
            self.sort_col, self.sort_desc = None, False
        self.tree["columns"] = self.columns
        for c in self.columns:
            width = max(90, min(260, 9 * max([len(c)] + [len(str(r[self.columns.index(c)])) for r in self.rows[:50]])))
            self.tree.heading(c, text=self._title(c), command=lambda col=c: self.sort_by(col))
            self.tree.column(c, width=width, minwidth=60, stretch=True, anchor="w")
        self.render()

    def _title(self, c):
        if c != self.sort_col:
            return c
        return f"{c} {'▼' if self.sort_desc else '▲'}"

    def sort_by(self, col):
        if self.sort_col == col:
            self.sort_desc = not self.sort_desc
        else:
            self.sort_col, self.sort_desc = col, False
        for c in self.columns:
            self.tree.heading(c, text=self._title(c))
        self.render()

    def set_filter(self, text):
        self.filter_text = text.strip().lower()
        self.render()

    def render(self):
        rows = self.rows
        if self.filter_text:
            rows = [r for r in rows if any(self.filter_text in str(v).lower() for v in r if v is not None)]
        if self.sort_col in self.columns:
            i = self.columns.index(self.sort_col)
            rows = sorted(rows, key=lambda r: sort_key(r[i]), reverse=self.sort_desc)
        self.shown = rows
        self.tree.delete(*self.tree.get_children())
        status_i = self.columns.index("status") if "status" in self.columns else None
        for n, r in enumerate(rows):
            tags = ["odd"] if n % 2 else []
            if status_i is not None and r[status_i] in STATUS_TAG:
                tags.append(STATUS_TAG[r[status_i]])
            self.tree.insert("", "end", iid=str(n), values=["NULL" if v is None else v for v in r], tags=tags)

    def selected(self):
        sel = self.tree.selection()
        if not sel:
            return None
        return dict(zip(self.columns, self.shown[int(sel[0])]))

    def count_text(self):
        if len(self.shown) == len(self.rows):
            return f"Строк: {len(self.rows)}"
        return f"Показано {len(self.shown)} из {len(self.rows)}"


class Card(ttk.Frame):
    def __init__(self, parent, title=None, F=None, **kw):
        super().__init__(parent, style="Card.TFrame", padding=16, **kw)
        if title:
            ttk.Label(self, text=title, style="H2.TLabel", font=F["h2"] if F else None).pack(anchor="w", pady=(0, 10))


class Message(ttk.Label):
    def __init__(self, parent, **kw):
        super().__init__(parent, text="", style="Card.TLabel", wraplength=700, **kw)

    def show(self, kind, text):
        self.configure(text=text, style=f"Msg{kind}.TLabel")

    def clear(self):
        self.configure(text="", style="Card.TLabel")


class LookupCombo(ttk.Combobox):
    def __init__(self, parent, items=(), optional=False, **kw):
        super().__init__(parent, state="readonly", **kw)
        self.optional = optional
        self.set_items(items)

    def set_items(self, items):
        self.items = [(None, "")] + list(items) if self.optional else list(items)
        self["values"] = [label for _, label in self.items]

    def get_key(self):
        label = self.get()
        for key, text in self.items:
            if text == label:
                return key
        return None

    def set_key(self, key):
        for k, text in self.items:
            if str(k) == str(key):
                self.set(text)
                return


def scrolled_text(parent, F, height=8, **kw):
    frame = ttk.Frame(parent, style="Card.TFrame")
    text = tk.Text(frame, height=height, font=F["mono"], bg=C["surface"], fg=C["text"], relief="flat",
                   insertbackground=C["text"], wrap="none", undo=True, borderwidth=0,
                   highlightthickness=1, highlightcolor=C["primary"], highlightbackground=C["border"], **kw)
    ys = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
    text.configure(yscrollcommand=ys.set)
    text.pack(side="left", fill="both", expand=True)
    ys.pack(side="right", fill="y")
    return frame, text

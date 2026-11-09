import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

C = {
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
    "info": "#3D6FB6",
    "info_bg": "#E4EDF9",
    "warning": "#B7791F",
    "warning_bg": "#FBF0DC",
    "danger": "#C0392B",
    "danger_bg": "#FBE5E2",
    "row_alt": "#F9FAFC",
    "selected": "#DCE7F7",
}

STATUS_TAG = {"в эксплуатации": "success", "в резерве": "info", "в ремонте": "warning", "списан": "danger"}

FAMILY = "Arial"
MONO = "Menlo"


def fonts(root):
    families = set(tkfont.families(root))
    family = next((f for f in ("Arial", "Helvetica", "Segoe UI", "DejaVu Sans") if f in families), "TkDefaultFont")
    mono = next((f for f in ("Menlo", "Consolas", "DejaVu Sans Mono", "Courier New") if f in families), "TkFixedFont")
    return {
        "h1": (family, 20, "bold"),
        "h2": (family, 15, "bold"),
        "body": (family, 13),
        "bold": (family, 13, "bold"),
        "small": (family, 11),
        "mono": (mono, 12),
    }


def setup(root):
    F = fonts(root)
    root.configure(bg=C["bg"])
    s = ttk.Style(root)
    s.theme_use("clam")
    s.configure(".", background=C["bg"], foreground=C["text"], font=F["body"], bordercolor=C["border"],
                lightcolor=C["border"], darkcolor=C["border"], troughcolor=C["bg"], focuscolor=C["primary"])
    s.configure("TFrame", background=C["bg"])
    s.configure("Card.TFrame", background=C["surface"], relief="solid", borderwidth=1)
    s.configure("Inner.TFrame", background=C["surface"], relief="flat", borderwidth=0)
    s.configure("Top.TFrame", background=C["surface"])
    s.configure("TLabel", background=C["bg"], foreground=C["text"], font=F["body"])
    s.configure("Card.TLabel", background=C["surface"])
    s.configure("Title.TLabel", background=C["surface"], font=F["h1"])
    s.configure("Crumb.TLabel", background=C["surface"], foreground=C["muted"], font=F["small"])
    s.configure("H2.TLabel", background=C["surface"], font=F["h2"])
    s.configure("Field.TLabel", background=C["surface"], font=F["bold"])
    s.configure("Muted.TLabel", foreground=C["muted"], font=F["small"])
    s.configure("CardMuted.TLabel", background=C["surface"], foreground=C["muted"], font=F["small"])
    s.configure("Error.TLabel", background=C["surface"], foreground=C["danger"], font=F["small"])
    for kind in ("success", "info", "warning", "danger"):
        s.configure(f"Stat{kind}.TLabel", background=C["surface"], foreground=C[kind], font=(F["h1"][0], 30, "bold"))
        s.configure(f"Msg{kind}.TLabel", background=C[f"{kind}_bg"], foreground=C[kind], font=F["bold"],
                    padding=(12, 10))
    s.configure("TButton", padding=(14, 7), width=-4, background=C["surface"], foreground=C["text"], borderwidth=1)
    s.map("TButton", background=[("active", C["primary_light"]), ("disabled", C["bg"])],
          foreground=[("disabled", C["muted"])])
    s.configure("Primary.TButton", background=C["primary"], foreground="#FFFFFF", bordercolor=C["primary"],
                font=F["bold"])
    s.map("Primary.TButton", background=[("active", C["primary_dark"]), ("disabled", C["border"])])
    s.configure("Danger.TButton", background=C["danger"], foreground="#FFFFFF", bordercolor=C["danger"],
                font=F["bold"])
    s.map("Danger.TButton", background=[("active", "#9E2E22")])
    s.configure("Nav.TButton", background=C["sidebar"], foreground=C["sidebar_text"], borderwidth=0,
                anchor="w", padding=(16, 9), font=F["body"])
    s.map("Nav.TButton", background=[("active", "#2A3850")], foreground=[("active", "#FFFFFF")])
    s.configure("NavActive.TButton", background=C["primary"], foreground="#FFFFFF", borderwidth=0,
                anchor="w", padding=(16, 9), font=F["bold"])
    s.map("NavActive.TButton", background=[("active", C["primary_dark"])])
    s.configure("Sidebar.TFrame", background=C["sidebar"])
    s.configure("Sidebar.TLabel", background=C["sidebar"], foreground=C["sidebar_text"], font=F["small"])
    s.configure("Brand.TLabel", background=C["sidebar"], foreground="#FFFFFF", font=F["h2"])
    s.configure("TEntry", fieldbackground=C["surface"], padding=6)
    s.configure("Bad.TEntry", fieldbackground=C["danger_bg"], bordercolor=C["danger"], padding=6)
    s.configure("TCombobox", fieldbackground=C["surface"], padding=5)
    s.configure("Bad.TCombobox", fieldbackground=C["danger_bg"], bordercolor=C["danger"], padding=5)
    s.configure("TCheckbutton", background=C["surface"])
    s.configure("TRadiobutton", background=C["surface"])
    s.configure("Treeview", background=C["surface"], fieldbackground=C["surface"], rowheight=28, font=F["body"])
    s.configure("Treeview.Heading", background=C["primary_light"], foreground=C["text"], font=F["bold"],
                relief="flat", padding=(8, 6))
    s.map("Treeview", background=[("selected", C["selected"])], foreground=[("selected", C["text"])])
    s.configure("Horizontal.TProgressbar", background=C["success"], troughcolor=C["bg"])
    return F


def style_tree(tree):
    tree.tag_configure("odd", background=C["row_alt"])
    for status, kind in STATUS_TAG.items():
        tree.tag_configure(kind, foreground=C[kind])


def text_widget(parent, F, **kw):
    t = tk.Text(parent, font=F["mono"], bg=C["surface"], fg=C["text"], insertbackground=C["text"],
                relief="solid", borderwidth=1, highlightthickness=1, highlightcolor=C["primary"],
                highlightbackground=C["border"], wrap="none", undo=True, **kw)
    return t

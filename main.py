import time
import tkinter as tk
from tkinter import ttk, messagebox

FIELDS = [  # key, label, default
    ("grid_v", "Grid voltage (V)", "400"),
    ("gen_v", "Generator voltage (V)", "400"),
    ("grid_f", "Grid frequency (Hz)", "50"),
    ("gen_f", "Generator frequency (Hz)", "50"),
    ("phase", "Phase angle (°)", "0"),
]
CHARTS = {  # chart name -> [(key, legend, color)]
    "Voltage (V)": [("grid_v", "Grid", "#2563eb"), ("gen_v", "Generator", "#e67e22")],
    "Frequency (Hz)": [("grid_f", "Grid", "#2563eb"), ("gen_f", "Generator", "#e67e22")],
    "Phase angle (°)": [("phase", "Phase", "#2e9e4f")],
}
LIM_DV, LIM_DF, LIM_DPH = 5.0, 0.2, 10.0  # % , Hz , deg
OK, BAD, GREY = "#2e9e4f", "#c0392b", "#9aa0a6"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sync Data Viewer")
        self.geometry("1050x680")
        self.minsize(900, 600)
        self.rows = []  # list of dicts

        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self._build_inputs()
        self._build_display()
        self.refresh()

    # ---------------- inputs (left) ----------------
    def _build_inputs(self):
        f = ttk.LabelFrame(self, text="Enter values", padding=12)
        f.grid(row=0, column=0, sticky="ns", padx=(10, 5), pady=10)
        self.entries = {}
        for key, label, default in FIELDS:
            ttk.Label(f, text=label).pack(anchor="w", pady=(8, 0))
            e = ttk.Entry(f, width=22)
            e.insert(0, default)
            e.pack(fill="x")
            e.bind("<Return>", lambda _e: self.add_reading())
            self.entries[key] = e
        ttk.Button(f, text="Add reading", command=self.add_reading).pack(fill="x", pady=(18, 4))
        ttk.Button(f, text="Clear all", command=self.clear).pack(fill="x")

    # ---------------- display (right) ----------------
    def _build_display(self):
        right = ttk.Frame(self)
        right.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        # cards
        cards = ttk.Frame(right)
        cards.grid(row=0, column=0, sticky="ew")
        self.card_vals = {}
        for i, (key, label, _) in enumerate(FIELDS):
            cards.columnconfigure(i, weight=1, uniform="card")
            c = tk.Frame(cards, bg="white", highlightbackground="#d0d4da", highlightthickness=1)
            c.grid(row=0, column=i, sticky="ew", padx=3)
            tk.Label(c, text=label, bg="white", fg="#555", font=("Segoe UI", 8)).pack(pady=(6, 0))
            v = tk.Label(c, text="--", bg="white", font=("Segoe UI", 18, "bold"))
            v.pack(pady=(0, 6))
            self.card_vals[key] = v

        self.status = tk.Label(right, text="", fg="white", font=("Segoe UI", 11, "bold"), pady=5)
        self.status.grid(row=0, column=0, sticky="ew", pady=(62, 0))

        # chart
        cf = ttk.LabelFrame(right, text="Chart", padding=6)
        cf.grid(row=1, column=0, sticky="nsew", pady=(8, 6))
        cf.columnconfigure(0, weight=1)
        cf.rowconfigure(1, weight=1)
        self.chart_choice = ttk.Combobox(cf, values=list(CHARTS), state="readonly", width=20)
        self.chart_choice.current(0)
        self.chart_choice.grid(row=0, column=0, sticky="w")
        self.chart_choice.bind("<<ComboboxSelected>>", lambda _e: self.draw_chart())
        self.canvas = tk.Canvas(cf, bg="white", highlightthickness=0)
        self.canvas.grid(row=1, column=0, sticky="nsew", pady=(6, 0))
        self.canvas.bind("<Configure>", lambda _e: self.draw_chart())

        # table
        tf = ttk.LabelFrame(right, text="History", padding=6)
        tf.grid(row=2, column=0, sticky="ew")
        cols = ["#", "Time"] + [lbl.split(" (")[0] for _, lbl, _ in FIELDS]
        self.table = ttk.Treeview(tf, columns=cols, show="headings", height=5)
        for c in cols:
            self.table.heading(c, text=c)
            self.table.column(c, width=60 if c == "#" else 110, anchor="center")
        sb = ttk.Scrollbar(tf, command=self.table.yview)
        self.table.config(yscrollcommand=sb.set)
        self.table.pack(side="left", fill="x", expand=True)
        sb.pack(side="right", fill="y")

    # ---------------- actions ----------------
    def add_reading(self):
        row = {}
        try:
            for key, label, _ in FIELDS:
                row[key] = float(self.entries[key].get().replace(",", "."))
        except ValueError:
            messagebox.showerror("Invalid input", "Please enter numbers only in every field.")
            return
        row["time"] = time.strftime("%H:%M:%S")
        self.rows.append(row)
        self.refresh()

    def clear(self):
        self.rows.clear()
        self.refresh()

    # ---------------- refresh ----------------
    def refresh(self):
        # table
        self.table.delete(*self.table.get_children())
        for i, r in enumerate(self.rows, 1):
            self.table.insert("", "end", values=[i, r["time"]] + [f"{r[k]:g}" for k, _, _ in FIELDS])
        if self.rows:
            self.table.yview_moveto(1)

        # cards + status
        last = self.rows[-1] if self.rows else None
        for key, _, _ in FIELDS:
            self.card_vals[key].config(text=f"{last[key]:g}" if last else "--")
        if last:
            dv = abs(last["gen_v"] - last["grid_v"]) / last["grid_v"] * 100 if last["grid_v"] else 999
            df = abs(last["gen_f"] - last["grid_f"])
            dph = abs(last["phase"])
            ok = dv <= LIM_DV and df <= LIM_DF and dph <= LIM_DPH
            self.status.config(
                text=("IN SYNC RANGE" if ok else "OUT OF SYNC RANGE")
                     + f"   |   ΔV {dv:.1f}%   Δf {df:.2f} Hz   φ {dph:.1f}°",
                bg=OK if ok else BAD)
        else:
            self.status.config(text="No readings yet", bg=GREY)
        self.draw_chart()

    # ---------------- chart ----------------
    def draw_chart(self):
        c = self.canvas
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        if w < 50 or h < 50:
            return
        series = CHARTS[self.chart_choice.get()]
        l, r, t, b = 60, 20, 20, 30
        n = len(self.rows)
        if n == 0:
            c.create_text(w / 2, h / 2, text="Add a reading to see the chart", fill=GREY,
                          font=("Segoe UI", 12))
            return

        data = [[row[k] for row in self.rows] for k, _, _ in series]
        lo = min(min(d) for d in data)
        hi = max(max(d) for d in data)
        if hi - lo < 1e-9:
            lo, hi = lo - 1, hi + 1
        pad = (hi - lo) * 0.1
        lo, hi = lo - pad, hi + pad

        def X(i):
            return l + (i * (w - l - r) / (n - 1) if n > 1 else (w - l - r) / 2)

        def Y(v):
            return t + (hi - v) / (hi - lo) * (h - t - b)

        # grid + y labels
        for i in range(6):
            v = lo + (hi - lo) * i / 5
            y = Y(v)
            c.create_line(l, y, w - r, y, fill="#e5e7eb")
            c.create_text(l - 6, y, text=f"{v:.2f}".rstrip("0").rstrip("."), anchor="e",
                          font=("Segoe UI", 8), fill="#555")
        # x labels
        step = max(1, n // 10)
        for i in range(0, n, step):
            c.create_text(X(i), h - b + 12, text=str(i + 1), font=("Segoe UI", 8), fill="#555")
        c.create_line(l, t, l, h - b, fill="#888")
        c.create_line(l, h - b, w - r, h - b, fill="#888")
        c.create_text((l + w - r) / 2, h - 4, text="Reading #", font=("Segoe UI", 8), fill="#555")

        # lines + points
        for (key, name, color), d in zip(series, data):
            pts = [(X(i), Y(v)) for i, v in enumerate(d)]
            if n > 1:
                c.create_line(*[p for xy in pts for p in xy], fill=color, width=2)
            for x, y in pts:
                c.create_oval(x - 3, y - 3, x + 3, y + 3, fill=color, outline="white")

        # legend
        x0 = w - r - 110 * len(series)
        for i, (_, name, color) in enumerate(series):
            c.create_rectangle(x0 + i * 110, 4, x0 + i * 110 + 12, 14, fill=color, outline="")
            c.create_text(x0 + i * 110 + 18, 9, text=name, anchor="w", font=("Segoe UI", 9))


if __name__ == "__main__":
    App().mainloop()

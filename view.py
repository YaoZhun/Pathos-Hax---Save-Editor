# view.py  —  pathosHax View Layer (tkinter UI)
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from typing import Callable, Optional

# ── Palette ───────────────────────────────────────────
BG    = "#0d1f0d"
PANEL = "#0f2a0f"
CARD  = "#132213"
INP   = "#0b1a0b"
BRD   = "#1e4a1e"
GRN   = "#00ff41"
GRN_D = "#39d353"
GRN_M = "#1a6a1a"
GOLD  = "#ffd700"
GOLD_D= "#a88a00"
RED   = "#ff5555"
TXT   = "#c8ffc8"
TXT_S = "#5fa85f"
TXT_M = "#2d5f2d"
HP_C  = "#ff6666"
MP_C  = "#5599ff"


class PathosView(tk.Tk):
    """Pure View: builds UI, exposes vars and callback hooks."""

    # ── Field keys that map to Entry widgets ──────────
    TEXT_FIELDS = ["name", "race", "class", "gender", "alignment"]
    NUM_FIELDS  = ["level", "experience"]
    ATTR_FIELDS = ["strength", "dexterity", "constitution",
                   "intelligence", "wisdom", "charisma"]
    VITAL_PAIRS = [("hp_current","hp_maximum"), ("mp_current","mp_maximum")]

    def __init__(self):
        super().__init__()
        self.title("pathosHax — Pathos Save Editor")
        self.configure(bg=BG)
        self.geometry("1100x720")
        self.minsize(900, 580)

        # ── Public StringVars (controller reads/writes) ──
        all_keys = (self.TEXT_FIELDS + self.NUM_FIELDS + self.ATTR_FIELDS
                    + [k for pair in self.VITAL_PAIRS for k in pair])
        self.sv: dict[str, tk.StringVar] = {
            k: tk.StringVar(self) for k in all_keys
        }
        self.sl: dict[str, tk.IntVar] = {
            k: tk.IntVar(self, 10) for k in self.ATTR_FIELDS
        }
        self.hp_bar = tk.DoubleVar(self, 0.5)
        self.mp_bar = tk.DoubleVar(self, 0.5)
        self.inv_var = tk.StringVar(self)

        # ── Callback hooks (set by Controller) ──────────
        self.on_open:   Callable   = lambda: None
        self.on_save:   Callable   = lambda: None
        self.on_save_as:Callable   = lambda: None
        self.on_backup: Callable   = lambda: None
        self.on_demo:   Callable   = lambda: None
        self.on_max_hp: Callable   = lambda: None
        self.on_max_mp: Callable   = lambda: None
        self.on_max_attrs: Callable= lambda: None
        self.on_rst_attrs: Callable= lambda: None
        self.on_field_change: Callable[[str, str], None] = lambda k, v: None
        self.on_inv_add:    Callable = lambda: None
        self.on_inv_update: Callable = lambda: None
        self.on_inv_delete: Callable = lambda: None
        self.on_inv_clear:  Callable = lambda: None
        self.on_inv_quick:  Callable[[str], None] = lambda item: None
        self.known_items: list[str]  = []

        self._build()
        self._bind_slider_sync()

    # ════════════════════════════════════════════════════
    #  Public API used by Controller
    # ════════════════════════════════════════════════════
    def set_fields(self, fields: dict):
        """Write parsed fields into all StringVars + sliders."""
        for key, var in self.sv.items():
            val = fields.get(key, "")
            var.set(val)
        for key, ivar in self.sl.items():
            try:
                ivar.set(int(fields.get(key, "10") or 10))
            except ValueError:
                ivar.set(10)
        # force repaint
        self.update_idletasks()

    def set_inventory(self, items: list[str]):
        self._inv_lb.delete(0, "end")
        for i, item in enumerate(items):
            self._inv_lb.insert("end", f"  {i+1:>2}.  {item}")
        self._inv_count.config(text=f"{len(items)} 件")

    def set_bars(self, hp_ratio: float, mp_ratio: float):
        self.hp_bar.set(max(0.0, min(1.0, hp_ratio)))
        self.mp_bar.set(max(0.0, min(1.0, mp_ratio)))

    def set_preview(self, text: str):
        self._raw.config(state="normal")
        self._raw.delete("1.0", "end")
        self._raw.insert("1.0", text)
        self._raw.config(state="disabled")

    def set_status(self, text: str, ok: bool = True):
        self._lbl_status.config(text=text, fg=GRN if ok else RED)

    def set_filename(self, text: str):
        self._lbl_file.config(text=text, fg=TXT)

    def set_savedir_hint(self, path: str):
        self._lbl_dir.config(text=path[-40:] if len(path) > 40 else path)

    def get_inv_input(self) -> str:
        return self.inv_var.get().strip()

    def get_inv_selection(self) -> Optional[int]:
        sel = self._inv_lb.curselection()
        return sel[0] if sel else None

    def clear_inv_input(self):
        self.inv_var.set("")
        self._ac_lb.delete(0, "end")

    def update_autocomplete(self, suggestions: list[str]):
        self._ac_lb.delete(0, "end")
        for s in suggestions:
            self._ac_lb.insert("end", s)

    def ask_save_path(self, initialdir: str, initialfile: str) -> str:
        return filedialog.asksaveasfilename(
            title="另存存檔", initialdir=initialdir, initialfile=initialfile,
            defaultextension=".Adventure",
            filetypes=[("Pathos Save", "*.Adventure *.adventure"), ("All", "*.*")])

    def ask_open_path(self, initialdir: str) -> str:
        return filedialog.askopenfilename(
            title="選擇 Pathos 存檔", initialdir=initialdir,
            filetypes=[("Pathos Save", "*.Adventure *.adventure *.backup"),
                       ("All", "*.*")])

    def confirm(self, title: str, msg: str) -> bool:
        return messagebox.askyesno(title, msg)

    def error(self, msg: str):
        messagebox.showerror("錯誤", msg)

    def info(self, msg: str):
        messagebox.showinfo("完成", msg)

    def ask_string(self, title: str, prompt: str, init: str) -> Optional[str]:
        return simpledialog.askstring(title, prompt, initialvalue=init, parent=self)

    # ════════════════════════════════════════════════════
    #  Build UI
    # ════════════════════════════════════════════════════
    def _build(self):
        self._build_header()
        self._build_toolbar()
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=0)
        body.rowconfigure(0, weight=1)
        self._build_notebook(body)
        self._build_sidebar(body)

    def _build_header(self):
        h = tk.Frame(self, bg=PANEL, height=54)
        h.pack(fill="x"); h.pack_propagate(False)
        tk.Label(h, text="⚔", font=("Helvetica", 22), bg=PANEL, fg=GRN).pack(side="left", padx=(14, 6))
        lf = tk.Frame(h, bg=PANEL); lf.pack(side="left")
        tk.Label(lf, text="pathosHax", font=("Courier", 17, "bold"), bg=PANEL, fg=GRN).pack(anchor="w")
        tk.Label(lf, text="PATHOS: NETHACK CODEX — SAVE EDITOR",
                 font=("Courier", 8), bg=PANEL, fg=TXT_M).pack(anchor="w")
        self._lbl_status = tk.Label(h, text="● 等待存檔", font=("Courier", 11),
                                     bg=PANEL, fg=TXT_M)
        self._lbl_status.pack(side="right", padx=18)

    def _build_toolbar(self):
        bar = tk.Frame(self, bg=PANEL, pady=5)
        bar.pack(fill="x", padx=8)
        self._btn(bar,"📂 開啟存檔", lambda: self.on_open(), GRN_M, GRN).pack(side="left", padx=(4,6))
        self._btn(bar,"💾 覆寫儲存", lambda: self.on_save(), "#3a2800", GOLD).pack(side="left", padx=3)
        self._btn(bar,"💾 另存新檔", lambda: self.on_save_as(), CARD, TXT_S).pack(side="left", padx=3)
        self._btn(bar,"📋 備份",     lambda: self.on_backup(), CARD, TXT_S).pack(side="left", padx=3)
        tk.Frame(bar, bg=BRD, width=1).pack(side="left", fill="y", padx=8, pady=4)
        self._btn(bar,"🎲 範例",     lambda: self.on_demo(), BG, TXT_M, relief="flat").pack(side="left")
        self._lbl_file = tk.Label(bar, text="未載入", font=("Courier", 9), bg=PANEL, fg=TXT_M)
        self._lbl_file.pack(side="right", padx=8)

    def _build_notebook(self, parent):
        self._style_notebook()
        self.nb = ttk.Notebook(parent)
        self.nb.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=8)
        self._build_tab_info()
        self._build_tab_vitals()
        self._build_tab_attrs()
        self._build_tab_inv()

    def _style_notebook(self):
        s = ttk.Style(self); s.theme_use("default")
        s.configure("TNotebook", background=PANEL, borderwidth=0)
        s.configure("TNotebook.Tab", background=CARD, foreground=TXT_S,
                    font=("Courier", 11, "bold"), padding=[16, 7], borderwidth=0)
        s.map("TNotebook.Tab",
              background=[("selected", "#1a4a1a")],
              foreground=[("selected", GRN)])
        s.configure("hp.Horizontal.TProgressbar", background=HP_C,
                    troughcolor=BRD, borderwidth=0)
        s.configure("mp.Horizontal.TProgressbar", background=MP_C,
                    troughcolor=BRD, borderwidth=0)
        s.configure("TScrollbar", background=BRD, troughcolor=BG, arrowcolor=TXT_M)

    # ── Tab 1 ─────────────────────────────────────────
    def _build_tab_info(self):
        tab = tk.Frame(self.nb, bg=BG)
        self.nb.add(tab, text="🧙 角色資訊")
        for c in range(3): tab.columnconfigure(c, weight=1)
        defs = (self.TEXT_FIELDS + ["level", "experience"])
        labels = {
            "name":"角色名稱","race":"種族","class":"職業",
            "gender":"性別","alignment":"陣營","level":"等級","experience":"經驗值",
        }
        for i, key in enumerate(defs):
            r, c = divmod(i, 3)
            self._field_card(tab, key, labels[key],
                             is_num=(key in self.NUM_FIELDS), row=r, col=c)

    # ── Tab 2 ─────────────────────────────────────────
    def _build_tab_vitals(self):
        tab = tk.Frame(self.nb, bg=BG)
        self.nb.add(tab, text="❤️ 生命 / 金幣")
        for c in range(2): tab.columnconfigure(c, weight=1)

        for col, (key_c, key_m, color, style, label) in enumerate([
            ("hp_current","hp_maximum",HP_C,"hp","❤️  HEALTH POINTS"),
            ("mp_current","mp_maximum",MP_C,"mp","💙  MANA POINTS"),
        ]):
            card = self._card(tab, color)
            card.grid(row=0, column=col, sticky="nsew", padx=6, pady=8)
            tk.Label(card, text=label, font=("Courier", 10, "bold"),
                     bg=CARD, fg=color).pack(anchor="w", padx=12, pady=(8,4))
            rf = tk.Frame(card, bg=CARD); rf.pack(fill="x", padx=12, pady=(0,4))
            for k in (key_c, key_m):
                e = tk.Entry(rf, textvariable=self.sv[k],
                             font=("Courier", 22, "bold"), bg=INP, fg=color,
                             insertbackground=color, relief="flat", bd=1, width=6)
                e.pack(side="left")
                e.bind("<FocusOut>", lambda ev, _k=k: self.on_field_change(_k, self.sv[_k].get()))
                if k == key_c:
                    tk.Label(rf, text=" / ", font=("Courier", 18),
                             bg=CARD, fg=TXT_M).pack(side="left")
            bar_var = self.hp_bar if style == "hp" else self.mp_bar
            ttk.Progressbar(card, variable=bar_var, maximum=1.0,
                            style=f"{style}.Horizontal.TProgressbar"
                            ).pack(fill="x", padx=12, pady=(0,10))

        # Buttons
        bf = tk.Frame(tab, bg=BG); bf.grid(row=1, column=0, columnspan=2, sticky="w", padx=10, pady=6)
        self._btn(bf,"❤️ HP回滿",lambda: self.on_max_hp(),"#3a1010",HP_C).pack(side="left",padx=(0,8))
        self._btn(bf,"💙 MP回滿",lambda: self.on_max_mp(),"#101030",MP_C).pack(side="left",padx=(0,8))
        self._btn(bf,"⚡ 全滿",  lambda: (self.on_max_hp(), self.on_max_mp()),GRN_M,GRN).pack(side="left")

    # ── Tab 3 ─────────────────────────────────────────
    def _build_tab_attrs(self):
        tab = tk.Frame(self.nb, bg=BG)
        self.nb.add(tab, text="💪 屬性值")
        for c in range(2): tab.columnconfigure(c, weight=1)
        labels = {"strength":"STR 力量","dexterity":"DEX 敏捷",
                  "constitution":"CON 體質","intelligence":"INT 智力",
                  "wisdom":"WIS 智慧","charisma":"CHA 魅力"}
        for i, key in enumerate(self.ATTR_FIELDS):
            self._attr_card(tab, key, labels[key], row=i//2, col=i%2)
        bf = tk.Frame(tab,bg=BG); bf.grid(row=3,column=0,columnspan=2,sticky="w",padx=10,pady=10)
        self._btn(bf,"⚡ 全屬性 MAX(25)",lambda: self.on_max_attrs(),GRN_M,GRN,px=18).pack(side="left",padx=(0,10))
        self._btn(bf,"🔄 重置為10",      lambda: self.on_rst_attrs(),CARD,TXT_S,px=18).pack(side="left")

    # ── Tab 4 ─────────────────────────────────────────
    def _build_tab_inv(self):
        tab = tk.Frame(self.nb, bg=BG)
        self.nb.add(tab, text="🎒 背包道具")
        tab.columnconfigure(0, weight=1); tab.columnconfigure(1, weight=0)
        tab.rowconfigure(1, weight=1)

        ih = tk.Frame(tab, bg=PANEL)
        ih.grid(row=0, column=0, columnspan=2, sticky="ew", padx=8, pady=(8,4))
        tk.Label(ih, text="🎒 背包道具", font=("Courier",11,"bold"), bg=PANEL, fg=GRN).pack(side="left",padx=10,pady=6)
        self._inv_count = tk.Label(ih, text="0 件", font=("Courier",10), bg=PANEL, fg=TXT_M)
        self._inv_count.pack(side="left")

        lf = tk.Frame(tab, bg=BG); lf.grid(row=1,column=0,sticky="nsew",padx=(10,4),pady=4)
        lf.rowconfigure(0,weight=1); lf.columnconfigure(0,weight=1)
        self._inv_lb = tk.Listbox(lf, font=("Courier",12), bg=CARD, fg=TXT,
                                    selectbackground=GRN_M, selectforeground=GRN,
                                    activestyle="none", relief="flat", bd=0,
                                    highlightthickness=1, highlightbackground=BRD)
        self._inv_lb.grid(row=0, column=0, sticky="nsew")
        vsb = ttk.Scrollbar(lf, orient="vertical", command=self._inv_lb.yview)
        self._inv_lb.configure(yscrollcommand=vsb.set)
        vsb.grid(row=0, column=1, sticky="ns")
        self._inv_lb.bind("<<ListboxSelect>>", self._on_inv_sel)
        self._inv_lb.bind("<Double-1>", lambda e: self._inv_edit())

        rp = tk.Frame(tab, bg=CARD, highlightbackground=BRD, highlightthickness=1)
        rp.grid(row=1, column=1, sticky="nsew", padx=(0,10), pady=4)
        tk.Label(rp, text="道具名稱", font=("Courier",10,"bold"), bg=CARD, fg=TXT_S).pack(anchor="w",padx=12,pady=(14,4))
        ie = tk.Entry(rp, textvariable=self.inv_var, font=("Courier",13),
                      bg=INP, fg=TXT, insertbackground=GRN, relief="flat", bd=1, width=28)
        ie.pack(fill="x", padx=12, pady=(0,4))
        ie.bind("<Return>", lambda e: self.on_inv_add())
        ie.bind("<KeyRelease>", self._ac_update)

        acf = tk.Frame(rp, bg=CARD); acf.pack(fill="x", padx=12, pady=(0,6))
        self._ac_lb = tk.Listbox(acf, font=("Courier",10), bg=INP, fg=GRN_D,
                                   selectbackground=GRN_M, height=5, relief="flat", bd=0,
                                   highlightthickness=1, highlightbackground=BRD)
        self._ac_lb.pack(fill="x")
        self._ac_lb.bind("<<ListboxSelect>>", self._ac_pick)

        tk.Frame(rp,bg=BRD,height=1).pack(fill="x",padx=10,pady=4)
        self._btn(rp,"➕ 新增",     lambda: self.on_inv_add(),    GRN_M,GRN,  px=10,py=5).pack(fill="x",padx=12,pady=2)
        self._btn(rp,"✏️ 更新選取", lambda: self.on_inv_update(), CARD, GRN_D,px=10,py=5).pack(fill="x",padx=12,pady=2)
        self._btn(rp,"🗑️ 刪除選取", lambda: self.on_inv_delete(), "#2a0a0a",RED,px=10,py=5).pack(fill="x",padx=12,pady=2)
        self._btn(rp,"🗑️ 清空背包", lambda: self.on_inv_clear(),  "#1a0505",RED,px=10,py=5).pack(fill="x",padx=12,pady=2)
        tk.Frame(rp,bg=BRD,height=1).pack(fill="x",padx=10,pady=4)
        tk.Label(rp,text="快速新增：",font=("Courier",9),bg=CARD,fg=TXT_M).pack(anchor="w",padx=12)
        for lbl, it in [("🔮 全治療藥水","potion of full healing"),
                         ("💙 魔力藥水",  "potion of gain energy"),
                         ("⭐ 許願魔杖",  "wand of wishing"),
                         ("🍀 鑑定卷軸",  "scroll of identify"),
                         ("💍 再生戒指",  "ring of regeneration"),
                         ("🛡️ 魔抗斗篷",  "cloak of magic resistance")]:
            self._btn(rp,lbl,lambda i=it: self.on_inv_quick(i),
                      CARD,TXT_S,px=8,py=2,fs=9,relief="flat").pack(fill="x",padx=12,pady=1)

    # ── Sidebar ───────────────────────────────────────
    def _build_sidebar(self, parent):
        side = tk.Frame(parent, bg=PANEL, width=265)
        side.grid(row=0, column=1, sticky="nsew")
        side.pack_propagate(False)
        hf = tk.Frame(side, bg=CARD, highlightbackground=BRD, highlightthickness=1)
        hf.pack(fill="x", padx=10, pady=(10,6))
        tk.Label(hf, text="📍 存檔位置", font=("Courier",9,"bold"), bg=CARD, fg=TXT).pack(anchor="w",padx=10,pady=(8,2))
        self._lbl_dir = tk.Label(hf, text="偵測中...", font=("Courier",8),
                                  bg=CARD, fg=GRN, wraplength=225, justify="left")
        self._lbl_dir.pack(anchor="w", padx=10, pady=(0,8))
        tk.Frame(side,bg=BRD,height=1).pack(fill="x",padx=10,pady=4)
        tk.Label(side,text="📄 玩家原始資料",font=("Courier",9),bg=PANEL,fg=TXT_S).pack(anchor="w",padx=12,pady=(2,2))
        rf = tk.Frame(side,bg=PANEL); rf.pack(fill="both",expand=True,padx=10,pady=(0,10))
        rf.rowconfigure(0,weight=1); rf.columnconfigure(0,weight=1)
        self._raw = tk.Text(rf, font=("Courier",8), bg=INP, fg=TXT_S,
                             insertbackground=GRN, relief="flat", bd=0,
                             wrap="word", state="disabled")
        self._raw.grid(row=0,column=0,sticky="nsew")
        vsb = ttk.Scrollbar(rf,orient="vertical",command=self._raw.yview)
        self._raw.configure(yscrollcommand=vsb.set)
        vsb.grid(row=0,column=1,sticky="ns")

    # ── Widget helpers ────────────────────────────────
    def _card(self, parent, border=None):
        return tk.Frame(parent, bg=CARD,
                        highlightbackground=border or BRD,
                        highlightthickness=1)

    def _btn(self, parent, text, cmd, bg, fg, px=12, py=5, fs=10, relief="groove"):
        return tk.Button(parent, text=text, command=cmd,
                         bg=bg, fg=fg, font=("Courier",fs,"bold"),
                         activebackground=GRN_M, activeforeground=GRN,
                         relief=relief, bd=1, cursor="hand2", padx=px, pady=py)

    def _field_card(self, parent, key, label, is_num, row, col):
        card = self._card(parent)
        card.grid(row=row, column=col, sticky="ew", padx=6, pady=6, ipady=4)
        tk.Label(card, text=label.upper(), font=("Courier",8),
                 bg=CARD, fg=TXT_M).pack(anchor="w", padx=10, pady=(8,2))
        e = tk.Entry(card, textvariable=self.sv[key],
                     font=("Courier",14,"bold"), bg=INP, fg=TXT,
                     insertbackground=GRN, relief="flat", bd=1)
        if is_num:
            vcmd = (self.register(lambda s: s.isdigit() or s == ""), "%P")
            e.config(validate="key", validatecommand=vcmd)
        e.pack(fill="x", padx=10, pady=(0,8))
        e.bind("<FocusOut>", lambda ev, k=key: self.on_field_change(k, self.sv[k].get()))

    def _attr_card(self, parent, key, label, row, col):
        card = self._card(parent)
        card.grid(row=row, column=col, sticky="ew", padx=6, pady=5, ipady=2)
        hdr = tk.Frame(card, bg=CARD); hdr.pack(fill="x", padx=12, pady=(10,2))
        tk.Label(hdr, text=label.upper(), font=("Courier",9,"bold"),
                 bg=CARD, fg=TXT_S).pack(side="left")
        ne = tk.Entry(hdr, textvariable=self.sv[key],
                      font=("Courier",16,"bold"), bg=INP, fg=GRN,
                      insertbackground=GRN, relief="flat", bd=1, width=4, justify="center")
        vcmd = (self.register(lambda s: s.isdigit() or s == ""), "%P")
        ne.config(validate="key", validatecommand=vcmd)
        ne.pack(side="right")
        sl = tk.Scale(card, from_=3, to=25, orient="horizontal",
                      variable=self.sl[key],
                      bg=CARD, fg=TXT_M, troughcolor=BRD,
                      activebackground=GRN, highlightthickness=0,
                      showvalue=False, sliderlength=16)
        sl.pack(fill="x", padx=12, pady=(0,8))
        # expose change via on_field_change
        ne.bind("<FocusOut>", lambda ev, k=key: self.on_field_change(k, self.sv[k].get()))
        sl.bind("<ButtonRelease-1>", lambda ev, k=key: self.on_field_change(k, str(self.sl[k].get())))

    def _bind_slider_sync(self):
        """Keep entry <-> slider in sync visually without triggering controller."""
        for key in self.ATTR_FIELDS:
            def _sl_trace(*_, k=key):
                try: self.sv[k].set(str(self.sl[k].get()))
                except: pass
            self.sl[key].trace_add("write", _sl_trace)

    # ── Inventory internal helpers ────────────────────
    def _on_inv_sel(self, e=None):
        sel = self._inv_lb.curselection()
        if sel:
            raw = self._inv_lb.get(sel[0])
            self.inv_var.set(raw.strip().split(".", 1)[-1].strip())

    def _ac_update(self, e=None):
        q = self.inv_var.get().lower()
        self._ac_lb.delete(0, "end")
        if len(q) >= 2:
            for it in self.known_items:
                if q in it.lower():
                    self._ac_lb.insert("end", it)

    def _ac_pick(self, e=None):
        sel = self._ac_lb.curselection()
        if sel:
            self.inv_var.set(self._ac_lb.get(sel[0]))
            self._ac_lb.delete(0, "end")

    def _inv_edit(self):
        sel = self._inv_lb.curselection()
        if not sel: return
        raw = self._inv_lb.get(sel[0])
        old = raw.strip().split(".", 1)[-1].strip()
        new = self.ask_string("編輯道具", "道具名稱：", old)
        if new and new.strip():
            self.inv_var.set(new.strip())
            self.on_inv_update()

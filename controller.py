# controller.py  —  pathosHax Controller Layer
import shutil
from pathlib import Path
from typing import Optional
import model
from view import PathosView


class PathosController:
    """Connects Model ↔ View; owns application state."""

    def __init__(self, view: PathosView):
        self.view       = view
        self.raw_text   = ""
        self.fields     = {}
        self.inventory  = []
        self.save_path  = None
        self.save_dir   = model.find_save_dir()

        # Inject known items for autocomplete
        view.known_items = model.KNOWN_ITEMS

        # Wire callbacks
        view.on_open         = self.open_file
        view.on_save         = self.save_file
        view.on_save_as      = self.save_as
        view.on_backup       = self.backup
        view.on_demo         = self.load_demo
        view.on_max_hp       = self.max_hp
        view.on_max_mp       = self.max_mp
        view.on_max_attrs    = self.max_attrs
        view.on_rst_attrs    = self.rst_attrs
        view.on_field_change = self.on_field_change
        view.on_inv_add      = self.inv_add
        view.on_inv_update   = self.inv_update
        view.on_inv_delete   = self.inv_delete
        view.on_inv_clear    = self.inv_clear
        view.on_inv_quick    = self.inv_quick

        # Show save dir hint
        view.set_savedir_hint(self.save_dir)

    # ── Load ─────────────────────────────────────────
    def load_text(self, text: str, path: Optional[str]):
        self.raw_text       = text
        self.fields, self.inventory = model.parse(text)
        self.save_path      = path
        if path:
            self.save_dir = str(Path(path).parent)
            self.view.set_savedir_hint(self.save_dir)

        # Push data to View
        self.view.set_fields(self.fields)
        self.view.set_inventory(self.inventory)
        self._push_bars()
        self._push_preview()

        fname = Path(path).name if path else "（範例存檔）"
        self.view.set_filename(f"📄 {fname}")
        self.view.set_status(f"● 已載入：{fname}")
        self.view.title(f"pathosHax — {fname}")

    def _push_bars(self):
        try:
            hp_c = float(self.fields.get("hp_current", 0) or 0)
            hp_m = float(self.fields.get("hp_maximum", 1) or 1)
        except: hp_c, hp_m = 0, 1
        try:
            mp_c = float(self.fields.get("mp_current", 0) or 0)
            mp_m = float(self.fields.get("mp_maximum", 1) or 1)
        except: mp_c, mp_m = 0, 1
        self.view.set_bars(hp_c / max(hp_m, 1), mp_c / max(mp_m, 1))

    def _push_preview(self):
        _, pline = model._player_line(self.raw_text)
        if not pline:
            self.view.set_preview("（未找到玩家資料行）"); return
        preview = pline
        for tok in ["skills ", "knowledge ", "masteries ", "equipment ", "inventory ", "square "]:
            preview = preview.replace(tok, f"\n{tok}")
        self.view.set_preview(preview)

    # ── Field edit ───────────────────────────────────
    def on_field_change(self, key: str, value: str):
        self.fields[key] = value
        self._push_bars()

    # ── File ops ─────────────────────────────────────
    def open_file(self):
        path = self.view.ask_open_path(self.save_dir)
        if not path: return
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                self.load_text(f.read(), path)
        except Exception as e:
            self.view.error(f"無法開啟：{e}")

    def save_file(self):
        if not self.save_path:
            self.save_as(); return
        self._write(self.save_path)

    def save_as(self):
        default = Path(self.save_path).name if self.save_path else \
                  (self.fields.get("name", "character") + ".Adventure")
        path = self.view.ask_save_path(self.save_dir, default)
        if path:
            self.save_path = path
            self._write(path)

    def _write(self, path: str):
        # Pull latest values from view vars into fields
        for key, var in self.view.sv.items():
            self.fields[key] = var.get()
        try:
            final = model.serialize(self.raw_text, self.fields, self.inventory)
            with open(path, "w", encoding="utf-8") as f:
                f.write(final)
            self.raw_text = final
            self.view.set_status("✅ 已儲存")
            self.view.info(f"存檔已儲存：\n{path}")
        except Exception as e:
            self.view.error(f"無法儲存：{e}")

    def backup(self):
        if not self.save_path:
            self.view.error("請先開啟存檔"); return
        src = Path(self.save_path)
        dst = src.with_suffix(".Adventure.bak")
        try:
            shutil.copy2(src, dst)
            self.view.info(f"已備份至：\n{dst}")
        except Exception as e:
            self.view.error(f"備份失敗：{e}")

    def load_demo(self):
        self.load_text(model.DEMO_TEXT, None)

    # ── Shortcuts ────────────────────────────────────
    def max_hp(self):
        mx = self.fields.get("hp_maximum", "9999")
        self.fields["hp_current"] = mx
        self.view.sv["hp_current"].set(mx)
        self._push_bars()

    def max_mp(self):
        mx = self.fields.get("mp_maximum", "9999")
        self.fields["mp_current"] = mx
        self.view.sv["mp_current"].set(mx)
        self._push_bars()

    def max_attrs(self):
        for k in self.view.ATTR_FIELDS:
            self.fields[k] = "25"
            self.view.sv[k].set("25")
            self.view.sl[k].set(25)

    def rst_attrs(self):
        for k in self.view.ATTR_FIELDS:
            self.fields[k] = "10"
            self.view.sv[k].set("10")
            self.view.sl[k].set(10)

    # ── Inventory ────────────────────────────────────
    def inv_add(self):
        name = self.view.get_inv_input()
        if not name:
            self.view.error("請輸入道具名稱"); return
        self.inventory.append(name)
        self.view.set_inventory(self.inventory)
        self.view.clear_inv_input()

    def inv_update(self):
        idx = self.view.get_inv_selection()
        if idx is None:
            self.view.error("請先選取要修改的道具"); return
        name = self.view.get_inv_input()
        if not name:
            self.view.error("名稱不能空白"); return
        self.inventory[idx] = name
        self.view.set_inventory(self.inventory)

    def inv_delete(self):
        idx = self.view.get_inv_selection()
        if idx is None:
            self.view.error("請先選取道具"); return
        if self.view.confirm("確認", "刪除此道具？"):
            del self.inventory[idx]
            self.view.set_inventory(self.inventory)
            self.view.clear_inv_input()

    def inv_clear(self):
        if not self.inventory: return
        if self.view.confirm("確認", f"清空全部 {len(self.inventory)} 件道具？"):
            self.inventory.clear()
            self.view.set_inventory(self.inventory)

    def inv_quick(self, item: str):
        self.inventory.append(item)
        self.view.set_inventory(self.inventory)

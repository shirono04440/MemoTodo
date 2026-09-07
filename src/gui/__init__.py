"""TodoApp GUI 包 — 备忘软件主界面

使用 Mixin 模式将原单文件拆分为多个功能模块。
继承链按 MRO 排列：Utils → TitleBar → Resize → List → DragDrop → Dialog*。
所有 Mixin 间无直接 import，依赖通过 TodoApp 实例在运行时解析。
"""

import tkinter as tk
from themes import THEMES
from settings import load_settings

# ── Mixin 导入 ──────────────────────────────────────────
from ._utils import UtilsMixin
from ._title_bar import TitleBarMixin
from ._resize import ResizeMixin
from ._list import ListMixin
from ._drag_drop import DragDropMixin
from ._dialog_base import DialogBaseMixin
from ._dialog_edit import DialogEditMixin
from ._dialog_add import DialogAddMixin
from ._dialog_settings import DialogSettingsMixin


from ._tray import TrayMixin


class TodoApp(UtilsMixin,
              TitleBarMixin,
              ResizeMixin,
              ListMixin,
              DragDropMixin,
              DialogBaseMixin,
              DialogEditMixin,
              DialogAddMixin,
              DialogSettingsMixin,
              TrayMixin):
    """备忘软件主界面"""

    def __init__(self, monitor=None):
        self.monitor = monitor
        self.config = load_settings()

        self.root = tk.Tk()
        self.root.configure(bg=self.theme["bg_primary"])
        fs = self.config.get("font_size", 11)
        min_w = max(420, 180 + fs * 20)
        min_h = max(320, fs * 24)
        self.root.minsize(min_w, min_h)
        self._apply_window_geometry()

        # 去掉系统标题栏和边框（全部自绘）
        self.root.overrideredirect(True)

        self._apply_window_opacity()
        self._apply_window_on_top()

        self._base_font_size = tk.IntVar(value=self.config["font_size"])
        self._make_fonts()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._tk_icons = {}
        self._bg_photo = None
        self._refreshing = False
        self._items_cache = []   # 内存缓存，避免每秒查库
        c = self.config
        self._last_visual = f"{c['theme']}|{c['font_size']}|{c['icon_size']}|{c['bg_image_path']}|{c['bg_image_opacity']}"
        self._pinned = False
        self._drag_x = 0
        self._drag_y = 0

        self._build_main_ui()
        self._apply_background_bind()
        self.root.after(150, self._refresh_list)
        self._setup_tray()

    # ================================================================
    #  属性 & 基础方法
    # ================================================================

    @property
    def theme(self):
        name = self.config.get("theme", "light")
        return THEMES.get(name, THEMES["light"])

    def _make_fonts(self):
        size = self._base_font_size.get()
        self.font_normal = ("Microsoft YaHei", size)
        self.font_bold = ("Microsoft YaHei", size, "bold")
        self.font_small = ("Microsoft YaHei", max(8, size - 2))

    def _apply_window_geometry(self):
        w = self.config.get("window_width", 800)
        h = self.config.get("window_height", 600)
        x = self.config.get("window_x", -1)
        y = self.config.get("window_y", -1)
        if x >= 0 and y >= 0:
            self.root.geometry(f"{w}x{h}+{x}+{y}")
        else:
            self.root.geometry(f"{w}x{h}")

    def _save_window_position(self):
        """保存当前窗口位置到 config 并写库"""
        try:
            x = self.root.winfo_x()
            y = self.root.winfo_y()
        except tk.TclError:
            return
        self.config["window_x"] = x
        self.config["window_y"] = y
        from settings import save_settings
        save_settings({"window_x": x, "window_y": y})

    def _apply_window_opacity(self):
        self.root.attributes("-alpha", self.config.get("window_opacity", 1.0))

    def _apply_window_on_top(self):
        self.root.attributes("-topmost", bool(self.config.get("window_on_top", 0)))

    # ================================================================
    #  主界面结构（委托给各 Mixin）
    # ================================================================

    def _build_main_ui(self):
        self._build_header()        # TitleBarMixin
        self._build_summary_bar()   # ListMixin
        self._build_list_area()     # ListMixin
        self._build_resize_grip()   # ResizeMixin

    # ================================================================
    #  监控回调 & 生命周期
    # ================================================================

    def on_monitor_status_change(self):
        self.root.after(0, self._refresh_list)

    def _on_close(self):
        """关闭窗口 → 最小化到系统托盘"""
        self._save_window_position()
        self.root.withdraw()

    def run(self):
        self.root.mainloop()

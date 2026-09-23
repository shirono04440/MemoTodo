"""事项列表 Mixin — 摘要条、卡片列表、滚动区域"""

import os
import tkinter as tk
from PIL import ImageTk

from database import get_all_items
from icon_utils import extract_icon, load_custom_icon, make_default_icon
from themes import THEMES
from ._widgets import RoundedCard


class ListMixin:
    """摘要条、Canvas 列表区、卡片构建与刷新"""

    # ================================================================
    #  摘要条
    # ================================================================

    def _build_summary_bar(self):
        th = self.theme
        self.summary_bar = tk.Frame(self.root, bg=th["bg_primary"], height=22,
                                    bd=0, highlightthickness=0)
        self.summary_bar.pack(fill=tk.X)
        self.summary_bar.pack_propagate(False)
        self.summary_label = tk.Label(self.summary_bar, text="", font=self.font_small,
                                      bg=th["bg_primary"], fg=th["text_muted"], bd=0)
        self.summary_label.pack(side=tk.LEFT, padx=16)
        self._update_summary()

    def _update_summary(self):
        items = self._items_cache
        opened = sum(1 for i in items if i.get("opened_today"))
        total = len(items)
        self.summary_label.config(text=f"已完成 {opened}/{total}")

    # ================================================================
    #  事项列表
    # ================================================================

    def _build_list_area(self):
        th = self.theme
        self.list_container = tk.Frame(self.root, bg=th["bg_primary"], bd=0, highlightthickness=0)
        self.list_container.pack(fill=tk.BOTH, expand=True)

        # Canvas 仅用于滚动，卡片是真实的 Frame 放在 inner 里
        self.canvas = tk.Canvas(self.list_container, highlightthickness=0, bd=0)
        self.canvas.configure(bg=th["bg_primary"])
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas.configure(yscrollcommand=self._on_canvas_scroll)

        self.canvas.bind("<Enter>", lambda e: self._bind_mousewheel())
        self.canvas.bind("<Leave>", lambda e: self._unbind_mousewheel())

        # inner_frame 是卡片的直接父容器，放在 Canvas 窗口里
        self._inner_frame = tk.Frame(self.canvas, bg=th["bg_primary"], bd=0, highlightthickness=0)
        self._inner_id = self.canvas.create_window((0, 0), window=self._inner_frame,
                                                    anchor="nw", tags="inner")
        self._inner_frame.bind("<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>",
            lambda e: self.canvas.itemconfig(self._inner_id, width=e.width))

        self._card_frames = []   # 当前显示的卡片 Frame 列表
        self._card_windows = []  # 保持兼容（不再使用 canvas window，但保留属性）

    def _on_canvas_scroll(self, *args):
        self._pin_bg_to_viewport()

    def _bind_mousewheel(self):
        def on_wheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            self._pin_bg_to_viewport()
        self._mousewheel_id = self.canvas.bind("<MouseWheel>", on_wheel)

    def _unbind_mousewheel(self):
        self.canvas.unbind("<MouseWheel>", self._mousewheel_id)


    # ================================================================
    #  刷新列表
    # ================================================================

    def _refresh_list(self):
        if self._refreshing:
            return
        self._refreshing = True
        try:
            self._refresh_list_inner()
        finally:
            self._refreshing = False

    def _make_section_label(self, text, count):
        """区段标题"""
        th = self.theme
        txt = f"{text}  ·  {count}"
        lbl = tk.Label(self._inner_frame, text=txt, font=self.font_small,
                       bg=th["bg_primary"], fg=th["text_muted"],
                       anchor="w", justify="left")
        lbl.pack(fill=tk.X, padx=(16, 12), pady=(10, 4))
        return lbl

    def _build_card_frame(self, item, idx):
        """为事项创建圆角卡片"""
        th = self.theme
        icon_size = self.config.get("icon_size", 48)
        notes = item.get("notes", "")
        is_open = item.get("opened_today", 0)
        radius = 12

        card = RoundedCard(self._inner_frame, bg=th["bg_card"],
                           outer_bg=th["bg_primary"], radius=radius, cursor="hand2")
        card.pack(fill=tk.X, padx=12, pady=3)
        body = card.inner  # 内容实际放在这里

        # 色条
        strip = tk.Frame(body, bg=th["accent"] if is_open else th["text_dim"],
                        width=4, bd=0, highlightthickness=0)
        strip.pack(side=tk.LEFT, fill=tk.Y)

        # 图标
        custom_icon = item.get("icon_path", "")
        if custom_icon and os.path.exists(custom_icon):
            icon_img = load_custom_icon(custom_icon, size=icon_size)
        else:
            icon_img = extract_icon(item["exe_path"], size=icon_size)
        if icon_img is None:
            icon_img = make_default_icon(size=icon_size)

        tk_icon = ImageTk.PhotoImage(icon_img)
        self._tk_icons[f"item_{item['id']}"] = tk_icon

        icon_lbl = tk.Label(body, image=tk_icon, bg=th["bg_card"], bd=0, cursor="hand2")
        icon_lbl.pack(side=tk.LEFT, padx=(8, 12), pady=8)
        icon_lbl.bind("<Button-1>", lambda e, p=item["exe_path"]: self._on_launch(p))

        # 文字区 —— 空白处可拖拽排序
        ta = tk.Frame(body, bg=th["bg_card"], bd=0, highlightthickness=0)
        ta.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=8)
        ta.bind("<Button-1>", lambda e, i=idx: self._drag_press(e, i))
        ta.bind("<B1-Motion>", self._drag_card_move)
        ta.bind("<ButtonRelease-1>", self._drag_card_stop)

        name_lbl = tk.Label(ta, text=item["name"],
                           font=self.font_bold, fg=th["text_primary"],
                           bg=th["bg_card"], anchor="w", justify="left")
        name_lbl.pack(anchor="w")
        if notes:
            tk.Label(ta, text=f"💬 {notes}", font=self.font_small,
                    fg=th["text_muted"], bg=th["bg_card"],
                    anchor="w", justify="left", wraplength=300).pack(anchor="w")

        name_lbl.bind("<Button-1>",
            lambda e, p=item["exe_path"]: (self._on_launch(p) or "break"))

        # 右键编辑
        for w in (card, body, name_lbl, ta, icon_lbl):
            w.bind("<Button-3>", lambda e, i=item: self._on_edit_item(i))

        # 操作按钮
        actions = tk.Frame(body, bg=th["bg_card"], bd=0, highlightthickness=0)
        actions.pack(side=tk.RIGHT, padx=(0, 10), pady=8)

        gear_btn = tk.Label(actions, text="⚙", font=("Microsoft YaHei", 12),
                           bg=th["bg_card"], fg=th["text_muted"],
                           cursor="hand2", padx=3, pady=1)
        gear_btn.pack(side=tk.LEFT)
        gear_btn.bind("<Button-1>", lambda e, i=item: self._on_edit_item(i))
        self._bind_fg_hover(gear_btn, th["text_muted"], th["accent"])

        launch_btn = tk.Label(actions, text="▶", font=("Microsoft YaHei", 12),
                             bg=th["btn_launch"], fg=th["btn_launch_fg"],
                             cursor="hand2", padx=3, pady=1)
        launch_btn.pack(side=tk.LEFT, padx=(4, 0))
        launch_btn.bind("<Button-1>", lambda e, p=item["exe_path"]: self._on_launch(p))
        self._bind_hover(launch_btn, th["btn_launch"], th["btn_launch_hover"], th["btn_launch_fg"])

        ch = "✓" if is_open else "✗"
        cc = th["success"] if is_open else th["text_muted"]
        check_btn = tk.Label(actions, text=f" {ch} ", font=("Microsoft YaHei", 12),
                            fg=cc, bg=th["bg_card"], cursor="hand2", padx=3, pady=1)
        check_btn.pack(side=tk.LEFT, padx=(4, 0))
        check_btn.bind("<Button-1>",
            lambda e, iid=item["id"], cur=is_open: self._toggle_status(iid, cur))

        # hover：整卡换色（内部子控件递归同步）
        hov = self._lighten(th["bg_card"], -10 if th is THEMES["dark"] else -6)
        def on_enter(e, c=card, bg=th["bg_card"], hv=hov):
            c.set_bg(hv)
        def on_leave(e, c=card, bg=th["bg_card"]):
            c.set_bg(bg)
        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)

        card._item_id = item["id"]
        return card

    # ================================================================
    #  刷新列表
    # ================================================================

    def _refresh_list_inner(self):
        th = self.theme
        self._tk_icons.clear()
        self._card_frames.clear()
        self._card_windows.clear()

        # 清空 inner_frame 旧内容
        for w in self._inner_frame.winfo_children():
            w.destroy()

        self._render_bg_on_canvas()

        items = get_all_items()
        self._items_cache = items

        if not items:
            tk.Label(self._inner_frame, text="还没有备忘事项",
                    font=self.font_bold, fg=th["text_muted"],
                    bg=th["bg_primary"]).pack(pady=(90, 0))
            tk.Label(self._inner_frame, text="点击顶部「＋ 添加事项」开始记录",
                    font=self.font_small, fg=th["text_dim"],
                    bg=th["bg_primary"]).pack(pady=(8, 0))
            self.canvas.yview_moveto(0)
            self._update_summary()
            return

        opened = [i for i in items if i.get("opened_today")]
        pending = [i for i in items if not i.get("opened_today")]

        if opened:
            self._make_section_label("✅ 今天已完成", len(opened))
            for item in opened:
                self._card_frames.append(self._build_card_frame(item, len(self._card_frames)))

        if pending:
            if opened:
                tk.Frame(self._inner_frame, height=6, bg=th["bg_primary"],
                        bd=0).pack(fill=tk.X)
            self._make_section_label("⏳ 待完成", len(pending))
            for item in pending:
                self._card_frames.append(self._build_card_frame(item, len(self._card_frames)))

        # 底部留白
        tk.Frame(self._inner_frame, height=12, bg=th["bg_primary"],
                bd=0).pack(fill=tk.X)

        self.canvas.yview_moveto(0)
        self._update_summary()

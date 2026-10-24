"""自定义标题栏 Mixin — 拖动、按钮、图钉"""

import tkinter as tk
from themes import THEMES


class TitleBarMixin:
    """自定义标题栏：按钮区、拖动移动窗口、图钉固定"""

    # ================================================================
    #  自定义标题栏（拖动 + 按钮 + X 关闭）
    # ================================================================

    def _build_header(self):
        th = self.theme
        bar_h = 44
        self._title_bar = tk.Frame(self.root, bg=th["bg_header"], height=bar_h,
                                   bd=0, highlightthickness=0, relief="flat")
        self._title_bar.pack(fill=tk.X)
        self._title_bar.pack_propagate(False)

        # 底部装饰线
        tk.Frame(self._title_bar, bg=th["accent"], height=2,
                 bd=0, highlightthickness=0).pack(side=tk.BOTTOM, fill=tk.X)

        # 拖动区 —— 标题栏除了按钮之外的区域都能按住拖动
        self._title_bar.bind("<Button-1>", self._drag_start)
        self._title_bar.bind("<B1-Motion>", self._drag_do)
        self._title_bar.bind("<ButtonRelease-1>", self._drag_stop)

        # 标题
        self._title_label = tk.Label(self._title_bar, text="📋  二游日常表",
                 font=("Microsoft YaHei", self._base_font_size.get() + 2, "bold"),
                 bg=th["bg_header"], fg=th["text_header"], bd=0)
        self._title_label.pack(side=tk.LEFT, padx=16, pady=4)

        # 右边按钮区
        self._title_btn_bar = tk.Frame(self._title_bar, bg=th["bg_header"], bd=0, highlightthickness=0)
        self._title_btn_bar.pack(side=tk.RIGHT, padx=8)

        self._add_btn = tk.Button(self._title_btn_bar, text="＋",
                            font=("Microsoft YaHei", self._base_font_size.get(), "bold"),
                            bg=th["btn_add"], fg=th["btn_add_fg"],
                            activebackground=th["btn_add_hover"], activeforeground=th["btn_add_fg"],
                            relief="flat", bd=0, width=3, height=1, cursor="hand2",
                            command=self._on_add)
        self._add_btn.pack(side=tk.LEFT, padx=3)
        self._bind_hover(self._add_btn, th["btn_add"], th["btn_add_hover"], th["btn_add_fg"])
        self._add_button_tooltip(self._add_btn, "添加事项")

        self._set_btn = tk.Button(self._title_btn_bar, text="⚙",
                            font=("Microsoft YaHei", self._base_font_size.get()),
                            bg=th["btn_settings"], fg=th["btn_settings_fg"],
                            activebackground=th["btn_settings_hover"], activeforeground=th["btn_settings_fg"],
                            relief="flat", bd=0, width=3, height=1, cursor="hand2",
                            command=self._on_settings)
        self._set_btn.pack(side=tk.LEFT, padx=3)
        self._bind_hover(self._set_btn, th["btn_settings"], th["btn_settings_hover"], th["btn_settings_fg"])
        self._add_button_tooltip(self._set_btn, "设置")

        self._pin_btn = tk.Button(self._title_btn_bar, text="📌",
                            font=("Segoe UI Emoji", self._base_font_size.get() + 2),
                            bg=th["btn_lock"], fg=th["btn_lock_fg"],
                            activebackground=th["btn_lock_hover"], activeforeground=th["btn_lock_fg"],
                            relief="flat", bd=0, width=3, height=1, cursor="hand2",
                            command=self._toggle_pin)
        self._pin_btn.pack(side=tk.LEFT, padx=3)
        self._bind_hover(self._pin_btn, th["btn_lock"], th["btn_lock_hover"], th["btn_lock_fg"])
        self._add_button_tooltip(self._pin_btn, "固定窗口")

        # 分隔线
        sep = tk.Frame(self._title_btn_bar, bg=self._lighten(th["bg_header"], 20),
                       width=1, bd=0, highlightthickness=0)
        sep.pack(side=tk.LEFT, fill=tk.Y, padx=6, pady=8)
        self._title_sep = sep

        # 关闭按钮
        self._close_btn = tk.Button(self._title_btn_bar, text="✕",
                            font=("Microsoft YaHei", self._base_font_size.get(), "bold"),
                            bg=th["danger"], fg="white",
                            activebackground=self._lighten(th["danger"], -20),
                            activeforeground="white",
                            relief="flat", bd=0, width=3, height=1, cursor="hand2",
                            command=self._on_quit)
        self._close_btn.pack(side=tk.LEFT, padx=3)
        self._bind_hover(self._close_btn, th["danger"], self._lighten(th["danger"], -20))
        self._add_button_tooltip(self._close_btn, "退出程序")

    def _add_button_tooltip(self, widget, text):
        """为标题栏按钮添加悬停提示"""
        tip = [None]
        def _show(event):
            if tip[0] is not None:
                return
            tw = tk.Toplevel(widget)
            tw.wm_overrideredirect(True)
            tw.wm_geometry(f"+{event.x_root + 12}+{event.y_root + 18}")
            lb = tk.Label(tw, text=text, font=("Microsoft YaHei", 9),
                          bg="#333355", fg="#EEEEFF",
                          relief="flat", bd=0, padx=8, pady=3)
            lb.pack()
            tip[0] = tw
        def _hide(event):
            if tip[0] is not None:
                tip[0].destroy()
                tip[0] = None
        widget.bind("<Enter>", _show, add="+")
        widget.bind("<Leave>", _hide, add="+")

    # ================================================================
    #  标题栏主题刷新
    # ================================================================

    def _retitle_bar(self):
        """根据当前主题/字体刷新自绘标题栏所有部件的颜色和字号"""
        th = self.theme
        fs = self._base_font_size.get()
        f_title = ("Microsoft YaHei", fs + 2, "bold")
        f_btn   = ("Microsoft YaHei", fs, "bold")
        f_norm  = ("Microsoft YaHei", fs)
        f_emoji = ("Segoe UI Emoji", fs + 2)

        self._title_bar.configure(bg=th["bg_header"])
        self._title_label.configure(bg=th["bg_header"], fg=th["text_header"], font=f_title)
        self._title_btn_bar.configure(bg=th["bg_header"])
        self._title_sep.configure(bg=self._lighten(th["bg_header"], 20))

        self._add_btn._h = (th["btn_add"], th["btn_add_hover"], th["btn_add_fg"])
        self._add_btn.configure(bg=th["btn_add"], fg=th["btn_add_fg"], font=f_btn,
                                 activebackground=th["btn_add_hover"], activeforeground=th["btn_add_fg"])

        self._set_btn._h = (th["btn_settings"], th["btn_settings_hover"], th["btn_settings_fg"])
        self._set_btn.configure(bg=th["btn_settings"], fg=th["btn_settings_fg"], font=f_norm,
                                 activebackground=th["btn_settings_hover"], activeforeground=th["btn_settings_fg"])

        if not self._pinned:
            self._pin_btn._h = (th["btn_lock"], th["btn_lock_hover"], th["btn_lock_fg"])
            self._pin_btn.configure(bg=th["btn_lock"], fg=th["btn_lock_fg"],
                                     activebackground=th["btn_lock_hover"], activeforeground=th["btn_lock_fg"])
        else:
            self._pin_btn._h = (th["btn_lock_active"], th["btn_lock_active_hover"], th["btn_lock_fg"])
            self._pin_btn.configure(bg=th["btn_lock_active"], fg=th["btn_lock_fg"],
                                     activebackground=th["btn_lock_active_hover"], activeforeground=th["btn_lock_fg"])
        self._pin_btn.configure(font=f_emoji)

        self._close_btn._h = (th["danger"], self._lighten(th["danger"], -20), "white")
        self._close_btn.configure(bg=th["danger"], font=f_btn,
                                   activebackground=self._lighten(th["danger"], -20))

    # ================================================================
    #  标题栏拖动
    # ================================================================

    def _drag_start(self, event):
        # 按在按钮上不启动拖动
        if self._pinned or isinstance(event.widget, tk.Button):
            return
        self._drag_x = event.x_root - self.root.winfo_x()
        self._drag_y = event.y_root - self.root.winfo_y()

    def _drag_do(self, event):
        if self._pinned or self._drag_x is None:
            return
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        self.root.geometry(f"+{x}+{y}")

    def _drag_stop(self, event):
        self._drag_x = 0
        self._drag_y = 0
        self._save_window_position()

    # ================================================================
    #  图钉：固定窗口位置和大小
    # ================================================================

    def _toggle_pin(self):
        self._pinned = not self._pinned
        if self._pinned:
            for fr in self._resize_frames.values():
                fr.place_forget()
        else:
            self._rebuild_resize_frames()
        self._retitle_bar()

    def _rebuild_resize_frames(self):
        """重新放置所有缩放边条和角块"""
        cw = self._resize_corner
        corners = [
            ("tl", 0,   0,   0,  0),
            ("tr", 1.0, 0,  -cw, 0),
            ("bl", 0,   1.0, 0, -cw),
            ("br", 1.0, 1.0, -cw, -cw),
        ]
        for key, rx, ry, ox, oy in corners:
            fr = self._resize_frames.get(key)
            if fr is not None:
                fr.place(relx=rx, rely=ry, x=ox, y=oy, width=cw, height=cw)

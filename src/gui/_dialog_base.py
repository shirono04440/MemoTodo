"""对话框基础组件 Mixin — 滚动容器、卡片模板、小按钮"""

import tkinter as tk


class DialogBaseMixin:
    """对话框复用组件：可滚动画布容器、模块卡片、小按钮"""

    def _make_scroll_inner(self, parent):
        """创建带滚轮的 Canvas 容器（无滚动条），返回 (canvas, inner_frame, cleanup_fn)"""
        th = self.theme
        outer = tk.Frame(parent, bg=th["bg_primary"])
        outer.pack(fill=tk.BOTH, expand=True, padx=0, pady=(0, 4))
        cv = tk.Canvas(outer, bg=th["bg_primary"], highlightthickness=0)
        cv.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        def _on_enter(e):
            cv.bind_all("<MouseWheel>",
                lambda ev: cv.yview_scroll(int(-1 * (ev.delta / 120)), "units"))
        def _on_leave(e):
            cv.unbind_all("<MouseWheel>")
        cv.bind("<Enter>", _on_enter)
        cv.bind("<Leave>", _on_leave)

        inner = tk.Frame(cv, bg=th["bg_primary"])
        cw_id = cv.create_window((0, 0), window=inner, anchor="nw", tags="cw")
        inner.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.bind("<Configure>", lambda e: cv.itemconfig(cw_id, width=e.width))

        def _cleanup():
            cv.unbind_all("<MouseWheel>")
        return cv, inner, _cleanup

    def _make_module_card(self, parent, title, emoji):
        """统一风格的模块卡片，返回内容容器 Frame"""
        th = self.theme
        fs = self._base_font_size.get()
        card = tk.Frame(parent, bg=th["bg_card"], bd=0, highlightthickness=0)
        card.pack(fill=tk.X, padx=16, pady=(0, 12))
        hdr = tk.Frame(card, bg=th["bg_card"])
        hdr.pack(fill=tk.X, padx=16, pady=(14, 6))
        tk.Label(hdr, text=f"{emoji}  {title}",
                 font=("Microsoft YaHei", fs, "bold"),
                 bg=th["bg_card"], fg=th["text_primary"]).pack(side=tk.LEFT)
        return card

    def _make_small_btn(self, parent, text, bg_color, hover_color, cmd, **kw):
        """统一风格的小按钮，自动绑定 hover"""
        fs = self._base_font_size.get()
        side = kw.pop("side", tk.LEFT)
        fg = kw.pop("fg", "white")
        btn = tk.Button(parent, text=text, font=("Microsoft YaHei", max(8, fs - 1)),
                        bg=bg_color, fg=fg,
                        activebackground=hover_color, activeforeground=fg,
                        relief="flat", bd=0, padx=12, pady=4, cursor="hand2",
                        command=cmd)
        btn.pack(side=side, padx=3)
        self._bind_hover(btn, bg_color, hover_color, fg=fg)
        return btn

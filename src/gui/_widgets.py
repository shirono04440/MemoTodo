"""圆角控件 — 用 Canvas 自绘圆角矩形背景的卡片容器。

tkinter 原生 Frame/Button/Entry 都是直角，无法直接圆角。
这里用 Canvas 画圆角矩形作为背景，内容放进 inner Frame（一个 canvas window），
四个角露出父容器背景色，形成圆角效果。

尺寸同步采用与 _list.py 滚动容器一致的机制：
inner 作为 canvas window，宽度由 canvas 约束（fill 撑满减圆角），
高度由 inner 内容自动撑开，<Configure> 回调里反推 canvas 高度。
"""

import tkinter as tk


def round_rect_points(x1, y1, x2, y2, r):
    """返回圆角矩形的多边形顶点（配合 smooth=True 使用）"""
    r = max(0, min(r, (x2 - x1) // 2, (y2 - y1) // 2))
    return [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
    ]


class RoundedCard(tk.Canvas):
    """圆角卡片容器。内容放在 `self.inner`（bg=卡片色的普通 Frame）里。

    参数：
        bg:       卡片背景色
        outer_bg: 父容器背景色（四角露出该颜色）
        radius:   圆角半径（像素）
    """

    def __init__(self, parent, bg, outer_bg, radius=12, outline="", outline_width=0, **kw):
        super().__init__(parent, bg=outer_bg, bd=0, highlightthickness=0, **kw)
        self._card_bg = bg
        self._radius = radius
        self._outline = outline
        self._outline_width = outline_width

        self.inner = tk.Frame(self, bg=bg, bd=0, highlightthickness=0)
        self._win = self.create_window(radius, radius, window=self.inner, anchor="nw")

        self.inner.bind("<Configure>", self._on_inner_config)
        self.bind("<Configure>", self._on_canvas_config)

    # ---- 尺寸同步 ----
    def _on_inner_config(self, _e=None):
        r = self._radius
        ih = max(self.inner.winfo_height(), 1)
        self.configure(height=ih + 2 * r)
        self._redraw()

    def _on_canvas_config(self, _e=None):
        w = max(self.winfo_width(), 1)
        r = self._radius
        self.itemconfig(self._win, width=max(w - 2 * r, 1))
        self._redraw()

    # ---- 绘制 ----
    def _redraw(self):
        self.delete("bg")
        w = max(self.winfo_width(), 2)
        h = max(self.winfo_height(), 2)
        pts = round_rect_points(0, 0, w - 1, h - 1, self._radius)
        kw = dict(fill=self._card_bg)
        if self._outline:
            kw["outline"] = self._outline
            kw["width"] = self._outline_width
        self.create_polygon(pts, smooth=True, tags="bg", **kw)

    # ---- 换色（hover）----
    def set_bg(self, color):
        old = self._card_bg
        self._card_bg = color
        self._set_widget_bg(self.inner, old, color)
        self._redraw()

    def _set_widget_bg(self, w, old, new):
        try:
            if w.cget("bg") == old:
                w.configure(bg=new)
        except tk.TclError:
            pass
        for ch in w.winfo_children():
            self._set_widget_bg(ch, old, new)

"""工具方法 Mixin — 颜色、窗口、hover 绑定、基础操作"""

import os
import subprocess
import tkinter as tk
from tkinter import messagebox
from datetime import datetime

from database import update_opened_status, delete_item


class UtilsMixin:
    """颜色工具、窗口位置、hover 绑定、启动/删除/切换状态"""

    def _lighten(self, hex_color, amount):
        r = int(hex_color[1:3], 16) + amount
        g = int(hex_color[3:5], 16) + amount
        b = int(hex_color[5:7], 16) + amount
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        return f"#{r:02x}{g:02x}{b:02x}"

    def _clamp_to_screen(self, w, h, x, y, margin=20):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = max(margin, min(x, sw - w - margin))
        y = max(margin, min(y, sh - h - margin))
        return w, h, x, y

    def _bind_hover(self, widget, normal_bg, hover_bg, fg=None):
        """绑定 hover 颜色变化，并将色值存到 widget._h 供 _retitle_bar 更新"""
        widget._h = (normal_bg, hover_bg, fg)
        def on_enter(e):
            w = e.widget
            nh, hh, f = w._h
            w.configure(bg=hh)
            if f is not None: w.configure(fg=f)
        def on_leave(e):
            w = e.widget
            nh, hh, f = w._h
            w.configure(bg=nh)
            if f is not None: w.configure(fg=f)
        widget.bind("<Enter>", on_enter, add="+")
        widget.bind("<Leave>", on_leave, add="+")

    def _bind_fg_hover(self, widget, normal_fg, hover_fg):
        widget._fh = (normal_fg, hover_fg)
        def on_enter(e):
            e.widget.configure(fg=e.widget._fh[1])
        def on_leave(e):
            e.widget.configure(fg=e.widget._fh[0])
        widget.bind("<Enter>", on_enter, add="+")
        widget.bind("<Leave>", on_leave, add="+")

    # ================================================================
    #  操作
    # ================================================================

    def _on_launch(self, exe_path):
        if not os.path.exists(exe_path):
            messagebox.showerror("错误", f"文件不存在:\n{exe_path}")
            return
        try:
            subprocess.Popen(exe_path, shell=False,
                             cwd=os.path.dirname(exe_path))
        except Exception as e:
            messagebox.showerror("启动失败", f"无法启动:\n{exe_path}\n\n错误: {e}")

    def _on_delete(self, item_id):
        if messagebox.askyesno("确认删除", "确定要删除这个备忘事项吗？"):
            delete_item(item_id)
            self._refresh_list()

    def _toggle_status(self, item_id, current_is_open):
        new_val = 0 if current_is_open else 1
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        update_opened_status(item_id, opened_at=now_str, opened_today=new_val)
        self._refresh_list()

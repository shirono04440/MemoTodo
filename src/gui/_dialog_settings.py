"""对话框 Mixin — 设置"""

import tkinter as tk
from tkinter import filedialog

from settings import save_settings
from autostart import set_autostart


class DialogSettingsMixin:
    """设置对话框：主题、字体、图标、背景图、窗口参数"""

    def _on_settings(self):
        th = self.theme
        dialog = tk.Toplevel(self.root)
        dialog.title("二游日常表 - 设置")
        dialog.configure(bg=th["bg_primary"])
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        w, h = 440, 480
        x = self.root.winfo_x() + 80
        y = self.root.winfo_y() + 20
        w, h, x, y = self._clamp_to_screen(w, h, x, y)
        dialog.geometry(f"{w}x{h}+{x}+{y}")

        btn_frame = tk.Frame(dialog, bg=th["bg_primary"])
        btn_frame.pack(fill=tk.X, padx=16, pady=(8, 14), side=tk.BOTTOM)

        _vars = {}

        def apply():
            c = {"theme": _vars["theme"].get(),
                 "font_size": _vars["font"].get(), "icon_size": _vars["icon"].get(),
                 "window_width": _vars["ww"].get(), "window_height": _vars["wh"].get(),
                 "bg_image_path": _vars["bg"].get().strip(),
                 "bg_image_opacity": _vars["op"].get(),
                 "window_opacity": _vars["wo"].get(), "window_on_top": _vars["ot"].get(),
                 "auto_start": _vars["auto_start"].get()}
            save_settings(c)
            set_autostart(bool(c["auto_start"]))
            self.config.update(c)
            self._make_fonts()
            self._retitle_bar()
            self._apply_window_geometry(); self._apply_window_opacity(); self._apply_window_on_top()

            # 仅当影响卡片渲染的设置变化时才重建列表
            new_visual = f"{c['theme']}|{c['font_size']}|{c['icon_size']}|{c['bg_image_path']}|{c['bg_image_opacity']}"
            if new_visual != self._last_visual:
                self._last_visual = new_visual
                self._refresh_list()
            else:
                # 仅更新容器 bg（不影响卡片内容）
                self.root.configure(bg=self.theme["bg_primary"])
                self._update_summary()

            dialog.destroy()

        save = tk.Button(btn_frame, text="✔ 保存", font=("Microsoft YaHei", 12, "bold"),
                         bg=th["accent"], fg="white", activebackground=self._lighten(th["accent"], 20),
                         activeforeground="white", relief="flat", bd=0, padx=22, pady=6, cursor="hand2",
                         command=apply)
        save.pack(side=tk.RIGHT, padx=4)
        self._bind_hover(save, th["accent"], self._lighten(th["accent"], 20))
        cancel = tk.Button(btn_frame, text="取消", font=("Microsoft YaHei", 11),
                           bg=th["bg_primary"], fg=th["text_muted"], relief="flat", bd=0,
                           padx=22, pady=6, cursor="hand2",
                           command=lambda: _close_dialog())
        cancel.pack(side=tk.RIGHT, padx=4)
        self._bind_fg_hover(cancel, th["text_muted"], th["text_primary"])

        tk.Label(dialog, text="设置", font=("Microsoft YaHei", 15, "bold"),
                 bg=th["bg_primary"], fg=th["text_primary"]).pack(pady=(18, 6))

        cv, inner, _wheel_cleanup = self._make_scroll_inner(dialog)

        def _close_dialog():
            _wheel_cleanup()
            dialog.destroy()

        dialog.protocol("WM_DELETE_WINDOW", _close_dialog)
        save.configure(command=lambda: (apply(), _close_dialog()))
        cancel.configure(command=_close_dialog)

        def sec(title):
            tk.Label(inner, text=title, font=("Microsoft YaHei", 11, "bold"),
                     bg=th["bg_primary"], fg=th["text_primary"], anchor="w"
                     ).pack(fill=tk.X, padx=4, pady=(10, 0))

        def row_slider(label, var, lo, hi, step=1, fmt=None):
            r = tk.Frame(inner, bg=th["bg_primary"])
            r.pack(fill=tk.X, padx=8, pady=4)
            tk.Label(r, text=label, font=("Microsoft YaHei", 11),
                     bg=th["bg_primary"], fg=th["text_secondary"], width=5, anchor="e"
                     ).pack(side=tk.LEFT, padx=(8, 8))
            e = tk.Entry(r, textvariable=var, font=("Microsoft YaHei", 11),
                         width=6, justify="center", bd=0, highlightthickness=0,
                         bg=th["bg_card"], fg=th["text_entry"],
                         insertbackground=th["text_entry"])
            e.pack(side=tk.LEFT, padx=(0, 8))
            cw, ch = 180, 22
            cv2 = tk.Canvas(r, width=cw, height=ch,
                           bg=th["bg_primary"], highlightthickness=0, bd=0)
            cv2.pack(side=tk.LEFT, padx=(0, 4))
            lx, ly, lx2 = 8, ch // 2, cw - 8
            cv2.create_line(lx, ly, lx2, ly, fill=th["bg_card"], width=4, tags="track")
            dot_r = 7
            dot = cv2.create_oval(0, 0, dot_r * 2, dot_r * 2,
                                 fill=th["accent"], outline=th["accent"], tags="dot")
            fill_line = cv2.create_line(0, 0, 0, 0, fill=th["accent"], width=4, tags="fill")

            def _val_to_x(v):
                frac = (v - lo) / (hi - lo) if hi != lo else 0
                return lx + frac * (lx2 - lx)

            def _pos_to_val(x, snap=False):
                frac = max(0, min(1, (x - lx) / (lx2 - lx)))
                v = lo + frac * (hi - lo)
                if snap: v = round(v / step) * step
                return max(lo, min(hi, v))

            def _redraw(v):
                x = _val_to_x(v)
                cv2.coords(dot, x - dot_r, ly - dot_r, x + dot_r, ly + dot_r)
                cv2.coords(fill_line, lx, ly, x, ly)

            _dragging = False
            def _start_drag(event):
                nonlocal _dragging
                _dragging = True
                _redraw(_pos_to_val(event.x))
            def _stop_drag(event):
                nonlocal _dragging
                _dragging = False
                v = _pos_to_val(event.x, snap=True)
                var.set(int(v) if isinstance(lo, int) and step >= 1 else round(v, 2))
            def _on_motion(event):
                if _dragging:
                    _redraw(_pos_to_val(event.x))
            def _on_click(event):
                v = _pos_to_val(event.x, snap=True)
                var.set(int(v) if isinstance(lo, int) and step >= 1 else round(v, 2))

            cv2.tag_bind("dot", "<Button-1>", _start_drag)
            cv2.bind("<B1-Motion>", _on_motion)
            cv2.bind("<ButtonRelease-1>", _stop_drag)
            cv2.tag_bind("track", "<Button-1>", _on_click)
            cv2.tag_bind("fill", "<Button-1>", _on_click)
            _redraw(var.get())
            var.trace_add("write", lambda *a: _redraw(var.get()))
            if fmt:
                l = tk.Label(r, text=fmt.format(var.get()), font=("Microsoft YaHei", 10),
                             bg=th["bg_primary"], fg=th["text_muted"], width=5, anchor="w")
                l.pack(side=tk.LEFT)
                def _upd(*a, ll=l, ff=fmt, vv=var):
                    try: ll.config(text=ff.format(vv.get()))
                    except Exception: pass
                var.trace_add("write", _upd)
            return r

        sec("🎨 主题")
        _vars["theme"] = tk.StringVar(value=self.config.get("theme", "light"))
        fr = tk.Frame(inner, bg=th["bg_primary"])
        fr.pack(fill=tk.X, padx=8, pady=4)
        tk.Radiobutton(fr, text="☀️ 亮色", variable=_vars["theme"], value="light",
            font=("Microsoft YaHei", 11), bg=th["bg_primary"], fg=th["text_primary"],
            activebackground=th["bg_primary"], selectcolor=th["bg_primary"]
        ).pack(side=tk.LEFT, padx=(72, 14))
        tk.Radiobutton(fr, text="🌙 暗色", variable=_vars["theme"], value="dark",
            font=("Microsoft YaHei", 11), bg=th["bg_primary"], fg=th["text_primary"],
            activebackground=th["bg_primary"], selectcolor=th["bg_primary"]
        ).pack(side=tk.LEFT)

        sec("📐 外观")
        _vars["font"] = tk.IntVar(value=self.config["font_size"])
        row_slider("字体", _vars["font"], 8, 24)
        _vars["icon"] = tk.IntVar(value=self.config.get("icon_size", 48))
        row_slider("图标", _vars["icon"], 24, 96)

        _vars["bg"] = tk.StringVar(value=self.config.get("bg_image_path", ""))
        br = tk.Frame(inner, bg=th["bg_primary"])
        br.pack(fill=tk.X, padx=8, pady=4)
        tk.Label(br, text="背景图:", font=("Microsoft YaHei", 11),
                 bg=th["bg_primary"], fg=th["text_muted"], width=5, anchor="e").pack(side=tk.LEFT, padx=(8, 12))
        ee = tk.Entry(br, textvariable=_vars["bg"], font=("Microsoft YaHei", 9),
                     width=20, bd=0, relief="flat", bg=th["bg_card"], fg=th["text_entry"])
        ee.pack(side=tk.LEFT, padx=(0, 4))
        def pick_img():
            p = filedialog.askopenfilename(title="选择背景图片",
                filetypes=[("图片文件", "*.png;*.jpg;*.jpeg;*.bmp;*.gif"), ("所有文件", "*.*")])
            if p: _vars["bg"].set(p)
        tk.Button(br, text="…", font=("Microsoft YaHei", 9, "bold"),
                  bg=th["btn_outline_bg"], fg=th["btn_outline_fg"], relief="flat", bd=0,
                  padx=6, pady=1, cursor="hand2", command=pick_img).pack(side=tk.LEFT)

        _vars["op"] = tk.IntVar(value=self.config.get("bg_image_opacity", 70))
        row_slider("不透明", _vars["op"], 10, 100, step=5, fmt="{}%")

        sec("🪟 窗口")
        _vars["ww"] = tk.IntVar(value=self.config["window_width"])
        row_slider("宽度", _vars["ww"], 400, 1400)
        _vars["wh"] = tk.IntVar(value=self.config["window_height"])
        row_slider("高度", _vars["wh"], 300, 1000)
        _vars["wo"] = tk.DoubleVar(value=self.config.get("window_opacity", 1.0))
        row_slider("透明度", _vars["wo"], 0.3, 1.0, step=0.05, fmt="{:.0%}")
        _vars["ot"] = tk.IntVar(value=self.config.get("window_on_top", 0))
        fr2 = tk.Frame(inner, bg=th["bg_primary"])
        fr2.pack(fill=tk.X, padx=8, pady=4)
        tk.Label(fr2, text="置顶:", font=("Microsoft YaHei", 11), bg=th["bg_primary"],
                 fg=th["text_muted"], width=5, anchor="e").pack(side=tk.LEFT, padx=(8, 12))
        tk.Checkbutton(fr2, text="始终在最前", variable=_vars["ot"],
            font=("Microsoft YaHei", 10), bg=th["bg_primary"], activebackground=th["bg_primary"],
            selectcolor=th["bg_primary"], fg=th["text_primary"]).pack(side=tk.LEFT)

        sec("🚀 启动")
        _vars["auto_start"] = tk.IntVar(value=self.config.get("auto_start", 0))
        fr3 = tk.Frame(inner, bg=th["bg_primary"])
        fr3.pack(fill=tk.X, padx=8, pady=4)
        tk.Label(fr3, text="自启动:", font=("Microsoft YaHei", 11), bg=th["bg_primary"],
                 fg=th["text_muted"], width=5, anchor="e").pack(side=tk.LEFT, padx=(8, 12))
        tk.Checkbutton(fr3, text="开机自动启动", variable=_vars["auto_start"],
            font=("Microsoft YaHei", 10), bg=th["bg_primary"], activebackground=th["bg_primary"],
            selectcolor=th["bg_primary"], fg=th["text_primary"]).pack(side=tk.LEFT)

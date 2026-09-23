"""缩放抓手 + 背景图渲染 Mixin"""

import os
import sys
import ctypes
import tkinter as tk

from PIL import Image, ImageTk

from settings import save_settings


class ResizeMixin:
    """8 方向缩放抓手、背景图渲染与视口绑定"""

    # ================================================================
    #  右下角缩放抓手
    # ================================================================

    def _build_resize_grip(self):
        """8 个可拖动边框 + 4 角抓手，允许从任意方向缩放窗口"""
        self._resize_edge_w = 4
        self._resize_corner = 8

        # 方向 → (cursor, dx_sgn, dy_sgn)
        zones = {
            "top":    ("top_side",           0, -1),
            "bottom": ("bottom_side",        0,  1),
            "left":   ("left_side",         -1,  0),
            "right":  ("right_side",         1,  0),
            "tl":     ("top_left_corner",   -1, -1),
            "tr":     ("top_right_corner",   1, -1),
            "bl":     ("bottom_left_corner",-1,  1),
            "br":     ("bottom_right_corner",1,  1),
        }

        self._resize_frames = {}
        self._resize_dir = (0, 0)
        self._resize_active = False
        self._resize_zones = zones

        # 四边条：用绝对坐标，由 _sync_resize_edges 随窗口尺寸刷新
        ew, cw = self._resize_edge_w, self._resize_corner
        for key in ("top", "bottom", "left", "right"):
            fr = tk.Frame(self.root, bg="", bd=0, highlightthickness=0,
                          cursor=zones[key][0])
            fr.place(x=0, y=0)
            self._resize_frames[key] = fr

        # 四角
        corners = [
            ("tl", 0,   0,   0,  0),
            ("tr", 1.0, 0,  -cw, 0),
            ("bl", 0,   1.0, 0, -cw),
            ("br", 1.0, 1.0, -cw, -cw),
        ]
        for key, rx, ry, ox, oy in corners:
            fr = tk.Frame(self.root, bg="", bd=0, highlightthickness=0,
                          cursor=zones[key][0])
            fr.place(relx=rx, rely=ry, x=ox, y=oy, width=cw, height=cw)
            self._resize_frames[key] = fr

        # 统一绑定事件
        for key, fr in self._resize_frames.items():
            _, dx, dy = zones[key]
            fr.bind("<Button-1>",
                    lambda e, ddx=dx, ddy=dy: self._edge_start(e, ddx, ddy))
            fr.bind("<B1-Motion>", self._edge_move)
            fr.bind("<ButtonRelease-1>", self._edge_stop)

        self._resize_active = False
        self._sync_resize_edges()
        # 窗口尺寸变化时重算边条位置
        self.root.bind("<Configure>", lambda e: self._sync_resize_edges(), add="+")

    def _sync_resize_edges(self, *_):
        """根据窗口当前尺寸重新放置四边条"""
        try:
            ww = self.root.winfo_width()
            wh = self.root.winfo_height()
        except tk.TclError:
            return
        ew = self._resize_edge_w
        cw = self._resize_corner
        fr = self._resize_frames.get("top")
        if fr: fr.place(x=cw, y=0, width=ww - 2*cw, height=ew)
        fr = self._resize_frames.get("bottom")
        if fr: fr.place(x=cw, y=wh - ew, width=ww - 2*cw, height=ew)
        fr = self._resize_frames.get("left")
        if fr: fr.place(x=0, y=cw, width=ew, height=wh - 2*cw)
        fr = self._resize_frames.get("right")
        if fr: fr.place(x=ww - ew, y=cw, width=ew, height=wh - 2*cw)

        self._apply_rounded_corners()

    # ================================================================
    #  圆角窗口（Windows）
    # ================================================================

    def _apply_rounded_corners(self):
        """用 SetWindowRgn 把无边框窗口裁成圆角矩形（仅 Windows）"""
        if sys.platform != "win32":
            return
        try:
            user32 = ctypes.windll.user32
            gdi32 = ctypes.windll.gdi32
            user32.GetParent.restype = ctypes.c_void_p
            user32.GetParent.argtypes = [ctypes.c_void_p]
            gdi32.CreateRoundRectRgn.restype = ctypes.c_void_p
            user32.SetWindowRgn.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_bool]

            # overrideredirect 下 winfo_id 是子窗口，真正的顶层是它的父窗口
            hwnd = user32.GetParent(self.root.winfo_id())
            if not hwnd:
                hwnd = self.root.winfo_id()

            w = self.root.winfo_width()
            h = self.root.winfo_height()
            if w < 2 or h < 2:
                return

            radius = int(self.config.get("corner_radius", 16))
            r = max(0, min(radius, min(w, h) // 2))
            if r <= 0:
                return
            rgn = gdi32.CreateRoundRectRgn(0, 0, w + 1, h + 1, r * 2, r * 2)
            user32.SetWindowRgn(hwnd, rgn, True)
        except Exception:
            pass

    def _edge_start(self, event, dx, dy):
        if self._pinned:
            return
        self._resize_active = True
        self._resize_dir = (dx, dy)
        self._rz_start = (event.x_root, event.y_root,
                           self.root.winfo_width(), self.root.winfo_height(),
                           self.root.winfo_x(), self.root.winfo_y())

    def _edge_move(self, event):
        if not self._resize_active:
            return
        dx, dy = self._resize_dir
        sx, sy, sw, sh, wx, wy = self._rz_start
        # 屏幕位移
        dd = (event.x_root - sx, event.y_root - sy)
        nw = max(200, sw + dd[0] * dx)
        nh = max(200, sh + dd[1] * dy)
        # 当 dx<0 时左边在移动，同时调整 x
        nx = wx
        if dx < 0:
            nx = wx + dd[0]
            # 限制最小宽度
            if nw == 200:
                nx = wx + sw - 200
        if dy < 0:
            ny = wy + dd[1]
            if nh == 200:
                ny = wy + sh - 200
        else:
            ny = wy
        self.root.geometry(f"{nw}x{nh}+{nx}+{ny}")

    def _edge_stop(self, event):
        self._resize_active = False
        self._resize_dir = (0, 0)
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        self.config["window_width"] = w
        self.config["window_height"] = h
        save_settings(self.config)
        self._save_window_position()
        self._refresh_list()

    # ================================================================
    #  背景渲染
    # ================================================================

    def _render_bg_on_canvas(self):
        th = self.theme
        color = th["bg_primary"]
        self._bg_photo = None
        self.root.configure(bg=color)
        self.list_container.configure(bg=color)
        self.canvas.configure(bg=color)
        # 同步更新容器背景色（主题切换时需要）
        if hasattr(self, '_inner_frame') and self._inner_frame.winfo_exists():
            self._inner_frame.configure(bg=color)
        if hasattr(self, 'summary_bar') and self.summary_bar.winfo_exists():
            self.summary_bar.configure(bg=color)
            self.summary_label.configure(bg=color, fg=th["text_muted"])

        img_path = self.config.get("bg_image_path", "")
        if not img_path or not os.path.exists(img_path):
            return
        try:
            cw = max(self.canvas.winfo_width(),
                     self.list_container.winfo_width(),
                     self.config.get("window_width", 800) - 60)
            ch = max(self.canvas.winfo_height(),
                     self.list_container.winfo_height(),
                     self.config.get("window_height", 600) - 100)
            if cw < 20 or ch < 20:
                return
            opacity = int(self.config.get("bg_image_opacity", 70))
            pil = Image.open(img_path).convert("RGBA")
            iw, ih = pil.size
            scale = max(cw / iw, ch / ih)
            nw, nh = int(iw * scale), int(ih * scale)
            pil = pil.resize((nw, nh), Image.LANCZOS)
            left, top = (nw - cw) // 2, (nh - ch) // 2
            pil = pil.crop((left, top, left + cw, top + ch))
            alpha = int(255 * (100 - opacity) / 100)
            overlay = Image.new('RGBA', pil.size, (255, 255, 255, alpha))
            blended = Image.alpha_composite(pil, overlay).convert("RGB")
            self._bg_photo = ImageTk.PhotoImage(blended)
            self.canvas.create_image(0, 0, image=self._bg_photo, anchor="nw", tags="bg")
        except Exception:
            pass

    def _pin_bg_to_viewport(self):
        y = self.canvas.canvasy(0)
        for iid in self.canvas.find_withtag("bg"):
            try:
                self.canvas.coords(iid, 0, y)
            except tk.TclError:
                pass

    def _apply_background_bind(self):
        self._resize_after_id = None

        def on_root_resize(event):
            if event.widget != self.root:
                return
            if self._resize_after_id:
                self.root.after_cancel(self._resize_after_id)
            self._resize_after_id = self.root.after(400, self._on_window_resized)

        self.root.bind("<Configure>", on_root_resize, add="+")

    def _on_window_resized(self):
        self._resize_after_id = None
        if self._pinned:
            return
        self._refresh_list()

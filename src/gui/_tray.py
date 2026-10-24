"""系统托盘 Mixin — 最小化到托盘，右键菜单退出"""

import os
import sys
import threading
import time
import traceback
import tkinter as tk

import win32gui
import win32con
import win32api

from PIL import Image, ImageDraw


class TrayMixin:
    """系统托盘：图标 + 左键显示/隐藏 + 右键菜单"""

    _WM_TRAY = win32con.WM_USER + 100

    # ================================================================
    #  启动托盘
    # ================================================================

    def _setup_tray(self):
        """在后台线程启动托盘图标和消息循环"""
        self._tray_running = True
        self._tray_icon_added = False
        self._tray_thread = threading.Thread(
            target=self.__tray_thread_run, daemon=True
        )
        self._tray_thread.start()

    # ================================================================
    #  后台线程
    # ================================================================

    def __tray_thread_run(self):
        """注册窗口类 → 创建隐藏窗口 → 添加图标 → 消息循环"""
        try:
            hinst = win32api.GetModuleHandle(None)

            wc = win32gui.WNDCLASS()
            wc.lpfnWndProc = self.__tray_wnd_proc
            wc.lpszClassName = "MemoTodoTrayClass"
            wc.hInstance = hinst
            class_atom = win32gui.RegisterClass(wc)

            self._tray_hwnd = win32gui.CreateWindow(
                class_atom, "MemoTodoTray", 0,
                0, 0, 0, 0, 0, 0,
                hinst, None
            )

            self.__add_tray_icon()

            while self._tray_running:
                win32gui.PumpWaitingMessages()
                # 没有消息时让出 CPU。原先这里是无睡眠的忙轮询，
                # 空闲时也会占满一个 CPU 核心。
                time.sleep(0.05)

            self.__remove_tray_icon()
            win32gui.DestroyWindow(self._tray_hwnd)
        except Exception:
            traceback.print_exc()

    # ================================================================
    #  窗口消息处理
    # ================================================================

    def __tray_wnd_proc(self, hwnd, msg, wparam, lparam):
        if msg == self._WM_TRAY:
            if lparam == win32con.WM_LBUTTONUP:
                self.root.after(0, self._toggle_window_visibility)
            elif lparam == win32con.WM_RBUTTONUP:
                self.__show_popup_menu()
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    # ================================================================
    #  托盘图标
    # ================================================================

    def __add_tray_icon(self):
        try:
            hicon = self.__make_tray_icon()
            # flat tuple: (hWnd, uID, uFlags, uCallbackMessage, hIcon, szTip)
            nid = (
                self._tray_hwnd,
                1,
                win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP,
                self._WM_TRAY,
                hicon,
                "日程表",
            )
            win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, nid)
            self._tray_icon_added = True
        except Exception:
            traceback.print_exc()

    def __remove_tray_icon(self):
        if self._tray_icon_added:
            nid = (self._tray_hwnd, 1)
            win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
            self._tray_icon_added = False

    def __make_tray_icon(self):
        """生成 32×32 托盘图标。优先用 test_icon.png，失败则绘制默认图标"""
        if getattr(sys, 'frozen', False):
            base = sys._MEIPASS
        else:
            base = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
        icon_path = os.path.normpath(os.path.join(base, "assets", "test_icon.png"))

        try:
            if os.path.exists(icon_path):
                img = Image.open(icon_path).convert("RGBA").resize((32, 32), Image.LANCZOS)
            else:
                raise FileNotFoundError("no icon file")
        except Exception:
            # 绘制默认图标：蓝紫圆底 + 白色对勾
            img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.rounded_rectangle([1, 1, 30, 30], radius=6,
                                   fill=(63, 54, 151, 255))  # 蓝紫色
            draw.line([10, 16, 14, 21, 22, 10], fill="white", width=3)

        return self.__pil_to_hicon(img)

    @staticmethod
    def __pil_to_hicon(img):
        """PIL RGBA Image → Windows HICON（纯 win32gui GDI，不依赖 MFC）"""
        from PIL import ImageWin

        w, h = img.size

        hdc_screen = win32gui.GetDC(0)
        mem_dc = win32gui.CreateCompatibleDC(hdc_screen)

        # 颜色位图
        color_bmp = win32gui.CreateCompatibleBitmap(hdc_screen, w, h)
        old_bmp = win32gui.SelectObject(mem_dc, color_bmp)

        dib = ImageWin.Dib(img)
        dib.draw(mem_dc, (0, 0, w, h))

        win32gui.SelectObject(mem_dc, old_bmp)

        # 遮罩位图
        mask_bmp = win32gui.CreateCompatibleBitmap(hdc_screen, w, h)

        # 组合成 ICON
        icon_info = (
            True,              # fIcon
            0, 0,              # xHotspot, yHotspot
            mask_bmp,          # hbmMask
            color_bmp,         # hbmColor
        )
        hicon = win32gui.CreateIconIndirect(icon_info)

        # 清理
        win32gui.DeleteDC(mem_dc)
        win32gui.ReleaseDC(0, hdc_screen)
        win32gui.DeleteObject(color_bmp)
        win32gui.DeleteObject(mask_bmp)

        return hicon

    # ================================================================
    #  右键菜单（Win32 原生弹出菜单）
    # ================================================================

    def __show_popup_menu(self):
        menu = win32gui.CreatePopupMenu()
        win32gui.AppendMenu(menu, win32con.MF_STRING, 1, "显示 / 隐藏")
        win32gui.AppendMenu(menu, win32con.MF_SEPARATOR, 0, "")
        win32gui.AppendMenu(menu, win32con.MF_STRING, 2, "退出")

        x, y = win32gui.GetCursorPos()
        # 必须在 TrackPopupMenu 前让窗口置前，否则菜单不会自动消失
        win32gui.SetForegroundWindow(self._tray_hwnd)
        cmd = win32gui.TrackPopupMenu(
            menu, win32con.TPM_RETURNCMD | win32con.TPM_NONOTIFY,
            x, y, 0, self._tray_hwnd, None
        )
        win32gui.PostMessage(self._tray_hwnd, win32con.WM_NULL, 0, 0)
        win32gui.DestroyMenu(menu)

        if cmd == 1:
            self.root.after(0, self._toggle_window_visibility)
        elif cmd == 2:
            self.root.after(0, self._on_quit)

    # ================================================================
    #  窗口显隐 & 退出
    # ================================================================

    def _toggle_window_visibility(self):
        try:
            if self.root.state() == "withdrawn":
                self.root.deiconify()
                self.root.lift()
                self.root.focus_force()
            else:
                self._save_window_position()
                self.root.withdraw()
        except tk.TclError:
            pass

    def _on_quit(self):
        """彻底退出"""
        self._save_window_position()
        if self.monitor:
            self.monitor.stop()
        self._tray_running = False
        self.root.destroy()

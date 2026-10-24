"""对话框 Mixin — 添加事项"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox

from database import add_item


class DialogAddMixin:
    """添加事项对话框：名称、exe 路径、图标、注释"""

    def _on_add(self):
        th = self.theme
        dialog = tk.Toplevel(self.root)
        dialog.title("日程表 - 添加事项")
        dialog.configure(bg=th["bg_primary"])
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        w, h = 500, 460
        x = self.root.winfo_x() + 80
        y = self.root.winfo_y() + 60
        w, h, x, y = self._clamp_to_screen(w, h, x, y)
        dialog.geometry(f"{w}x{h}+{x}+{y}")

        fs = self._base_font_size.get()
        btn_frame = tk.Frame(dialog, bg=th["bg_primary"])
        btn_frame.pack(fill=tk.X, padx=16, pady=(8, 14), side=tk.BOTTOM)

        tk.Label(dialog, font=("Microsoft YaHei", fs + 4, "bold"),
                 bg=th["bg_primary"], fg=th["text_primary"]).pack(pady=(20, 10))

        content = tk.Frame(dialog, bg=th["bg_primary"])
        content.pack(fill=tk.BOTH, expand=True, padx=16)
        label_width = 4

        def _entry_row(label, var=None):
            f = tk.Frame(content, bg=th["bg_card"], bd=0, highlightthickness=0)
            f.pack(fill=tk.X, pady=4)
            tk.Label(f, text=label, font=("Microsoft YaHei", fs),
                     bg=th["bg_card"], fg=th["text_muted"], width=label_width, anchor="e").pack(
                side=tk.LEFT, padx=(12, 8), pady=8)
            if var is None:
                var = tk.StringVar(master=dialog)
            e = tk.Entry(f, textvariable=var, font=("Microsoft YaHei", fs),
                         bd=0, highlightthickness=0, bg=th["bg_card"],
                         fg=th["text_entry"], insertbackground=th["text_entry"])
            e.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), pady=8)
            return var, e

        name_var, name_entry = _entry_row("名称")
        name_entry.focus_set()
        path_var, _ = _entry_row("路径")

        browse_row = tk.Frame(content, bg=th["bg_primary"])
        browse_row.pack(fill=tk.X, pady=(0, 6))
        tk.Label(browse_row, text="", font=("Microsoft YaHei", fs),
                 bg=th["bg_primary"], width=label_width, anchor="e").pack(
            side=tk.LEFT, padx=(12, 8))

        def browse():
            p = filedialog.askopenfilename(
                title="选择可执行文件",
                filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")])
            if p:
                path_var.set(p)
                if not name_var.get():
                    name_var.set(os.path.splitext(os.path.basename(p))[0])

        tk.Button(browse_row, text="📂  浏览选择 EXE", font=("Microsoft YaHei", max(8, fs - 1)),
                  bg=th["btn_outline_bg"], fg=th["btn_outline_fg"],
                  activebackground=th["btn_outline_hover"],
                  relief="flat", bd=0, padx=10, pady=3, cursor="hand2",
                  command=browse).pack(side=tk.LEFT)

        icon_var, _ = _entry_row("图标")
        icon_btn_row = tk.Frame(content, bg=th["bg_primary"])
        icon_btn_row.pack(fill=tk.X, pady=(0, 6))
        tk.Label(icon_btn_row, text="", font=("Microsoft YaHei", fs),
                 bg=th["bg_primary"], width=label_width, anchor="e").pack(
            side=tk.LEFT, padx=(12, 8))

        def browse_icon():
            p = filedialog.askopenfilename(
                title="选择图标图片",
                filetypes=[("图片文件", "*.png;*.jpg;*.jpeg;*.ico;*.bmp;*.gif"),
                           ("所有文件", "*.*")])
            if p:
                icon_var.set(p)

        tk.Button(icon_btn_row, text="🖼  选择图标图片", font=("Microsoft YaHei", max(8, fs - 1)),
                  bg=th["btn_outline_bg"], fg=th["btn_outline_fg"],
                  activebackground=th["btn_outline_hover"],
                  relief="flat", bd=0, padx=10, pady=3, cursor="hand2",
                  command=browse_icon).pack(side=tk.LEFT)

        notes_f = tk.Frame(content, bg=th["bg_card"], bd=0, highlightthickness=0)
        notes_f.pack(fill=tk.X, pady=4)
        tk.Label(notes_f, text="注释", font=("Microsoft YaHei", fs),
                 bg=th["bg_card"], fg=th["text_muted"], width=label_width, anchor="e").pack(
            side=tk.LEFT, padx=(12, 8), pady=(8, 0))
        notes_text = tk.Text(notes_f, font=("Microsoft YaHei", fs), wrap=tk.WORD,
                             height=3, bd=0, highlightthickness=0, padx=4, pady=4,
                             bg=th["bg_card"], fg=th["text_entry"],
                             insertbackground=th["text_entry"])
        notes_text.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), pady=6)

        def confirm():
            name = name_var.get().strip()
            exe = path_var.get().strip()
            icon = icon_var.get().strip()
            notes = notes_text.get("1.0", "end-1c").strip()
            if not name: messagebox.showwarning("提示", "请输入名称"); return
            if not exe: messagebox.showwarning("提示", "请选择软件路径"); return
            if not os.path.exists(exe): messagebox.showwarning("提示", "所选文件不存在"); return
            if icon and not os.path.exists(icon): messagebox.showwarning("提示", "所选图标文件不存在"); return
            add_item(name, exe, notes, icon)
            dialog.destroy()
            self._refresh_list()

        add_btn = tk.Button(btn_frame, text="✔ 确认添加", font=("Microsoft YaHei", fs + 1, "bold"),
                  bg=th["accent"], fg="white", activebackground=self._lighten(th["accent"], 20),
                  activeforeground="white",
                  relief="flat", bd=0, padx=22, pady=6, cursor="hand2",
                  command=confirm)
        add_btn.pack(side=tk.RIGHT, padx=4)
        self._bind_hover(add_btn, th["accent"], self._lighten(th["accent"], 20))

        cancel_btn = tk.Button(btn_frame, text="取消", font=("Microsoft YaHei", fs),
                  bg=th["bg_primary"], fg=th["text_muted"],
                  activebackground=th["bg_primary"], activeforeground=th["text_primary"],
                  relief="flat", bd=0, padx=22, pady=6, cursor="hand2",
                  command=dialog.destroy)
        cancel_btn.pack(side=tk.RIGHT, padx=4)
        self._bind_fg_hover(cancel_btn, th["text_muted"], th["text_primary"])

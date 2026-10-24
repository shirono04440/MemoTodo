"""对话框 Mixin — 编辑事项"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import ImageTk

from database import update_item_notes, update_item_icon
from icon_utils import load_custom_icon, extract_icon, make_default_icon, clear_cache


class DialogEditMixin:
    """编辑事项对话框：备注自动保存、图标更换、删除"""

    def _on_edit_item(self, item):
        th = self.theme
        dialog = tk.Toplevel(self.root)
        dialog.title("二游日常表 - 编辑事项")
        dialog.configure(bg=th["bg_primary"])
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        fs = self._base_font_size.get()
        icon_size = self.config.get("icon_size", 48)

        notes_val = item.get("notes") or ""
        notes_rows = max(3, min(6, len(notes_val) // 30 + 3))
        notes_h = notes_rows * (fs + 8) + 80
        icon_h_val = icon_size + 50
        danger_h = 70
        w, h = 480, 200 + notes_h + icon_h_val + danger_h
        h = min(h, self.root.winfo_screenheight() - 80)
        h = max(h, 460)
        x = self.root.winfo_pointerx() - w // 2
        y = self.root.winfo_pointery() - 40
        w, h, x, y = self._clamp_to_screen(w, h, x, y)
        dialog.geometry(f"{w}x{h}+{x}+{y}")

        _edit_icons = {}

        def _load_preview_icon(icon_path):
            if icon_path and os.path.exists(icon_path):
                img = load_custom_icon(icon_path, size=icon_size)
            else:
                img = extract_icon(item["exe_path"], size=icon_size)
            if img is None:
                img = make_default_icon(size=icon_size)
            return ImageTk.PhotoImage(img)

        cv, inner, _wheel_cleanup = self._make_scroll_inner(dialog)

        def _cleanup():
            _wheel_cleanup()
            dialog.destroy()
            self._refresh_list()

        dialog.protocol("WM_DELETE_WINDOW", _cleanup)

        tk.Label(dialog, text=item["name"], font=("Microsoft YaHei", fs + 3, "bold"),
                 bg=th["bg_primary"], fg=th["text_primary"],
                 anchor="center", justify="center").pack(fill=tk.X, padx=24, pady=(22, 10))

        # 备注
        notes_card = self._make_module_card(inner, "备注", "📝")
        notes_text = tk.Text(notes_card, font=("Microsoft YaHei", fs), wrap=tk.WORD,
                             height=notes_rows, bd=0, highlightthickness=0,
                             padx=10, pady=8,
                             bg=th["bg_card"], fg=th["text_entry"],
                             insertbackground=th["text_entry"])
        notes_text.pack(fill=tk.X, padx=16, pady=(0, 4))
        if notes_val:
            notes_text.insert("1.0", notes_val)
        notes_text.focus_set()

        notes_btn_row = tk.Frame(notes_card, bg=th["bg_card"])
        notes_btn_row.pack(fill=tk.X, padx=16, pady=(4, 14))

        _debounce_id = [None]
        _dirty = [False]

        def _save_notes():
            _debounce_id[0] = None
            new_notes = notes_text.get("1.0", "end-1c").strip()
            if new_notes == item.get("notes", ""):
                _dirty[0] = False
                return
            update_item_notes(item["id"], new_notes)
            item["notes"] = new_notes
            _dirty[0] = False
            save_btn.configure(text="✓ 已保存", fg=th["accent"],
                               bg=th["bg_card"], activebackground=th["bg_card"])
            dialog.after(1200, lambda: save_btn.configure(
                text="📝 自动保存中", fg=th["text_dim"],
                bg=th["bg_card"], activebackground=th["bg_card"]))

        def _on_notes_change(event=None):
            _dirty[0] = True
            if _debounce_id[0] is not None:
                dialog.after_cancel(_debounce_id[0])
            _debounce_id[0] = dialog.after(800, _save_notes)

        notes_text.bind("<KeyRelease>", _on_notes_change, add="+")

        save_btn = tk.Label(notes_btn_row, text="📝 自动保存中",
                            font=("Microsoft YaHei", max(8, fs - 1)),
                            bg=th["bg_card"], fg=th["text_dim"], cursor="hand2")
        save_btn.pack(side=tk.RIGHT, padx=3)
        save_btn.bind("<Button-1>", lambda e: (_debounce_id[0] is not None and
            dialog.after_cancel(_debounce_id[0]), _save_notes()))

        _orig_cleanup = _cleanup
        def _cleanup():
            if _dirty[0]:
                if _debounce_id[0] is not None:
                    dialog.after_cancel(_debounce_id[0])
                _save_notes()
            _orig_cleanup()
        dialog.protocol("WM_DELETE_WINDOW", _cleanup)

        # 图标
        icon_card = self._make_module_card(inner, "图标", "🖼")
        icon_body = tk.Frame(icon_card, bg=th["bg_card"])
        icon_body.pack(fill=tk.X, padx=16, pady=(2, 14))

        current_icon = item.get("icon_path", "")
        tk_icon = _load_preview_icon(current_icon)
        _edit_icons["preview"] = tk_icon

        preview = tk.Label(icon_body, image=tk_icon, bg=th["bg_card"], bd=0)
        preview.pack(side=tk.LEFT, padx=(0, 14))

        icon_btn_col = tk.Frame(icon_body, bg=th["bg_card"])
        icon_btn_col.pack(side=tk.LEFT)

        def _change_icon():
            path = filedialog.askopenfilename(
                title="选择图标图片",
                filetypes=[("图片文件", "*.png;*.jpg;*.jpeg;*.ico;*.bmp;*.gif"),
                           ("所有文件", "*.*")])
            if not path:
                return
            update_item_icon(item["id"], path)
            item["icon_path"] = path
            clear_cache()
            _edit_icons["preview"] = _load_preview_icon(path)
            preview.configure(image=_edit_icons["preview"])

        def _reset_icon():
            if not item.get("icon_path"):
                return
            update_item_icon(item["id"], "")
            item["icon_path"] = ""
            clear_cache()
            _edit_icons["preview"] = _load_preview_icon("")
            preview.configure(image=_edit_icons["preview"])

        self._make_small_btn(icon_btn_col, "🖼  更换图标", th["btn_outline_bg"],
                   th["btn_outline_hover"], _change_icon, fg=th["btn_outline_fg"])
        self._make_small_btn(icon_btn_col, "↺  恢复默认", th["bg_primary"],
                   self._lighten(th["bg_primary"], -20), _reset_icon, fg=th["text_primary"])

        icon_hint = item.get("icon_path", "") or "(使用程序自带图标)"
        tk.Label(icon_btn_col, text=icon_hint[:50], font=("Microsoft YaHei", max(7, fs - 3)),
                 bg=th["bg_card"], fg=th["text_dim"], anchor="w").pack(pady=(4, 0))

        # 危险操作
        danger_card = self._make_module_card(inner, "危险操作", "⚠")
        danger_body = tk.Frame(danger_card, bg=th["bg_card"])
        danger_body.pack(fill=tk.X, padx=16, pady=(2, 14))

        delete_btn = tk.Button(danger_body, text="✕  删除事项",
                               font=("Microsoft YaHei", fs, "bold"),
                               bg=th["danger"], fg="white",
                               activebackground=self._lighten(th["danger"], -20),
                               activeforeground="white",
                               relief="flat", bd=0, padx=18, pady=6, cursor="hand2",
                               command=lambda: _confirm_delete())
        delete_btn.pack(fill=tk.X)
        self._bind_hover(delete_btn, th["danger"], self._lighten(th["danger"], -20))

        def _confirm_delete():
            if messagebox.askyesno("确认删除", f'确定要删除 "{item["name"]}" 吗？\n\n此操作不可撤销。'):
                _cleanup()
                self._on_delete(item["id"])

        close_btn = tk.Label(dialog, text="关闭", font=("Microsoft YaHei", fs),
                             bg=th["bg_primary"], fg=th["text_muted"], cursor="hand2")
        close_btn.pack(pady=(0, 18))
        close_btn.bind("<Button-1>", lambda e: _cleanup())
        self._bind_fg_hover(close_btn, th["text_muted"], th["text_primary"])

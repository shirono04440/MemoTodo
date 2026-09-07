"""拖拽排序 Mixin — 卡片拖放重排"""

import tkinter as tk

from database import reorder_items


class DragDropMixin:
    """拖拽排序：按下阈值检测 → ghost 浮动卡片 → 指示线 → 提交排序"""

    def _drag_press(self, event, idx):
        """按下拖拽手柄——仅记录位置，等移动超过阈值才真正启动拖拽"""
        self._drag_idx = idx
        self._drag_from = idx
        self._drag_start_x = event.x_root
        self._drag_start_y = event.y_root
        self._drag_card = None      # 等移动后才设
        self._drag_ghost = None
        self._drag_indicator = None
        self._drag_active = False

    def _drag_card_move(self, event):
        # 如果还没启动拖拽，检查是否达到了移动阈值
        if getattr(self, "_drag_active", False) is False:
            dx = abs(event.x_root - self._drag_start_x)
            dy = abs(event.y_root - self._drag_start_y)
            if dx < 5 and dy < 5:
                return  # 没超过阈值，不启动
            # 超过阈值 → 正式启动拖拽
            idx = self._drag_from
            if idx < 0 or idx >= len(self._card_frames):
                return
            self._drag_card = self._card_frames[idx]
            self._drag_card.configure(bg=self._lighten(self.theme["bg_card"], -15))
            self._drag_active = True
            self._drag_card.pack_forget()

        if self._drag_card is None:
            return

        # 创建浮动 ghost（只做一次）
        if self._drag_ghost is None:
            card = self._drag_card
            self._drag_ghost = tk.Frame(self.root, bg=self.theme["bg_card"],
                                        bd=1, relief="solid",
                                        highlightthickness=0)
            # 简单文字代替原卡片外观
            gid = card._item_id
            tk.Label(self._drag_ghost, text="⠿ 拖拽中...",
                    font=self.font_bold, bg=self.theme["bg_card"],
                    fg=self.theme["text_primary"]).pack(padx=20, pady=10)
            self._drag_ghost.lift()
            self._drag_card.pack_forget()

        # ghost 跟随鼠标
        gh = self._drag_ghost
        w = self._drag_card.winfo_width() or 300
        gh.place(x=self.root.winfo_pointerx() - w // 2,
                 y=self.root.winfo_pointery()  - 20,
                 width=w)

        # 计算插入位置
        target_y = self.root.winfo_pointery()
        target_idx = self._drag_from
        for i, cf in enumerate(self._card_frames):
            if i == self._drag_from:
                continue
            try:
                mid = cf.winfo_rooty() + cf.winfo_height() // 2
                if target_y < mid:
                    target_idx = i
                    break
                target_idx = i + 1
            except tk.TclError:
                pass

        # 移动指示线
        if target_idx != self._drag_idx and 0 <= target_idx <= len(self._card_frames):
            # 移除旧指示线
            if self._drag_indicator:
                self._drag_indicator.destroy()
            ind = tk.Frame(self._inner_frame, height=3,
                          bg=self.theme["accent"], bd=0)
            # 找到目标位置插入
            before = None
            if target_idx < len(self._card_frames):
                # 在 target_idx 卡片之前插入
                children = self._inner_frame.winfo_children()
                card_list = [w for w in children if hasattr(w, "_item_id")]
                if target_idx < len(card_list):
                    before = card_list[target_idx]
            if before:
                ind.pack(fill=tk.X, before=before, padx=12)
            else:
                ind.pack(fill=tk.X, padx=12, side=tk.BOTTOM)
            self._drag_indicator = ind
            self._drag_idx = target_idx

    def _drag_card_stop(self, event):
        # 如果没有超过移动阈值（仅是点击），什么都不做
        if not getattr(self, "_drag_active", False):
            self._drag_card = None
            self._drag_ghost = None
            self._drag_indicator = None
            return

        clean = getattr(self, "_drag_card", None)
        if clean is None:
            return
        # 清理 ghost & indicator
        if self._drag_ghost:
            self._drag_ghost.destroy()
            self._drag_ghost = None
        if self._drag_indicator:
            self._drag_indicator.destroy()
            self._drag_indicator = None

        clean.configure(bg=self.theme["bg_card"])
        self._drag_card = None
        self._drag_active = False

        from_idx = self._drag_from
        to_idx = self._drag_idx
        if from_idx != to_idx and 0 <= to_idx <= len(self._card_frames):
            ids = [cf._item_id for cf in self._card_frames]
            moved = ids.pop(from_idx)
            insert_at = to_idx if to_idx < from_idx else to_idx - 1
            ids.insert(insert_at, moved)
            reorder_items(ids)
        self._refresh_list()

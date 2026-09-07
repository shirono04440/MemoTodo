"""后台进程监控模块 — 轻量轮询：name 初筛 + exe 精匹配"""

import os
import threading
import time
import psutil
from datetime import datetime, timedelta

from database import get_all_items, update_opened_status, reset_all_opened_today


class ProcessMonitor:
    """后台监控线程，用 name 初筛减少 exe 抓取次数，降低 CPU 开销"""

    def __init__(self, interval=30, on_status_change=None):
        self.interval = interval
        self.on_status_change = on_status_change
        self._running = False
        self._thread = None
        self._last_reset_day = self._current_window_key()
        self._scan_count = 0                # 累计扫描次数

    # ================================================================
    #  4am 边界计算
    # ================================================================

    def get_today_window(self):
        now = datetime.now()
        today_4am = now.replace(hour=4, minute=0, second=0, microsecond=0)
        if now < today_4am:
            window_start = today_4am - timedelta(days=1)
        else:
            window_start = today_4am
        window_end = window_start + timedelta(days=1)
        return window_start, window_end

    def _current_window_key(self):
        start, _ = self.get_today_window()
        return start.strftime("%Y-%m-%d %H:%M")

    # ================================================================
    #  轻量扫描（name 初筛，仅匹配时抓 exe）
    # ================================================================

    def _build_index(self):
        """返回 (name_lookup, path_lookup)，按 exe 名称分组"""
        items = get_all_items(enabled_only=True)
        name_lookup = {}      # exe名(小写) → [(id, norm_path)]
        path_lookup = {}      # norm_path → id
        for item in items:
            base = os.path.basename(item["exe_path"]).lower()
            norm = os.path.normpath(item["exe_path"]).lower()
            path_lookup[norm] = item["id"]
            name_lookup.setdefault(base, []).append((item["id"], norm))
        return name_lookup, path_lookup

    def scan_once(self):
        """轻量扫描：先只取 name，命中时才抓 exe（省掉 99% 的系统调用）"""
        name_lookup, _ = self._build_index()
        if not name_lookup:
            return

        tracked_names = set(name_lookup.keys())
        found_ids = set()

        # 第一遍：只取 name（极轻量，纯查进程表）
        for proc in psutil.process_iter(['name']):
            try:
                name = (proc.info.get('name') or "").lower()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

            if name not in tracked_names:
                continue

            # 第二遍：name 命中后才抓 exe（昂贵的系统调用，仅对 ~2-3 个进程）
            try:
                exe = proc.exe()  # 按需获取
            except (psutil.NoSuchProcess, psutil.AccessDenied,
                    psutil.ZombieProcess):
                continue

            if not exe:
                continue

            norm_exe = os.path.normpath(exe).lower()
            for iid, norm_path in name_lookup.get(name, []):
                if norm_exe == norm_path:
                    found_ids.add(iid)
                    break

        if found_ids:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for item_id in found_ids:
                update_opened_status(item_id, opened_at=now_str, opened_today=1)
            if self.on_status_change:
                self.on_status_change()

    # ================================================================
    #  后台线程
    # ================================================================

    def _run(self):
        while self._running:
            current_key = self._current_window_key()
            if current_key != self._last_reset_day:
                reset_all_opened_today()
                self._last_reset_day = current_key
                if self.on_status_change:
                    self.on_status_change()

            self.scan_once()
            self._scan_count += 1
            time.sleep(self.interval)

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def set_interval(self, interval):
        self.interval = max(5, int(interval))

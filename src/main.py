"""备忘 Todo 软件 — 入口文件"""

import sys
import os
import traceback
import ctypes

# 高 DPI 清晰渲染（必须在导入 GUI 库之前调用）
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)  # System DPI Aware
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# 打包后将异常写入日志文件
if getattr(sys, 'frozen', False):
    log_path = os.path.join(os.path.dirname(sys.executable), "MemoTodo_error.log")
    sys.stderr = open(log_path, "w", encoding="utf-8")

from database import init_db
from settings import load_settings
from monitor import ProcessMonitor
from gui import TodoApp


def main():
    try:
        # 1. 初始化数据库
        init_db()

        # 2. 加载设置（填充默认值到数据库）
        load_settings()

        # 3. 创建监控器（先不启动，拿到 app 引用后设回调）
        monitor = ProcessMonitor(interval=30)

        # 4. 创建 GUI
        app = TodoApp(monitor=monitor)

        # 5. 把 GUI 刷新回调注册到监控器
        monitor.on_status_change = app.on_monitor_status_change

        # 6. 启动后台监控
        monitor.start()

        # 7. 进入主循环
        app.run()
    except Exception:
        traceback.print_exc()
        # 弹窗显示错误（仅在打包后）
        if getattr(sys, 'frozen', False):
            import tkinter.messagebox as mb
            mb.showerror("MemoTodo 错误", traceback.format_exc())


if __name__ == "__main__":
    main()

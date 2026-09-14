"""开机自启动模块 — 通过注册表 HKCU\\...\\Run 键控制（当前用户，无需管理员权限）"""

import os
import sys
import winreg

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "MemoTodo"


def _launch_command():
    """构造开机时执行的启动命令"""
    if getattr(sys, "frozen", False):
        # 打包后：直接指向 exe 自身
        return f'"{sys.executable}"'
    # 源码运行：python 解释器 + 入口脚本
    main_py = os.path.abspath(os.path.join(os.path.dirname(__file__), "main.py"))
    return f'"{sys.executable}" "{main_py}"'


def is_autostart_enabled():
    """查询当前是否已注册开机自启动"""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            value, _ = winreg.QueryValueEx(key, APP_NAME)
            return bool(value)
    except FileNotFoundError:
        return False
    except OSError:
        return False


def set_autostart(enable):
    """开启/关闭开机自启动。开启时写入 Run 键，关闭时删除对应键值"""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE
        )
    except FileNotFoundError:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY)

    with key:
        if enable:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, _launch_command())
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass

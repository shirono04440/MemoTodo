"""数据库操作模块 — SQLite 数据库的初始化与 CRUD 操作"""

import sqlite3
import os
import sys
from datetime import datetime

if getattr(sys, 'frozen', False):
    # PyInstaller 打包后 __file__ 在临时目录，数据库应放在 exe 旁边
    DB_PATH = os.path.join(os.path.dirname(sys.executable), "todo.db")
else:
    # 源码运行：数据库放在项目根目录（src/ 的上一级）
    DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "todo.db")


def get_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """初始化数据库：创建表和默认设置"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS todo_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            exe_path TEXT NOT NULL,
            notes TEXT DEFAULT '',
            icon_path TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_opened_at TIMESTAMP,
            opened_today INTEGER DEFAULT 0,
            enabled INTEGER DEFAULT 1
        )
    """)

    # 兼容旧表：增量添加新列
    for col, col_def in [
        ("notes", "TEXT DEFAULT ''"),
        ("icon_path", "TEXT DEFAULT ''"),
        ("sort_order", "INTEGER DEFAULT 0"),
    ]:
        try:
            cursor.execute(f"ALTER TABLE todo_items ADD COLUMN {col} {col_def}")
        except sqlite3.OperationalError:
            pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    # 插入默认设置（如果不存在）
    defaults = {
        "font_size": "12",
        "window_width": "800",
        "window_height": "600",
        "bg_color": "#F0F0F0",
    }
    for key, value in defaults.items():
        cursor.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            (key, value)
        )

    # 为已有数据分配递增 sort_order（新列默认值 0）
    try:
        cursor.execute("""
            UPDATE todo_items SET sort_order = (
                SELECT COUNT(*) FROM todo_items t2 WHERE t2.id <= todo_items.id
            )
        """)
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()


# ============================================================
#  事项 CRUD
# ============================================================

def add_item(name, exe_path, notes="", icon_path=""):
    """添加一个备忘事项，返回新行的 id"""
    conn = get_connection()
    cursor = conn.cursor()
    max_order = cursor.execute(
        "SELECT COALESCE(MAX(sort_order), 0) FROM todo_items"
    ).fetchone()[0]
    cursor.execute(
        "INSERT INTO todo_items (name, exe_path, notes, icon_path, sort_order) VALUES (?, ?, ?, ?, ?)",
        (name, exe_path, notes, icon_path, max_order + 1)
    )
    conn.commit()
    item_id = cursor.lastrowid
    conn.close()
    return item_id


def delete_item(item_id):
    """根据 id 删除事项"""
    conn = get_connection()
    conn.execute("DELETE FROM todo_items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()


def get_all_items(enabled_only=False):
    """获取所有事项（可选仅启用），按创建时间倒序"""
    conn = get_connection()
    sql = "SELECT * FROM todo_items"
    if enabled_only:
        sql += " WHERE enabled = 1"
    rows = conn.execute(sql + " ORDER BY sort_order ASC, id ASC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_opened_status(item_id, opened_at=None, opened_today=1):
    """更新事项的打开状态"""
    conn = get_connection()
    if opened_at is None:
        opened_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "UPDATE todo_items SET last_opened_at = ?, opened_today = ? WHERE id = ?",
        (opened_at, opened_today, item_id)
    )
    conn.commit()
    conn.close()


def update_item_notes(item_id, notes):
    """更新事项的注释文本"""
    conn = get_connection()
    conn.execute(
        "UPDATE todo_items SET notes = ? WHERE id = ?",
        (notes, item_id)
    )
    conn.commit()
    conn.close()


def update_item_icon(item_id, icon_path):
    """更新事项的自定义图标路径（空字符串 = 清除，使用自动提取）"""
    conn = get_connection()
    conn.execute(
        "UPDATE todo_items SET icon_path = ? WHERE id = ?",
        (icon_path, item_id)
    )
    conn.commit()
    conn.close()


def update_sort_order(item_id, sort_order):
    """更新单个事项的排序序号"""
    conn = get_connection()
    conn.execute(
        "UPDATE todo_items SET sort_order = ? WHERE id = ?",
        (sort_order, item_id)
    )
    conn.commit()
    conn.close()


def reorder_items(ordered_ids):
    """批量更新排序：ordered_ids 为按新顺序排列的 id 列表"""
    conn = get_connection()
    for i, item_id in enumerate(ordered_ids, 1):
        conn.execute(
            "UPDATE todo_items SET sort_order = ? WHERE id = ?",
            (i, item_id)
        )
    conn.commit()
    conn.close()


def reset_all_opened_today():
    """将所有事项的 opened_today 重置为 0（跨4am时调用）"""
    conn = get_connection()
    conn.execute("UPDATE todo_items SET opened_today = 0")
    conn.commit()
    conn.close()


# ============================================================
#  设置读写
# ============================================================

def get_setting(key, default=None):
    """读取单个设置值"""
    conn = get_connection()
    row = conn.execute(
        "SELECT value FROM settings WHERE key = ?", (key,)
    ).fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key, value):
    """写入/更新单个设置"""
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        (key, str(value))
    )
    conn.commit()
    conn.close()


def get_all_settings():
    """读取所有设置为字典"""
    conn = get_connection()
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    conn.close()
    return {r["key"]: r["value"] for r in rows}

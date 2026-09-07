"""图标提取工具 — 从 Windows exe 文件中提取图标，或加载自定义图片，转为 PIL Image"""

import os
import logging
import win32ui
import win32gui
import win32con
import win32api
from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)

# 图标缓存（按 key）: { "exe|path|size" or "custom|path|size": PIL.Image }
_icon_cache = {}


def extract_icon(exe_path, size=48):
    """
    从 exe 文件中提取图标。
    返回 size×size 的 PIL.Image，失败返回 None（调用方可画默认图标）。
    结果会缓存，避免每次刷新都重新提取。
    """
    cache_key = f"{exe_path}|{size}"
    if cache_key in _icon_cache:
        return _icon_cache[cache_key]

    if not os.path.exists(exe_path):
        return None

    large_icons = small_icons = []
    screen_dc = dc = mem_dc = bmp = None
    try:
        # 提取第一个大图标
        large_icons, small_icons = win32gui.ExtractIconEx(exe_path, 0)

        hicon = None
        if large_icons:
            hicon = large_icons[0]
        elif small_icons:
            hicon = small_icons[0]

        if hicon is None:
            return None

        # 屏幕 DC
        screen_dc = win32gui.GetDC(0)
        dc = win32ui.CreateDCFromHandle(screen_dc)
        mem_dc = dc.CreateCompatibleDC()

        # 创建目标位图
        bmp = win32ui.CreateBitmap()
        bmp.CreateCompatibleBitmap(dc, size, size)
        mem_dc.SelectObject(bmp)

        # 将图标绘制到位图
        win32gui.DrawIconEx(
            mem_dc.GetHandleOutput(),
            0, 0,
            hicon,
            size, size,
            0, None,
            win32con.DI_NORMAL
        )

        # 读取位图数据
        bmp_info = bmp.GetInfo()
        bmp_bits = bmp.GetBitmapBits(True)

        # 转为 PIL Image（BGRA → RGBA）
        img = Image.frombuffer(
            'RGBA',
            (bmp_info['bmWidth'], bmp_info['bmHeight']),
            bmp_bits, 'raw', 'BGRA', 0, 1
        )

        _icon_cache[cache_key] = img
        return img

    except Exception:
        logger.warning("extract_icon failed for %s (size=%d)", exe_path, size, exc_info=True)
        return None

    finally:
        if mem_dc: mem_dc.DeleteDC()
        if screen_dc: win32gui.ReleaseDC(0, screen_dc)
        if bmp: win32gui.DeleteObject(bmp.GetHandle())
        for h in large_icons:
            if h: win32gui.DestroyIcon(h)
        for h in small_icons:
            if h: win32gui.DestroyIcon(h)


def load_custom_icon(icon_path, size=48):
    """
    加载自定义图标文件（png / jpg / ico / bmp 等）。
    返回 size×size 的 RGBA PIL.Image，失败返回 None。
    结果会缓存。
    """
    if not icon_path or not os.path.exists(icon_path):
        return None

    cache_key = f"custom|{icon_path}|{size}"
    if cache_key in _icon_cache:
        return _icon_cache[cache_key]

    try:
        img = Image.open(icon_path)
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        # 缩放到目标尺寸
        img = img.resize((size, size), Image.LANCZOS)
        _icon_cache[cache_key] = img
        return img
    except Exception:
        logger.warning("load_custom_icon failed for %s (size=%d)", icon_path, size, exc_info=True)
        return None


def make_default_icon(size=48, color="#CCCCCC"):
    """生成一个默认的占位图标"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    margin = 3
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=4, fill=color, outline="#AAAAAA"
    )
    # 画一个应用方块
    cx, cy = size // 2, size // 2
    s = max(4, size // 8)
    draw.rectangle([cx - s, cy - s, cx + s, cy + s], fill="#FFFFFF")
    return img


def clear_cache():
    """清空图标缓存"""
    _icon_cache.clear()

"""配置管理模块 — 默认值与数据库读写的桥梁"""

from database import get_setting, set_setting, get_all_settings

# 默认值
DEFAULTS = {
    "theme": "light",
    "font_size": 12,
    "window_width": 800,
    "window_height": 600,
    "window_x": -1,
    "window_y": -1,
    "bg_image_path": "",
    "bg_image_opacity": 70,
    "window_opacity": 1.0,
    "window_on_top": 0,
    "icon_size": 48,
}


def load_settings():
    """从数据库加载所有设置，缺失的用默认值补上并写回数据库"""
    saved = get_all_settings()
    result = {}

    for key, default in DEFAULTS.items():
        if key in saved:
            # 根据默认值类型转换
            if isinstance(default, int):
                result[key] = int(saved[key])
            elif isinstance(default, float):
                result[key] = float(saved[key])
            else:
                result[key] = saved[key]
        else:
            result[key] = default
            # 把默认值写回数据库
            set_setting(key, str(default))

    return result


def save_settings(settings_dict):
    """将设置字典保存到数据库"""
    for key, value in settings_dict.items():
        set_setting(key, str(value))

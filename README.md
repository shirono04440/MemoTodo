# MemoTodo · 日程表

一个 Windows 桌面备忘 Todo 软件：把常用程序（游戏/工具）登记成卡片，双击即启动，自动统计「今天是否已打开」，支持自定义图标、备注、背景图、亮/暗主题、拖拽排序、系统托盘常驻。

> 界面标题为「日程表」，项目代号 **MemoTodo**，两者是同一个软件。

## 功能特性

- **事项卡片**：名称 + exe 路径 + 图标 + 备注，点击卡片或 ▶ 按钮直接启动程序
- **今日完成标记**：后台轻量轮询进程列表，检测到对应程序运行即标记「今天已完成」，跨 4am 自动重置
- **拖拽排序**：按住卡片空白处拖动重排
- **外观自定义**：亮/暗主题、字体大小、图标尺寸、背景图（含透明度）、窗口透明度、置顶
- **无边框自绘窗口**：自绘标题栏，8 方向缩放，图钉固定位置
- **系统托盘**：最小化到托盘，右键菜单显示/隐藏/退出
- **数据本地存储**：SQLite（`todo.db`），无需联网

## 目录结构

```
todo/
├── src/                    # 全部源码
│   ├── main.py             #   入口：初始化 → 监控 → GUI → 主循环
│   ├── database.py         #   SQLite 初始化与事项/设置 CRUD
│   ├── settings.py         #   默认设置值 + 数据库读写桥接
│   ├── themes.py           #   亮/暗两套配色
│   ├── monitor.py          #   后台进程监控（4am 边界 + 轻量轮询）
│   ├── icon_utils.py       #   exe 图标提取 / 自定义图标加载 / 默认图标
│   └── gui/                #   GUI 包（Mixin 拆分的界面模块）
│       ├── __init__.py         # TodoApp 主类（组装各 Mixin）
│       ├── _title_bar.py       # 自绘标题栏 + 图钉 + 拖动
│       ├── _list.py            # 摘要条 + 卡片列表 + 滚动
│       ├── _resize.py          # 8 方向缩放 + 背景图渲染
│       ├── _drag_drop.py       # 拖拽排序
│       ├── _dialog_base.py     # 对话框复用组件
│       ├── _dialog_add.py      # 添加事项对话框
│       ├── _dialog_edit.py     # 编辑事项对话框
│       ├── _dialog_settings.py # 设置对话框
│       ├── _tray.py            # 系统托盘
│       └── _utils.py           # 颜色/窗口/hover/启动删除等工具方法
├── tests/                  # 测试
│   └── test_all.py         # 全功能检测脚本
├── assets/                 # 资源
│   └── test_icon.png       # 托盘图标（打包时也作为 exe 图标）
├── MemoTodo.spec           # PyInstaller 打包配置（根目录）
├── requirements.txt        # 依赖清单
└── todo.db                 # 运行后自动生成的数据库（不入库）
```

## 环境要求

- Windows（依赖 `win32gui`/`win32ui` 等 Windows API）
- Python 3.11+（自带 `tkinter`）

## 安装

```bash
# 1. 创建虚拟环境（可选）
python -m venv .venv
# Windows 下激活：
.venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt
```

## 运行

```bash
python src/main.py
```

## 测试

```bash
python tests/test_all.py
```

覆盖：模块导入、数据库 CRUD、设置持久化、图标提取、4am 边界、GUI 组件。

## 打包为 exe

```bash
pyinstaller MemoTodo.spec --noconfirm
# 产物在 dist/MemoTodo.exe
```

打包后数据库 `todo.db` 会生成在 exe 同目录下；异常会写入 `MemoTodo_error.log`。

## 数据与设置

- 事项与设置保存在 `todo.db`（SQLite，WAL 模式）
- 「今天已完成」以每天凌晨 4:00 为分界重置，适合熬夜场景
- 关闭窗口默认最小化到托盘；托盘右键「退出」才彻底结束程序

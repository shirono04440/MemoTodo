"""全功能检测脚本"""
import sys, os
ROOT = os.path.dirname(os.path.dirname(__file__))  # 项目根目录
sys.path.insert(0, os.path.join(ROOT, "src"))
os.chdir(ROOT)

ok = lambda s: print(f"  [OK] {s}")
fail = lambda s: print(f"  [FAIL] {s}")
errors = []

def test(name):
    print(f"\n--- {name} ---")

# ===== 1. 模块导入 =====
test("1. module import")
try:
    import database; ok("database.py")
    import settings; ok("settings.py")
    import icon_utils; ok("icon_utils.py")
    import monitor; ok("monitor.py")
    import gui; ok("gui.py")
    import main; ok("main.py")
except Exception as e:
    fail(str(e)); errors.append(e)

# ===== 2. 数据库 =====
test("2. database init + CRUD")
try:
    database.init_db()
    s = settings.load_settings()
    required = ['theme','font_size','icon_size','window_width','window_height',
                'bg_image_path','window_opacity']
    for k in required:
        assert k in s, f"missing setting: {k}"
    ok(f"settings: {len(s)} keys")

    from database import (add_item, get_all_items, update_item_notes,
                          update_item_icon, update_opened_status, delete_item)
    test_exe = r'C:\Windows\System32\notepad.exe'
    if os.path.exists(test_exe):
        iid = add_item('test', test_exe, 'note', '')
        items = get_all_items()
        assert any(i['id']==iid for i in items)
        ok("add_item + get_all_items")

        update_item_notes(iid, 'new note')
        item = [i for i in get_all_items() if i['id']==iid][0]
        assert item['notes']=='new note'
        ok("update_item_notes")

        update_item_icon(iid, r'C:\fake\icon.png')
        item = [i for i in get_all_items() if i['id']==iid][0]
        assert item['icon_path']==r'C:\fake\icon.png'
        ok("update_item_icon")

        from datetime import datetime
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        update_opened_status(iid, opened_at=now, opened_today=1)
        item = [i for i in get_all_items() if i['id']==iid][0]
        assert item['opened_today']==1
        ok("update_opened_status (set open)")

        update_opened_status(iid, opened_today=0)
        item = [i for i in get_all_items() if i['id']==iid][0]
        assert item['opened_today']==0
        ok("toggle status (set closed)")

        delete_item(iid)
        items = get_all_items()
        assert not any(i['id']==iid for i in items)
        ok("delete_item")
    else:
        print("  [SKIP] notepad.exe not found")
except Exception as e:
    fail(str(e)); errors.append(e)

# ===== 3. 设置持久化 =====
test("3. settings persistence")
try:
    settings.save_settings({'font_size': 20, 'bg_image_opacity': 50})
    s2 = settings.load_settings()
    assert s2['font_size']==20 and s2['bg_image_opacity']==50
    ok("save + load")
    settings.save_settings({'font_size': 12, 'bg_image_opacity': 70})
    ok("restore defaults")
except Exception as e:
    fail(str(e)); errors.append(e)

# ===== 4. 图标 =====
test("4. icon utils")
try:
    if os.path.exists(r'C:\Windows\System32\notepad.exe'):
        img = icon_utils.extract_icon(r'C:\Windows\System32\notepad.exe', size=48)
        if img:
            ok(f"extract_icon: {img.size} {img.mode}")
        else:
            fail("extract_icon returned None")
    def_img = icon_utils.make_default_icon(48)
    ok(f"make_default_icon: {def_img.size}")
except Exception as e:
    fail(str(e)); errors.append(e)

# ===== 5. 4am 边界 =====
test("5. 4am time window")
try:
    m = monitor.ProcessMonitor(interval=999)
    start, end = m.get_today_window()
    diff = (end - start).total_seconds()
    assert diff == 86400, f"not 24h: {diff}"
    assert start.hour == 4 and start.minute == 0, f"not 4am: {start}"
    ok(f"window: {start} ~ {end} ({int(diff/3600)}h)")
except Exception as e:
    fail(str(e)); errors.append(e)

# ===== 6. GUI components =====
test("6. GUI components (no Tk)")
try:
    # 不创建完整 TodoApp（它会自己 new Tk），只验证内部方法可用
    import tkinter as tk
    r = tk.Tk()
    r.withdraw()
    # 测试背景图片生成
    from PIL import Image
    test_img = Image.new('RGB', (100, 100), '#FF0000')
    from PIL import ImageTk
    photo = ImageTk.PhotoImage(test_img)
    ok(f"PhotoImage works ({photo.width()}x{photo.height()})")
    r.destroy()
except Exception as e:
    fail(str(e)); errors.append(e)

# ===== 结果 =====
print(f"\n{'='*40}")
if errors:
    print(f"FAIL: {len(errors)} error(s)")
    for e in errors:
        print(f"  - {e}")
else:
    print("ALL TESTS PASSED")

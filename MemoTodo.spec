# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=[],
    datas=[('assets/test_icon.png', 'assets')],
    hiddenimports=['psutil'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['numpy', 'scipy', 'pandas', 'matplotlib', 'PIL.ImageFilter',
               '_tkinter.tkinter', 'tkinter.tix', 'tkinter.ttk',
               'mkl', 'mkl_intel_thread', 'mkl_core', 'mkl_rt',
               'libiomp5md', 'mkl_pgi_thread', 'mkl_blacs',
               'omptarget', 'sycl6', 'impi', 'msmpi', 'pgmath', 'pgc', 'pgf90'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='MemoTodo',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/test_icon.png',
    uac_admin=False,
)

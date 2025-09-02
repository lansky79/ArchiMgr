# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src\\main.py'],
    pathex=['C:\\Users\\franc\\Projects\\ArchiMgr\\src'],
    binaries=[],
    datas=[('resources', 'resources'), ('src', 'src')],
    hiddenimports=['utils', 'PIL._tkinter_finder', 'urllib3', 'urllib3.util', 'urllib3.connectionpool', 'urllib3.exceptions'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='档案检索系统',
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
    icon=['resources\\app.ico'],
)

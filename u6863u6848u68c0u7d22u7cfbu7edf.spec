# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('resources', 'resources'), ('config', 'config')],
    hiddenimports=['urllib3'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['torch', 'huggingface_hub', 'matplotlib', 'scipy', 'PIL', 'pandas.tests', 'numpy.testing', 'numpy.distutils', 'sqlalchemy.testing', 'tkinter.test', 'unittest', 'pytest'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='u6863u6848u68c0u7d22u7cfbu7edf',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['resources\\app.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=['*.dll', '*.pyd'],
    name='u6863u6848u68c0u7d22u7cfbu7edf',
)

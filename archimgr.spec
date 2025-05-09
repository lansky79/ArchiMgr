# -*- mode: python ; coding: utf-8 -*-
import os

ROOT_DIR = os.path.abspath(SPECPATH)
SITE_PACKAGES = r'C:\Users\franc\.conda\envs\archimgr_lite\Lib\site-packages'

def exclude_mkl(binary_tuple):
    """过滤 MKL 相关文件"""
    binary_path = binary_tuple[0]
    return not (binary_path.startswith('mkl') or 'mkl' in binary_path.lower())

a = Analysis(
    ['src/main.py'],
    pathex=[ROOT_DIR],
    binaries=[],
    datas=[
        ('config', 'config'),
        ('resources', 'resources'),
        ('src/models/*', 'models'),
        ('src/ui/*', 'ui'),
        ('src/utils/*', 'utils'),
        ('src/controllers/*', 'controllers'),
        ('src/config/*', 'src/config'),
        (os.path.join(SITE_PACKAGES, 'openpyxl'), 'openpyxl'),
        (os.path.join(SITE_PACKAGES, 'et_xmlfile'), 'et_xmlfile'),
    ],
    excludes=[
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'wx',
        'matplotlib'
    ],
    noarchive=False,
)

# 过滤 MKL 文件
a.binaries = list(filter(exclude_mkl, a.binaries))

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='档案管理系统v1.0',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/app.ico'
)

COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=['vcruntime140.dll', 'python312.dll'],
    name='档案管理系统v1.0'
) 
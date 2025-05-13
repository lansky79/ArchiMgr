#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import shutil
import subprocess
from datetime import datetime

def clean_build_dirs():
    """清理构建目录"""
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"清理目录: {dir_name}")
            shutil.rmtree(dir_name)

def build_executable():
    """使用PyInstaller构建可执行文件"""
    print("开始构建可执行文件...")
    
    # 确保PyInstaller已安装
    try:
        import PyInstaller
    except ImportError:
        print("正在安装PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # 检查UPX是否存在
    upx_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools', 'upx')
    has_upx = os.path.exists(upx_dir) and len([f for f in os.listdir(upx_dir) if f.startswith('upx')]) > 0
    
    if not has_upx:
        print("未找到UPX压缩工具，将创建tools/upx目录")
        os.makedirs(upx_dir, exist_ok=True)
        print("请从 https://github.com/upx/upx/releases 下载UPX并解压到tools/upx目录")
        print("然后重新运行此脚本以使用UPX压缩")
    
    # 构建命令
    build_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=档案检索系统",
        "--icon=resources/app.ico",
        "--noconsole",
        "--add-data=resources;resources",
        "--add-data=config;config",
        "--clean",  # 清理临时文件
        "--exclude-module=matplotlib",  # 排除不必要的大型模块
        "--exclude-module=scipy",
        "--exclude-module=tkinter.test",
        "--exclude-module=unittest",
    ]
    
    # 如果有UPX，添加UPX压缩选项
    if has_upx:
        build_cmd.extend([
            f"--upx-dir={upx_dir}",
            "--upx"
        ])
        print("将使用UPX进行压缩，这将显著减小文件大小")
    else:
        print("不使用UPX压缩，最终文件将会较大")
    
    # 添加主文件
    build_cmd.append("src/main.py")
    
    # 执行构建
    print(f"执行命令: {' '.join(build_cmd)}")
    subprocess.check_call(build_cmd)
    
    print("构建完成!")

def create_installer():
    """创建安装程序"""
    print("准备创建安装程序...")
    
    # 检查是否安装了NSIS
    nsis_path = r"C:\Program Files (x86)\NSIS\makensis.exe"
    if not os.path.exists(nsis_path):
        print("警告: 未找到NSIS安装程序。请安装NSIS后再运行此脚本创建安装程序。")
        print("NSIS下载地址: https://nsis.sourceforge.io/Download")
        return False
    
    # 创建NSIS脚本
    nsis_script = "installer.nsi"
    version = "1.0"
    current_date = datetime.now().strftime("%Y%m%d")
    
    with open(nsis_script, "w", encoding="utf-8") as f:
        f.write(f'''
; 档案检索系统安装脚本
!include "MUI2.nsh"

; 应用程序信息
Name "档案检索系统"
OutFile "档案检索系统_v{version}_{current_date}_安装程序.exe"
InstallDir "$PROGRAMFILES\\档案检索系统"

; 界面设置
!define MUI_ICON "resources\\app.ico"
!define MUI_UNICON "resources\\app.ico"
!define MUI_WELCOMEFINISHPAGE_BITMAP "resources\\installer-welcome.bmp"
!define MUI_UNWELCOMEFINISHPAGE_BITMAP "resources\\installer-welcome.bmp"

; 页面
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; 语言
!insertmacro MUI_LANGUAGE "SimpChinese"

Section "安装程序文件" SecMain
    SetOutPath "$INSTDIR"
    File /r "dist\\档案检索系统\\*.*"
    
    ; 创建卸载程序
    WriteUninstaller "$INSTDIR\\卸载.exe"
    
    ; 创建开始菜单快捷方式
    CreateDirectory "$SMPROGRAMS\\档案检索系统"
    CreateShortcut "$SMPROGRAMS\\档案检索系统\\档案检索系统.lnk" "$INSTDIR\\档案检索系统.exe"
    CreateShortcut "$SMPROGRAMS\\档案检索系统\\卸载.lnk" "$INSTDIR\\卸载.exe"
    
    ; 创建桌面快捷方式
    CreateShortcut "$DESKTOP\\档案检索系统.lnk" "$INSTDIR\\档案检索系统.exe"
SectionEnd

Section "Uninstall"
    ; 删除程序文件
    RMDir /r "$INSTDIR"
    
    ; 删除开始菜单快捷方式
    RMDir /r "$SMPROGRAMS\\档案检索系统"
    
    ; 删除桌面快捷方式
    Delete "$DESKTOP\\档案检索系统.lnk"
SectionEnd
''')
    
    # 运行NSIS编译器
    print(f"使用NSIS创建安装程序...")
    subprocess.check_call([nsis_path, nsis_script])
    
    print("安装程序创建完成!")
    return True

def main():
    print("=== 档案检索系统打包工具 ===")
    print("此脚本将构建可执行文件并创建安装程序")
    print("")
    
    # 清理旧的构建文件
    clean_build_dirs()
    
    # 构建可执行文件
    build_executable()
    
    # 创建安装程序
    if create_installer():
        print("\n打包过程完成! 安装程序已创建在当前目录中。")
    else:
        print("\n打包过程部分完成。可执行文件已创建，但安装程序创建失败。")

if __name__ == "__main__":
    main()

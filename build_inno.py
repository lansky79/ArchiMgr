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
        "src/main.py"
    ]
    
    # 执行构建
    print(f"执行命令: {' '.join(build_cmd)}")
    subprocess.check_call(build_cmd)
    
    print("构建完成!")

def create_inno_installer():
    """创建Inno Setup安装程序"""
    print("准备创建安装程序...")
    
    # 检查是否安装了Inno Setup
    inno_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
        r"C:\Program Files\Inno Setup 5\ISCC.exe"
    ]
    
    inno_path = None
    for path in inno_paths:
        if os.path.exists(path):
            inno_path = path
            break
    
    if not inno_path:
        print("警告: 未找到Inno Setup编译器。请安装Inno Setup后再运行此脚本。")
        print("Inno Setup下载地址: https://jrsoftware.org/isdl.php")
        return False
    
    # 创建Inno Setup脚本
    iss_script = "installer.iss"
    version = "1.0"
    current_date = datetime.now().strftime("%Y%m%d")
    app_name = "档案检索系统"
    output_name = f"{app_name}_v{version}_{current_date}_安装程序"
    
    # 获取应用程序目录的绝对路径
    app_dir = os.path.abspath(f"dist/{app_name}")
    
    # 获取图标文件的绝对路径
    icon_path = os.path.abspath("resources/app.ico")
    
    # 创建Inno Setup脚本
    with open(iss_script, "w", encoding="utf-8") as f:
        f.write(f"""; 档案检索系统 Inno Setup 安装脚本

#define MyAppName "档案检索系统"
#define MyAppVersion "1.0"
#define MyAppPublisher "档案检索系统开发团队"
#define MyAppURL ""
#define MyAppExeName "档案检索系统.exe"

[Setup]
AppId={{{{5A8D62C7-8734-4F52-B9D1-7E6F49A3B121}}}}
AppName={{{{#MyAppName}}}}
AppVersion={{{{#MyAppVersion}}}}
AppPublisher={{{{#MyAppPublisher}}}}
AppPublisherURL={{{{#MyAppURL}}}}
AppSupportURL={{{{#MyAppURL}}}}
AppUpdatesURL={{{{#MyAppURL}}}}
DefaultDirName={{{{autopf}}}}\{{{{#MyAppName}}}}
DefaultGroupName={{{{#MyAppName}}}}
AllowNoIcons=yes
OutputDir=.
OutputBaseFilename={output_name}
SetupIconFile={icon_path}
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "{{{{cm:CreateDesktopIcon}}}}"; GroupDescription: "{{{{cm:AdditionalIcons}}}}"; Flags: checkedonce

[Files]
Source: "{app_dir}\*"; DestDir: "{{{{app}}}}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{{{{group}}}}\{{{{#MyAppName}}}}"; Filename: "{{{{app}}}}\{{{{#MyAppExeName}}}}"
Name: "{{{{group}}}}\{{{{cm:UninstallProgram,{{{{#MyAppName}}}}}}}}"; Filename: "{{{{uninstallexe}}}}"
Name: "{{{{commondesktop}}}}\{{{{#MyAppName}}}}"; Filename: "{{{{app}}}}\{{{{#MyAppExeName}}}}"; Tasks: desktopicon

[Run]
Filename: "{{{{app}}}}\{{{{#MyAppExeName}}}}"; Description: "{{{{cm:LaunchProgram,{{{{#StringChange(MyAppName, '&', '&&')}}}}}}}}"; Flags: nowait postinstall skipifsilent
""")
    
    # 运行Inno Setup编译器
    print(f"使用Inno Setup创建安装程序...")
    subprocess.check_call([inno_path, iss_script])
    
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
    if create_inno_installer():
        print("\n打包过程完成! 安装程序已创建在当前目录中。")
    else:
        print("\n打包过程部分完成。可执行文件已创建，但安装程序创建失败。")

if __name__ == "__main__":
    main()

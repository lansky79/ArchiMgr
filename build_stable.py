import os
import shutil
import subprocess
import sys

def build_executable():
    """构建稳定的可执行文件，解决所有依赖问题"""
    try:
        print("正在清理旧的构建文件...")
        # 清理旧的构建文件
        for item in ['build', 'dist']:
            if os.path.exists(item):
                shutil.rmtree(item, ignore_errors=True)
        
        # 确保必要的目录存在
        os.makedirs('dist', exist_ok=True)
        
        print("正在构建可执行文件...")
        # 构建命令 - 包含所有必要的依赖
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--onedir",
            "--windowed",
            "--noconfirm",
            "--noupx",  # 禁用UPX压缩，提高稳定性
            "--name", "ArchiveManager",
            "--icon", os.path.join('resources', 'app.ico'),
            # 添加数据文件
            "--add-data", f"resources{os.pathsep}resources",
            "--add-data", f"config{os.pathsep}config",
            "--add-data", f"src{os.pathsep}src",
            # 明确包含 Excel 相关依赖
            "--collect-all", "openpyxl",
            "--collect-all", "pandas",
            "--hidden-import=openpyxl",
            "--hidden-import=openpyxl.cell",
            "--hidden-import=openpyxl.workbook",
            "--hidden-import=openpyxl.reader.excel",
            "--hidden-import=openpyxl.writer.excel",
            "--hidden-import=openpyxl.styles",
            "--hidden-import=openpyxl.worksheet",
            "--hidden-import=openpyxl.worksheet.worksheet",
            "--hidden-import=openpyxl.utils",
            "--hidden-import=pandas",
            "--hidden-import=pandas.io.excel",
            "--hidden-import=pandas.io.excel._openpyxl",
            "--hidden-import=pandas._libs.parsers",
            "--hidden-import=pandas._libs.tslibs.np_datetime",
            "--hidden-import=pandas._libs.tslibs.nattype",
            "--hidden-import=pandas._libs.tslibs.timezones",
            "--hidden-import=pandas._libs.tslibs.base",
            "--hidden-import=pandas._libs.tslibs.parsing",
            "--hidden-import=pandas._libs.tslibs.strptime",
            "--hidden-import=pandas._libs.tslibs.conversion",
            "--hidden-import=pandas._libs.tslibs.fields",
            "--hidden-import=pandas._libs.tslibs.offsets",
            "--hidden-import=pandas._libs.tslibs.timedeltas",
            "--hidden-import=pandas._libs.tslibs.timestamps",
            "--hidden-import=pandas._libs.tslibs.tzconversion",
            "--hidden-import=pandas._libs.tslibs.vectorized",
            "--hidden-import=pandas._libs.tslibs.np_datetime",
            "--hidden-import=pandas._libs.tslibs.parsing",
            # 包含其他必要的依赖
            "--hidden-import=utils",
            "--hidden-import=PIL._tkinter_finder",
            "--hidden-import=urllib3",
            "--hidden-import=urllib3.util",
            "--hidden-import=urllib3.connectionpool",
            "--hidden-import=urllib3.exceptions",
            # 添加路径
            "--paths", os.path.join(os.getcwd(), 'src'),
            # 主脚本
            os.path.join('src', 'main.py')
        ]
        
        # 运行构建命令
        result = subprocess.run(cmd, check=True)
        
        if result.returncode == 0:
            print("\n构建成功！")
            exe_dir = os.path.join('dist', 'ArchiveManager')
            exe_path = os.path.join(exe_dir, 'ArchiveManager.exe')
            print(f"可执行文件位置: {os.path.abspath(exe_path)}")
            
            # 复制必要的资源文件（在 --onedir 模式下，PyInstaller 会自动处理 --add-data 指定的文件）
            print("\n正在验证资源文件...")
            for dir_name in ['resources', 'config']:
                src = dir_name
                dst = os.path.join(exe_dir, dir_name)
                if not os.path.exists(dst):
                    print(f"警告: 未找到预期的资源目录: {dst}")
                else:
                    print(f"资源目录存在: {dst}")
            
            # 创建注册文件
            create_registration_file(exe_dir)
            
            print("\n构建完成！")
            print(f"请运行 {os.path.abspath(exe_path)} 启动程序。")
            return True
        else:
            print("\n构建失败！")
            return False
            
    except Exception as e:
        print(f"构建过程中出错: {str(e)}")
        return False

def create_registration_file(target_dir):
    """创建注册文件
    
    Args:
        target_dir (str): 目标目录路径
    """
    try:
        # 确保配置目录存在
        config_dir = os.path.join(target_dir, 'config')
        os.makedirs(config_dir, exist_ok=True)
        
        # 注册信息
        reg_info = "2xdqzr5zyghj|新都区自然资源规划局"
        
        # 简单加密（每个字符ASCII码+1）
        encrypted = ''.join(chr(ord(c) + 1) for c in reg_info)
        
        # 写入文件
        with open(os.path.join(config_dir, 'registration.dat'), 'w', encoding='utf-8') as f:
            f.write(encrypted)
            
        print("注册文件已创建！")
        return True
        
    except Exception as e:
        print(f"创建注册文件失败: {e}")
        return False

if __name__ == "__main__":
    if build_executable():
        sys.exit(0)
    else:
        sys.exit(1)

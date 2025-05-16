import os
import sys
import subprocess

def main():
    print("=== 开始构建档案检索系统 ===")
    
    # 确保dist目录存在
    os.makedirs("dist", exist_ok=True)
    
    # 构建命令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=档案检索系统",
        "--icon=resources/app.ico",
        "--noconsole",
        "--add-data=resources;resources",
        "--add-data=config;config",
        "--clean",
        "src/main.py"
    ]
    
    print("执行命令:", " ".join(cmd))
    
    try:
        subprocess.check_call(cmd)
        print("\n构建成功! 可执行文件位于 dist/档案检索系统 目录下")
    except subprocess.CalledProcessError as e:
        print(f"\n构建失败，错误代码: {e.returncode}")
        sys.exit(1)

if __name__ == "__main__":
    main()

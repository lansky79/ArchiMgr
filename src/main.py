import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import logging
from datetime import datetime

# 正确的导入路径
from models.database import Database
from ui.main_window import MainWindow

# 应用程序常量
APP_NAME = "archimgr"
DISPLAY_NAME = "人事档案软件"
VERSION = "1.0.0"

def setup_paths():
    """设置程序路径"""
    if getattr(sys, 'frozen', False):
        # 打包后的环境
        app_dir = os.path.dirname(sys.executable)
        # 从 _internal 目录读取配置和资源
        config_dir = os.path.join(app_dir, '_internal', 'config')
        resources_dir = os.path.join(app_dir, '_internal', 'resources')
        icon_path = os.path.join(resources_dir, 'app.ico')
    else:
        # 开发环境
        app_dir = os.path.dirname(os.path.dirname(__file__))
        # 直接从项目根目录读取
        config_dir = os.path.join(app_dir, 'config')
        resources_dir = os.path.join(app_dir, 'resources')
        icon_path = os.path.join(resources_dir, 'app.ico')

    # 需要写入的目录（在主目录下）
    paths = {
        'user_data': os.path.join(app_dir, 'database'),
        'archives': os.path.join(app_dir, 'archives'),
        'logs': os.path.join(app_dir, 'logs'),
        'config': config_dir,
        'resources': resources_dir,
        'icon': icon_path
    }
    
    # 只创建需要写入的目录
    writable_dirs = ['user_data', 'archives', 'logs']
    for key in writable_dirs:
        os.makedirs(paths[key], exist_ok=True)
        
    return app_dir, paths

def setup_logging():
    """配置日志"""
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(
        log_dir,
        f"debug_{datetime.now().strftime('%Y%m%d')}.log"
    )
    
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def main():
    try:
        # 设置路径
        app_dir, paths = setup_paths()
        
        # 设置日志
        setup_logging()
        
        # 创建主窗口
        root = tk.Tk()
        root.title(DISPLAY_NAME)
        root.state('zoomed')
        
        try:
            root.iconbitmap(paths['icon'])
        except Exception as e:
            logging.warning(f"无法加载程序图标: {str(e)}")
        
        # 初始化数据库
        db = Database()
        db.connect()
        
        # 创建主应用
        app = MainWindow(root, db)
        
        # 启动主循环
        root.mainloop()
        
    except Exception as e:
        messagebox.showerror("错误", f"程序启动失败: {str(e)}")
        logging.critical(f"程序启动失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()

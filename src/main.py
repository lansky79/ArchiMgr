#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import tkinter as tk
import logging
from datetime import datetime
import subprocess

# 添加项目根目录到 sys.path
# 添加项目根目录到 sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

# 导入路径管理模块
from src.utils.paths import (
    get_application_path, get_user_data_dir, get_resources_path, 
    get_icon_path, get_exports_dir, get_temp_dir
)

# 正确的导入路径
from src.models.database import Database
from src.ui.main_window import MainWindow
from src.config.logger import setup_logger

# 应用程序常量
VERSION = "1.0"

def main():
    """程序入口点函数"""
    # 初始化日志
    setup_logger()
    
    logging.info(f"启动应用，版本: {VERSION}")
    
    try:
        # 设置路径 - 使用路径管理模块
        app_dir = get_application_path()
        
        # 初始化数据库
        db = Database()
        
        # 创建GUI
        root = tk.Tk()
        root.title(f"档案检索系统v{VERSION}")
        root.geometry("1200x800")
        
        # 设置程序图标
        try:
            icon_path = get_icon_path()
            if os.path.exists(icon_path):
                root.iconbitmap(icon_path)
                logging.info(f"已设置程序图标: {icon_path}")
            else:
                logging.warning(f"程序图标文件不存在: {icon_path}")
        except Exception as e:
            logging.warning(f"设置图标失败: {str(e)}")
            # 继续运行，不因图标问题而终止
        
        # 创建主窗口
        main_window = MainWindow(root, db)
        
        # 进入主循环
        root.mainloop()
        
    except Exception as e:
        error_msg = f"程序启动失败: {str(e)}"
        logging.error(error_msg, exc_info=True)
        print(error_msg)
        sys.exit(1)

if __name__ == "__main__":
    main()

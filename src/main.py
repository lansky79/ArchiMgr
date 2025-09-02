#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import tkinter as tk
from tkinter import messagebox
import logging
from datetime import datetime
import subprocess

# 设置导入路径，同时支持开发环境和打包环境
def setup_paths():
    """设置导入路径"""
    if getattr(sys, 'frozen', False):
        # 打包环境
        base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
        sys.path.append(base_path)
    else:
        # 开发环境
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if base_path not in sys.path:
            sys.path.insert(0, base_path)
    return base_path

# 初始化路径
BASE_PATH = setup_paths()

# 导入路径管理模块
try:
    # 统一导入方式，让 Python 在 sys.path 中查找模块
    from utils.paths import (
        get_application_path, get_user_data_dir, get_resources_path, 
        get_icon_path, get_exports_dir, get_temp_dir
    )
    from models.database import Database
    from ui.main_window import MainWindow
    from config.logger import setup_logger
except ImportError as e:
    print(f"导入错误: {e}")
    print(f"当前路径: {os.getcwd()}")
    print(f"sys.path: {sys.path}")
    input("按回车键退出...")
    sys.exit(1)

# 预加载必要的模块
try:
    # 尝试预加载必要的模块
    if getattr(sys, 'frozen', False):
        # 打包环境
        from utils.preload import preload_modules
    else:
        # 开发环境
        from src.utils.preload import preload_modules
    
    # 执行预加载
    preload_modules()
    logging.info("预加载模块完成")
except Exception as e:
    print(f"预加载模块失败: {str(e)}")
    logging.error(f"预加载模块失败: {str(e)}")

# 应用程序常量
VERSION = "1.0(0522)"

def setup_logging():
    """配置日志记录，同时输出到控制台和文件"""
    try:
        # 使用Windows本地应用数据目录
        import ctypes
        from ctypes import wintypes
        
        # 获取本地应用数据目录
        CSIDL_LOCAL_APPDATA = 0x001c  # 本地应用数据目录
        SHGFP_TYPE_CURRENT = 0  # 获取当前值
        
        buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(0, CSIDL_LOCAL_APPDATA, 0, SHGFP_TYPE_CURRENT, buf)
        app_data_dir = buf.value
        
        # 创建应用专属日志目录
        log_dir = os.path.join(app_data_dir, 'ArchiMgr', 'Logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # 生成带日期的日志文件名
        log_file = os.path.join(log_dir, f'archimgr_{datetime.now().strftime("%Y%m%d")}.log')
        
    except Exception as e:
        # 如果获取应用数据目录失败，使用用户主目录
        log_dir = os.path.join(os.path.expanduser('~'), 'ArchiMgr', 'Logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f'archimgr_{datetime.now().strftime("%Y%m%d")}.log')
        logging.error(f"使用备用日志目录: {log_file}, 错误: {str(e)}")
    
    # 记录日志文件路径
    logging.info(f"日志文件路径: {log_file}")
    
    # 创建格式化器
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 创建文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # 禁用SQLAlchemy的日志
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)
    
    # 移除所有现有的处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 添加处理器
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    logging.info(f"日志文件已创建: {log_file}")

def main():
    """主函数"""
    # 在函数作用域内声明变量
    db = None
    root = None
    is_cleaning = False  # 标记是否正在清理中
    
    # 调试信息输出函数
    def debug_log_msg(msg):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        debug_msg = f'[{timestamp}] {msg}'
        print(debug_msg, file=sys.stderr)  # 输出到标准错误，避免与GUI冲突
        try:
            with open('debug.log', 'a', encoding='utf-8') as f:
                f.write(debug_msg + '\n')
        except Exception as e:
            print(f'[ERROR] 无法写入调试日志: {e}', file=sys.stderr)
    
    debug_log_msg('=' * 50)
    debug_log_msg('程序开始启动')
    debug_log_msg(f'当前工作目录: {os.getcwd()}')
    debug_log_msg(f'Python路径: {sys.executable}')
    debug_log_msg(f'命令行参数: {sys.argv}')
    debug_log_msg('系统路径:')
    for p in sys.path:
        debug_log_msg(f'  {p}')
    debug_log_msg(f'文件编码: {sys.getdefaultencoding()}')
    debug_log_msg(f'文件系统编码: {sys.getfilesystemencoding()}')
    
    setup_logging()
    
    def cleanup():
        """清理资源"""
        nonlocal db, root, is_cleaning
        is_cleaning = True
        try:
            logging.info("开始清理资源...")
            if db is not None:
                logging.info("正在关闭数据库连接...")
            if hasattr(db, 'conn') and db.conn:  # 检查是否有 conn 属性
                db.conn.close()  # 使用 conn 属性关闭数据库连接
                logging.info("数据库连接已关闭")
            else:
                logging.warning("数据库连接对象不存在或已关闭")
            
            if root is not None:
                logging.info("正在销毁主窗口...")
                try:
                    root.destroy()
                except Exception as e:
                    logging.error(f"销毁主窗口时出错: {e}")
                    
            logging.info("资源清理完成")
        except Exception as e:
            logging.exception("清理资源时发生错误")
            import traceback
            traceback.print_exc()
    
    try:
        # 初始化日志系统
        setup_logger()
        logging.info(f"启动应用，版本: {VERSION}")
        
        # 初始化数据库
        logging.info("正在初始化数据库...")
        db = Database()
        logging.info("数据库初始化完成")
        
        try:
            # 设置路径 - 使用路径管理模块
            app_dir = get_application_path()
            
            # 创建GUI
            logging.info("正在创建主窗口...")
            root = tk.Tk()
            root.title(f"档案检索系统v{VERSION}")
            root.geometry("1200x800")
            
            # 设置窗口关闭时的处理
            def on_closing():
                logging.info("检测到窗口关闭事件...")
                cleanup()
                root.quit()
                
            root.protocol("WM_DELETE_WINDOW", on_closing)
            logging.info("主窗口创建完成")
            
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
            logging.info("正在初始化主窗口组件...")
            main_window = MainWindow(root, db, version=VERSION)
            logging.info("主窗口组件初始化完成")
            
            # 进入主循环
            logging.info("进入主事件循环...")
            root.mainloop()
            logging.info("主事件循环结束")
            
        except Exception as e:
            logging.exception("创建主窗口时发生错误")
            messagebox.showerror("错误", f"无法创建主窗口: {str(e)}")
            raise  # 重新抛出异常，让外部处理
            
    except Exception as e:
        logging.exception("程序初始化失败")
        messagebox.showerror("错误", f"程序初始化失败: {str(e)}")
        return 1  # 返回非零表示错误
        
    finally:
        # 只在 finally 中清理资源，如果还没有被清理过的话
        if not is_cleaning and (db is not None or root is not None):
            cleanup()
        logging.info("程序正常退出")
        return 0  # 返回0表示成功

if __name__ == "__main__":
    main()

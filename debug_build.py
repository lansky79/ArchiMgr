import os
import sys
import traceback
import logging
from datetime import datetime

def setup_logging():
    """设置日志记录"""
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f'debug_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stderr)
        ]
    )
    return log_file

def main():
    """主函数"""
    try:
        # 设置日志
        log_file = setup_logging()
        logging.info("="*50)
        logging.info("开始调试构建...")
        
        # 记录环境信息
        logging.info(f"Python 路径: {sys.executable}")
        logging.info(f"工作目录: {os.getcwd()}")
        logging.info(f"系统路径: {sys.path}")
        
        # 尝试导入必要的模块
        logging.info("\n尝试导入模块...")
        try:
            import tkinter as tk
            from tkinter import messagebox
            logging.info("✅ 成功导入 tkinter")
            
            # 尝试导入项目模块
            try:
                from src.utils.paths import get_icon_path
                logging.info("✅ 成功导入项目模块")
            except ImportError as e:
                logging.error(f"❌ 导入项目模块失败: {e}")
                
            # 测试 tkinter
            try:
                root = tk.Tk()
                root.withdraw()  # 不显示主窗口
                messagebox.showinfo("测试", "Tkinter 运行正常！")
                root.destroy()
                logging.info("✅ Tkinter 测试通过")
            except Exception as e:
                logging.error(f"❌ Tkinter 测试失败: {e}")
                
        except ImportError as e:
            logging.error(f"❌ 导入 tkinter 失败: {e}")
            
        # 检查资源文件
        logging.info("\n检查资源文件...")
        resource_dirs = ['resources', 'config']
        for dir_name in resource_dirs:
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), dir_name)
            if os.path.exists(path):
                logging.info(f"✅ 找到目录: {dir_name}")
            else:
                logging.error(f"❌ 目录不存在: {dir_name}")
        
        # 测试图标文件
        try:
            icon_path = os.path.join('resources', 'app.ico')
            if os.path.exists(icon_path):
                logging.info(f"✅ 找到图标文件: {icon_path}")
            else:
                logging.error(f"❌ 图标文件不存在: {icon_path}")
        except Exception as e:
            logging.error(f"❌ 检查图标文件时出错: {e}")
        
        logging.info("\n调试信息已保存到: " + log_file)
        input("\n按 Enter 键退出...")
        
    except Exception as e:
        error_msg = f"调试过程中发生错误: {str(e)}\n\n{traceback.format_exc()}"
        logging.error(error_msg)
        print(error_msg)
        input("\n按 Enter 键退出...")

if __name__ == "__main__":
    main()

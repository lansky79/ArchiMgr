import os
import sys
import tkinter as tk

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# 导入其他模块
from src.config.logger import setup_logging
from src.ui.main_window import MainWindow
from src.models.database import Database

def main():
    # 设置日志
    setup_logging()
    
    # 创建主窗口
    root = tk.Tk()
    root.title("人事档案软件")
    root.state('zoomed')
    
    # 初始化数据库
    db = Database()
    db.connect()

    
    # 创建主应用，传入数据库连接
    app = MainWindow(root, db)
    
    # 启动主循环
    root.mainloop()

if __name__ == "__main__":
    main()

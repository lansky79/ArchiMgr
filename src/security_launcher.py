#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
档案安全模块启动器
用于启动档案完整性检查工具
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox
import logging
import threading
import json
import datetime

# 确保导入路径正确
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# 导入核心模块
try:
    from core.integrity import IntegrityChecker
    from utils.hash_utils import calculate_file_hash
    from utils.file_utils import scan_directory
    from utils.config_utils import load_config, save_config
    from utils.logging_utils import setup_logger, get_logger
    
    # 设置日志
    log_dir = os.path.join(os.path.expanduser("~"), "ArchiMgr", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"security_{datetime.datetime.now().strftime('%Y%m%d')}.log")
    setup_logger(log_file)
    logger = get_logger("SecurityModule")
    logger.info("安全模块启动器初始化")
except ImportError as e:
    print(f"导入错误: {e}")
    print(f"当前路径: {os.getcwd()}")
    print(f"sys.path: {sys.path}")
    input("按回车键退出...")
    sys.exit(1)

class LogHandler(logging.Handler):
    """将日志输出到文本控件的处理器"""
    def __init__(self, text_widget):
        logging.Handler.__init__(self)
        self.text_widget = text_widget
        self.formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    def emit(self, record):
        msg = self.formatter.format(record)
        def append():
            self.text_widget.configure(state='normal')
            self.text_widget.insert(tk.END, msg + '\n')
            self.text_widget.see(tk.END)
            self.text_widget.configure(state='disabled')
        # 在主线程中更新UI
        self.text_widget.after(0, append)

class IntegrityCheckApp:
    """完整性检查应用程序"""
    def __init__(self, root):
        self.root = root
        self.root.title("档案完整性检查工具")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # 配置
        self.config_file = os.path.join(os.path.expanduser("~"), "ArchiMgr", "config", "integrity_check.json")
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        self.config = self.load_config()
        
        # 创建界面
        self.create_ui()
        
        # 设置日志输出到文本控件
        self.log_handler = LogHandler(self.log_text)
        logger.addHandler(self.log_handler)
        
        logger.info("档案完整性检查工具已启动")
        
    def load_config(self):
        """加载配置"""
        default_config = {
            "archive_dir": "",
            "database_file": ""
        }
        try:
            if os.path.exists(self.config_file):
                config = load_config(self.config_file)
                logger.info(f"已加载配置: {self.config_file}")
                # 确保所有必要的键都存在
                for key in default_config:
                    if key not in config:
                        config[key] = default_config[key]
                return config
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
        
        return default_config
    
    def save_config(self):
        """保存配置"""
        try:
            save_config(self.config_file, self.config)
            logger.info(f"已保存配置: {self.config_file}")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
    
    def create_ui(self):
        """创建用户界面"""
        # 创建主框架
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建顶部控制区域
        control_frame = tk.LabelFrame(main_frame, text="控制面板", padx=10, pady=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 档案目录设置
        dir_frame = tk.Frame(control_frame)
        dir_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(dir_frame, text="档案目录:").pack(side=tk.LEFT)
        self.dir_entry = tk.Entry(dir_frame)
        self.dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
        if self.config["archive_dir"]:
            self.dir_entry.insert(0, self.config["archive_dir"])
        
        browse_dir_btn = tk.Button(dir_frame, text="浏览...", command=self.browse_directory)
        browse_dir_btn.pack(side=tk.RIGHT)
        
        # 数据库文件设置
        db_frame = tk.Frame(control_frame)
        db_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(db_frame, text="数据库文件:").pack(side=tk.LEFT)
        self.db_entry = tk.Entry(db_frame)
        self.db_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
        if self.config["database_file"]:
            self.db_entry.insert(0, self.config["database_file"])
        
        browse_db_btn = tk.Button(db_frame, text="浏览...", command=self.browse_database)
        browse_db_btn.pack(side=tk.RIGHT)
        
        # 操作按钮
        btn_frame = tk.Frame(control_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        self.build_btn = tk.Button(btn_frame, text="构建完整性数据库", command=self.build_database)
        self.build_btn.pack(side=tk.LEFT, padx=5)
        
        self.verify_btn = tk.Button(btn_frame, text="验证文件完整性", command=self.verify_integrity)
        self.verify_btn.pack(side=tk.LEFT, padx=5)
        
        self.update_btn = tk.Button(btn_frame, text="更新完整性数据库", command=self.update_database)
        self.update_btn.pack(side=tk.LEFT, padx=5)
        
        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = tk.Label(main_frame, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 日志显示区域
        log_frame = tk.LabelFrame(main_frame, text="操作日志", padx=10, pady=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建滚动条
        scrollbar = tk.Scrollbar(log_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 创建文本控件
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.configure(state='disabled')
        
        # 配置滚动条
        scrollbar.config(command=self.log_text.yview)
    
    def browse_directory(self):
        """浏览选择档案目录"""
        from tkinter import filedialog
        directory = filedialog.askdirectory(title="选择档案目录")
        if directory:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, directory)
            self.config["archive_dir"] = directory
            self.save_config()
            logger.info(f"已设置档案目录: {directory}")
    
    def browse_database(self):
        """浏览选择数据库文件"""
        from tkinter import filedialog
        file_path = filedialog.asksaveasfilename(
            title="选择数据库文件",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        if file_path:
            self.db_entry.delete(0, tk.END)
            self.db_entry.insert(0, file_path)
            self.config["database_file"] = file_path
            self.save_config()
            logger.info(f"已设置数据库文件: {file_path}")
    
    def update_status(self, message):
        """更新状态栏"""
        self.status_var.set(message)
    
    def disable_buttons(self):
        """禁用按钮"""
        self.build_btn.config(state=tk.DISABLED)
        self.verify_btn.config(state=tk.DISABLED)
        self.update_btn.config(state=tk.DISABLED)
    
    def enable_buttons(self):
        """启用按钮"""
        self.build_btn.config(state=tk.NORMAL)
        self.verify_btn.config(state=tk.NORMAL)
        self.update_btn.config(state=tk.NORMAL)
    
    def build_database(self):
        """构建完整性数据库"""
        archive_dir = self.dir_entry.get()
        database_file = self.db_entry.get()
        
        if not archive_dir or not database_file:
            messagebox.showwarning("警告", "请先设置档案目录和数据库文件")
            return
        
        self.disable_buttons()
        self.update_status("正在构建完整性数据库...")
        
        def task():
            try:
                checker = IntegrityChecker(archive_dir, database_file)
                checker.build_database()
                self.root.after(0, lambda: self.update_status("完整性数据库构建完成"))
            except Exception as e:
                logger.error(f"构建完整性数据库失败: {e}")
                self.root.after(0, lambda: self.update_status("构建失败"))
            finally:
                self.root.after(0, self.enable_buttons)
        
        threading.Thread(target=task).start()
    
    def verify_integrity(self):
        """验证文件完整性"""
        archive_dir = self.dir_entry.get()
        database_file = self.db_entry.get()
        
        if not archive_dir or not database_file:
            messagebox.showwarning("警告", "请先设置档案目录和数据库文件")
            return
        
        if not os.path.exists(database_file):
            messagebox.showwarning("警告", "数据库文件不存在，请先构建完整性数据库")
            return
        
        self.disable_buttons()
        self.update_status("正在验证文件完整性...")
        
        def task():
            try:
                checker = IntegrityChecker(archive_dir, database_file)
                result = checker.verify_integrity()
                
                # 显示结果统计
                modified_count = len(result.get('modified', []))
                missing_count = len(result.get('missing', []))
                new_count = len(result.get('new', []))
                
                summary = f"完整性验证完成: 修改={modified_count}, 丢失={missing_count}, 新增={new_count}"
                logger.info(summary)
                
                # 显示详细结果
                if modified_count > 0:
                    logger.info("修改的文件:")
                    for item in result.get('modified', []):
                        logger.info(f"  {item}")
                
                if missing_count > 0:
                    logger.info("丢失的文件:")
                    for item in result.get('missing', []):
                        logger.info(f"  {item}")
                
                if new_count > 0:
                    logger.info("新增的文件:")
                    for item in result.get('new', []):
                        logger.info(f"  {item}")
                
                self.root.after(0, lambda: self.update_status(summary))
            except Exception as e:
                logger.error(f"验证文件完整性失败: {e}")
                self.root.after(0, lambda: self.update_status("验证失败"))
            finally:
                self.root.after(0, self.enable_buttons)
        
        threading.Thread(target=task).start()
    
    def update_database(self):
        """更新完整性数据库"""
        archive_dir = self.dir_entry.get()
        database_file = self.db_entry.get()
        
        if not archive_dir or not database_file:
            messagebox.showwarning("警告", "请先设置档案目录和数据库文件")
            return
        
        if not os.path.exists(database_file):
            messagebox.showwarning("警告", "数据库文件不存在，请先构建完整性数据库")
            return
        
        self.disable_buttons()
        self.update_status("正在更新完整性数据库...")
        
        def task():
            try:
                checker = IntegrityChecker(archive_dir, database_file)
                checker.update_database()
                self.root.after(0, lambda: self.update_status("完整性数据库更新完成"))
            except Exception as e:
                logger.error(f"更新完整性数据库失败: {e}")
                self.root.after(0, lambda: self.update_status("更新失败"))
            finally:
                self.root.after(0, self.enable_buttons)
        
        threading.Thread(target=task).start()

def main():
    """主函数"""
    root = tk.Tk()
    app = IntegrityCheckApp(root)
    root.mainloop()

if __name__ == "__main__":
    main() 
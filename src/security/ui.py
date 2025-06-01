#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
安全模块UI组件 - 提供安全功能的图形界面组件
"""

import os
import sys
import time
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import logging
from datetime import datetime

# 导入安全模块
try:
    from src.security.integrity import IntegrityChecker
except ImportError:
    # 打包环境
    from security.integrity import IntegrityChecker

class LogHandler(logging.Handler):
    """将日志输出到文本控件的处理器"""
    
    def __init__(self, text_widget):
        """初始化处理器"""
        logging.Handler.__init__(self)
        self.text_widget = text_widget
        
        # 设置格式化器
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.setFormatter(formatter)
    
    def emit(self, record):
        """输出日志记录"""
        msg = self.format(record)
        
        # 在UI线程中更新文本控件
        def update():
            self.text_widget.configure(state='normal')
            self.text_widget.insert(tk.END, msg + '\n')
            self.text_widget.see(tk.END)
            self.text_widget.configure(state='disabled')
        
        # 确保在主线程中更新UI
        if self.text_widget.winfo_exists():
            self.text_widget.after(0, update)

class IntegrityCheckDialog(tk.Toplevel):
    """档案完整性检查对话框"""
    
    def __init__(self, parent, archives_dir=None):
        """初始化对话框"""
        super().__init__(parent)
        self.title("档案完整性检查")
        self.geometry("800x600")
        self.minsize(600, 500)
        
        # 设置模态对话框
        self.transient(parent)
        self.grab_set()
        
        # 初始化变量
        self.archives_dir = archives_dir
        self.database_path = None
        
        # 创建日志记录器
        self.logger = logging.getLogger('security.ui.integrity')
        
        # 创建完整性检查器
        self.integrity_checker = IntegrityChecker(
            archives_dir=self.archives_dir,
            database_path=self.database_path
        )
        
        # 创建UI组件
        self.create_widgets()
        
        # 居中显示
        self.center_window()
        
        # 运行中的线程
        self.running_thread = None
        
        # 添加窗口关闭处理
        self.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def create_widgets(self):
        """创建UI组件"""
        # 主框架
        main_frame = ttk.Frame(self, padding=(10, 10, 10, 10))
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建选项框架
        options_frame = ttk.LabelFrame(main_frame, text="档案设置", padding=(5, 5, 5, 10))
        options_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 档案目录设置
        ttk.Label(options_frame, text="档案目录:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.dir_var = tk.StringVar(value=self.archives_dir or "")
        dir_entry = ttk.Entry(options_frame, textvariable=self.dir_var, width=50)
        dir_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        ttk.Button(options_frame, text="浏览...", command=self.browse_archives_dir).grid(row=0, column=2, padx=5, pady=5)
        
        # 数据库文件设置
        ttk.Label(options_frame, text="数据库文件:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.db_var = tk.StringVar(value=self.database_path or "")
        db_entry = ttk.Entry(options_frame, textvariable=self.db_var, width=50)
        db_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        ttk.Button(options_frame, text="浏览...", command=self.browse_database_file).grid(row=1, column=2, padx=5, pady=5)
        
        # 设置列权重
        options_frame.columnconfigure(1, weight=1)
        
        # 创建操作按钮框架
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 添加操作按钮
        self.build_btn = ttk.Button(buttons_frame, text="构建完整性数据库", command=self.build_database)
        self.build_btn.pack(side=tk.LEFT, padx=5)
        
        self.verify_btn = ttk.Button(buttons_frame, text="验证文件完整性", command=self.verify_integrity)
        self.verify_btn.pack(side=tk.LEFT, padx=5)
        
        self.update_btn = ttk.Button(buttons_frame, text="更新完整性数据库", command=self.update_database)
        self.update_btn.pack(side=tk.LEFT, padx=5)
        
        self.abort_btn = ttk.Button(buttons_frame, text="中止操作", command=self.abort_operation, state=tk.DISABLED)
        self.abort_btn.pack(side=tk.LEFT, padx=5)
        
        # 创建状态框架
        status_frame = ttk.LabelFrame(main_frame, text="状态", padding=(5, 5, 5, 5))
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 添加进度条
        ttk.Label(status_frame, text="进度:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, length=100, mode='determinate')
        self.progress_bar.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # 添加状态标签
        ttk.Label(status_frame, text="当前文件:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, wraplength=500)
        status_label.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 设置列权重
        status_frame.columnconfigure(1, weight=1)
        
        # 创建日志框架
        log_frame = ttk.LabelFrame(main_frame, text="操作日志", padding=(5, 5, 5, 5))
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 添加日志文本框
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, width=80, height=15)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text['yscrollcommand'] = scrollbar.set
        
        # 禁用文本编辑
        self.log_text.config(state=tk.DISABLED)
        
        # 添加日志处理器
        log_handler = LogHandler(self.log_text)
        logging.getLogger('security').addHandler(log_handler)
        
        # 添加关闭按钮
        close_btn = ttk.Button(main_frame, text="关闭", command=self.on_close)
        close_btn.pack(side=tk.RIGHT, padx=5, pady=10)
    
    def center_window(self):
        """居中显示窗口"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def browse_archives_dir(self):
        """浏览选择档案目录"""
        dir_path = filedialog.askdirectory(title="选择档案目录")
        if dir_path:
            self.dir_var.set(dir_path)
            self.archives_dir = dir_path
            self.integrity_checker.archives_dir = dir_path
    
    def browse_database_file(self):
        """浏览选择数据库文件"""
        file_path = filedialog.asksaveasfilename(
            title="选择数据库文件",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        if file_path:
            self.db_var.set(file_path)
            self.database_path = file_path
            self.integrity_checker.database_path = file_path
    
    def update_progress(self, progress, current_file):
        """更新进度显示"""
        self.progress_var.set(progress)
        if current_file:
            # 显示相对路径
            if self.archives_dir and current_file.startswith(self.archives_dir):
                rel_path = os.path.relpath(current_file, self.archives_dir)
                self.status_var.set(rel_path)
            else:
                self.status_var.set(current_file)
    
    def build_database(self):
        """构建完整性数据库"""
        # 检查档案目录
        if not self.archives_dir or not os.path.isdir(self.archives_dir):
            messagebox.showerror("错误", "请选择有效的档案目录")
            return
        
        # 设置数据库路径（如果未指定）
        if not self.database_path:
            config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'config')
            os.makedirs(config_dir, exist_ok=True)
            self.database_path = os.path.join(config_dir, 'integrity_db.json')
            self.db_var.set(self.database_path)
            self.integrity_checker.database_path = self.database_path
        
        # 禁用按钮
        self.disable_buttons()
        
        # 在后台线程中执行操作
        self.running_thread = threading.Thread(target=self._build_database_thread)
        self.running_thread.daemon = True
        self.running_thread.start()
        
        # 启动进度更新定时器
        self.after(100, self.update_progress_timer)
    
    def _build_database_thread(self):
        """构建数据库的后台线程"""
        success = self.integrity_checker.build_database()
        
        # 在UI线程中更新状态
        self.after(0, lambda: self.on_operation_complete(
            success, 
            "完整性数据库构建完成" if success else "完整性数据库构建失败"
        ))
    
    def verify_integrity(self):
        """验证文件完整性"""
        # 检查数据库文件
        if not self.database_path or not os.path.exists(self.database_path):
            messagebox.showerror("错误", "请先构建或选择有效的完整性数据库文件")
            return
        
        # 禁用按钮
        self.disable_buttons()
        
        # 在后台线程中执行操作
        self.running_thread = threading.Thread(target=self._verify_integrity_thread)
        self.running_thread.daemon = True
        self.running_thread.start()
        
        # 启动进度更新定时器
        self.after(100, self.update_progress_timer)
    
    def _verify_integrity_thread(self):
        """验证完整性的后台线程"""
        result = self.integrity_checker.verify_integrity()
        
        # 在UI线程中更新状态
        self.after(0, lambda: self.on_verification_complete(result))
    
    def update_database(self):
        """更新完整性数据库"""
        # 检查数据库文件
        if not self.database_path or not os.path.exists(self.database_path):
            messagebox.showerror("错误", "请先构建或选择有效的完整性数据库文件")
            return
        
        # 禁用按钮
        self.disable_buttons()
        
        # 在后台线程中执行操作
        self.running_thread = threading.Thread(target=self._update_database_thread)
        self.running_thread.daemon = True
        self.running_thread.start()
        
        # 启动进度更新定时器
        self.after(100, self.update_progress_timer)
    
    def _update_database_thread(self):
        """更新数据库的后台线程"""
        success = self.integrity_checker.update_database()
        
        # 在UI线程中更新状态
        self.after(0, lambda: self.on_operation_complete(
            success, 
            "完整性数据库更新完成" if success else "完整性数据库更新失败"
        ))
    
    def update_progress_timer(self):
        """定时更新进度"""
        if self.running_thread and self.running_thread.is_alive():
            # 获取当前进度
            progress_info = self.integrity_checker.get_progress()
            
            # 更新UI
            self.update_progress(progress_info['progress'], progress_info['current_file'])
            
            # 继续定时更新
            self.after(100, self.update_progress_timer)
        else:
            # 操作已完成，恢复按钮状态
            if not self.running_thread:
                self.enable_buttons()
    
    def on_operation_complete(self, success, message):
        """操作完成时的处理"""
        # 启用按钮
        self.enable_buttons()
        
        # 显示完成消息
        if success:
            messagebox.showinfo("完成", message)
        else:
            messagebox.showerror("错误", message)
        
        # 重置进度条
        self.progress_var.set(0)
        self.status_var.set("就绪")
    
    def on_verification_complete(self, result):
        """验证完成时的处理"""
        # 启用按钮
        self.enable_buttons()
        
        # 检查验证结果
        if result['status'] == 'success':
            # 构建报告消息
            message = f"档案完整性验证完成\n\n"
            message += f"验证时间: {result['verified_time']}\n"
            message += f"数据库创建时间: {result['database_time']}\n"
            message += f"档案目录: {result['archives_dir']}\n\n"
            message += f"总文件数: {result['total_files']}\n"
            message += f"验证通过: {result['verified_files']}\n"
            message += f"已修改文件: {len(result['modified_files'])}\n"
            message += f"丢失文件: {len(result['missing_files'])}\n"
            message += f"新增文件: {len(result['new_files'])}\n\n"
            
            # 显示详细报告
            self.show_verification_details(result)
            
        else:
            # 显示错误消息
            messagebox.showerror("验证失败", f"档案完整性验证失败: {result.get('message', '未知错误')}")
        
        # 重置进度条
        self.progress_var.set(0)
        self.status_var.set("就绪")
    
    def show_verification_details(self, result):
        """显示验证详细信息"""
        # 创建详细信息窗口
        details_dialog = tk.Toplevel(self)
        details_dialog.title("档案完整性验证结果")
        details_dialog.geometry("700x500")
        details_dialog.minsize(600, 400)
        
        # 使窗口成为模态
        details_dialog.transient(self)
        details_dialog.grab_set()
        
        # 创建主框架
        main_frame = ttk.Frame(details_dialog, padding=(10, 10, 10, 10))
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 添加统计信息
        stats_frame = ttk.LabelFrame(main_frame, text="验证统计", padding=(5, 5, 5, 5))
        stats_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 格式化统计信息
        stats_text = f"验证时间: {result['verified_time']}\n"
        stats_text += f"数据库时间: {result['database_time']}\n"
        stats_text += f"总文件数: {result['total_files']}   "
        stats_text += f"验证通过: {result['verified_files']}   "
        stats_text += f"修改: {len(result['modified_files'])}   "
        stats_text += f"丢失: {len(result['missing_files'])}   "
        stats_text += f"新增: {len(result['new_files'])}"
        
        stats_label = ttk.Label(stats_frame, text=stats_text, wraplength=650)
        stats_label.pack(fill=tk.X, padx=5, pady=5)
        
        # 创建选项卡控件
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 添加已修改文件选项卡
        modified_frame = ttk.Frame(notebook, padding=(5, 5, 5, 5))
        notebook.add(modified_frame, text=f"已修改文件 ({len(result['modified_files'])})")
        
        # 添加丢失文件选项卡
        missing_frame = ttk.Frame(notebook, padding=(5, 5, 5, 5))
        notebook.add(missing_frame, text=f"丢失文件 ({len(result['missing_files'])})")
        
        # 添加新增文件选项卡
        new_frame = ttk.Frame(notebook, padding=(5, 5, 5, 5))
        notebook.add(new_frame, text=f"新增文件 ({len(result['new_files'])})")
        
        # 填充已修改文件列表
        self._fill_file_list(modified_frame, result['modified_files'], "已修改文件")
        
        # 填充丢失文件列表
        self._fill_file_list(missing_frame, result['missing_files'], "丢失文件")
        
        # 填充新增文件列表
        self._fill_file_list(new_frame, result['new_files'], "新增文件")
        
        # 添加关闭按钮
        close_btn = ttk.Button(main_frame, text="关闭", command=details_dialog.destroy)
        close_btn.pack(side=tk.RIGHT, padx=5, pady=10)
        
        # 居中显示窗口
        details_dialog.update_idletasks()
        width = details_dialog.winfo_width()
        height = details_dialog.winfo_height()
        x = (details_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (details_dialog.winfo_screenheight() // 2) - (height // 2)
        details_dialog.geometry(f'{width}x{height}+{x}+{y}')
    
    def _fill_file_list(self, parent, file_list, title):
        """填充文件列表"""
        if not file_list:
            # 如果没有文件，显示空消息
            label = ttk.Label(parent, text=f"没有{title}")
            label.pack(fill=tk.X, padx=5, pady=20)
            return
        
        # 创建列表框架
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建滚动条
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 创建列表框
        listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set, font=('Microsoft YaHei', 10))
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 配置滚动条
        scrollbar.config(command=listbox.yview)
        
        # 添加文件到列表
        for file_path in file_list:
            listbox.insert(tk.END, file_path)
        
        # 双击打开文件
        def on_double_click(event):
            selection = listbox.curselection()
            if selection:
                file_path = file_list[selection[0]]
                full_path = os.path.join(result['archives_dir'], file_path)
                if os.path.exists(full_path):
                    try:
                        if sys.platform == 'win32':
                            os.startfile(full_path)
                        elif sys.platform == 'darwin':
                            import subprocess
                            subprocess.call(['open', full_path])
                        else:
                            import subprocess
                            subprocess.call(['xdg-open', full_path])
                    except Exception as e:
                        self.logger.error(f"打开文件时出错: {str(e)}")
                        messagebox.showerror("错误", f"无法打开文件: {str(e)}")
        
        listbox.bind('<Double-1>', on_double_click)
    
    def disable_buttons(self):
        """禁用操作按钮"""
        self.build_btn.config(state=tk.DISABLED)
        self.verify_btn.config(state=tk.DISABLED)
        self.update_btn.config(state=tk.DISABLED)
        self.abort_btn.config(state=tk.NORMAL)
    
    def enable_buttons(self):
        """启用操作按钮"""
        self.build_btn.config(state=tk.NORMAL)
        self.verify_btn.config(state=tk.NORMAL)
        self.update_btn.config(state=tk.NORMAL)
        self.abort_btn.config(state=tk.DISABLED)
    
    def abort_operation(self):
        """中止当前操作"""
        if self.running_thread and self.running_thread.is_alive():
            # 设置中止标志
            self.integrity_checker.abort()
            self.logger.info("正在中止操作...")
            self.status_var.set("正在中止...")
    
    def on_close(self):
        """关闭窗口时的处理"""
        # 中止操作（如果正在运行）
        if self.running_thread and self.running_thread.is_alive():
            self.integrity_checker.abort()
            self.logger.info("等待操作完成...")
            self.running_thread.join(2.0)  # 等待最多2秒
        
        # 移除日志处理器
        for handler in logging.getLogger('security').handlers:
            if isinstance(handler, LogHandler) and handler.text_widget == self.log_text:
                logging.getLogger('security').removeHandler(handler)
        
        # 关闭窗口
        self.destroy() 
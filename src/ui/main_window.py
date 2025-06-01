import tkinter as tk
from tkinter import ttk
import logging
import shutil
import os
from tkinter import filedialog, messagebox, simpledialog
import pandas as pd
import subprocess
import sys
import re
import time
import json
import hashlib
import socket
import datetime
from tkinter import font as tkfont
from tkinter import scrolledtext

# 使用兼容性导入
try:
    # 打包环境下的导入方式
    if getattr(sys, 'frozen', False):
        from utils.excel_utils import get_excel_info, ExcelFileNotFound
    else:
        # 开发环境下的导入方式
        from src.utils.excel_utils import get_excel_info, ExcelFileNotFound
except ImportError as e:
    import logging
    logging.error(f"导入excel_utils模块失败: {e}")
    # 不直接退出，让程序继续运行并在需要时报错

class MainWindow:
    def __init__(self, root, db=None, version="1.0"):
        self.root = root
        self.db = db
        self.version = version
        
        # 设置日志级别和格式 - 正式版为INFO级别
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        
        # 确保至少有一个处理器，否则添加一个
        if not logger.handlers:
            # 创建控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # 设置日志格式
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            
            # 添加处理器到日志记录器
            logger.addHandler(console_handler)
            
            # 添加文件处理器
            log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'logs')
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, f"app_{time.strftime('%Y%m%d')}.log")
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
            logging.info("初始化日志系统完成")
        
        logging.info("=== 档案检索系统启动 ===")
        
        logging.info(f"系统版本: {self.version}")
        
        # 初始化文件列表和分类映射
        self.all_files = []
        self.category_mapping = {}
        self.version = version
        self.db = db
        self.root = root
        
        # 配置目录
        self.config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'config')
        os.makedirs(self.config_dir, exist_ok=True)
        
        # 设置文件路径
        self.settings_file = os.path.join(self.config_dir, 'user_settings.json')
        
        # 注册文件路径
        self.registration_file = os.path.join(self.config_dir, 'registration.dat')
        
        # 注册状态
        self.is_registered = False
        self.current_org = None  # 当前注册单位
        
        # 检查是否已注册
        if os.path.exists(self.registration_file) and os.path.getsize(self.registration_file) > 0:
            logging.debug(f"注册文件存在: {self.registration_file}, 正在检查注册状态")
            self.is_registered = self.check_registration()
        else:
            logging.debug(f"注册文件不存在或为空: {self.registration_file}, 状态设为未注册")
            self.is_registered = False
        
        logging.info(f"注册状态: {'已注册' if self.is_registered else '未注册'}")
        
        # 加载用户设置
        self.settings = self.load_settings()
        
        # 导入文件的根目录（从设置中加载）
        self.import_root_dir = self.settings.get('import_root_dir')
        
        # 登录状态
        self.current_user = None
        self.login_status_var = tk.StringVar()
        self.login_status_var.set("未登录")
        
        # 确保数据库中有users表并初始化管理员账号
        self.init_users_table()
        self.create_admin_user()
        
        # 工具菜单引用，用于权限控制
        self.tools_menu = None
        
        # 设置UI
        self.setup_ui()
        
        # 初始化数据
        self.init_data()
        
        self.current_search_name = None  # 添加当前搜索人名的记录
        self.current_search_id = None  # 添加当前搜索编号的记录
        self.has_searched = False  # 标记是否进行过搜索
        
        # 初始状态为未登录
        self.current_user = None
        self.login_status_var.set("未登录")
        self.update_menu_by_role(None)
        self.update_tools_permission(False)
        
        # 根据注册状态更新界面
        self.update_ui_by_registration()
        
        # 获取本地IP地址
        self.local_ip = self._get_local_ip()
        logging.info(f"本地IP地址: {self.local_ip}")
        
    def _get_local_ip(self):
        """获取本地IP地址"""
        try:
            # 创建一个临时socket连接，获取本地IP地址
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # 不需要真正连接
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception as e:
            logging.error(f"获取本地IP地址失败: {str(e)}")
            return "127.0.0.1"  # 返回本地回环地址作为默认值
    
    def init_users_table(self):
        """初始化用户表"""
        try:
            self.db.cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    real_name TEXT,
                    role TEXT DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            self.db.conn.commit()
            logging.info("用户表初始化完成")
        except Exception as e:
            logging.error(f"初始化用户表失败: {str(e)}")
            
    def create_admin_user(self):
        """创建管理员账号"""
        try:
            # 检查管理员账号是否存在
            self.db.cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', ('admin',))
            if self.db.cursor.fetchone()[0] == 0:
                # 创建管理员账号
                hashed_password = self.hash_password('admin123')
                self.db.cursor.execute(
                    'INSERT INTO users (username, password, real_name, role) VALUES (?, ?, ?, ?)',
                    ('admin', hashed_password, '系统管理员', 'admin')
                )
                self.db.conn.commit()
                logging.info("已创建管理员账号")
            else:
                logging.info("管理员账号已存在")
        except Exception as e:
            logging.error(f"创建管理员账号失败: {str(e)}")
            
    def update_menu_by_role(self, role):
        """根据用户角色更新菜单"""
        # 清空文件菜单
        self.file_menu.delete(0, tk.END)
        
        if role == 'admin':
            # 管理员菜单
            self.file_menu.add_command(label="修改密码", command=self.show_change_password_dialog)
            self.file_menu.add_command(label="添加用户", command=self.show_register_dialog)
            self.file_menu.add_command(label="退出登录", command=self.logout)
            self.file_menu.add_separator()
            self.file_menu.add_command(label="退出系统", command=self.root.quit)
            
            # 启用工具菜单
            self.update_tools_permission(True)
            
            # 启用日志菜单
            self.log_menu.entryconfigure("查看操作日志", state=tk.NORMAL)
            self.log_menu.entryconfigure("导出日志", state=tk.NORMAL)
            
        elif role == 'user':
            # 普通用户菜单
            self.file_menu.add_command(label="退出登录", command=self.logout)
            self.file_menu.add_separator()
            self.file_menu.add_command(label="退出系统", command=self.root.quit)
            
            # 禁用工具菜单
            self.update_tools_permission(False)
            
            # 禁用日志菜单
            self.log_menu.entryconfigure("查看操作日志", state=tk.DISABLED)
            self.log_menu.entryconfigure("导出日志", state=tk.DISABLED)
            
        else:
            # 未登录菜单
            self.file_menu.add_command(label="登录", command=self.show_login_dialog)
            self.file_menu.add_separator()
            self.file_menu.add_command(label="退出系统", command=self.root.quit)
            
            # 禁用日志菜单
            self.log_menu.entryconfigure("查看操作日志", state=tk.DISABLED)
            self.log_menu.entryconfigure("导出日志", state=tk.DISABLED)
        
    def update_tools_permission(self, is_admin):
        """更新工具栏权限"""
        if hasattr(self, 'import_file_btn'):
            # 搜索按钮和导入文件按钮状态 - 只要登录了（无论是管理员还是普通用户）就可以使用
            if self.current_user:  # 如果已登录（任何角色）
                # 启用搜索按钮
                if hasattr(self, 'search_button'):
                    self.search_button.config(state=tk.NORMAL)
                # 启用导入文件按钮
                self.import_file_btn.config(state=tk.NORMAL)
            else:  # 未登录
                # 禁用搜索按钮
                if hasattr(self, 'search_button'):
                    self.search_button.config(state=tk.DISABLED)
                # 禁用导入文件按钮
                self.import_file_btn.config(state=tk.DISABLED)
            
            # 管理员特有权限
            if is_admin:
                # 启用清理数据库菜单
                if hasattr(self, 'tools_menu'):
                    self.tools_menu.entryconfigure("清理数据库", state=tk.NORMAL)
                # 启用安全菜单
                if hasattr(self, 'security_menu'):
                    self.security_menu.entryconfigure("档案完整性检查", state=tk.NORMAL)
            else:
                # 禁用清理数据库菜单
                if hasattr(self, 'tools_menu'):
                    self.tools_menu.entryconfigure("清理数据库", state=tk.DISABLED)
                # 禁用安全菜单
                if hasattr(self, 'security_menu'):
                    self.security_menu.entryconfigure("档案完整性检查", state=tk.DISABLED)

    def setup_ui(self):
        """设置用户界面"""
        # 设置窗口标题
        self.root.title(f"档案检索系统 {self.version}")
        
        # 设置窗口大小和位置
        window_width = 1024
        window_height = 768
        self.root.geometry(f"{window_width}x{window_height}")
        self.root.minsize(800, 600)  # 设置最小尺寸
        
        # 将窗口居中
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 创建菜单栏
        self.create_menu()
        
        # 创建工具栏
        self.create_toolbar()
        
        # 初始化搜索结果状态变量
        self.search_result_var = tk.StringVar()
        self.search_result_var.set("就绪")
        
        # 创建主框架
        self.create_main_frame()
        
        # 创建状态栏（最后创建，显示在底部）
        self.create_status_bar()
        
        # 确保状态栏显示与注册状态一致（调试）
        logging.debug(f"初始化UI完成，注册状态: {'已注册' if self.is_registered else '未注册'}")
        if hasattr(self, 'reg_status_var'):
            status_text = self.reg_status_var.get()
            logging.debug(f"状态栏显示: {status_text}")
            
            # 确保状态栏显示与注册状态一致
            expected_status = "已注册" if self.is_registered else "未注册"
            if expected_status not in status_text:
                logging.warning(f"状态栏显示与注册状态不一致，强制更新")
                self.update_status_bar()
        
    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        self.file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=self.file_menu)
        
        # 先添加登录选项（默认显示）
        self.file_menu.add_command(label="登录", command=self.show_login_dialog)
        
        # 帮助菜单
        self.help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=self.help_menu)
        self.help_menu.add_command(label="使用说明", command=self.show_help)
        
        # 添加用户注册选项（未注册时可用）
        self.help_menu.add_command(label="用户注册", command=self.show_registration_dialog)
        
        # 根据注册状态设置注册菜单项的状态
        # reg_state = tk.DISABLED if self.is_registered else tk.NORMAL
        # self.help_menu.entryconfigure("用户注册", state=reg_state)
        
        self.help_menu.add_command(label="关于", command=self.show_about)
        
        # 工具菜单
        self.tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=self.tools_menu)
        self.tools_menu.add_command(label="打开程序安装目录", command=self.open_install_directory)
        self.tools_menu.add_command(label="打开档案文件目录", command=self.open_archive_directory)
        self.tools_menu.add_command(label="打开数据库位置", command=self.open_database_location)
        self.tools_menu.add_separator()
        self.tools_menu.add_command(label="清理数据库", command=self.cleanup_database)
        
        # 安全菜单
        self.security_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="安全", menu=self.security_menu)
        self.security_menu.add_command(label="档案完整性检查", command=self.show_integrity_check)
        
        # 日志菜单
        self.log_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="日志", menu=self.log_menu)
        self.log_menu.add_command(label="查看操作日志", command=self.show_operation_logs)
        self.log_menu.add_command(label="导出日志", command=self.export_logs)
        
        # 用户管理菜单（初始时不显示，管理员登录后再添加）
        self.user_menu = tk.Menu(menubar, tearoff=0)
        
        # 初始不添加到菜单栏，管理员登录后再添加
        self.user_menu_index = None
        
    def create_toolbar(self):
        """创建工具栏"""
        toolbar_frame = ttk.Frame(self.root)
        toolbar_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 左侧按钮框架
        button_frame = ttk.Frame(toolbar_frame)
        button_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        # 导入文件按钮
        self.import_file_btn = ttk.Button(
            button_frame, 
            text="导入档案", 
            command=self.import_files
        )
        self.import_file_btn.pack(side=tk.LEFT)
        
        # 右侧搜索框架
        search_frame = ttk.Frame(toolbar_frame)
        search_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        # 登录状态显示
        login_status_label = ttk.Label(search_frame, textvariable=self.login_status_var)
        login_status_label.pack(side=tk.RIGHT, padx=(10, 0))
        
        # 姓名搜索框
        name_label = ttk.Label(search_frame, text="姓名:")
        name_label.pack(side=tk.LEFT, padx=(0, 2))
        self.search_name_var = tk.StringVar()
        name_entry = ttk.Entry(search_frame, textvariable=self.search_name_var, width=10)
        name_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # 编号搜索框
        id_label = ttk.Label(search_frame, text="编号:")
        id_label.pack(side=tk.LEFT, padx=(0, 2))
        self.search_id_var = tk.StringVar()
        id_entry = ttk.Entry(search_frame, textvariable=self.search_id_var, width=10)
        id_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # 搜索按钮
        self.search_button = ttk.Button(search_frame, text="搜索", command=self.search_person)
        self.search_button.pack(side=tk.LEFT)
        
    def create_main_frame(self):
        """创建主框架"""
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建左右分隔窗口
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # 创建白色背景样式
        style = ttk.Style()
        style.configure('White.TFrame', background='white')
        
        # 创建左侧框架（用于分类树）
        self.left_frame = ttk.Frame(paned, style='White.TFrame')
        paned.add(self.left_frame, weight=1)
        
        # 创建右侧框架（用于文件列表）
        self.right_frame = ttk.Frame(paned)
        paned.add(self.right_frame, weight=3)
        
        # 设置分类树
        self.setup_category_tree()
        
        # 设置文件列表
        self.setup_file_list()
        
    def setup_category_tree(self):
        """设置分类树"""
        # 创建树形控件，使用borderwidth=0去掉边框
        self.tree = ttk.Treeview(self.left_frame, show='tree')
        
        # 设置样式去掉边框和背景色
        style = ttk.Style()
        style.configure("Treeview", borderwidth=0, background='white')
        # 修改选中项的背景色为蓝色，前景色（文字）为白色
        style.map("Treeview", 
                 background=[('selected', '#0078d7')],
                 foreground=[('selected', 'white')])
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # 添加滚动条，只在需要时显示
        scrollbar = ttk.Scrollbar(self.left_frame, orient=tk.VERTICAL, command=self.tree.yview)
        
        # 配置滚动条和树形控件的关联
        def set_scrollbar(*args):
            # 只在内容超出可视区域时显示滚动条
            if float(args[0]) == 0.0 and float(args[1]) == 1.0:
                scrollbar.pack_forget()  # 隐藏滚动条
            else:
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)  # 显示滚动条
        
        self.tree.configure(yscrollcommand=set_scrollbar)
        # 初始不显示滚动条，等待内容加载后再决定
        
        # 绑定选择事件
        self.tree.bind('<<TreeviewSelect>>', self.on_category_selected)
        
        # 从数据库加载分类
        self.load_categories_from_db()
        
    def setup_file_list(self):
        """设置文件列表"""
        # 创建文件列表框架
        list_frame = ttk.Frame(self.right_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建Treeview，添加新的列（编号、姓名、类号、材料名称、文件名、日期、页数）
        self.file_list = ttk.Treeview(
            list_frame, 
            columns=('file_id', 'person', 'class_code', 'material_name', 'filename', 'date', 'page_count', 'path'),
            show='headings'
        )
        
        # 设置列标题
        self.file_list.heading('file_id', text='编号')
        self.file_list.heading('person', text='姓名')
        self.file_list.heading('class_code', text='类号')
        self.file_list.heading('material_name', text='材料名称')
        self.file_list.heading('filename', text='文件名')
        self.file_list.heading('date', text='日期')
        self.file_list.heading('page_count', text='页数')
        self.file_list.heading('path', text='路径')
        
        # 设置除路径列外的所有列为等宽
        equal_width = 100
        self.file_list.column('file_id', width=equal_width)
        self.file_list.column('person', width=equal_width)
        self.file_list.column('class_code', width=equal_width)
        self.file_list.column('material_name', width=equal_width)
        self.file_list.column('filename', width=equal_width)
        self.file_list.column('date', width=equal_width)
        self.file_list.column('page_count', width=equal_width)
        # 路径列保持较宽
        self.file_list.column('path', width=200)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_list.yview)
        self.file_list.configure(yscrollcommand=scrollbar.set)
        
        # 布局
        self.file_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定双击事件
        self.file_list.bind('<Double-1>', self.on_file_double_click)

    def update_file_list(self, files):
        """更新文件列表"""
        # 清空现有列表
        self.file_list.delete(*self.file_list.get_children())
        
        # 添加右键菜单
        self.create_file_context_menu()
        
        # 添加文件到列表
        for file in files:
            # 检查文件数据结构
            if len(file) < 2:
                logging.warning(f"文件数据结构不完整: {file}")
                continue
                
            try:
                # 提取文件信息
                # 根据数据库查询结果解析数据
                # person_files表结构: id, person_name, file_name, file_path, category_id, dir_name, file_id
                if len(file) >= 7:  # 完整的person_files记录
                    file_id = file[6] if file[6] else ""  # file_id
                    person_name = file[1] if file[1] else ""  # person_name
                    
                    # 从文件名中提取类号和材料名称
                    file_name = file[2] if file[2] else ""  # file_name
                    
                    # 提取类号 - 应该是3-1, 4-1-1这种格式
                    class_code = ""
                    material_name = ""
                    date = ""
                    page_count = ""
                    
                    # 解析文件名，提取信息
                    # 文件名格式可能是: 3-1-1-会议记录.pdf 或 3-1-会议记录.pdf
                    if "-" in file_name:
                        parts = file_name.split("-")
                        
                        # 提取类号部分
                        if len(parts) >= 2:
                            # 检查前两部分是否都是数字，构建类号
                            if parts[0].isdigit():
                                class_code = parts[0]
                                if len(parts) >= 2 and parts[1].isdigit():
                                    class_code += "-" + parts[1]
                                    if len(parts) >= 3 and parts[2].isdigit():
                                        class_code += "-" + parts[2]
                        
                        # 提取材料名称
                        # 材料名称是类号后面的部分，直到文件扩展名前
                        material_index = 0
                        for i, part in enumerate(parts):
                            if not part.isdigit() or i >= 3:
                                material_index = i
                                break
                        
                        if material_index > 0 and material_index < len(parts):
                            # 获取材料名称部分
                            material_name_parts = parts[material_index:]
                            material_name_str = "-".join(material_name_parts)
                            
                            # 移除文件扩展名
                            if "." in material_name_str:
                                material_name = material_name_str.split(".")[0]
                            else:
                                material_name = material_name_str
                    
                    # 文件路径
                    file_path = file[3] if file[3] else ""  # file_path
                    
                elif len(file) == 2:  # 简单的文件名和路径
                    file_name = file[0] if file[0] else ""
                    file_path = file[1] if file[1] else ""
                    
                    # 其他字段留空
                    file_id = ""
                    person_name = ""
                    class_code = ""
                    material_name = ""
                    date = ""
                    page_count = ""
                    
                    # 尝试从文件名中提取类号和材料名称
                    if "-" in file_name:
                        parts = file_name.split("-")
                        
                        # 提取类号部分
                        if len(parts) >= 2:
                            # 检查前两部分是否都是数字，构建类号
                            if parts[0].isdigit():
                                class_code = parts[0]
                                if len(parts) >= 2 and parts[1].isdigit():
                                    class_code += "-" + parts[1]
                                    if len(parts) >= 3 and parts[2].isdigit():
                                        class_code += "-" + parts[2]
                        
                        # 提取材料名称
                        material_index = 0
                        for i, part in enumerate(parts):
                            if not part.isdigit() or i >= 3:
                                material_index = i
                                break
                        
                        if material_index > 0 and material_index < len(parts):
                            # 获取材料名称部分
                            material_name_parts = parts[material_index:]
                            material_name_str = "-".join(material_name_parts)
                            
                            # 移除文件扩展名
                            if "." in material_name_str:
                                material_name = material_name_str.split(".")[0]
                            else:
                                material_name = material_name_str
                else:
                    # 尝试从现有数据中提取
                    file_id = file[0] if len(file) > 0 else ""
                    person_name = file[1] if len(file) > 1 else ""
                    class_code = file[2] if len(file) > 2 else ""
                    material_name = file[3] if len(file) > 3 else ""
                    file_name = file[4] if len(file) > 4 else ""
                    date = file[5] if len(file) > 5 else ""
                    page_count = file[6] if len(file) > 6 else ""
                    file_path = file[7] if len(file) > 7 else ""
                
                # 确保文件路径是字符串
                if not isinstance(file_path, str):
                    file_path = str(file_path) if file_path is not None else ""
                    
                # 插入到列表
                self.file_list.insert('', tk.END, values=(
                    file_id, person_name, class_code, material_name, file_name, date, page_count, file_path
                ))
            except Exception as e:
                logging.error(f"处理文件记录时出错: {str(e)}, 文件: {file}")
            
        # 更新状态栏
        self.update_status_bar()
        
    def create_file_context_menu(self):
        """创建文件列表右键菜单"""
        self.file_context_menu = tk.Menu(self.root, tearoff=0)
        self.file_context_menu.add_command(label="打开", command=self.open_selected_file)
        self.file_context_menu.add_command(label="打印", command=self.print_selected_file)
        
        # 绑定右键点击事件
        self.file_list.bind("<Button-3>", self.show_file_context_menu)
        
    def show_file_context_menu(self, event):
        """显示右键菜单"""
        # 获取鼠标点击位置对应的项
        item = self.file_list.identify_row(event.y)
        if item:
            # 选中该项
            self.file_list.selection_set(item)
            # 显示菜单
            self.file_context_menu.post(event.x_root, event.y_root)
            
    def open_selected_file(self):
        """打开选中的文件"""
        selection = self.file_list.selection()
        if selection:
            # 模拟双击事件
            self.on_file_double_click(None)
            
    def print_selected_file(self):
        """打印选中的文件"""
        selection = self.file_list.selection()
        if not selection:
            return
            
        # 获取文件路径
        item = self.file_list.item(selection[0])
        values = item['values']
        if len(values) < 8:  # 确保有足够的列
            messagebox.showerror("错误", "无法获取文件路径")
            return
            
        file_path = values[7]  # 路径在第8列
        file_id = values[0]    # 编号在第1列
        person_name = values[1]  # 姓名在第2列
        
        if not os.path.exists(file_path):
            messagebox.showerror("错误", f"文件不存在: {file_path}")
            return
            
        try:
            # 打印确认
            confirm = messagebox.askyesno("打印确认", f"确定要打印文件 {os.path.basename(file_path)} 吗？")
            if not confirm:
                return
                
            # 打印文件
            if sys.platform.startswith('win'):
                # Windows系统使用默认打印机打印
                os.startfile(file_path, "print")
            else:
                # 其他系统使用lpr命令打印
                try:
                    subprocess.call(['lpr', file_path])
                except:
                    messagebox.showerror("错误", "当前系统不支持直接打印，请手动打开文件后打印")
                    # 打开文件
                    if sys.platform.startswith('darwin'):
                        subprocess.call(['open', file_path])
                    else:
                        subprocess.call(['xdg-open', file_path])
            
            # 记录打印日志
            if self.current_user:
                self.db.add_log(
                    username=self.current_user[1],  # 使用用户名而不是整个用户元组
                    operation_type="print",
                    target_id=file_id,
                    target_name=person_name,
                    details=f"打印文件: {os.path.basename(file_path)}",
                    ip_address=self.local_ip
                )
                
            messagebox.showinfo("打印", "文件已发送到打印机")
                
        except Exception as e:
            logging.error(f"打印文件失败: {str(e)}")
            messagebox.showerror("错误", f"打印文件失败: {str(e)}")
            
    def on_file_double_click(self, event):
        """双击文件时的处理"""
        # 获取选中的项
        selection = self.file_list.selection()
        if not selection:
            return
            
        # 获取文件路径
        item = self.file_list.item(selection[0])
        values = item['values']
        if not values or len(values) < 8:  # 确保有足够的列
            messagebox.showerror("错误", "无法获取文件路径")
            return
            
        file_path = values[7]  # 路径在第8列
        file_id = values[0]    # 编号在第1列
        person_name = values[1]  # 姓名在第2列
        
        if not file_path or not isinstance(file_path, str):
            messagebox.showerror("错误", "文件路径无效")
            return
        
        # 去除可能的空格
        file_path = file_path.strip()
        
        if not os.path.exists(file_path):
            messagebox.showerror("错误", f"文件不存在: {file_path}")
            return
            
        try:
            # 打开文件
            logging.info(f"尝试打开文件: {file_path}")
            if sys.platform.startswith('win'):
                os.startfile(file_path)
            elif sys.platform.startswith('darwin'):
                subprocess.call(['open', file_path])
            else:
                subprocess.call(['xdg-open', file_path])
                
            # 记录查看日志
            if hasattr(self, 'current_user') and self.current_user:
                username = self.current_user[1] if isinstance(self.current_user, (list, tuple)) and len(self.current_user) > 1 else "未知用户"
                self.db.add_log(
                    username=username,
                    operation_type="view",
                    target_id=file_id,
                    target_name=person_name,
                    details=f"查看文件: {os.path.basename(file_path)}",
                    ip_address=self.local_ip
                )
                
        except Exception as e:
            logging.error(f"打开文件失败: {str(e)}")
            messagebox.showerror("错误", f"打开文件失败: {str(e)}")

    def hash_password(self, password):
        """对密码进行哈希加密"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, username, password, real_name):
        """注册新用户"""
        try:
            # 检查用户名是否已存在
            self.db.cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', (username,))
            if self.db.cursor.fetchone()[0] > 0:
                return False, "用户名已存在"
            
            # 密码加密
            hashed_password = self.hash_password(password)
            
            # 插入新用户
            self.db.cursor.execute(
                'INSERT INTO users (username, password, real_name) VALUES (?, ?, ?)',
                (username, hashed_password, real_name)
            )
            self.db.conn.commit()
            return True, "注册成功"
        except Exception as e:
            logging.error(f"注册用户失败: {str(e)}")
            return False, f"注册失败: {str(e)}"
    
    def validate_login(self, username, password):
        """验证用户登录"""
        try:
            # 查询用户信息
            self.db.cursor.execute('SELECT id, username, real_name, role, password FROM users WHERE username = ?', (username,))
            result = self.db.cursor.fetchone()
            
            if result is None:
                return False, None  # 用户不存在
                
            user_id, user_name, real_name, role, stored_password = result
            
            # 验证密码
            hashed_password = self.hash_password(password)
            if hashed_password == stored_password:
                # 记录登录日志
                self.db.add_log(
                    username=username,
                    operation_type="login",
                    details="用户登录成功",
                    ip_address=self.local_ip
                )
                # 返回完整的用户信息元组
                return True, (user_id, user_name, real_name, role)
            else:
                return False, None  # 密码错误
        except Exception as e:
            logging.error(f"验证登录失败: {str(e)}")
            return False, None
    
    def show_register_dialog(self):
        """显示用户注册对话框（仅管理员可用）"""
        logging.debug("显示注册对话框")
        
        # 检查权限
        if not self.current_user or self.current_user[3] != 'admin':
            messagebox.showerror("权限错误", "只有管理员可以添加用户")
            return
        
        # 创建注册对话框
        register_dialog = tk.Toplevel(self.root)
        register_dialog.title("添加用户")
        register_dialog.geometry("350x250")  # 进一步增加对话框尺寸
        register_dialog.resizable(False, False)
        register_dialog.transient(self.root)
        register_dialog.grab_set()
        
        # 表单框架
        form_frame = ttk.Frame(register_dialog, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # 用户名
        ttk.Label(form_frame, text="用户名:").grid(row=0, column=0, sticky=tk.W, pady=5)
        username_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=username_var, width=20).grid(row=0, column=1, pady=5)
        
        # 密码
        ttk.Label(form_frame, text="密码:").grid(row=1, column=0, sticky=tk.W, pady=5)
        password_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=password_var, show="*", width=20).grid(row=1, column=1, pady=5)
        
        # 确认密码
        ttk.Label(form_frame, text="确认密码:").grid(row=2, column=0, sticky=tk.W, pady=5)
        confirm_password_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=confirm_password_var, show="*", width=20).grid(row=2, column=1, pady=5)
        
        # 真实姓名
        ttk.Label(form_frame, text="真实姓名:").grid(row=3, column=0, sticky=tk.W, pady=5)
        real_name_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=real_name_var, width=20).grid(row=3, column=1, pady=5)
        
        # 错误信息
        error_var = tk.StringVar()
        error_label = ttk.Label(form_frame, textvariable=error_var, foreground="red")
        error_label.grid(row=4, column=0, columnspan=2, pady=5)
        
        # 注册按钮
        def do_register():
            username = username_var.get().strip()
            password = password_var.get()
            confirm_password = confirm_password_var.get()
            real_name = real_name_var.get().strip()
            
            # 验证表单
            if not username:
                error_var.set("用户名不能为空")
                return
            
            if not password:
                error_var.set("密码不能为空")
                return
            
            if password != confirm_password:
                error_var.set("两次输入的密码不一致")
                return
            
            if not real_name:
                error_var.set("请输入真实姓名")
                return
            
            # 注册用户
            success, message = self.register_user(username, password, real_name)
            if success:
                messagebox.showinfo("添加成功", message)
                register_dialog.destroy()
            else:
                error_var.set(message)
        
        # 创建一个按钮框架
        buttons_frame = ttk.Frame(form_frame)
        buttons_frame.grid(row=5, column=0, columnspan=2, pady=15)  # 增加垂直间距
        
        # 添加更大的按钮
        ttk.Button(buttons_frame, text="确定", command=do_register, width=15).pack(side=tk.LEFT, padx=15)  # 增加按钮宽度和间距
        ttk.Button(buttons_frame, text="取消", command=register_dialog.destroy, width=15).pack(side=tk.LEFT, padx=15)  # 增加按钮宽度和间距
        
        # 居中对话框
        register_dialog.update_idletasks()
        width = register_dialog.winfo_width()
        height = register_dialog.winfo_height()
        x = (register_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (register_dialog.winfo_screenheight() // 2) - (height // 2)
        register_dialog.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        register_dialog.wait_window()
    
    def show_login_dialog(self):
        """显示登录对话框"""
        logging.debug("显示登录对话框")
        
        # 如果已经登录，显示信息并提供退出选项
        if self.current_user:
            result = messagebox.askyesno("已登录", 
                                        f"当前已经以 {self.current_user[2]} 身份登录。\n\n是否要退出登录？")
            if result:
                self.logout()
            return
        
        # 创建登录对话框
        login_dialog = tk.Toplevel(self.root)
        login_dialog.title("用户登录")
        login_dialog.geometry("280x180")  # 增加对话框尺寸
        login_dialog.resizable(False, False)
        login_dialog.transient(self.root)
        login_dialog.grab_set()
        
        # 表单框架
        form_frame = ttk.Frame(login_dialog, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # 用户名
        ttk.Label(form_frame, text="用户名:").grid(row=0, column=0, sticky=tk.W, pady=5)
        username_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=username_var, width=15).grid(row=0, column=1, pady=5)
        
        # 密码
        ttk.Label(form_frame, text="密码:").grid(row=1, column=0, sticky=tk.W, pady=5)
        password_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=password_var, show="*", width=15).grid(row=1, column=1, pady=5)
        
        # 错误信息
        error_var = tk.StringVar()
        error_label = ttk.Label(form_frame, textvariable=error_var, foreground="red")
        error_label.grid(row=2, column=0, columnspan=2, pady=5)
        
        # 登录按钮
        def do_login():
            username = username_var.get().strip()
            password = password_var.get()
            
            # 验证表单
            if not username or not password:
                error_var.set("用户名和密码不能为空")
                return
            
            # 验证登录
            success, user = self.validate_login(username, password)
            if success:
                self.current_user = user
                # 显示真实姓名
                self.login_status_var.set(f"已登录: {user[2]}")
                messagebox.showinfo("登录成功", f"欢迎回来，{user[2]}！")
                
                # 更新菜单和权限
                self.update_menu_by_role(user[3])
                
                # 确保状态栏显示正确的注册状态
                self.update_status_bar()
                
                login_dialog.destroy()
            else:
                error_var.set("用户名或密码错误")
        
        # 创建一个按钮框架
        buttons_frame = ttk.Frame(form_frame)
        buttons_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        # 添加更大的按钮
        ttk.Button(buttons_frame, text="登录", command=do_login, width=10).pack(side=tk.LEFT, padx=10)
        ttk.Button(buttons_frame, text="取消", command=login_dialog.destroy, width=10).pack(side=tk.LEFT, padx=10)
        
        # 居中对话框
        login_dialog.update_idletasks()
        width = login_dialog.winfo_width()
        height = login_dialog.winfo_height()
        x = (login_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (login_dialog.winfo_screenheight() // 2) - (height // 2)
        login_dialog.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        login_dialog.wait_window()
    
    def logout(self):
        """退出登录"""
        self.current_user = None
        self.login_status_var.set("未登录")
        logging.info("用户已退出登录")
        
        # 清空搜索状态和右侧文件列表
        self.has_searched = False
        self.current_search_name = None
        self.current_search_id = None
        if hasattr(self, 'file_list'):
            self.file_list.delete(*self.file_list.get_children())

        # 更新菜单和权限
        self.update_menu_by_role(None)
        
        # 确保状态栏显示正确的注册状态
        self.update_status_bar()
    
    def show_help(self):
        """显示帮助信息"""
        logging.debug("显示帮助信息")
        
        # 创建帮助窗口
        help_window = tk.Toplevel(self.root)
        help_window.title("使用说明 - 档案检索系统 V1.0")
        help_window.geometry("800x600")  # 设置更大的窗口大小
        
        # 添加滚动条
        frame = ttk.Frame(help_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 添加文本框
        text = tk.Text(
            frame, 
            wrap=tk.WORD, 
            yscrollcommand=scrollbar.set,
            font=('Microsoft YaHei', 10),
            padx=10,
            pady=10
        )
        text.pack(fill=tk.BOTH, expand=True)
        
        # 配置滚动条
        scrollbar.config(command=text.yview)
        
        # 设置帮助文本
        help_text = """档案检索系统使用说明 (v1.0)

1. 系统注册
   * 初次使用请点击"帮助"菜单中的"用户注册"
   * 输入注册码和用户名称进行注册
   * 注册成功后重启程序即可使用全部功能
   * 注册信息保存在程序目录下的registration.dat文件中

2. 用户登录
   * 默认管理员账号: admin 密码: admin123
   * 点击"文件"菜单中的"登录"选项进入登录界面
   * 管理员可以添加新用户和修改密码

3. 搜索功能
   * 登录后在右上角输入姓名或编号进行搜索
   * 不支持模糊搜索，请确保输入完整的姓名或编号
   * 当有同名档案时，系统会提示输入编号进行精确搜索
   * 搜索结果会显示材料名称、日期和页数信息
   * 支持按左侧分类目录筛选搜索结果

4. 文件浏览
   * 左侧为档案分类目录
   * 右侧显示文件列表，包含材料名称、日期和页数
   * 双击文件可以打开查看
   * 支持按列排序（点击列标题）

5. 导入功能
   * 导入档案: 导入档案文件（所有登录用户可用）
   * 支持批量导入（请选择包含PDF图片的上级目录）
   * 自动识别并导入PDF文件
   * 自动从Excel文件读取材料信息

6. 工具功能
   * 打开程序安装目录: 快速访问程序文件
   * 打开档案文件目录: 直接浏览档案文件
   * 打开数据库位置: 查看或备份数据库
   * 清理数据库(仅管理员): 清理重复和无效记录

7. 系统要求
   * 操作系统: Windows 7/10/11
   * 内存: 4GB 或更高
   * 存储空间: 至少500MB可用空间
   * 需要安装Microsoft Office或WPS Office查看文档
"""
        # 插入帮助文本
        text.insert(tk.END, help_text)
        
        # 禁用文本编辑
        text.config(state=tk.DISABLED)
        
        # 添加关闭按钮
        button_frame = ttk.Frame(help_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Button(button_frame, text="关闭", command=help_window.destroy).pack(side=tk.RIGHT)
        
        # 设置窗口居中
        help_window.update_idletasks()
        width = help_window.winfo_width()
        height = help_window.winfo_height()
        x = (help_window.winfo_screenwidth() // 2) - (width // 2)
        y = (help_window.winfo_screenheight() // 2) - (height // 2)
        help_window.geometry(f'{width}x{height}+{x}+{y}')
        
        # 设置窗口焦点
        help_window.focus_set()
        help_window.grab_set()
        
    def show_about(self):
        """显示关于信息"""
        logging.debug("显示关于信息")
        
        # 获取注册状态
        is_registered = hasattr(self, 'is_registered') and self.is_registered
        registration_info = f"已注册：{self.current_org}" if is_registered else "未注册"
        
        # 创建关于窗口
        about_window = tk.Toplevel(self.root)
        about_window.title("关于")
        about_window.resizable(False, False)
        
        # 设置窗口样式
        style = ttk.Style()
        
        # 主框架
        main_frame = ttk.Frame(about_window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题和版本信息
        ttk.Label(
            main_frame, 
            text=f"档案检索系统\n\n版本: {self.version}\n{registration_info}",
            justify=tk.CENTER
        ).pack(pady=10)
        
        # 分隔线
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # 确保窗口大小合适
        about_window.update_idletasks()
        
        # 设置窗口大小固定为合适尺寸
        about_window.geometry("300x150")
        
        # 设置窗口居中
        about_window.update_idletasks()
        width = 300
        height = 180
        x = (about_window.winfo_screenwidth() // 2) - (width // 2)
        y = (about_window.winfo_screenheight() // 2) - (height // 2)
        about_window.geometry(f'{width}x{height}+{x}+{y}')
        
        # 设置窗口焦点
        about_window.focus_set()
        about_window.grab_set()

    def import_categories(self):
        """导入分类"""
        try:
            file_path = filedialog.askopenfilename(
                title="选择分类文件",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
            )
            
            if not file_path:
                return
            
            logging.info(f"开始导入分类文件: {file_path}")
            
            # 读取Excel文件的所有列
            df = pd.read_excel(file_path, engine='openpyxl')
            
            # 清空现有分类
            self.tree.delete(*self.tree.get_children())
            self.db.cursor.execute('DELETE FROM categories')
            
            # 清空映射
            self.category_mapping = {}
            
            # 中文数字映射
            chinese_numbers = {
                1: "一", 2: "二", 3: "三", 4: "四", 5: "五",
                6: "六", 7: "七", 8: "八", 9: "九", 10: "十"
            }
            
            # 用于存储一级分类节点的字典
            parent_nodes = {}
            
            # 手动添加所有一级分类
            all_main_categories = [
                (1, "履历材料"),
                (2, "自传材料"),
                (3, "鉴定、考核材料"),
                (4, "学历学位、职称、学术、培训等材料"),
                (5, "政审材料"),
                (6, "党团材料"),
                (7, "奖励材料"),
                (8, "处分材料"),
                (9, "工资、任免、出国、会议等材料"),
                (10, "其他材料")
            ]
            
            # 创建一级分类
            for main_num, category_name in all_main_categories:
                # 添加中文数字前缀，使用中文顿号"、"
                chinese_num = chinese_numbers.get(main_num, str(main_num))
                display_text = f"{chinese_num}、{category_name}"
                
                # 创建树节点
                node_id = self.tree.insert('', 'end', text=display_text)
                parent_nodes[category_name] = node_id
                
                # 存入数据库
                self.db.cursor.execute(
                    'INSERT INTO categories (category, parent_category, main_category_num, sub_category_num) VALUES (?, ?, ?, ?)',
                    (category_name, None, main_num, None)
                )
                
                # 添加到映射
                self.category_mapping[category_name] = str(main_num)
                logging.debug(f"插入一级分类: {category_name}, 主分类号: {main_num}")
            
            # 第4类的二级分类
            subcategories_4 = [
                (4, 1, "学历学位材料"),
                (4, 2, "专业技术职务材料"),
                (4, 3, "科研学术材料"),
                (4, 4, "培训材料")
            ]
            
            # 第9类的二级分类
            subcategories_9 = [
                (9, 1, "工资材料"),
                (9, 2, "任免材料"),
                (9, 3, "出国（境）审批材料"),
                (9, 4, "会议代表材料")
            ]
            
            # 合并所有二级分类
            all_subcategories = subcategories_4 + subcategories_9
            
            # 创建二级分类
            for main_num, sub_num, subcat_name in all_subcategories:
                # 查找父分类
                parent_category = None
                for name, code in self.category_mapping.items():
                    if code == str(main_num) and not isinstance(name, tuple):
                        parent_category = name
                        break
                
                if parent_category and parent_category in parent_nodes:
                    # 添加阿拉伯数字前缀，使用中文顿号"、"
                    display_text = f"{sub_num}、{subcat_name}"
                    
                    # 创建树节点
                    child_id = self.tree.insert(parent_nodes[parent_category], 'end', text=display_text)
                    
                    # 存入数据库
                    self.db.cursor.execute(
                        'INSERT INTO categories (category, parent_category, main_category_num, sub_category_num) VALUES (?, ?, ?, ?)',
                        (subcat_name, parent_category, main_num, sub_num)
                    )
                    
                    # 添加到映射
                    key = (parent_category, subcat_name)
                    value = f"{main_num}-{sub_num}"
                    self.category_mapping[key] = value
                    logging.debug(f"插入二级分类映射: {key} -> {value}")
                else:
                    logging.warning(f"找不到父分类(编码 {main_num})，无法创建二级分类: {subcat_name}")
            
            self.db.conn.commit()
            
            # 验证数据库中的记录并记录日志
            self.db.cursor.execute('SELECT category, parent_category, main_category_num, sub_category_num FROM categories')
            all_categories = self.db.cursor.fetchall()
            logging.info(f"数据库中的分类记录: {len(all_categories)} 条")
            
            # 检查分类（输出到日志）
            self.db.cursor.execute('SELECT category, main_category_num FROM categories WHERE parent_category IS NULL ORDER BY main_category_num')
            main_categories = self.db.cursor.fetchall()
            
            logging.info(f"共导入 {len(main_categories)} 个一级分类:")
            for cat, num in main_categories:
                chinese_num = chinese_numbers.get(num, str(num))
                logging.info(f"  一级分类: {chinese_num}、{cat}, 编码: {num}")
                
                # 检查其子分类
                self.db.cursor.execute('SELECT category, sub_category_num FROM categories WHERE parent_category = ? ORDER BY sub_category_num', (cat,))
                subcats = self.db.cursor.fetchall()
                for subcat, subnum in subcats:
                    logging.info(f"    子分类: {subnum}、{subcat}, 子编码: {num}-{subnum}")
            
            # 打印完整的映射字典
            logging.debug("完整的分类映射字典:")
            for k, v in self.category_mapping.items():
                if isinstance(k, tuple):
                    logging.debug(f"  二级分类: {k[0]} -> {k[1]} = {v}")
                else:
                    logging.debug(f"  一级分类: {k} = {v}")
            
            logging.info("分类导入完成")
            messagebox.showinfo("成功", "分类导入成功！")
            
        except Exception as e:
            logging.error(f"导入分类失败: {str(e)}", exc_info=True)
            messagebox.showerror("错误", f"导入分类失败：{str(e)}")

    def import_files(self):
        """导入文件"""
        try:
            # 选择文件夹，使用上次的路径作为初始目录
            initial_dir = self.import_root_dir if self.import_root_dir and os.path.exists(self.import_root_dir) else None
            folder_path = filedialog.askdirectory(title="选择人员档案文件夹", initialdir=initial_dir)
            if not folder_path:
                return
            
            # 保存导入目录
            self.import_root_dir = folder_path
            logging.info(f"设置导入文件根目录: {self.import_root_dir}")
            
            # 保存设置
            self.save_settings()
            
            # 清空现有文件记录
            self.db.cursor.execute('DELETE FROM person_files')
            
            # 遍历文件夹
            imported_count = 0
            for root, _, files in os.walk(folder_path):
                dir_name = os.path.basename(root)
                
                # 从目录名中提取编号和人名
                # 正则表达式提取开头的连续数字作为编号
                match = re.match(r'^(\d+)(.*)', dir_name)
                file_id = ""
                person_name = dir_name
                
                if match:
                    file_id = match.group(1)
                    # 处理姓名，去掉数字部分只保留人名
                    person_name = match.group(2).strip()
                
                logging.debug(f"处理目录: {dir_name}, 编号: {file_id}, 人名: {person_name}")
                
                for file in files:
                    if file.startswith('.') or file.startswith('~'):
                        continue
                    
                    file_path = os.path.join(root, file)
                    # 存储绝对路径，而不是相对路径
                    abs_path = os.path.abspath(file_path)
                    
                    self.db.cursor.execute('''
                        INSERT INTO person_files (person_name, file_name, file_path, dir_name, file_id)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (person_name, file, abs_path, dir_name, file_id))
                    imported_count += 1
            
            self.db.conn.commit()
            messagebox.showinfo("成功", f"文件导入成功，共导入 {imported_count} 个文件")
            
            # 刷新文件列表
            self.search_person()
            
        except Exception as e:
            self.db.conn.rollback()
            logging.error(f"导入文件失败: {str(e)}")
            messagebox.showerror("错误", f"导入文件失败：{str(e)}")

    def import_archives(self):
        """导入档案"""
        try:
            # 使用上次的路径作为初始目录
            initial_dir = self.import_root_dir if self.import_root_dir and os.path.exists(self.import_root_dir) else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'archives')
            folder_path = filedialog.askdirectory(
                title="选择档案目录",
                initialdir=initial_dir
            )
            
            if not folder_path:
                return
            
            # 保存导入目录
            self.import_root_dir = folder_path
            logging.info(f"设置导入档案根目录: {self.import_root_dir}")
            
            # 保存设置
            self.save_settings()
            
            # 先清理数据库中的重复记录
            self.db.cursor.execute('''
                DELETE FROM person_files 
                WHERE rowid NOT IN (
                    SELECT MIN(rowid)
                    FROM person_files
                    GROUP BY person_name, file_name, file_path
                )
            ''')
            
            # 遍历选择的目录
            imported_count = 0
            file_count = 0
            for person_folder in os.listdir(folder_path):
                person_path = os.path.join(folder_path, person_folder)
                if os.path.isdir(person_path):
                    person_name = person_folder  # 文件夹名即为人名
                    
                    # 在数据库中记录人员信息
                    self.db.cursor.execute('''
                        INSERT OR REPLACE INTO persons (name, folder_path)
                        VALUES (?, ?)
                    ''', (person_name, os.path.abspath(person_path)))
                    
                    # 记录该人下的所有文件
                    for root, _, files in os.walk(person_path):
                        for file in files:
                            # 跳过临时文件和隐藏文件
                            if file.startswith('~') or file.startswith('.'):
                                continue
                            
                            file_path = os.path.join(root, file)
                            abs_path = os.path.abspath(file_path)
                            
                            # 从目录名中提取编号和人名
                            match = re.match(r'^(\d+)(.*)', person_folder)
                            file_id = ""
                            dir_name = person_folder
                            
                            if match:
                                file_id = match.group(1)
                                # 如果人名不是从目录名提取的，则保持原来的人名
                                # person_name = match.group(2).strip()
                            
                            # 检查文件是否已存在
                            self.db.cursor.execute('''
                                SELECT COUNT(*) FROM person_files 
                                WHERE person_name = ? AND file_name = ? AND file_path = ?
                            ''', (person_name, file, abs_path))
                            
                            if self.db.cursor.fetchone()[0] == 0:
                                self.db.cursor.execute('''
                                    INSERT INTO person_files (person_name, file_name, file_path, dir_name, file_id)
                                    VALUES (?, ?, ?, ?, ?)
                                ''', (person_name, file, abs_path, dir_name, file_id))
                                file_count += 1
                        
                    imported_count += 1
            
            self.db.conn.commit()
            messagebox.showinfo("成功", f"成功导入 {imported_count} 个人员的档案，共 {file_count} 个文件！")
            
            # 刷新文件列表
            self.search_person()
            
        except Exception as e:
            logging.error(f"导入档案失败: {str(e)}")
            messagebox.showerror("错误", f"导入失败：{str(e)}")

    def search_person(self):
        """搜索人员档案"""
        search_name = self.search_name_var.get().strip()
        search_id = self.search_id_var.get().strip()
        
        if not search_name and not search_id:
            messagebox.showinfo("提示", "请输入姓名或编号进行搜索")
            return
            
        # 保存当前搜索条件
        self.current_search_name = search_name
        self.current_search_id = search_id
        self.has_searched = True
        
        try:
            # 构建查询条件
            conditions = []
            params = []
            
            if search_name:
                conditions.append("person_name LIKE ?")
                params.append(f"%{search_name}%")
                
            if search_id:
                conditions.append("file_id LIKE ?")
                params.append(f"%{search_id}%")
                
            # 组合查询条件
            query = """
                SELECT 
                    id, person_name, file_name, file_path, 
                    category_id, dir_name, file_id
                FROM person_files 
                WHERE """ + " OR ".join(conditions) + """
                ORDER BY person_name, file_name
            """
            
            # 执行查询
            self.db.cursor.execute(query, params)
            results = self.db.cursor.fetchall()
            
            # 检查是否有结果
            if not results:
                messagebox.showinfo("提示", "未找到匹配的档案")
                self.file_list.delete(*self.file_list.get_children())
                self.search_result_var.set("搜索结果: 0 个文件")
                return
                
            # 检查是否有重名情况
            if search_name and not search_id:
                names = set(row[1] for row in results)  # 获取所有人名
                if len(names) > 1:
                    self.has_duplicate_names = True
                    messagebox.showwarning("提示", "存在多个同名人员，请输入编号进一步筛选")
                else:
                    self.has_duplicate_names = False
            else:
                self.has_duplicate_names = False
            
            # 更新文件列表
            self.update_file_list(results)
            
            # 记录搜索日志
            if self.current_user:
                details = f"搜索条件: 姓名={search_name}, 编号={search_id}, 结果数量={len(results)}"
                self.db.add_log(
                    username=self.current_user[1],  # 使用用户名而不是整个用户元组
                    operation_type="search",
                    target_name=search_name or search_id,
                    details=details,
                    ip_address=self.local_ip
                )
            
            # 更新状态栏
            self.search_result_var.set(f"搜索结果: {len(results)} 个文件")
            
        except Exception as e:
            logging.error(f"搜索失败: {str(e)}")
            messagebox.showerror("错误", f"搜索失败: {str(e)}")
    
    def extract_category_num(self, filename):
        """从文件名中提取分类号"""
        if not filename or not isinstance(filename, str):
            return None
            
        # 文件名格式可能是: 3-1-1-会议记录.pdf 或 3-1-会议记录.pdf
        parts = filename.split('-')
        if len(parts) < 2 or not parts[0].isdigit():
            return None
            
        # 构建类号
        class_code = parts[0]
        if len(parts) >= 2 and parts[1].isdigit():
            class_code += "-" + parts[1]
            if len(parts) >= 3 and parts[2].isdigit():
                class_code += "-" + parts[2]
                
        return class_code

    def on_category_selected(self, event):
        """处理分类选择事件"""
        selected_items = self.tree.selection()
        if not selected_items:
            return

        # 未登录时不显示任何内容
        if not hasattr(self, 'current_user') or self.current_user is None:
            self.file_list.delete(*self.file_list.get_children())
            logging.info("未登录状态，点击分类不显示文件")
            return

        # 判断是否进行过搜索，如果没有搜索过则右侧列表为空
        if not hasattr(self, 'has_searched') or not self.has_searched:
            self.file_list.delete(*self.file_list.get_children())
            logging.info("未进行搜索，不显示文件")
            return

        selected_item = selected_items[0]
        selected_text = self.tree.item(selected_item)['text']
        parent_item = self.tree.parent(selected_item)
        
        # 从显示文本中提取原始分类名称（去除数字前缀）
        # 例如：从"一、履历材料"提取"履历材料"
        if '、' in selected_text:
            category_name = selected_text.split('、', 1)[1]
        else:
            category_name = selected_text
        
        try:
            if parent_item:  # 二级分类
                parent_text = self.tree.item(parent_item)['text']
                
                # 从父分类显示文本中提取原始名称
                if '、' in parent_text:
                    parent_category_name = parent_text.split('、', 1)[1]
                else:
                    parent_category_name = parent_text
                
                category_key = (parent_category_name, category_name)
                category_code = self.category_mapping.get(category_key)
                
                logging.debug(f"二级分类选择: {parent_category_name} -> {category_name}")
                logging.debug(f"二级分类编码: {category_code}")
                
                if category_code:
                    # 构建查询，精确匹配分类代码-开头
                    query = '''
                        SELECT 
                            id, person_name, file_name, file_path, 
                            category_id, dir_name, file_id
                        FROM person_files 
                        WHERE (
                            file_name LIKE ? OR    -- 精确的分类代码-开头 (4-1-%)
                            file_name LIKE ? OR    -- 带点的格式 (4.1.%)
                            file_name LIKE ?       -- 简单格式 (4-%)
                        )
                        AND file_name NOT LIKE '~%'
                        AND file_name NOT LIKE '.%'
                        AND file_name LIKE '%.pdf'
                    '''
                    # 多种模式匹配
                    category_parts = category_code.split('-')
                    if len(category_parts) == 2:  # 二级分类，如 4-1
                        main_code, sub_code = category_parts
                        params = [
                            f'{main_code}-{sub_code}-%',  # 4-1-%
                            f'{main_code}.{sub_code}.%',  # 4.1.%
                            f'{main_code}-%'              # 4-%
                        ]
                    else:
                        params = [
                            f'{category_code}-%',  # 任何以该编码开头的
                            f'{category_code.replace("-", ".")}%',  # 替换-为.的格式
                            f'{category_code.split("-")[0]}-%'  # 只匹配主分类
                        ]
                    
                    # 检查是否有搜索条件
                    if not (hasattr(self, 'current_search_name') and self.current_search_name):
                        # 清空文件列表
                        self.file_list.delete(*self.file_list.get_children())
                        self.search_result_var.set("请先输入姓名进行搜索")
                        return
                    
                    # 检查是否有重名但未输入编号的情况
                    if hasattr(self, 'has_duplicate_names') and self.has_duplicate_names and \
                       not (hasattr(self, 'current_search_id') and self.current_search_id):
                        # 清空文件列表
                        self.file_list.delete(*self.file_list.get_children())
                        self.search_result_var.set("发现重名，请输入编号后重试")
                        return
                        
                    # 添加人名过滤条件
                    query += ' AND person_name = ?'
                    params.append(self.current_search_name)
                    
                    # 如果有编号，添加编号过滤条件
                    if hasattr(self, 'current_search_id') and self.current_search_id:
                        query += ' AND file_id = ?'
                        params.append(self.current_search_id)
                    
                    query += ' ORDER BY file_name'
                    
                    logging.debug(f"二级分类查询: {query}, 参数: {params}")
                    
                    self.db.cursor.execute(query, params)
                    files = self.db.cursor.fetchall()
                    
                    # 记录查询结果
                    logging.debug(f"二级分类查询结果数量: {len(files)}")
                    if len(files) > 0:
                        logging.debug(f"第一个结果: {files[0]}")
                    
                    self.update_file_list(files)
                    
                    # 更新状态栏显示搜索结果数量
                    self.search_result_var.set(f"搜索结果: {len(files)} 个文件")
                    
                    logging.info(f"二级分类查询: {category_code}, 找到文件数量: {len(files)}")
                else:
                    logging.warning(f"未找到分类编码: {category_key}")
            else:  # 一级分类
                category_code = self.category_mapping.get(category_name)
                
                logging.debug(f"一级分类选择: {category_name}")
                logging.debug(f"一级分类编码: {category_code}")
                
                if category_code:
                    # 检查是否有子分类
                    self.db.cursor.execute('''
                        SELECT COUNT(*) 
                        FROM categories 
                        WHERE parent_category = ?
                    ''', (category_name,))
                    
                    has_subcategories = self.db.cursor.fetchone()[0] > 0
                    
                    if has_subcategories:
                        # 如果有子分类，不显示任何文件
                        self.file_list.delete(*self.file_list.get_children())
                        logging.info(f"一级分类有子分类，不显示文件")
                    else:
                        # 构建查询，精确匹配分类代码-开头
                        query = '''
                            SELECT 
                                id, person_name, file_name, file_path, 
                                category_id, dir_name, file_id
                            FROM person_files 
                            WHERE (
                                file_name LIKE ? OR    -- 精确的分类代码-开头 (4-%)
                                file_name LIKE ?       -- 点号分隔的格式 (4.%)
                            )
                            AND file_name NOT LIKE '~%'
                            AND file_name NOT LIKE '.%'
                            AND file_name LIKE '%.pdf'
                        '''
                        params = [f'{category_code}-%', f'{category_code}.%']
                        
                        # 检查是否有搜索条件
                        if not (hasattr(self, 'current_search_name') and self.current_search_name):
                            # 清空文件列表
                            self.file_list.delete(*self.file_list.get_children())
                            self.search_result_var.set("请先输入姓名进行搜索")
                            return
                        
                        # 检查是否有重名但未输入编号的情况
                        if hasattr(self, 'has_duplicate_names') and self.has_duplicate_names and \
                           not (hasattr(self, 'current_search_id') and self.current_search_id):
                            # 清空文件列表
                            self.file_list.delete(*self.file_list.get_children())
                            self.search_result_var.set("发现重名，请输入编号后重试")
                            return
                            
                        # 添加人名过滤条件
                        query += ' AND person_name = ?'
                        params.append(self.current_search_name)
                        
                        # 如果有编号，添加编号过滤条件
                        if hasattr(self, 'current_search_id') and self.current_search_id:
                            query += ' AND file_id = ?'
                            params.append(self.current_search_id)
                        
                        query += ' ORDER BY file_name'
                        
                        logging.debug(f"一级分类查询: {query}, 参数: {params}")
                        
                        self.db.cursor.execute(query, params)
                        files = self.db.cursor.fetchall()
                        
                        # 记录查询结果
                        logging.debug(f"一级分类查询结果数量: {len(files)}")
                        if len(files) > 0:
                            logging.debug(f"第一个结果: {files[0]}")
                            
                        self.update_file_list(files)
                        
                        logging.info(f"一级分类查询: {category_code}, 找到文件数量: {len(files)}")
                
        except Exception as e:
            logging.error(f"分类查询失败: {str(e)}", exc_info=True)
            messagebox.showerror("错误", f"获取分类文件失败：{str(e)}")

    def update_category_tree(self):
        """更新分类树显示"""
        self.tree.delete(*self.tree.get_children())  # 清空现有分类
        # 从数据库获取分类
        self.db.cursor.execute('SELECT category FROM categories')
        categories = self.db.cursor.fetchall()
        for category in categories:
            self.tree.insert('', 'end', text=category[0])
    
    def show_operation_logs(self):
        """显示操作日志"""
        if not self.current_user or not hasattr(self.db, 'get_logs'):
            messagebox.showerror("错误", "请先登录或系统不支持日志功能")
            return
            
        # 创建日志查询窗口
        log_window = tk.Toplevel(self.root)
        log_window.title("操作日志查询")
        log_window.geometry("900x600")
        log_window.minsize(800, 500)
        
        # 设置窗口图标
        try:
            from src.utils.paths import get_icon_path
            icon_path = get_icon_path()
            if os.path.exists(icon_path):
                log_window.iconbitmap(icon_path)
        except Exception as e:
            logging.warning(f"设置图标失败: {str(e)}")
        
        # 创建查询条件框架
        query_frame = ttk.Frame(log_window, padding="10 10 10 10")
        query_frame.pack(fill=tk.X)
        
        # 用户名筛选
        ttk.Label(query_frame, text="用户名:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        username_var = tk.StringVar()
        username_entry = ttk.Entry(query_frame, textvariable=username_var, width=15)
        username_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # 操作类型筛选
        ttk.Label(query_frame, text="操作类型:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        operation_type_var = tk.StringVar()
        operation_types = ["", "login", "search", "view", "print"]
        operation_type_combo = ttk.Combobox(query_frame, textvariable=operation_type_var, values=operation_types, width=10)
        operation_type_combo.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        
        # 日期范围筛选
        ttk.Label(query_frame, text="开始日期:").grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)
        start_date_var = tk.StringVar()
        start_date_entry = ttk.Entry(query_frame, textvariable=start_date_var, width=12)
        start_date_entry.grid(row=0, column=5, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(query_frame, text="结束日期:").grid(row=0, column=6, padx=5, pady=5, sticky=tk.W)
        end_date_var = tk.StringVar()
        end_date_entry = ttk.Entry(query_frame, textvariable=end_date_var, width=12)
        end_date_entry.grid(row=0, column=7, padx=5, pady=5, sticky=tk.W)
        
        # 设置默认日期为今天
        today = datetime.date.today().strftime("%Y-%m-%d")
        start_date_var.set(today)
        end_date_var.set(today)
        
        # 创建日志列表
        log_frame = ttk.Frame(log_window)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建Treeview显示日志
        columns = ('id', 'username', 'operation_type', 'target_id', 'target_name', 'details', 'operation_time', 'ip_address')
        log_tree = ttk.Treeview(log_frame, columns=columns, show='headings')
        
        # 设置列标题
        log_tree.heading('id', text='ID')
        log_tree.heading('username', text='用户名')
        log_tree.heading('operation_type', text='操作类型')
        log_tree.heading('target_id', text='目标ID')
        log_tree.heading('target_name', text='目标名称')
        log_tree.heading('details', text='详情')
        log_tree.heading('operation_time', text='操作时间')
        log_tree.heading('ip_address', text='IP地址')
        
        # 设置列宽
        log_tree.column('id', width=50)
        log_tree.column('username', width=80)
        log_tree.column('operation_type', width=80)
        log_tree.column('target_id', width=80)
        log_tree.column('target_name', width=100)
        log_tree.column('details', width=200)
        log_tree.column('operation_time', width=150)
        log_tree.column('ip_address', width=120)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=log_tree.yview)
        log_tree.configure(yscrollcommand=scrollbar.set)
        
        log_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 按钮框架
        button_frame = ttk.Frame(log_window, padding="10 5 10 10")
        button_frame.pack(fill=tk.X)
        
        # 查询按钮
        def query_logs():
            username = username_var.get().strip()
            operation_type = operation_type_var.get()
            start_date = start_date_var.get().strip()
            end_date = end_date_var.get().strip()
            
            # 清空现有数据
            for item in log_tree.get_children():
                log_tree.delete(item)
                
            # 查询日志
            logs = self.db.get_logs(
                username=username if username else None,
                operation_type=operation_type if operation_type else None,
                start_date=start_date if start_date else None,
                end_date=end_date if end_date else None
            )
            
            # 显示日志
            for log in logs:
                log_tree.insert('', tk.END, values=log)
                
            # 更新状态
            status_var.set(f"共找到 {len(logs)} 条日志记录")
        
        query_btn = ttk.Button(button_frame, text="查询", command=query_logs)
        query_btn.pack(side=tk.LEFT, padx=5)
        
        # 导出按钮
        def export_displayed_logs():
            # 获取当前显示的所有日志
            logs = []
            for item_id in log_tree.get_children():
                item = log_tree.item(item_id)
                logs.append(item['values'])
                
            if not logs:
                messagebox.showinfo("提示", "没有可导出的日志")
                return
                
            # 选择保存路径
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel文件", "*.xlsx"), ("所有文件", "*.*")],
                title="保存日志文件"
            )
            
            if not file_path:
                return
                
            try:
                # 创建DataFrame
                df = pd.DataFrame(logs, columns=columns)
                
                # 保存为Excel
                df.to_excel(file_path, index=False)
                messagebox.showinfo("成功", f"日志已导出到: {file_path}")
                
            except Exception as e:
                logging.error(f"导出日志失败: {str(e)}")
                messagebox.showerror("错误", f"导出失败: {str(e)}")
        
        export_btn = ttk.Button(button_frame, text="导出当前结果", command=export_displayed_logs)
        export_btn.pack(side=tk.LEFT, padx=5)
        
        # 关闭按钮
        close_btn = ttk.Button(button_frame, text="关闭", command=log_window.destroy)
        close_btn.pack(side=tk.RIGHT, padx=5)
        
        # 状态栏
        status_var = tk.StringVar()
        status_var.set("请设置查询条件并点击查询按钮")
        status_bar = ttk.Label(log_window, textvariable=status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 初始加载今天的日志
        query_logs()
        
        # 设置窗口为模态
        log_window.transient(self.root)
        log_window.grab_set()
        self.root.wait_window(log_window)
    
    def export_logs(self):
        """导出日志"""
        if not self.current_user:
            messagebox.showerror("错误", "请先登录")
            return
            
        # 创建导出窗口
        export_window = tk.Toplevel(self.root)
        export_window.title("导出操作日志")
        export_window.geometry("400x300")
        export_window.minsize(400, 300)
        
        # 设置窗口图标
        try:
            from src.utils.paths import get_icon_path
            icon_path = get_icon_path()
            if os.path.exists(icon_path):
                export_window.iconbitmap(icon_path)
        except Exception as e:
            logging.warning(f"设置图标失败: {str(e)}")
        
        # 创建查询条件框架
        query_frame = ttk.Frame(export_window, padding="10 10 10 10")
        query_frame.pack(fill=tk.X)
        
        # 用户名筛选
        ttk.Label(query_frame, text="用户名:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        username_var = tk.StringVar()
        username_entry = ttk.Entry(query_frame, textvariable=username_var, width=15)
        username_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # 操作类型筛选
        ttk.Label(query_frame, text="操作类型:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        operation_type_var = tk.StringVar()
        operation_types = ["", "login", "search", "view", "print"]
        operation_type_combo = ttk.Combobox(query_frame, textvariable=operation_type_var, values=operation_types, width=15)
        operation_type_combo.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # 日期范围筛选
        ttk.Label(query_frame, text="开始日期:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        start_date_var = tk.StringVar()
        start_date_entry = ttk.Entry(query_frame, textvariable=start_date_var, width=15)
        start_date_entry.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(query_frame, text="结束日期:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        end_date_var = tk.StringVar()
        end_date_entry = ttk.Entry(query_frame, textvariable=end_date_var, width=15)
        end_date_entry.grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)
        
        # 设置默认日期为本月第一天和今天
        today = datetime.date.today()
        first_day = today.replace(day=1).strftime("%Y-%m-%d")
        today_str = today.strftime("%Y-%m-%d")
        start_date_var.set(first_day)
        end_date_var.set(today_str)
        
        # 按钮框架
        button_frame = ttk.Frame(export_window, padding="10 5 10 10")
        button_frame.pack(fill=tk.X, pady=10)
        
        # 导出按钮
        def do_export():
            username = username_var.get().strip()
            operation_type = operation_type_var.get()
            start_date = start_date_var.get().strip()
            end_date = end_date_var.get().strip()
            
            # 选择保存路径
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel文件", "*.xlsx"), ("所有文件", "*.*")],
                title="保存日志文件"
            )
            
            if not file_path:
                return
                
            try:
                # 查询日志
                logs = self.db.get_logs(
                    username=username if username else None,
                    operation_type=operation_type if operation_type else None,
                    start_date=start_date if start_date else None,
                    end_date=end_date if end_date else None,
                    limit=10000  # 导出更多记录
                )
                
                if not logs:
                    messagebox.showinfo("提示", "没有符合条件的日志记录")
                    return
                    
                # 创建DataFrame
                columns = ['id', 'username', 'operation_type', 'target_id', 'target_name', 'details', 'operation_time', 'ip_address']
                df = pd.DataFrame(logs, columns=columns)
                
                # 保存为Excel
                df.to_excel(file_path, index=False)
                messagebox.showinfo("成功", f"已导出 {len(logs)} 条日志记录到: {file_path}")
                
                # 记录导出日志的操作
                self.db.add_log(
                    username=self.current_user[1],  # 使用用户名而不是整个用户元组
                    operation_type="export",
                    details=f"导出日志记录: {len(logs)} 条",
                    ip_address=self.local_ip
                )
                
                export_window.destroy()
                
            except Exception as e:
                logging.error(f"导出日志失败: {str(e)}")
                messagebox.showerror("错误", f"导出失败: {str(e)}")
        
        export_btn = ttk.Button(button_frame, text="导出", command=do_export)
        export_btn.pack(side=tk.LEFT, padx=5)
        
        # 取消按钮
        cancel_btn = ttk.Button(button_frame, text="取消", command=export_window.destroy)
        cancel_btn.pack(side=tk.RIGHT, padx=5)
        
        # 设置窗口为模态
        export_window.transient(self.root)
        export_window.grab_set()
        self.root.wait_window(export_window)

    def load_files_from_db(self):
        """从数据库加载所有文件"""
        try:
            self.db.cursor.execute('''
                SELECT file_name, file_path 
                FROM person_files
            ''')
            self.all_files = self.db.cursor.fetchall()
        except Exception as e:
            logging.error(f"加载文件失败: {str(e)}")
            self.all_files = []

    def open_install_directory(self):
        """打开程序安装目录"""
        try:
            install_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            logging.info(f"打开程序安装目录: {install_dir}")
            if os.path.exists(install_dir):
                # 使用系统默认的文件浏览器打开目录
                os.startfile(install_dir)
            else:
                messagebox.showerror("错误", "程序安装目录不存在")
        except Exception as e:
            logging.error(f"打开程序安装目录失败: {str(e)}")
            messagebox.showerror("错误", f"打开程序安装目录失败: {str(e)}")
    
    def open_archive_directory(self):
        """打开档案文件目录"""
        try:
            # 使用当前导入目录，如果存在且有效
            archive_dir = self.import_root_dir
            
            # 如果目录不存在或未设置，提示用户选择
            if not archive_dir or not os.path.exists(archive_dir):
                # 如果没有设置或目录不存在，询问用户选择目录
                messagebox.showinfo("提示", "档案文件目录未设置或不存在，请选择档案文件目录")
                archive_dir = filedialog.askdirectory(title="选择档案文件目录")
                if archive_dir:
                    # 更新导入目录并保存设置
                    self.import_root_dir = archive_dir
                    self.save_settings()
                else:
                    return
            
            logging.info(f"打开档案文件目录: {archive_dir}")
            # 使用系统默认的文件浏览器打开目录
            os.startfile(archive_dir)
        except Exception as e:
            logging.error(f"打开档案文件目录失败: {str(e)}")
            messagebox.showerror("错误", f"打开档案文件目录失败: {str(e)}")
    
    def open_database_location(self):
        """打开数据库位置"""
        try:
            # 获取数据库文件路径
            if hasattr(self.db, 'db_path') and self.db.db_path:
                db_dir = os.path.dirname(self.db.db_path)
            else:
                # 如果没有明确的数据库路径，使用默认位置
                db_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data')
            
            logging.info(f"打开数据库位置: {db_dir}")
            if os.path.exists(db_dir):
                # 使用系统默认的文件浏览器打开目录
                os.startfile(db_dir)
            else:
                messagebox.showerror("错误", "数据库目录不存在")
        except Exception as e:
            logging.error(f"打开数据库位置失败: {str(e)}")
            messagebox.showerror("错误", f"打开数据库位置失败: {str(e)}")
    
    def cleanup_database(self):
        """清理数据库中的重复记录和无效记录"""
        try:
            # 删除重复记录
            self.db.cursor.execute('''
                DELETE FROM person_files 
                WHERE rowid NOT IN (
                    SELECT MIN(rowid)
                    FROM person_files
                    GROUP BY person_name, file_name, file_path
                )
            ''')
            
            # 删除不存在的文件记录
            self.db.cursor.execute('SELECT file_path FROM person_files')
            for (file_path,) in self.db.cursor.fetchall():
                if not os.path.exists(file_path):
                    self.db.cursor.execute('DELETE FROM person_files WHERE file_path = ?', (file_path,))
            
            self.db.conn.commit()
            messagebox.showinfo("成功", "数据库清理完成！")
            
        except Exception as e:
            logging.error(f"数据库清理失败: {str(e)}")
            messagebox.showerror("错误", f"清理失败：{str(e)}")

    def init_data(self):
        """初始化数据：加载分类树和文件列表"""
        try:
            # 加载分类树（不依赖数据库）
            self.load_categories_from_db()
            logging.info("已加载分类树结构")
            
            # 检查文件记录是否存在
            self.db.cursor.execute('SELECT COUNT(*) FROM person_files')
            files_count = self.db.cursor.fetchone()[0]
            
            if files_count > 0:
                # 如果存在文件记录，直接加载
                self.load_files_from_db()
                logging.info(f"从数据库加载了 {files_count} 条文件记录")
                
        except Exception as e:
            logging.error(f"初始化数据失败: {str(e)}", exc_info=True)
            messagebox.showerror("错误", f"初始化数据失败：{str(e)}")

    def load_categories_from_db(self):
        """加载分类树并构建映射（不依赖数据库，直接在代码中写死）"""
        try:
            # 清空现有树和映射
            self.tree.delete(*self.tree.get_children())
            self.category_mapping = {}
            
            # 中文数字映射
            chinese_numbers = {
                1: "一", 2: "二", 3: "三", 4: "四", 5: "五",
                6: "六", 7: "七", 8: "八", 9: "九", 10: "十"
            }
            
            # 手动定义所有一级分类
            all_main_categories = [
                (1, "履历材料"),
                (2, "自传材料"),
                (3, "鉴定、考核材料"),
                (4, "学历学位、职称、学术、培训等材料"),
                (5, "政审材料"),
                (6, "党团材料"),
                (7, "奖励材料"),
                (8, "处分材料"),
                (9, "工资、任免、出国、会议等材料"),
                (10, "其他材料")
            ]
            
            # 创建一级分类节点和映射
            parent_nodes = {}
            for main_num, category in all_main_categories:
                # 添加中文数字前缀，使用中文顿号"、"
                chinese_num = chinese_numbers.get(main_num, str(main_num))
                display_text = f"{chinese_num}、{category}"
                
                # 创建树节点
                node_id = self.tree.insert('', 'end', text=display_text)
                parent_nodes[category] = node_id
                
                # 添加一级分类映射
                self.category_mapping[category] = str(main_num)
                logging.debug(f"添加一级分类映射: {category} -> {main_num}")
            
            # 手动定义第4类的二级分类
            subcategories_4 = [
                (4, 1, "学历学位材料"),
                (4, 2, "专业技术职务材料"),
                (4, 3, "科研学术材料"),
                (4, 4, "培训材料")
            ]
            
            # 手动定义第9类的二级分类
            subcategories_9 = [
                (9, 1, "工资材料"),
                (9, 2, "任免材料"),
                (9, 3, "出国（境）审批材料"),
                (9, 4, "会议代表材料")
            ]
            
            # 合并所有二级分类
            all_subcategories = subcategories_4 + subcategories_9
            
            # 创建二级分类节点和映射
            for main_num, sub_num, category in all_subcategories:
                # 查找父分类
                parent_category = None
                for name, code in self.category_mapping.items():
                    if code == str(main_num) and not isinstance(name, tuple):
                        parent_category = name
                        break
                
                if parent_category and parent_category in parent_nodes:
                    # 添加阿拉伯数字前缀，使用中文顿号"、"
                    display_text = f"{sub_num}、{category}"
                    
                    # 创建树节点
                    child_id = self.tree.insert(parent_nodes[parent_category], 'end', text=display_text)
                    
                    # 添加二级分类映射
                    key = (parent_category, category)
                    value = f"{main_num}-{sub_num}"
                    self.category_mapping[key] = value
                    logging.debug(f"添加二级分类映射: {key} -> {value}")
            
            # 打印完整的映射字典
            logging.debug("完整的分类映射字典:")
            for k, v in self.category_mapping.items():
                if isinstance(k, tuple):
                    logging.debug(f"  二级分类: {k[0]} -> {k[1]} = {v}")
                else:
                    logging.debug(f"  一级分类: {k} = {v}")
                
        except Exception as e:
            logging.error(f"加载分类树失败: {str(e)}", exc_info=True)
            # 如果出错，不抛出异常，只记录日志
            pass
            
    def load_settings(self):
        """加载用户设置"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                logging.info(f"成功加载用户设置: {settings}")
                return settings
            except Exception as e:
                logging.error(f"加载用户设置失败: {str(e)}")
                return {}
        else:
            logging.info("未找到用户设置文件，将使用默认设置")
            return {}
    
    def save_settings(self):
        """保存用户设置"""
        try:
            settings = {
                'import_root_dir': self.import_root_dir
            }
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            logging.info(f"成功保存用户设置: {settings}")
        except Exception as e:
            logging.error(f"保存用户设置失败: {str(e)}")

    def show_change_password_dialog(self):
        """显示修改密码对话框"""
        # 检查权限
        if not self.current_user or self.current_user[3] != 'admin':
            messagebox.showerror("权限错误", "只有管理员可以修改密码")
            return
            
        # 创建修改密码对话框
        change_pwd_dialog = tk.Toplevel(self.root)
        change_pwd_dialog.title("修改密码")
        change_pwd_dialog.geometry("320x200")  # 增加对话框尺寸
        change_pwd_dialog.resizable(False, False)
        change_pwd_dialog.transient(self.root)
        change_pwd_dialog.grab_set()
        
        # 表单框架
        form_frame = ttk.Frame(change_pwd_dialog, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # 旧密码
        ttk.Label(form_frame, text="当前密码:").grid(row=0, column=0, sticky=tk.W, pady=5)
        old_password_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=old_password_var, show="*", width=20).grid(row=0, column=1, pady=5)
        
        # 新密码
        ttk.Label(form_frame, text="新密码:").grid(row=1, column=0, sticky=tk.W, pady=5)
        new_password_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=new_password_var, show="*", width=20).grid(row=1, column=1, pady=5)
        
        # 确认新密码
        ttk.Label(form_frame, text="确认新密码:").grid(row=2, column=0, sticky=tk.W, pady=5)
        confirm_password_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=confirm_password_var, show="*", width=20).grid(row=2, column=1, pady=5)
        
        # 错误信息
        error_var = tk.StringVar()
        error_label = ttk.Label(form_frame, textvariable=error_var, foreground="red")
        error_label.grid(row=3, column=0, columnspan=2, pady=5)
        
        # 修改密码按钮
        def do_change_password():
            old_password = old_password_var.get()
            new_password = new_password_var.get()
            confirm_password = confirm_password_var.get()
            
            # 验证表单
            if not old_password or not new_password or not confirm_password:
                error_var.set("所有密码字段不能为空")
                return
            
            if new_password != confirm_password:
                error_var.set("两次输入的新密码不一致")
                return
            
            # 验证旧密码
            success, _ = self.validate_login(self.current_user[1], old_password)
            if not success:
                error_var.set("当前密码错误")
                return
                
            # 修改密码
            try:
                hashed_password = self.hash_password(new_password)
                self.db.cursor.execute(
                    'UPDATE users SET password = ? WHERE id = ?',
                    (hashed_password, self.current_user[0])
                )
                self.db.conn.commit()
                messagebox.showinfo("成功", "密码修改成功！")
                change_pwd_dialog.destroy()
            except Exception as e:
                error_var.set(f"修改失败: {str(e)}")
        
        # 创建一个按钮框架
        buttons_frame = ttk.Frame(form_frame)
        buttons_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        # 添加更大的按钮
        ttk.Button(buttons_frame, text="确定", command=do_change_password, width=10).pack(side=tk.LEFT, padx=10)
        ttk.Button(buttons_frame, text="取消", command=change_pwd_dialog.destroy, width=10).pack(side=tk.LEFT, padx=10)
        
        # 居中对话框
        change_pwd_dialog.update_idletasks()
        width = change_pwd_dialog.winfo_width()
        height = change_pwd_dialog.winfo_height()
        x = (change_pwd_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (change_pwd_dialog.winfo_screenheight() // 2) - (height // 2)
        change_pwd_dialog.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        change_pwd_dialog.wait_window()
    
    def check_registration(self):
        """检查是否已注册"""
        try:
            # 使用用户管理模块的注册验证逻辑
            from src.ui.user_management import UserManager
            if not hasattr(self, 'user_manager'):
                self.user_manager = UserManager(self)
                
            # 调用用户管理模块的检查注册方法
            is_registered = self.user_manager.check_registration()
            
            if is_registered:
                # 如果注册，尝试从注册文件中获取单位名称
                config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'config')
                registration_file = os.path.join(config_dir, 'registration.dat')
                
                if os.path.exists(registration_file):
                    with open(registration_file, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        # 简单解密处理
                        decoded_content = ''.join([chr(ord(c) - 1) for c in content])
                        parts = decoded_content.split('|')
                        
                        if len(parts) >= 2:
                            self.current_org = parts[1].strip()
                            logging.info(f"已注册单位: {self.current_org}")
            else:
                self.current_org = None
                
            return is_registered
                
        except Exception as e:
            logging.error(f"检查注册状态失败: {str(e)}")
            logging.debug(f"异常详情:", exc_info=True)
            # 如果出错，清除单位名并返回False（默认未注册）
            self.current_org = None
            return False
    
    def create_status_bar(self):
        """创建状态栏"""
        try:
            # 创建状态栏框架
            self.status_bar = ttk.Frame(self.root, height=20, relief=tk.SUNKEN)
            self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
            
            # 获取当前注册状态
            is_registered = hasattr(self, 'is_registered') and self.is_registered
            
            # 左侧状态标签 - 用于显示注册状态
            self.reg_status_var = tk.StringVar()
            
            # 根据注册状态设置初始文本和颜色
            if is_registered:
                status_text = f"已注册：{self.current_org}" if self.current_org else "已注册"
                foreground_color = 'green'
            else:
                status_text = "未注册"
                foreground_color = 'red'
                
            self.reg_status_var.set(status_text)
            logging.info(f"状态栏初始化为: {status_text}")
            
            reg_status_label = ttk.Label(
                self.status_bar, 
                textvariable=self.reg_status_var, 
                anchor=tk.W,
                relief=tk.SUNKEN,
                padding=(5, 0, 5, 0),
                width=20,
                foreground=foreground_color
            )
            reg_status_label.pack(side=tk.LEFT, padx=(0, 1))
            
            # 中间状态标签 - 用于显示一般状态信息
            self.status_var = tk.StringVar()
            self.status_var.set("就绪")
            status_label = ttk.Label(
                self.status_bar, 
                textvariable=self.status_var, 
                anchor=tk.W,
                relief=tk.SUNKEN,
                padding=(5, 0, 5, 0)
            )
            status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # 右侧版本信息标签
            version_label = ttk.Label(
                self.status_bar,
                text=f"版本: {self.version}",
                anchor=tk.E,
                relief=tk.SUNKEN,
                padding=(5, 0, 5, 0),
                width=15
            )
            version_label.pack(side=tk.RIGHT)
            
            logging.info("状态栏创建成功")
        except Exception as e:
            logging.error(f"创建状态栏时出错: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
    
    def update_status_bar(self):
        """更新状态栏中的注册状态"""
        try:
            if hasattr(self, 'reg_status_var'):
                logging.debug(f"更新状态栏，当前注册状态: {'已注册' if self.is_registered else '未注册'}")
                old_status = self.reg_status_var.get()
                
                if self.is_registered:
                    status_text = f"已注册：{self.current_org}" if self.current_org else "已注册"
                    self.reg_status_var.set(status_text)
                    # 已注册状态显示为绿色
                    for child in self.status_bar.winfo_children():
                        if isinstance(child, ttk.Label) and child.cget('textvariable') == str(self.reg_status_var):
                            child.configure(foreground='green')
                    logging.info(f"更新状态栏: {status_text}")
                else:
                    self.reg_status_var.set("未注册")
                    # 未注册状态显示为红色
                    for child in self.status_bar.winfo_children():
                        if isinstance(child, ttk.Label) and child.cget('textvariable') == str(self.reg_status_var):
                            child.configure(foreground='red')
                    logging.info("更新状态栏: 未注册")
                
                new_status = self.reg_status_var.get()
                if old_status != new_status:
                    logging.debug(f"状态栏显示已从 '{old_status}' 更改为 '{new_status}'")
            else:
                logging.warning("无法更新状态栏：状态变量不存在")
        except Exception as e:
            logging.error(f"更新状态栏时出错: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
    
    def update_ui_by_registration(self):
        """根据注册状态更新界面"""
        try:
            logging.info(f"开始更新界面，注册状态: {'已注册' if self.is_registered else '未注册'}")
            # 确保状态栏已创建
            if not hasattr(self, 'status_bar'):
                self.create_status_bar()
            
            # 更新状态栏显示
            self.update_status_bar()
            
            # 不再根据注册状态禁用注册菜单项，始终保持可用
            # if hasattr(self, 'help_menu'):
            #     try:
            #         # 直接设置注册菜单项状态
            #         state = tk.DISABLED if self.is_registered else tk.NORMAL
            #         self.help_menu.entryconfigure("用户注册", state=state)
            #         logging.info(f"更新注册菜单项状态: {'禁用' if self.is_registered else '启用'}")
            #     except Exception as e:
            #         logging.error(f"更新注册菜单项状态失败: {str(e)}")
            
            if not self.is_registered:
                # 未注册状态：禁用大部分功能，保留帮助菜单和退出选项
                # 禁用工具栏按钮
                if hasattr(self, 'import_category_btn'):
                    self.import_category_btn.config(state=tk.DISABLED)
                if hasattr(self, 'import_file_btn'):
                    self.import_file_btn.config(state=tk.DISABLED)
                if hasattr(self, 'search_button'):
                    self.search_button.config(state=tk.DISABLED)
                
                # 禁用搜索框
                for widget in self.root.winfo_children():
                    if isinstance(widget, ttk.Frame):
                        for child in widget.winfo_children():
                            if isinstance(child, ttk.Frame):
                                for subchild in child.winfo_children():
                                    if isinstance(subchild, ttk.Entry):
                                        subchild.config(state=tk.DISABLED)
                
                # 有选择地禁用文件菜单项，保留退出功能
                if hasattr(self, 'file_menu'):
                    # 遍历所有菜单项
                    for i in range(self.file_menu.index('end') + 1):
                        try:
                            # 获取菜单项标签
                            label = self.file_menu.entrycget(i, 'label')
                            # 如果不是退出相关选项，则禁用
                            if label != '退出' and label != '登录':
                                self.file_menu.entryconfigure(i, state=tk.DISABLED)
                        except:
                            pass
                
                # 禁用工具菜单
                if hasattr(self, 'tools_menu'):
                    for i in range(self.tools_menu.index('end') + 1):
                        try:
                            self.tools_menu.entryconfigure(i, state=tk.DISABLED)
                        except:
                            pass
                
                # 禁用安全菜单
                if hasattr(self, 'security_menu'):
                    for i in range(self.security_menu.index('end') + 1):
                        try:
                            self.security_menu.entryconfigure(i, state=tk.DISABLED)
                        except:
                            pass
                
                # 确保用户注册菜单项可用（在帮助菜单中）
                menubar = self.root.nametowidget(self.root['menu'])
                for i in range(menubar.index('end') + 1):
                    try:
                        if menubar.entrycget(i, 'label') == '帮助':
                            help_menu = menubar.nametowidget(menubar.entrycget(i, 'menu'))
                            for j in range(help_menu.index('end') + 1):
                                try:
                                    # 确保所有帮助菜单项可用
                                    help_menu.entryconfigure(j, state=tk.NORMAL)
                                except:
                                    pass
                            break
                    except:
                        pass
                
                logging.info("已设置为未注册状态界面")
            else:
                # 已注册状态：启用所有功能
                logging.info("已设置为已注册状态界面")
                
                # 不再隐藏用户注册菜单项，始终保持可用
                # menubar = self.root.nametowidget(self.root['menu'])
                # for i in range(menubar.index('end') + 1):
                #     try:
                #         if menubar.entrycget(i, 'label') == '帮助':
                #             help_menu = menubar.nametowidget(menubar.entrycget(i, 'menu'))
                #             for j in range(help_menu.index('end') + 1):
                #                 try:
                #                     if help_menu.entrycget(j, 'label') == '用户注册':
                #                         help_menu.entryconfigure(j, state=tk.DISABLED)
                #                 except:
                #                     pass
                #             break
                #     except:
                #         pass
        
        except Exception as e:
            logging.error(f"更新界面失败: {str(e)}")
    
    def register_system(self, reg_code, user_name):
        """注册系统"""
        try:
            # 使用用户管理模块的注册验证逻辑
            from src.ui.user_management import UserManager
            if not hasattr(self, 'user_manager'):
                self.user_manager = UserManager(self)
                
            # 调用用户管理模块的注册方法
            success, message = self.user_manager.register_system(reg_code, user_name)
            
            if success:
                # 更新注册状态
                self.is_registered = True
                self.current_org = user_name  # 保存当前单位名
                logging.info(f"系统注册状态已更新: 已注册，单位: {self.current_org}")
                
                # 强制更新状态栏
                if hasattr(self, 'reg_status_var'):
                    # 直接设置新状态，确保显示变化
                    status_text = f"已注册：{user_name}"
                    self.reg_status_var.set(status_text)
                    
                    # 设置颜色为绿色
                    for child in self.status_bar.winfo_children():
                        if isinstance(child, ttk.Label) and child.cget('textvariable') == str(self.reg_status_var):
                            child.configure(foreground='green')
                    
                    logging.info(f"状态栏已更新为: {status_text}")
                else:
                    logging.warning("无法更新状态栏：状态变量不存在")
                
                # 更新界面
                self.update_ui_by_registration()
                
                # 最后显示成功消息
                messagebox.showinfo("注册成功", message)
                return True
            else:
                logging.warning(f"注册失败: {message}")
                messagebox.showerror("注册失败", message)
                return False
        except Exception as e:
            logging.error(f"注册系统失败: {str(e)}")
            messagebox.showerror("注册错误", f"注册系统时发生错误：{str(e)}")
            return False
    
    def show_registration_dialog(self):
        """显示注册对话框"""
        logging.debug("显示注册对话框")
        
        # 创建注册对话框
        reg_dialog = tk.Toplevel(self.root)
        reg_dialog.title("系统注册")
        reg_dialog.geometry("350x200")
        reg_dialog.resizable(False, False)
        reg_dialog.transient(self.root)
        reg_dialog.grab_set()
        
        # 表单框架
        form_frame = ttk.Frame(reg_dialog, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # 注册码
        ttk.Label(form_frame, text="注册码:").grid(row=0, column=0, sticky=tk.W, pady=5)
        reg_code_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=reg_code_var, width=25).grid(row=0, column=1, pady=5)
        
        # 用户名称
        ttk.Label(form_frame, text="用户名称:").grid(row=1, column=0, sticky=tk.W, pady=5)
        user_name_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=user_name_var, width=25).grid(row=1, column=1, pady=5)
        
        # 错误信息
        error_var = tk.StringVar()
        error_label = ttk.Label(form_frame, textvariable=error_var, foreground="red")
        error_label.grid(row=2, column=0, columnspan=2, pady=5)
        
        # 注册按钮处理函数
        def do_register():
            reg_code = reg_code_var.get().strip()
            user_name = user_name_var.get().strip()
            
            # 验证表单
            if not reg_code:
                error_var.set("注册码不能为空")
                return
            
            if not user_name:
                error_var.set("用户名称不能为空")
                return
            
            # 注册系统
            if self.register_system(reg_code, user_name):
                reg_dialog.destroy()
            else:
                error_var.set("注册失败: 无效的注册码或用户名")
        
        # 创建一个按钮框架
        buttons_frame = ttk.Frame(form_frame)
        buttons_frame.grid(row=3, column=0, columnspan=2, pady=15)
        
        # 添加按钮
        ttk.Button(buttons_frame, text="确定", command=do_register, width=10).pack(side=tk.LEFT, padx=15)
        ttk.Button(buttons_frame, text="取消", command=reg_dialog.destroy, width=10).pack(side=tk.LEFT, padx=15)
        
        # 居中对话框
        reg_dialog.update_idletasks()
        width = reg_dialog.winfo_width()
        height = reg_dialog.winfo_height()
        x = (reg_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (reg_dialog.winfo_screenheight() // 2) - (height // 2)
        reg_dialog.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        reg_dialog.wait_window()

    # 状态栏相关方法已合并到上面的create_status_bar方法中

    # 其他方法...
    def some_other_method(self):
        if not hasattr(self, 'search_result_var'):
            self.search_result_var = tk.StringVar()
            self.search_result_var.set("就绪")

    # 添加安全功能相关方法
    def show_integrity_check(self):
        """显示档案完整性检查对话框"""
        try:
            # 获取档案目录
            archives_dir = None
            if hasattr(self, 'db') and self.db:
                # 从数据库或配置中获取档案目录
                try:
                    # 尝试从数据库获取
                    query = "SELECT value FROM system_settings WHERE key = 'archives_dir'"
                    result = self.db.execute_query(query)
                    if result and result[0][0]:
                        archives_dir = result[0][0]
                except:
                    # 如果出错，尝试从设置中获取
                    if hasattr(self, 'import_root_dir') and self.import_root_dir:
                        archives_dir = self.import_root_dir
            
            # 导入安全模块UI
            try:
                # 打包环境
                if getattr(sys, 'frozen', False):
                    from security.ui import IntegrityCheckDialog
                else:
                    # 开发环境
                    from src.security.ui import IntegrityCheckDialog
                
                # 显示对话框
                dialog = IntegrityCheckDialog(self.root, archives_dir=archives_dir)
                
                # 等待对话框关闭
                self.root.wait_window(dialog)
                
            except ImportError as e:
                logging.error(f"导入安全模块失败: {str(e)}")
                messagebox.showerror("错误", f"无法加载安全模块: {str(e)}")
        
        except Exception as e:
            logging.exception(f"显示档案完整性检查对话框时出错: {str(e)}")
            messagebox.showerror("错误", f"打开档案完整性检查工具时出错: {str(e)}")
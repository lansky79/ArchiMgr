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

from utils.excel_utils import get_excel_info, ExcelFileNotFound

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
        
        # 用户设置文件路径
        self.config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'config')
        os.makedirs(self.config_dir, exist_ok=True)
        self.settings_file = os.path.join(self.config_dir, 'user_settings.json')
        
        # 注册信息文件路径
        self.registration_file = os.path.join(self.config_dir, 'registration.txt')
        
        # 检查注册状态
        self.is_registered = self.check_registration()
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
        
        # 测试用：默认登录为管理员
        self.current_user = (1, 'admin', '管理员', 'admin')
        self.login_status_var.set(f"已登录: 管理员")
        self.update_menu_by_role('admin')
        self.update_tools_permission(True)
        
        # 根据注册状态更新界面
        self.update_ui_by_registration()
        
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
            
        elif role == 'user':
            # 普通用户菜单
            self.file_menu.add_command(label="退出登录", command=self.logout)
            self.file_menu.add_separator()
            self.file_menu.add_command(label="退出系统", command=self.root.quit)
            
            # 禁用工具菜单
            self.update_tools_permission(False)
            
        else:
            # 未登录菜单
            self.file_menu.add_command(label="登录", command=self.show_login_dialog)
            self.file_menu.add_separator()
            self.file_menu.add_command(label="退出系统", command=self.root.quit)
            
            # 禁用工具菜单
            self.update_tools_permission(False)
        
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
                self.tools_menu.entryconfigure("清理数据库", state=tk.NORMAL)
            else:
                # 禁用清理数据库菜单
                self.tools_menu.entryconfigure("清理数据库", state=tk.DISABLED)

    def setup_ui(self):
        """设置用户界面"""
        # 设置窗口标题
        self.root.title("档案检索系统")
        
        # 设置窗口大小和位置
        window_width = 1024
        window_height = 768
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
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明", command=self.show_help)
        
        # 添加用户注册选项（未注册时可用）
        help_menu.add_command(label="用户注册", command=self.show_registration_dialog)
        
        help_menu.add_command(label="关于", command=self.show_about)
        
        # 工具菜单
        self.tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=self.tools_menu)
        self.tools_menu.add_command(label="打开程序安装目录", command=self.open_install_directory)
        self.tools_menu.add_command(label="打开档案文件目录", command=self.open_archive_directory)
        self.tools_menu.add_command(label="打开数据库位置", command=self.open_database_location)
        self.tools_menu.add_separator()
        self.tools_menu.add_command(label="清理数据库", command=self.cleanup_database)
        
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
            text="导入文件", 
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
        
        logging.debug(f"要更新的文件列表数量: {len(files)}")
        if files:
            sample_files = files[:3]
            logging.debug(f"文件样本: {sample_files}")
        
        try:
            # 筛选只显示PDF文件
            pdf_files = []
            for file_name, file_path in files:
                # 将文件名转为小写进行判断
                if file_name.lower().endswith('.pdf'):
                    pdf_files.append((file_name, file_path))
                    
            logging.debug(f"筛选后的PDF文件数量: {len(pdf_files)}")
            
            # 插入新的文件记录
            for file_name, file_path in pdf_files:
                # 从文件路径中提取人名和文件夹名
                dir_name = os.path.basename(os.path.dirname(file_path))
                
                # 提取编号 - 获取文件夹名中的数字前缀
                # 正则表达式提取开头的连续数字
                match = re.match(r'^(\d+)(.*)', dir_name)
                file_id = ""
                person_name = dir_name
                
                if match:
                    file_id = match.group(1)
                    # 处理姓名，去掉数字部分只保留人名
                    person_name = match.group(2).strip()
                
                # 文件名就是类号（例如 3-1.pdf 的类号就是 3-1）
                class_code = os.path.splitext(file_name)[0]
                
                logging.debug(f"处理文件: {file_name}, 类号: {class_code}, 编号: {file_id}, 人名: {person_name}, 目录名: {dir_name}")
                
                # 从Excel获取文件信息（材料名称、日期、页数）
                try:
                    # dir_name = 文件夹名（如 123张三），需分解为编号和姓名
                    match = re.match(r'^(\d+)(.+)$', dir_name)
                    if match:
                        file_id = match.group(1)
                        person_name = match.group(2).strip()
                    else:
                        file_id = ''
                        person_name = dir_name
                    material_name, file_date, page_count = get_excel_info(self.import_root_dir, person_name, file_id, class_code)
                except ExcelFileNotFound as e:
                    logging.warning(str(e))
                    material_name, file_date, page_count = '', '', ''
                    messagebox.showwarning("未找到Excel文件", str(e))
                except Exception as e:
                    logging.error(f"Excel信息读取失败: {str(e)}")
                    material_name, file_date, page_count = '', '', ''
                    messagebox.showerror("Excel读取错误", f"读取Excel信息时发生错误：{str(e)}")
                
                # 插入到列表
                self.file_list.insert('', 'end', values=(
                    file_id,
                    person_name,
                    class_code,
                    material_name,
                    file_name,
                    file_date,
                    page_count,
                    file_path
                ))
                
        except Exception as e:
            logging.error(f"更新文件列表失败: {str(e)}")
            messagebox.showerror("错误", f"更新文件列表失败：{str(e)}")

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
        """验证登录信息"""
        try:
            hashed_password = self.hash_password(password)
            self.db.cursor.execute(
                'SELECT id, username, real_name, role FROM users WHERE username = ? AND password = ?',
                (username, hashed_password)
            )
            user = self.db.cursor.fetchone()
            if user:
                return True, user
            else:
                return False, None
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
                self.login_status_var.set(f"已登录: {user[2]}")
                messagebox.showinfo("登录成功", f"欢迎回来，{user[2]}！")
                
                # 更新菜单和权限
                self.update_menu_by_role(user[3])
                
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
        
    def show_help(self):
        """显示帮助信息"""
        logging.debug("显示帮助信息")
        
        # 创建帮助窗口
        help_window = tk.Toplevel(self.root)
        help_window.title("使用说明 - 档案检索系统 v1.0(0518)")
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
        help_text = """档案检索系统使用说明 (v1.0(0518))

1. 系统注册
   * 初次使用请点击"帮助"菜单中的"用户注册"
   * 输入注册码和用户名称进行注册
   * 注册成功后重启程序即可使用全部功能
   * 注册信息保存在程序目录下的registration.txt文件中

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
   * 导入文件: 导入档案文件（所有登录用户可用）
   * 支持批量导入整个目录
   * 自动识别并导入PDF文件
   * 自动从Excel文件读取材料信息
   * 导入时会自动去重，避免重复导入

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
        registration_info = "已注册：新都区自然资源规划局" if is_registered else "未注册"
        
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
            text=f"档案检索系统\n\n版本: v{self.version}\n{registration_info}",
            justify=tk.CENTER
        ).pack(pady=10)
        
        # 分隔线
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # 按钮框架
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(5, 0))
        
        # 确定按钮
        btn = ttk.Button(
            btn_frame, 
            text="确定", 
            command=about_window.destroy,
            width=10
        )
        btn.pack(side=tk.TOP, pady=5)
        
        # 确保窗口大小合适
        about_window.update_idletasks()
        
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
        """搜索人员档案（支持分类过滤）"""
        # 取消左侧分类的选择
        if hasattr(self, 'tree') and self.tree.selection():
            for item in self.tree.selection():
                self.tree.selection_remove(item)
        
        search_name = self.search_name_var.get().strip()
        search_id = self.search_id_var.get().strip()
        
        try:
            # 清理之前的搜索结果
            self.file_list.delete(*self.file_list.get_children())
            
            # 清理搜索状态
            if not search_name and not search_id:
                self.current_search_name = None
                self.current_search_id = None
                self.has_searched = False
                self.search_result_var.set("就绪")
                messagebox.showinfo("提示", "请输入姓名或编号进行搜索")
                return
            
            # 保存当前搜索的人名和编号
            self.current_search_name = search_name if search_name else None
            self.current_search_id = search_id if search_id else None
            
            # 标记已进行搜索
            self.has_searched = True
            
            logging.info(f"执行搜索：姓名='{search_name}', 编号='{search_id}'")
            # 直接执行搜索，不检查分类选择
            # 因为我们已经取消了分类选择，所以这里直接执行搜索逻辑
            
            # 如果只通过姓名搜索，检查是否有重名人员
            if search_name and not search_id:
                # 获取所有不同的编号
                self.db.cursor.execute('''
                    SELECT DISTINCT file_id 
                    FROM person_files 
                    WHERE person_name = ?
                    ORDER BY file_id
                ''', (search_name,))
                
                id_list = [str(row[0]) for row in self.db.cursor.fetchall() if row[0]]
                
                if len(id_list) > 1:
                    # 设置重名标志
                    self.has_duplicate_names = True
                    # 找到多个不同编号的相同姓名，显示所有编号并提示用户输入
                    id_text = ", ".join(id_list)
                    logging.info(f"发现 {len(id_list)} 个同名人员，编号: {id_text}")
                    self.search_result_var.set(f"发现 {len(id_list)} 个同名人员，请选择编号: {id_text}")
                    messagebox.showinfo(
                        "发现重名", 
                        f"发现 {len(id_list)} 个同名人员，请选择编号后重新搜索：\n\n" +
                        "\n".join([f"编号: {id}" for id in id_list])
                    )
                    # 清空文件列表，等待用户输入编号
                    self.file_list.delete(*self.file_list.get_children())
                    return
                else:
                    # 如果没有重名，清除重名标志
                    self.has_duplicate_names = False
            
            # 构建查询
            query = '''
                SELECT DISTINCT file_name, file_path 
                FROM person_files 
                WHERE 1=1
            '''
            params = []
            
            # 添加文件名过滤条件
            query += ' AND file_name NOT LIKE ? AND file_name NOT LIKE ? AND file_name LIKE ?'
            params.extend(['~%', '.%', '%.pdf'])
            
            # 添加人名过滤条件 - 使用完全匹配
            if search_name:
                query += ' AND person_name = ?'
                params.append(search_name)
            
            # 添加编号过滤条件
            if search_id:
                query += ' AND file_id = ?'
                params.append(search_id)
            
            query += ' ORDER BY file_name'
            
            logging.info(f"搜索查询SQL: {query}, 参数: {params}")
            
            # 执行查询
            self.db.cursor.execute(query, params)
            files = self.db.cursor.fetchall()
            
            # 更新文件列表显示
            self.update_file_list(files)
            
            # 更新状态栏显示搜索结果数量
            if files:
                result_text = f"找到 {len(files)} 个匹配文件"
                self.search_result_var.set(result_text)
                logging.info(f"搜索结果: {result_text}")
                
                # 显示搜索结果提示
                if len(files) > 0:
                    messagebox.showinfo("搜索结果", result_text)
            else:
                self.search_result_var.set("未找到匹配文件")
                logging.info("搜索结果: 未找到匹配文件")
                messagebox.showinfo("搜索结果", "未找到匹配文件")
                
        except Exception as e:
            logging.error(f"搜索失败: {str(e)}", exc_info=True)
            messagebox.showerror("错误", f"搜索失败：{str(e)}")
            self.search_result_var.set("搜索失败")

    def extract_category_num(self, filename):
        """从文件名中提取分类号"""
        parts = filename.split('-')
        if len(parts) >= 2 and parts[0].isdigit():
            return f"{parts[0]}-{parts[1]}" if parts[1].isdigit() else parts[0]
        return None

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
                        SELECT DISTINCT file_name, file_path 
                        FROM person_files 
                        WHERE (
                            file_name LIKE ? OR    -- 精确的分类代码-开头 (4-1-%)
                            file_name LIKE ?       -- 点号分隔的格式 (4.1.%)
                        )
                        AND file_name NOT LIKE '~%'
                        AND file_name NOT LIKE '.%'
                        AND file_name LIKE '%.pdf'
                    '''
                    # 两种模式匹配: 标准格式(4-1-%)和点分格式(4.1.%)
                    params = [f'{category_code}-%', f'{category_code.replace("-", ".")}%']
                    
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
                            SELECT DISTINCT file_name, file_path 
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
    
    def on_file_double_click(self, event):
        """处理文件双击事件"""
        selected_items = self.file_list.selection()
        if not selected_items:
            return
        
        # 获取选中项的完整路径
        item = selected_items[0]
        file_path = self.file_list.item(item)['values'][7]  # 第8列是路径
        
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                messagebox.showerror("错误", f"找不到文件：\n{file_path}")
                logging.error(f"文件不存在: {file_path}")
                return
            
            # 打开文件
            logging.debug(f"打开文件: {file_path}")
            if sys.platform == 'win32':
                os.startfile(file_path)
            elif sys.platform == 'darwin':  # macOS
                subprocess.run(['open', file_path])
            else:  # linux
                subprocess.run(['xdg-open', file_path])
            
        except Exception as e:
            error_msg = f"打开文件失败：{str(e)}"
            logging.error(error_msg)
            messagebox.showerror("错误", error_msg)

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
            # 从设置中获取档案文件目录，如果没有则使用默认目录
            archive_dir = self.settings.get('import_root_dir')
            if not archive_dir or not os.path.exists(archive_dir):
                # 如果没有设置或目录不存在，询问用户选择目录
                messagebox.showinfo("提示", "档案文件目录未设置或不存在，请选择档案文件目录")
                archive_dir = filedialog.askdirectory(title="选择档案文件目录")
                if archive_dir:
                    # 保存到设置中
                    self.settings['import_root_dir'] = archive_dir
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
            # 检查配置目录下的注册文件是否存在
            config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'config')
            if not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)
                
            registration_file = os.path.join(config_dir, 'registration.dat')
            
            if os.path.exists(registration_file):
                with open(registration_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    # 简单加密处理
                    decoded_content = ''.join([chr(ord(c) - 1) for c in content])
                    parts = decoded_content.split('|')
                    if len(parts) >= 2:
                        reg_code = parts[0].strip()
                        user_name = parts[1].strip()
                        # 验证注册码和用户名
                        if reg_code == "2xdqzr5zyghj" and user_name == "新都区自然资源规划局":
                            logging.info(f"注册验证成功: {user_name}")
                            return True
        
            # 如果没有找到有效的注册文件，返回False（未注册）
            logging.info("系统未注册")
            return False
        except Exception as e:
            logging.error(f"检查注册状态失败: {str(e)}")
            # 如果出错，返回False（默认未注册）
            return False
    
    def update_ui_by_registration(self):
        """根据注册状态更新界面"""
        try:
            if not self.is_registered:
                # 未注册状态：禁用大部分功能，保留帮助菜单和退出选项
                # 禁用工具栏按钮
                if hasattr(self, 'import_category_btn'):
                    self.import_category_btn.config(state=tk.DISABLED)
                if hasattr(self, 'import_file_btn'):
                    self.import_file_btn.config(state=tk.DISABLED)
                
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
                
                # 更新状态栏显示未注册信息
                if hasattr(self, 'status_var'):
                    self.status_var.set("未注册")
                
                logging.info("已设置为未注册状态界面")
            else:
                # 已注册状态：启用所有功能，隐藏注册菜单项
                logging.info("已设置为已注册状态界面")
                
                # 隐藏用户注册菜单项
                menubar = self.root.nametowidget(self.root['menu'])
                for i in range(menubar.index('end') + 1):
                    try:
                        if menubar.entrycget(i, 'label') == '帮助':
                            help_menu = menubar.nametowidget(menubar.entrycget(i, 'menu'))
                            for j in range(help_menu.index('end') + 1):
                                try:
                                    if help_menu.entrycget(j, 'label') == '用户注册':
                                        help_menu.entryconfigure(j, state=tk.DISABLED)
                                except:
                                    pass
                            break
                    except:
                        pass
                
                # 更新状态栏显示已注册信息
                if hasattr(self, 'status_var'):
                    self.status_var.set("已注册：新都区自然资源规划局")
        
        except Exception as e:
            logging.error(f"更新界面失败: {str(e)}")
    
    def register_system(self, reg_code, user_name):
        """注册系统"""
        try:
            # 验证注册码和用户名
            if reg_code == "2xdqzr5zyghj" and user_name == "新都区自然资源规划局":
                # 确保配置目录存在
                config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'config')
                if not os.path.exists(config_dir):
                    os.makedirs(config_dir, exist_ok=True)
                    
                # 保存注册信息到加密文件
                registration_file = os.path.join(config_dir, 'registration.dat')
                
                # 简单加密处理（每个字符ASCII码+1）
                encoded_content = ''.join([chr(ord(c) + 1) for c in f"{reg_code}|{user_name}"])
                
                with open(registration_file, 'w', encoding='utf-8') as f:
                    f.write(encoded_content)
                
                self.is_registered = True
                logging.info(f"系统注册成功: {user_name}")
                
                # 更新状态栏
                if hasattr(self, 'status_var'):
                    self.status_var.set(f"已注册：{user_name}")
                
                # 更新界面
                self.update_ui_by_registration()
                
                # 重启应用以应用注册
                messagebox.showinfo("注册成功", "系统已成功注册！请重启应用程序以应用所有功能。")
                return True
            else:
                logging.warning(f"注册失败: 无效的注册码或用户名")
                messagebox.showerror("注册失败", "无效的注册码或用户名，请联系系统管理员。")
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

    def create_status_bar(self):
        """创建状态栏"""
        # 创建状态栏框架
        status_frame = ttk.Frame(self.root)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 第一栏：注册状态和用户单位
        self.status_var = tk.StringVar()
        if hasattr(self, 'is_registered') and self.is_registered:
            self.status_var.set("已注册：新都区自然资源规划局")
        else:
            self.status_var.set("未注册")
            
        status_label1 = ttk.Label(
            status_frame, 
            textvariable=self.status_var, 
            relief=tk.SUNKEN, 
            anchor=tk.W,
            padding=(5, 2, 5, 2),
            width=30
        )
        status_label1.pack(side=tk.LEFT, fill=tk.X, padx=(0, 1))
        
        # 第二栏：版本信息
        version_text = f"版本: {self.version}"
        status_label2 = ttk.Label(
            status_frame, 
            text=version_text,
            relief=tk.SUNKEN, 
            anchor=tk.W,
            padding=(5, 2, 5, 2),
            width=15
        )
        status_label2.pack(side=tk.LEFT, fill=tk.X, padx=(0, 1))
        
        # 第三栏：搜索结果/状态信息
        if not hasattr(self, 'search_result_var'):
            self.search_result_var = tk.StringVar()
            self.search_result_var.set("就绪")
            
        status_label3 = ttk.Label(
            status_frame, 
            textvariable=self.search_result_var,
            relief=tk.SUNKEN, 
            anchor=tk.W,
            padding=(5, 2, 5, 2)
        )
        status_label3.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
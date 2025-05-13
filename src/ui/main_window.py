import tkinter as tk
from tkinter import ttk
import logging
import shutil
import os
from tkinter import filedialog, messagebox
import pandas as pd
import subprocess
import sys

class MainWindow:
    def __init__(self, root, db=None):
        self.root = root
        self.db = db
        
        # 设置日志级别为 DEBUG
        logging.getLogger().setLevel(logging.DEBUG)
        
        # 初始化文件列表和分类映射
        self.all_files = []
        self.category_mapping = {}
        
        # 设置UI
        self.setup_ui()
        
        # 初始化数据
        self.init_data()
        
        self.current_search_name = None  # 添加当前搜索人名的记录
<<<<<<< Updated upstream
=======
        self.current_search_id = None  # 添加当前搜索编号的记录
        self.has_searched = False  # 标记是否进行过搜索
        
        # 初始设置权限（未登录状态）
        self.update_menu_by_role(None)
        self.update_tools_permission(False)
        
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
            if is_admin:
                self.import_file_btn.config(state=tk.NORMAL)
                # 启用清理数据库菜单
                self.tools_menu.entryconfigure("清理数据库", state=tk.NORMAL)
            else:
                self.import_file_btn.config(state=tk.DISABLED)
                # 禁用清理数据库菜单
                self.tools_menu.entryconfigure("清理数据库", state=tk.DISABLED)

    def get_version(self):
        """获取系统版本号"""
        version_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'version.txt')
        if os.path.exists(version_file):
            try:
                with open(version_file, 'r') as f:
                    return f.read().strip()
            except Exception as e:
                logging.error(f"读取版本文件失败: {str(e)}")
                return "1.0.0"
        else:
            return "1.0.0"
>>>>>>> Stashed changes
        
    def setup_ui(self):
        """设置用户界面"""
        # 设置窗口标题
        self.root.title("档案管理系统")
        
        # 设置窗口大小和位置
        window_width = 1024
        window_height = 768
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 创建工具栏
        self.create_toolbar()
        
        # 创建主框架
        self.create_main_frame()
        
    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="登录", command=self.show_login_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明", command=self.show_help)
        help_menu.add_command(label="关于", command=self.show_about)
        
        # 工具菜单
<<<<<<< Updated upstream
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tools_menu)
        tools_menu.add_command(label="清理数据库", command=self.cleanup_database)
=======
        self.tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=self.tools_menu)
        self.tools_menu.add_command(label="打开程序安装目录", command=self.open_install_directory)
        self.tools_menu.add_command(label="打开档案文件目录", command=self.open_archive_directory)
        self.tools_menu.add_command(label="打开数据库位置", command=self.open_database_location)
        self.tools_menu.add_separator()
        self.tools_menu.add_command(label="清理数据库", command=self.cleanup_database)
        
        # 用户管理菜单（初始时不显示，管理员登录后再添加）
        self.user_menu = tk.Menu(menubar, tearoff=0)
>>>>>>> Stashed changes
        
    def create_toolbar(self):
        """创建工具栏"""
        # 创建工具栏框架
        toolbar_frame = ttk.Frame(self.root)
        toolbar_frame.pack(side=tk.TOP, fill=tk.X)
        
        # 添加搜索框
        ttk.Label(toolbar_frame, text="搜索:").pack(side=tk.LEFT, padx=5, pady=5)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(toolbar_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5, pady=5)
        
<<<<<<< Updated upstream
        # 导入分类按钮
        import_category_btn = ttk.Button(
            button_frame, 
            text="导入分类", 
            command=self.import_categories
        )
        import_category_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 导入文件按钮
        import_file_btn = ttk.Button(
            button_frame, 
            text="导入文件", 
            command=self.import_files
        )
        import_file_btn.pack(side=tk.LEFT)
        
        # 右侧搜索框架
        search_frame = ttk.Frame(toolbar_frame)
        search_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        # 搜索框
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # 搜索按钮
        search_button = ttk.Button(search_frame, text="搜索", command=self.search_person)
        search_button.pack(side=tk.LEFT)
        
    def create_main_frame(self):
        """创建主框架"""
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建左右分隔窗口
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # 创建左侧框架（用于分类树）
        self.left_frame = ttk.Frame(paned)
        paned.add(self.left_frame, weight=1)
=======
        # 添加搜索按钮
        search_button = ttk.Button(toolbar_frame, text="搜索", command=self.search_person)
        search_button.pack(side=tk.LEFT, padx=5, pady=5)
        
    def create_main_frame(self):
        """创建主框架"""
        # 创建白色背景样式
        style = ttk.Style()
        style.configure('White.TFrame', background='white')
        
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # 创建左侧框架（用于分类树）
        self.left_frame = ttk.Frame(main_frame, style='White.TFrame')
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
>>>>>>> Stashed changes
        
        # 创建右侧框架（用于文件列表）
        self.right_frame = ttk.Frame(main_frame)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 设置分类树
        self.setup_category_tree()
        
        # 设置文件列表
        self.setup_file_list()
        
    def setup_category_tree(self):
        """设置分类树"""
        # 创建树形控件
        self.tree = ttk.Treeview(self.left_frame, show='tree')
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(self.left_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定选择事件
        self.tree.bind('<<TreeviewSelect>>', self.on_category_selected)
        
        # 从数据库加载分类
        self.load_categories_from_db()
        
    def setup_file_list(self):
        """设置文件列表"""
        # 创建文件列表框架
        list_frame = ttk.Frame(self.right_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建Treeview，添加说明列
        self.file_list = ttk.Treeview(
            list_frame, 
            columns=('filename', 'person', 'category', 'description', 'path'),
            show='headings'
        )
        
        # 设置列标题
        self.file_list.heading('filename', text='文件名')
        self.file_list.heading('person', text='姓名')
        self.file_list.heading('category', text='分类')
        self.file_list.heading('description', text='说明')
        self.file_list.heading('path', text='路径')
        
        # 设置列宽度
        self.file_list.column('filename', width=100)
        self.file_list.column('person', width=80)
        self.file_list.column('category', width=150)
        self.file_list.column('description', width=200)
        self.file_list.column('path', width=300)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_list.yview)
        self.file_list.configure(yscrollcommand=scrollbar.set)
        
        # 布局
        self.file_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定双击事件
        self.file_list.bind('<Double-1>', self.on_file_double_click)

    def get_category_info(self, file_code):
        """根据文件编码获取分类信息"""
        try:
            main_num = file_code.split('-')[0]
            
            # 查询主分类名称
            self.db.cursor.execute('''
                SELECT category 
                FROM categories 
                WHERE main_category_num = ? 
                AND parent_category IS NULL
            ''', (main_num,))
            
            result = self.db.cursor.fetchone()
            if result:
                return result[0]
            return ""
            
        except Exception as e:
            logging.error(f"获取分类信息失败: {str(e)}")
            return ""

    def update_file_list(self, files):
        """更新文件列表"""
        # 清空现有列表
        self.file_list.delete(*self.file_list.get_children())
        
        try:
            # 插入新的文件记录
            for file_name, file_path in files:
                # 从文件路径中提取人名（文件夹名）
                person_name = os.path.basename(os.path.dirname(file_path))
                
                # 从文件名中提取分类编码（例如 9-2）
                file_code = '-'.join(file_name.split('-')[:2])
                
                # 获取分类名称
                category_name = self.get_category_info(file_code)
                
                # 分类列只显示编码
                category_display = file_code
                
                # 说明列显示分类名称
                description = category_name
                
                self.file_list.insert('', 'end', values=(
                    file_name,
                    person_name,
                    category_display,
                    description,
                    file_path
                ))
                
        except Exception as e:
            logging.error(f"更新文件列表失败: {str(e)}")
            messagebox.showerror("错误", f"更新文件列表失败：{str(e)}")

<<<<<<< Updated upstream
    # 事件处理方法
=======
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
        
        # 导入拼音工具
        from src.utils.pinyin_util import hanzi_to_pinyin, is_valid_pinyin_for_name
        
        # 严格检查权限 - 确保只有管理员登录后才能访问此功能
        if not self.current_user:
            messagebox.showerror("权限错误", "请先以管理员身份登录")
            # 显示登录对话框
            self.show_login_dialog()
            return
        elif self.current_user[3] != 'admin':
            messagebox.showerror("权限错误", "只有管理员可以添加用户")
            return
        
        # 创建注册对话框
        register_dialog = tk.Toplevel(self.root)
        register_dialog.title("添加用户")
        register_dialog.geometry("350x280")  # 增加对话框高度以容纳提示信息
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
        
        # 用户名提示
        username_hint = ttk.Label(form_frame, text="(必须为真实姓名的拼音，小写)", font=("SimSun", 8))
        username_hint.grid(row=0, column=2, sticky=tk.W, pady=5, padx=5)
        
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
        real_name_entry = ttk.Entry(form_frame, textvariable=real_name_var, width=20)
        real_name_entry.grid(row=3, column=1, pady=5)
        
        # 自动生成拼音按钮
        def generate_pinyin():
            real_name = real_name_var.get().strip()
            if real_name:
                pinyin = hanzi_to_pinyin(real_name)
                username_var.set(pinyin)
                error_var.set(f"已自动生成用户名: {pinyin}")
            else:
                error_var.set("请先输入真实姓名")
        
        ttk.Button(form_frame, text="生成用户名", command=generate_pinyin, width=10).grid(row=3, column=2, padx=5)
        
        # 错误信息
        error_var = tk.StringVar()
        error_label = ttk.Label(form_frame, textvariable=error_var, foreground="red", wraplength=300)
        error_label.grid(row=4, column=0, columnspan=3, pady=5)
        
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
            
            # 验证用户名是否为真实姓名的拼音
            is_valid, message = is_valid_pinyin_for_name(username, real_name)
            if not is_valid:
                error_var.set(message)
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
    
>>>>>>> Stashed changes
    def show_login_dialog(self):
        """显示登录对话框"""
        logging.debug("显示登录对话框")
        # TODO: 实现登录对话框
        
    def show_help(self):
        """显示帮助信息"""
        logging.debug("显示帮助信息")
        # TODO: 实现帮助对话框
        
    def show_about(self):
        """显示关于信息"""
        logging.debug("显示关于信息")
        # TODO: 实现关于对话框
        
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
            
            # 读取Excel文件的A列（分类号）、B列和D列
            df = pd.read_excel(file_path, usecols=[0, 1, 3], engine='openpyxl', header=None)
            
            # 清空现有分类
            self.tree.delete(*self.tree.get_children())
            self.db.cursor.execute('DELETE FROM categories')
            
            # 用于存储一级分类节点的字典
            parent_nodes = {}
            
            # 第一遍循环：处理所有分类
            for index, row in df.iterrows():
                category_num = str(row[0]).strip() if pd.notna(row[0]) else ""  # A列：分类号
                b_value = str(row[1]).strip() if pd.notna(row[1]) else ""      # B列
                d_value = str(row[3]).strip() if pd.notna(row[3]) else ""      # D列
                
                # 跳过空行
                if not category_num and not b_value and not d_value:
                    continue
                    
                # 解析分类号
                nums = category_num.split('-') if category_num else []
                main_num = int(nums[0]) if nums and nums[0].isdigit() else None
                sub_num = int(nums[1]) if len(nums) > 1 and nums[1].isdigit() else None
                
                if not b_value or b_value == 'nan':
                    # 这是一级分类
                    node_id = self.tree.insert('', 'end', text=d_value)
                    parent_nodes[d_value] = node_id
                    
                    # 存入数据库
                    self.db.cursor.execute(
                        'INSERT INTO categories (category, parent_category, main_category_num, sub_category_num) VALUES (?, ?, ?, ?)',
                        (d_value, None, main_num, None)
                    )
                    logging.debug(f"插入一级分类: {d_value}")
                
                # 如果B列不为空，说这是一个父分类，需要先把它加入数据库
                if b_value and b_value != 'nan':
                    # 检查父分类是否已经在数据库中
                    self.db.cursor.execute('SELECT category FROM categories WHERE category = ?', (b_value,))
                    if not self.db.cursor.fetchone():
                        # 分类不存在，先插入父分类
                        self.db.cursor.execute(
                            'INSERT INTO categories (category, parent_category, main_category_num, sub_category_num) VALUES (?, ?, ?, ?)',
                            (b_value, None, main_num, None)
                        )
                        logging.debug(f"插入父分类: {b_value}")
                        
                        # 创建树节点
                        if b_value not in parent_nodes:
                            node_id = self.tree.insert('', 'end', text=b_value)
                            parent_nodes[b_value] = node_id
            
            # 第二遍循环：创建所有二级分类
            for index, row in df.iterrows():
                category_num = str(row[0]).strip() if pd.notna(row[0]) else ""
                b_value = str(row[1]).strip() if pd.notna(row[1]) else ""
                d_value = str(row[3]).strip() if pd.notna(row[3]) else ""
                
                # 跳过空行
                if not category_num and not b_value and not d_value:
                    continue
                    
                # 解析分类号
                nums = category_num.split('-') if category_num else []
                main_num = int(nums[0]) if nums and nums[0].isdigit() else None
                sub_num = int(nums[1]) if len(nums) > 1 and nums[1].isdigit() else None
                
                if b_value and b_value != 'nan':
                    # 这是二级分类
                    if b_value in parent_nodes:
                        # 将D列内容作为B列内容的子分类
                        child_id = self.tree.insert(parent_nodes[b_value], 'end', text=d_value)
                        
                        # 存入数据库
                        self.db.cursor.execute(
                            'INSERT INTO categories (category, parent_category, main_category_num, sub_category_num) VALUES (?, ?, ?, ?)',
                            (d_value, b_value, main_num, sub_num)
                        )
                        logging.debug(f"插入二级分类: {d_value}, 父分类: {b_value}")
                    else:
                        logging.warning(f"找不到父分类: {b_value}")
            
            self.db.conn.commit()
            
            # 验证数据库中的记录
            self.db.cursor.execute('SELECT category, parent_category FROM categories')
            all_categories = self.db.cursor.fetchall()
            logging.info(f"数据库中的分类记录: {all_categories}")
            
            logging.info("分类导入完成")
            messagebox.showinfo("成功", "分类导入成功！")
            
        except Exception as e:
            logging.error(f"导入分类失败: {str(e)}", exc_info=True)
            messagebox.showerror("错误", f"导��失败：{str(e)}")

    def import_archives(self):
        """导入档案"""
        try:
            folder_path = filedialog.askdirectory(
                title="选择档案目录",
                initialdir=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'archives')
            )
            
            if not folder_path:
                return
            
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
            for person_folder in os.listdir(folder_path):
                person_path = os.path.join(folder_path, person_folder)
                if os.path.isdir(person_path):
                    person_name = person_folder  # 文件夹名即为人名
                    
                    # 在数据库中记录人员信息
                    self.db.cursor.execute('''
                        INSERT OR REPLACE INTO persons (name, folder_path)
                        VALUES (?, ?)
                    ''', (person_name, person_path))
                    
                    # 记录该人下的所有文件
                    for root, _, files in os.walk(person_path):
                        for file in files:
                            # 跳过临时文件和隐藏文件
                            if file.startswith('~') or file.startswith('.'):
                                continue
                            
                            file_path = os.path.join(root, file)
                            
                            # 检查文件是否已存在
                            self.db.cursor.execute('''
                                SELECT COUNT(*) FROM person_files 
                                WHERE person_name = ? AND file_name = ? AND file_path = ?
                            ''', (person_name, file, file_path))
                            
                            if self.db.cursor.fetchone()[0] == 0:
                                self.db.cursor.execute('''
                                    INSERT INTO person_files (person_name, file_name, file_path)
                                    VALUES (?, ?, ?)
                                ''', (person_name, file, file_path))
                    
                    imported_count += 1
            
            self.db.conn.commit()
            messagebox.showinfo("成功", f"成功导入 {imported_count} 个人员的档案！")
            
        except Exception as e:
            logging.error(f"导入档案失败: {str(e)}")
            messagebox.showerror("错误", f"导入失败：{str(e)}")

    def search_person(self):
        """搜索人员档案"""
        search_text = self.search_var.get().strip()
        
        try:
            # 清理之前的搜索结果
            self.file_list.delete(*self.file_list.get_children())
            
            # 保存当前搜索的人名
            self.current_search_name = search_text if search_text else None
            
            # 构建查询
            query = '''
                SELECT DISTINCT file_name, file_path 
                FROM person_files 
                WHERE file_name NOT LIKE '~%'
                AND file_name NOT LIKE '.%'
            '''
            params = []
            
            # 如果有搜索文本，添加人名过滤条件
            if search_text:
                query += ' AND person_name LIKE ?'
                params.append(f'%{search_text}%')
            
            query += ' ORDER BY file_name'
            
            # 执行查询
            self.db.cursor.execute(query, params)
            files = self.db.cursor.fetchall()
            self.update_file_list(files)
            
            if search_text:
                logging.info(f"搜索用户 '{search_text}', 找到文件数量: {len(files)}")
            else:
                logging.info(f"显示所有文件, 数量: {len(files)}")
            
        except Exception as e:
            logging.error(f"搜索失败: {str(e)}")
            messagebox.showerror("错误", f"搜索失败：{str(e)}")

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
        
        selected_item = selected_items[0]
        selected_text = self.tree.item(selected_item)['text']
        parent_item = self.tree.parent(selected_item)
        
        try:
            if parent_item:  # 二级分类
                parent_text = self.tree.item(parent_item)['text']
                category_key = (parent_text, selected_text)
                category_code = self.category_mapping.get(category_key)
                
                logging.debug(f"二级分类选择: {parent_text} -> {selected_text}")
                logging.debug(f"二级分类编码: {category_code}")
                
                if category_code:
                    # 构建查询
                    query = '''
                        SELECT DISTINCT file_name, file_path 
                        FROM person_files 
                        WHERE file_name LIKE ? 
                        AND file_name NOT LIKE '~%'
                        AND file_name NOT LIKE '.%'
                    '''
                    params = [f'{category_code}-%']
                    
                    # 如果有搜索条件，添加人名过滤
                    if self.current_search_name:
                        query += ' AND person_name LIKE ?'
                        params.append(f'%{self.current_search_name}%')
                    
                    query += ' ORDER BY file_name'
                    
                    self.db.cursor.execute(query, params)
                    all_files = self.db.cursor.fetchall()
                    
                    # 在 Python 中进行精确匹配过滤
                    files = []
                    for f in all_files:
                        parts = f[0].split('-')
                        if len(parts) >= 2:
                            file_code = f"{parts[0]}-{parts[1]}"
                            if file_code == category_code:
                                files.append(f)
                    
                    self.update_file_list(files)
                    logging.info(f"二级分类查询: {category_code}, 找到文件数量: {len(files)}")
                else:
                    logging.warning(f"未找到分类编码: {category_key}")
            else:  # 一级分类
                category_code = self.category_mapping.get(selected_text)
                
                logging.debug(f"一级分类选择: {selected_text}")
                logging.debug(f"一级分类编码: {category_code}")
                
                if category_code:
                    # 检查是否有子分类
                    self.db.cursor.execute('''
                        SELECT COUNT(*) 
                        FROM categories 
                        WHERE parent_category = ?
                    ''', (selected_text,))
                    
                    has_subcategories = self.db.cursor.fetchone()[0] > 0
                    
                    if has_subcategories:
                        # 如果有子分类，不显示任何文件
                        self.file_list.delete(*self.file_list.get_children())
                        logging.info(f"一级分类有子分类，不显示文件")
                    else:
                        # 构建查询
                        query = '''
                            SELECT DISTINCT file_name, file_path 
                            FROM person_files 
                            WHERE file_name LIKE ? 
                            AND file_name NOT LIKE '~%'
                            AND file_name NOT LIKE '.%'
                        '''
                        params = [f'{category_code}-%']
                        
                        # 如果有搜索条件，添加人名过滤
                        if self.current_search_name:
                            query += ' AND person_name LIKE ?'
                            params.append(f'%{self.current_search_name}%')
                        
                        query += ' ORDER BY file_name'
                        
                        self.db.cursor.execute(query, params)
                        files = self.db.cursor.fetchall()
                        self.update_file_list(files)
                        
                        logging.info(f"一级分类查询: {category_code}, 找到文件数量: {len(files)}")
                
        except Exception as e:
            logging.error(f"分类查询失败: {str(e)}")
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
        file_path = self.file_list.item(item)['values'][4]  # 第5列是路径
        
        try:
            if not os.path.exists(file_path):
                # 尝试使用相对路径
                base_dir = os.path.dirname(os.path.abspath(__file__))
                project_dir = os.path.dirname(os.path.dirname(base_dir))
                abs_path = os.path.join(project_dir, file_path.lstrip('/\\'))
                
                if not os.path.exists(abs_path):
                    messagebox.showerror("错误", f"找不到文件：\n{file_path}")
                    logging.error(f"文件不存在: {file_path}")
                    logging.debug(f"尝试的绝对路径: {abs_path}")
                    return
                file_path = abs_path
            
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
            # 检查分类树是否已存在
            self.db.cursor.execute('SELECT COUNT(*) FROM categories')
            categories_count = self.db.cursor.fetchone()[0]
            
            if categories_count > 0:
                # 如果存在分类数据，直接加载
                self.load_categories_from_db()
                logging.info(f"从数据库加载了 {categories_count} 条分类记录")
            
            # 检查文件记录是否存在
            self.db.cursor.execute('SELECT COUNT(*) FROM person_files')
            files_count = self.db.cursor.fetchone()[0]
            
            if files_count > 0:
                # 如果存在文件记录，直接加载
                self.load_files_from_db()
                logging.info(f"从数据库加载了 {files_count} 条文件记录")
            
        except Exception as e:
            logging.error(f"初始化数据失败: {str(e)}")
            messagebox.showerror("错误", f"初始化数据失败：{str(e)}")

    def load_categories_from_db(self):
        """从数据库加载分类树并构建映射"""
        try:
            # 清空现有树和映射
            self.tree.delete(*self.tree.get_children())
            self.category_mapping = {}
            
            # 先加载一级分类
            self.db.cursor.execute('''
                SELECT category, main_category_num 
                FROM categories 
                WHERE parent_category IS NULL
                ORDER BY main_category_num
            ''')
            
            parent_nodes = {}
            for category, main_num in self.db.cursor.fetchall():
                node_id = self.tree.insert('', 'end', text=category)
                parent_nodes[category] = node_id
                # 添加一级分类映射
                if main_num is not None:
                    self.category_mapping[category] = str(main_num)
                    logging.debug(f"添加一级分类映射: {category} -> {main_num}")
            
            # 再加载二级分类
            self.db.cursor.execute('''
                SELECT c.category, c.parent_category, c.main_category_num, c.sub_category_num
                FROM categories c
                WHERE c.parent_category IS NOT NULL
                ORDER BY c.main_category_num, c.sub_category_num
            ''')
            
            for category, parent_category, main_num, sub_num in self.db.cursor.fetchall():
                if parent_category in parent_nodes:
                    self.tree.insert(parent_nodes[parent_category], 'end', text=category)
                    # 添加二级分类映射
                    if main_num is not None and sub_num is not None:
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
            raise

    def import_files(self):
        """导入文件"""
        try:
            # 选择文件夹
            folder_path = filedialog.askdirectory(title="选择人员档案文件夹")
            if not folder_path:
                return
            
            # 清空现有文件记录
            self.db.cursor.execute('DELETE FROM person_files')
            
<<<<<<< Updated upstream
            # 遍历文件夹
            for root, _, files in os.walk(folder_path):
                person_name = os.path.basename(root)
                for file in files:
                    if file.startswith('.') or file.startswith('~'):
                        continue
=======
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
            # 使用路径管理模块获取配置目录
            from src.utils.paths import get_config_dir
            config_dir = get_config_dir()
                
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
                        # 验证注册码和用户名 - 不再使用硬编码的注册信息
                        logging.info(f"检查注册信息: {reg_code} | {user_name}")
                        # 返回 False，需要手动注册
                        return False
            
            # 如果没有找到有效的注册文件，返回False（未注册）
            logging.info("系统未注册")
            return False
        except Exception as e:
            logging.error(f"检查注册状态失败: {str(e)}")
            # 如果出错，返回false（默认未注册）
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
>>>>>>> Stashed changes
                    
                    file_path = os.path.join(root, file)
                    # 存储相对路径
                    rel_path = os.path.relpath(file_path, os.path.dirname(folder_path))
                    
                    self.db.cursor.execute('''
                        INSERT INTO person_files (person_name, file_name, file_path)
                        VALUES (?, ?, ?)
                    ''', (person_name, file, rel_path))
            
            self.db.conn.commit()
            messagebox.showinfo("成功", "文件导入成功")
            
            # 刷新文件列表
            self.search_person()
            
        except Exception as e:
            self.db.conn.rollback()
            logging.error(f"导入文件失败: {str(e)}")
            messagebox.showerror("错误", f"导入文件失败：{str(e)}")
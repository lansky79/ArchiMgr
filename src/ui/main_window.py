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
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tools_menu)
        tools_menu.add_command(label="清理数据库", command=self.cleanup_database)
        
    def create_toolbar(self):
        """创建工具栏"""
        toolbar_frame = ttk.Frame(self.root)
        toolbar_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 左侧按钮框架
        button_frame = ttk.Frame(toolbar_frame)
        button_frame.pack(side=tk.LEFT, padx=(0, 10))
        
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
        
        # 创建右侧框架（用于文件列表）
        self.right_frame = ttk.Frame(paned)
        paned.add(self.right_frame, weight=3)
        
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

    # 事件处理方法
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
            
            # 遍历文件夹
            for root, _, files in os.walk(folder_path):
                person_name = os.path.basename(root)
                for file in files:
                    if file.startswith('.') or file.startswith('~'):
                        continue
                    
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
import sqlite3
import logging
import os
import sys

class Database:
    def __init__(self):
        if getattr(sys, 'frozen', False):
            # PyInstaller 打包后的路径
            application_path = os.path.dirname(sys.executable)
        else:
            # 开发环境路径
            application_path = os.path.dirname(os.path.abspath(__file__))
            
        # 确保数据库目录存在
        db_dir = os.path.join(application_path, 'database')
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
            
        self.db_file = os.path.join(db_dir, 'archimgr.db')
        self.conn = None
        self.cursor = None
        
    def connect(self):
        try:
            # 连接数据库
            self.conn = sqlite3.connect(self.db_file)
            self.cursor = self.conn.cursor()
            
            # 创建表
            self._create_tables()
            
            logging.info(f"数据库连接成功: {self.db_file}")
        except Exception as e:
            logging.error(f"数据库连接失败: {e}")
            raise
    
    def _create_tables(self):
        """创建数据库表"""
        try:
            # 分类表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    parent_category TEXT,
                    main_category_num INTEGER,  -- 主分类号（第一级）
                    sub_category_num INTEGER,   -- 子分类号（第二级）
                    UNIQUE(category, parent_category)
                )
            ''')
            
            # 人员表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS persons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    folder_path TEXT NOT NULL
                )
            ''')
            
            # 人员文件表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS person_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    person_name TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    category_id INTEGER,
                    FOREIGN KEY (person_name) REFERENCES persons(name),
                    FOREIGN KEY (category_id) REFERENCES categories(id)
                )
            ''')
            
            # 文件表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    category TEXT NOT NULL,
                    main_category_num INTEGER,  -- 主分类号
                    sub_category_num INTEGER,   -- 子分类号
                    import_time DATETIME NOT NULL,
                    notes TEXT
                )
            ''')
            
            self.conn.commit()
            logging.info("数据库表创建成功")
        except Exception as e:
            logging.error(f"创建数据库表失败: {e}")
            raise
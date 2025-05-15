import sqlite3
import logging
import os
import sys

class Database:
    def __init__(self):
        """初始化数据库连接"""
        # 使用路径管理模块获取数据库路径
        from src.utils.paths import get_database_path
        self.db_path = get_database_path()
        
        # 确保数据库目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # 建立数据库连接
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            
            # 创建必要的表
            self._create_tables()
            
            # 执行数据库迁移，添加新列
            self._migrate_database()
            
            logging.info(f"数据库连接成功: {self.db_path}")
        except Exception as e:
            logging.error(f"数据库连接失败: {str(e)}", exc_info=True)
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
                    dir_name TEXT,    -- 目录名称（包含编号和姓名）
                    file_id TEXT,     -- 编号
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
            
    def _migrate_database(self):
        """数据库迁移，添加新列"""
        try:
            # 检查person_files表中是否有dir_name列
            self.cursor.execute("PRAGMA table_info(person_files)")
            columns = [column[1] for column in self.cursor.fetchall()]
            
            # 添加dir_name列
            if 'dir_name' not in columns:
                logging.info("添加dir_name列到person_files表")
                self.cursor.execute("ALTER TABLE person_files ADD COLUMN dir_name TEXT")
                
                # 更新现有数据的dir_name列
                self.cursor.execute('''
                    UPDATE person_files
                    SET dir_name = person_name
                    WHERE dir_name IS NULL
                ''')
            
            # 添加file_id列
            if 'file_id' not in columns:
                logging.info("添加file_id列到person_files表")
                self.cursor.execute("ALTER TABLE person_files ADD COLUMN file_id TEXT")
                
                # 更新现有数据的file_id列，尝试从目录名中提取编号
                self.cursor.execute('''
                    SELECT id, person_name FROM person_files WHERE file_id IS NULL
                ''')
                rows = self.cursor.fetchall()
                
                import re
                for row_id, person_name in rows:
                    # 尝试从人名中提取编号
                    match = re.match(r'^(\d+)(.*)', person_name)
                    if match:
                        file_id = match.group(1)
                        self.cursor.execute('''
                            UPDATE person_files
                            SET file_id = ?
                            WHERE id = ?
                        ''', (file_id, row_id))
            
            self.conn.commit()
            logging.info("数据库迁移成功")
        except Exception as e:
            self.conn.rollback()
            logging.error(f"数据库迁移失败: {str(e)}")
            # 不抛出异常，允许程序继续运行
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
    
    def get_connection(self):
        """获取数据库连接对象
        
        返回:
            sqlite3.Connection: 数据库连接对象
        """
        return self.conn
    
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
            
            # 操作日志表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS operation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,      -- 操作用户
                    operation_type TEXT NOT NULL, -- 操作类型: login, search, print, view
                    target_id TEXT,              -- 目标ID（如档案编号）
                    target_name TEXT,            -- 目标名称（如档案名称、人员姓名）
                    details TEXT,                -- 操作详情
                    operation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- 操作时间
                    ip_address TEXT,             -- IP地址
                    FOREIGN KEY (username) REFERENCES users(username)
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
    
    def add_log(self, username, operation_type, target_id=None, target_name=None, details=None, ip_address=None):
        """添加操作日志
        
        参数:
            username (str): 操作用户名
            operation_type (str): 操作类型 (login, search, print, view)
            target_id (str, optional): 目标ID，如档案编号
            target_name (str, optional): 目标名称，如档案名称、人员姓名
            details (str, optional): 操作详情
            ip_address (str, optional): IP地址
        """
        try:
            self.cursor.execute('''
                INSERT INTO operation_logs 
                (username, operation_type, target_id, target_name, details, ip_address)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, operation_type, target_id, target_name, details, ip_address))
            self.conn.commit()
            logging.info(f"记录操作日志: 用户={username}, 操作={operation_type}, 目标={target_name}")
            return True
        except Exception as e:
            self.conn.rollback()
            logging.error(f"记录操作日志失败: {str(e)}")
            return False
    
    def get_logs(self, username=None, operation_type=None, start_date=None, end_date=None, limit=1000):
        """获取操作日志
        
        参数:
            username (str, optional): 按用户名筛选
            operation_type (str, optional): 按操作类型筛选
            start_date (str, optional): 开始日期，格式 YYYY-MM-DD
            end_date (str, optional): 结束日期，格式 YYYY-MM-DD
            limit (int, optional): 限制返回记录数，默认1000条
            
        返回:
            list: 日志记录列表
        """
        query = "SELECT * FROM operation_logs WHERE 1=1"
        params = []
        
        if username:
            query += " AND username = ?"
            params.append(username)
        
        if operation_type:
            query += " AND operation_type = ?"
            params.append(operation_type)
        
        if start_date:
            query += " AND date(operation_time) >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND date(operation_time) <= ?"
            params.append(end_date)
        
        query += " ORDER BY operation_time DESC LIMIT ?"
        params.append(limit)
        
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except Exception as e:
            logging.error(f"获取操作日志失败: {str(e)}")
            return []
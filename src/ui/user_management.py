import logging
import hashlib
import os
from tkinter import messagebox

from utils.pinyin_util import get_pinyin  # 导入拼音工具，用于用户名验证

class UserManager:
    """用户管理类，包含所有用户管理相关的功能"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.db = main_window.db
    
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
            
            # 验证用户名是否符合拼音规则（必须是真实姓名的小写拼音）
            expected_pinyin = get_pinyin(real_name).lower()
            if username != expected_pinyin:
                return False, f"用户名必须是真实姓名的小写拼音，应为: {expected_pinyin}"
            
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
    
    def logout(self):
        """退出登录"""
        self.main_window.current_user = None
        self.main_window.login_status_var.set("未登录")
        
        # 更新菜单
        self.main_window.update_menu_by_role(None)
        
        # 禁用工具栏
        self.main_window.update_tools_permission(False)
        
        logging.info("用户已退出登录")
    
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
    
    def register_system(self, reg_code, user_name):
        """注册系统"""
        try:
            # 验证注册码
            if reg_code != "2xdqzr5zyghj" or user_name != "新都区自然资源规划局":
                return False, "注册码或单位名称错误"
                
            # 保存注册信息
            config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'config')
            os.makedirs(config_dir, exist_ok=True)
            
            registration_file = os.path.join(config_dir, 'registration.dat')
            
            # 简单加密处理
            content = f"{reg_code}|{user_name}"
            encoded_content = ''.join([chr(ord(c) + 1) for c in content])
            
            with open(registration_file, 'w', encoding='utf-8') as f:
                f.write(encoded_content)
                
            logging.info(f"系统注册成功: {user_name}")
            return True, "系统注册成功！"
        except Exception as e:
            logging.error(f"注册系统失败: {str(e)}")
            return False, f"注册失败: {str(e)}"
    
    def update_ui_by_registration(self):
        """根据注册状态更新界面"""
        try:
            # 获取窗口标题控件
            title = self.main_window.root.title()
            
            # 根据注册状态更新标题
            if self.main_window.is_registered:
                # 已注册版本
                if not title.endswith("【已注册】"):
                    self.main_window.root.title(f"{title} 【已注册】")
                
                # 启用所有功能
                if hasattr(self.main_window, 'import_file_btn'):
                    self.main_window.import_file_btn.config(state='normal')
                
                # 隐藏注册选项
                if hasattr(self.main_window, 'help_menu'):
                    try:
                        self.main_window.help_menu.delete("用户注册")
                    except:
                        pass
            else:
                # 未注册版本
                if "【已注册】" in title:
                    self.main_window.root.title(title.replace(" 【已注册】", ""))
                
                # 添加水印或其他未注册标识
                # 这里可以添加水印代码
                
                # 显示注册选项
                if hasattr(self.main_window, 'help_menu'):
                    try:
                        # 检查是否已有注册选项
                        has_reg_option = False
                        for i in range(self.main_window.help_menu.index('end') + 1):
                            if self.main_window.help_menu.entrycget(i, 'label') == "用户注册":
                                has_reg_option = True
                                break
                        
                        if not has_reg_option:
                            # 添加注册选项
                            self.main_window.help_menu.add_command(
                                label="用户注册", 
                                command=self.main_window.show_registration_dialog
                            )
                    except:
                        pass
                
            logging.info(f"界面已根据注册状态更新: {'已注册' if self.main_window.is_registered else '未注册'}")
        except Exception as e:
            logging.error(f"更新界面失败: {str(e)}")
    
    def cleanup_database(self):
        """清理数据库中的重复记录和无效记录"""
        # 检查权限
        if not self.main_window.current_user or self.main_window.current_user[3] != 'admin':
            messagebox.showerror("权限错误", "只有管理员可以清理数据库")
            return
            
        try:
            # 删除重复记录
            self.db.cursor.execute('''
                DELETE FROM person_files
                WHERE rowid NOT IN (
                    SELECT MIN(rowid)
                    FROM person_files
                    GROUP BY file_path
                )
            ''')
            
            # 删除不存在的文件记录
            self.db.cursor.execute('SELECT file_path FROM person_files')
            for (file_path,) in self.db.cursor.fetchall():
                if not os.path.exists(file_path):
                    self.db.cursor.execute('DELETE FROM person_files WHERE file_path = ?', (file_path,))
            
            self.db.conn.commit()
            messagebox.showinfo("成功", "数据库清理完成！")
            
            # 重新加载文件列表
            self.main_window.load_files_from_db()
        except Exception as e:
            logging.error(f"清理数据库失败: {str(e)}")
            messagebox.showerror("错误", f"清理数据库失败: {str(e)}")

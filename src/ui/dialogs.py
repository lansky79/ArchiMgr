import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import logging
import os
import json
import hashlib

class DialogManager:
    """对话框管理类，包含所有对话框相关的功能"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.root = main_window.root
        self.db = main_window.db
    
    def show_login_dialog(self):
        """显示登录对话框"""
        logging.debug("显示登录对话框")
        
        # 如果已经登录，显示信息并提供退出选项
        if self.main_window.current_user:
            result = messagebox.askyesno("已登录", 
                                        f"当前已经以 {self.main_window.current_user[2]} 身份登录。\n\n是否要退出登录？")
            if result:
                self.main_window.logout()
            return
        
        # 创建登录对话框
        login_dialog = tk.Toplevel(self.root)
        login_dialog.title("用户登录")
        login_dialog.geometry("300x180")  # 增加对话框尺寸
        login_dialog.resizable(False, False)
        login_dialog.transient(self.root)
        login_dialog.grab_set()
        
        # 表单框架
        form_frame = ttk.Frame(login_dialog, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # 用户名
        ttk.Label(form_frame, text="用户名:").grid(row=0, column=0, sticky=tk.W, pady=5)
        username_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=username_var, width=20).grid(row=0, column=1, pady=5)
        
        # 密码
        ttk.Label(form_frame, text="密码:").grid(row=1, column=0, sticky=tk.W, pady=5)
        password_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=password_var, show="*", width=20).grid(row=1, column=1, pady=5)
        
        # 错误信息
        error_var = tk.StringVar()
        error_label = ttk.Label(form_frame, textvariable=error_var, foreground="red")
        error_label.grid(row=2, column=0, columnspan=2, pady=5)
        
        # 登录按钮
        def do_login():
            username = username_var.get().strip()
            password = password_var.get()
            
            if not username or not password:
                error_var.set("用户名和密码不能为空")
                return
            
            # 验证登录
            success, user = self.main_window.validate_login(username, password)
            if success:
                self.main_window.current_user = user
                self.main_window.login_status_var.set(f"当前用户: {user[2]}")
                
                # 更新菜单
                self.main_window.update_menu_by_role(user[3])
                
                # 关闭对话框
                login_dialog.destroy()
                
                # 登录成功后，启用搜索按钮和导入文件按钮
                self.main_window.update_tools_permission(user[3] == 'admin')
                
                logging.info(f"用户 {username} 登录成功")
            else:
                error_var.set("用户名或密码错误")
                logging.warning(f"用户 {username} 登录失败")
        
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
    
    def show_register_dialog(self):
        """显示用户注册对话框（仅管理员可用）"""
        logging.debug("显示注册对话框")
        
        # 检查权限
        if not self.main_window.current_user or self.main_window.current_user[3] != 'admin':
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
            success, message = self.main_window.register_user(username, password, real_name)
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
    
    def show_change_password_dialog(self):
        """显示修改密码对话框"""
        # 检查权限
        if not self.main_window.current_user or self.main_window.current_user[3] != 'admin':
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
            success, _ = self.main_window.validate_login(self.main_window.current_user[1], old_password)
            if not success:
                error_var.set("当前密码错误")
                return
                
            # 修改密码
            try:
                hashed_password = self.main_window.hash_password(new_password)
                self.db.cursor.execute(
                    'UPDATE users SET password = ? WHERE id = ?',
                    (hashed_password, self.main_window.current_user[0])
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
    
    def show_registration_dialog(self):
        """显示系统注册对话框"""
        # 创建注册对话框
        registration_dialog = tk.Toplevel(self.root)
        registration_dialog.title("系统注册")
        registration_dialog.geometry("400x250")
        registration_dialog.resizable(False, False)
        registration_dialog.transient(self.root)
        registration_dialog.grab_set()
        
        # 表单框架
        form_frame = ttk.Frame(registration_dialog, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # 注册码
        ttk.Label(form_frame, text="注册码:").grid(row=0, column=0, sticky=tk.W, pady=5)
        reg_code_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=reg_code_var, width=30).grid(row=0, column=1, pady=5)
        
        # 用户名
        ttk.Label(form_frame, text="单位名称:").grid(row=1, column=0, sticky=tk.W, pady=5)
        user_name_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=user_name_var, width=30).grid(row=1, column=1, pady=5)
        
        # 错误信息
        error_var = tk.StringVar()
        error_label = ttk.Label(form_frame, textvariable=error_var, foreground="red")
        error_label.grid(row=2, column=0, columnspan=2, pady=5)
        
        # 注册按钮
        def do_register():
            reg_code = reg_code_var.get().strip()
            user_name = user_name_var.get().strip()
            
            # 验证表单
            if not reg_code:
                error_var.set("注册码不能为空")
                return
            
            if not user_name:
                error_var.set("单位名称不能为空")
                return
            
            # 注册系统
            success, message = self.main_window.register_system(reg_code, user_name)
            if success:
                messagebox.showinfo("注册成功", message)
                # 更新UI
                self.main_window.is_registered = True
                self.main_window.update_ui_by_registration()
                registration_dialog.destroy()
            else:
                error_var.set(message)
        
        # 创建一个按钮框架
        buttons_frame = ttk.Frame(form_frame)
        buttons_frame.grid(row=3, column=0, columnspan=2, pady=15)
        
        # 添加更大的按钮
        ttk.Button(buttons_frame, text="注册", command=do_register, width=15).pack(side=tk.LEFT, padx=15)
        ttk.Button(buttons_frame, text="取消", command=registration_dialog.destroy, width=15).pack(side=tk.LEFT, padx=15)
        
        # 居中对话框
        registration_dialog.update_idletasks()
        width = registration_dialog.winfo_width()
        height = registration_dialog.winfo_height()
        x = (registration_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (registration_dialog.winfo_screenheight() // 2) - (height // 2)
        registration_dialog.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        registration_dialog.wait_window()
    
    def show_help(self):
        """显示帮助信息"""
        help_text = """
        档案检索系统使用说明
        
        1. 登录系统
           - 使用管理员账号（admin/admin123）或已注册的用户账号登录
           
        2. 导入档案
           - 点击"导入文件"按钮，选择包含PDF档案的目录
           - 系统将自动扫描目录中的PDF文件并导入
           
        3. 搜索档案
           - 在搜索框中输入姓名或编号进行搜索
           - 可以通过左侧分类树筛选特定类别的档案
           
        4. 查看档案
           - 双击文件列表中的档案可以打开查看
           
        5. 管理功能（仅管理员）
           - 添加用户：文件菜单 -> 添加用户
           - 清理数据库：工具菜单 -> 清理数据库
        """
        messagebox.showinfo("使用说明", help_text)
    
    def show_about(self):
        """显示关于信息"""
        about_text = f"""
        档案检索系统
        
        版本: {self.main_window.version}
        
        本系统用于管理和检索电子档案，提供简便的导入、搜索和查看功能。
        
        技术支持: 
        电话: 028-12345678
        邮箱: support@example.com
        """
        messagebox.showinfo("关于", about_text)

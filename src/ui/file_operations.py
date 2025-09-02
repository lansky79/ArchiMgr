import os
import logging
import re
import shutil
import subprocess
from tkinter import filedialog, messagebox
import pandas as pd

from src.utils.excel_utils import get_excel_info, ExcelFileNotFound

class FileOperationManager:
    """文件操作管理类，包含所有文件操作相关的功能"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.root = main_window.root
        self.db = main_window.db
        self.import_root_dir = main_window.import_root_dir
    
    def import_files(self):
        """导入文件"""
        # 检查是否已登录
        if not self.main_window.current_user:
            messagebox.showwarning("警告", "请先登录")
            return
            
        # 选择导入目录
        import_dir = filedialog.askdirectory(title="选择导入目录")
        if not import_dir:
            return
            
        # 更新导入根目录
        self.main_window.import_root_dir = import_dir
        self.import_root_dir = import_dir
        
        # 更新主窗口标题
        if hasattr(self.main_window, 'update_window_title'):
            self.main_window.update_window_title()
            
        # 保存设置
        self.main_window.save_settings()
        
        # 扫描目录下的所有PDF文件
        all_files = []
        for root, _, files in os.walk(import_dir):
            for file in files:
                if file.lower().endswith('.pdf'):
                    file_path = os.path.join(root, file)
                    all_files.append((file, file_path))
        
        if not all_files:
            messagebox.showinfo("提示", "未找到PDF文件")
            return
            
        # 更新文件列表
        self.main_window.update_file_list(all_files)
        
        # 显示导入结果
        messagebox.showinfo("导入成功", f"成功导入 {len(all_files)} 个文件")
    
    def import_archives(self):
        """导入档案"""
        # 检查是否已登录
        if not self.main_window.current_user:
            messagebox.showwarning("警告", "请先登录")
            return
            
        # 选择导入目录
        import_dir = filedialog.askdirectory(title="选择导入目录")
        if not import_dir:
            return
            
        # 更新导入根目录
        self.main_window.import_root_dir = import_dir
        self.import_root_dir = import_dir
        
        # 更新主窗口标题
        if hasattr(self.main_window, 'update_window_title'):
            self.main_window.update_window_title()
            
        # 保存设置
        self.main_window.save_settings()
        
        # 扫描目录下的所有子目录（每个子目录代表一个人的档案）
        all_files = []
        person_count = 0
        file_count = 0
        
        for person_dir in os.listdir(import_dir):
            person_path = os.path.join(import_dir, person_dir)
            if os.path.isdir(person_path):
                person_count += 1
                # 扫描该人档案下的所有PDF文件
                for root, _, files in os.walk(person_path):
                    for file in files:
                        if file.lower().endswith('.pdf'):
                            file_path = os.path.join(root, file)
                            all_files.append((file, file_path))
                            file_count += 1
        
        if not all_files:
            messagebox.showinfo("提示", "未找到PDF文件")
            return
            
        # 更新文件列表
        self.main_window.update_file_list(all_files)
        
        # 显示导入结果
        messagebox.showinfo("导入成功", f"成功导入 {person_count} 人的 {file_count} 个档案文件")
    
    def update_file_list(self, files):
        """更新文件列表"""
        # 清空现有列表
        self.main_window.file_list.delete(*self.main_window.file_list.get_children())
        
        # 更新状态栏显示文件数量
        if hasattr(self.main_window, 'search_result_var'):
            self.main_window.search_result_var.set(f"搜索结果: {len(files)} 个文件")
        
        logging.debug(f"要更新的文件列表数量: {len(files)}")
        if files:
            sample_files = files[:3]
            logging.debug(f"文件样本: {sample_files}")
        
        try:
            # 筛选只显示PDF文件
            pdf_files = []
            for file_name, file_path in files:
                # 确保文件路径在'目录'子目录下
                if '目录' not in file_path.replace('\\', '/'):
                    continue
                    
                # 将文件名转为小写进行判断
                if file_name.lower().endswith('.pdf'):
                    pdf_files.append((file_name, file_path))
                    
            logging.debug(f"筛选后的PDF文件数量: {len(pdf_files)}")
            
            # 插入新的文件记录
            for file_name, file_path in pdf_files:
                # 从文件路径中提取人名和文件夹名
                dir_name = os.path.basename(os.path.dirname(os.path.dirname(file_path)))
                
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
                    material_name, file_date, page_count, data_list = get_excel_info(self.import_root_dir, person_name, file_id, class_code)
                    # 处理 data_list
                    if data_list:
                        logging.debug(f"处理文件: {file_name}, 类号: {class_code}, 编号: {file_id}, 人名: {person_name}, 目录名: {dir_name}, 数据列表: {data_list}")
                except ExcelFileNotFound as e:
                    logging.warning(str(e))
                    material_name, file_date, page_count = '', '', ''
                    messagebox.showwarning("未找到Excel文件", str(e))
                except Exception as e:
                    logging.error(f"Excel信息读取失败: {str(e)}")
                    material_name, file_date, page_count = '', '', ''
                    messagebox.showerror("Excel读取错误", f"读取Excel信息时发生错误：{str(e)}")
                
                # 插入到列表
                self.main_window.file_list.insert('', 'end', values=(
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
    
    def on_file_double_click(self, event):
        """处理文件双击事件"""
        # 获取选中的文件
        selected_item = self.main_window.file_list.selection()
        if not selected_item:
            return
            
        # 获取文件路径
        file_path = self.main_window.file_list.item(selected_item)['values'][-1]
        if not file_path or not os.path.exists(file_path):
            messagebox.showerror("错误", "文件不存在")
            return
            
        # 使用系统默认程序打开文件
        try:
            if os.name == 'nt':  # Windows
                os.startfile(file_path)
            elif os.name == 'posix':  # macOS, Linux
                subprocess.call(('xdg-open', file_path))
            logging.info(f"打开文件: {file_path}")
        except Exception as e:
            logging.error(f"打开文件失败: {str(e)}")
            messagebox.showerror("错误", f"打开文件失败: {str(e)}")
    
    def search_person(self):
        """搜索人员档案
        
        搜索规则：
        1. 只在'目录'子目录下搜索Excel文件
        2. 文件名必须完全匹配"编号+姓名.xlsx"
        3. 如果未找到匹配文件，只显示一次提示
        """
        # 检查是否已登录
        if not self.main_window.current_user:
            messagebox.showwarning("警告", "请先登录")
            return
            
        # 获取搜索条件
        search_name = self.main_window.search_name_var.get().strip()
        search_id = self.main_window.search_id_var.get().strip()
        
        logging.info(f"执行搜索：姓名='{search_name}', 编号='{search_id}'")
        
        # 确保至少提供了一个搜索条件
        if not search_id and not search_name:
            error_msg = "请输入编号或姓名进行搜索"
            logging.warning(error_msg)
            if hasattr(self.main_window, 'status_bar'):
                self.main_window.status_bar.show_message(error_msg, "warning")
            return
            
        # 记录搜索条件
        self.main_window.current_search_name = search_name
        self.main_window.current_search_id = search_id
        self.main_window.has_searched = True
        
        # 如果没有设置导入目录，提示用户
        if not self.main_window.import_root_dir:
            error_msg = "请先使用'导入档案'功能导入档案文件"
            logging.warning(error_msg)
            if hasattr(self.main_window, 'status_bar'):
                self.main_window.status_bar.show_message(error_msg, "warning")
            messagebox.showinfo("提示", error_msg)
            return
            
        # 如果搜索条件为空，提示用户
        if not search_name and not search_id:
            messagebox.showwarning("警告", "请输入姓名或编号")
            return
            
        logging.info(f"开始搜索: 姓名='{search_name}', 编号='{search_id}'")
        
        # 清空当前列表
        self.main_window.file_list.delete(*self.main_window.file_list.get_children())

        # 构建'目录'子目录路径
        import_root_dir = self.main_window.import_root_dir
        catalog_dir = os.path.join(import_root_dir, '目录')
        
        # 确保'目录'文件夹存在
        if not os.path.exists(catalog_dir):
            error_msg = f"目录不存在: {catalog_dir}"
            logging.error(error_msg)
            messagebox.showerror("错误", "未找到'目录'文件夹，请确保文件结构正确")
            if hasattr(self.main_window, 'status_bar'):
                self.main_window.status_bar.show_message("错误: 未找到'目录'文件夹", "error")
            return

        logging.info(f"在目录中搜索: {catalog_dir}")
        
        # 构建预期的Excel文件名
        expected_name = f"{search_id}{search_name}"
        expected_filename = f"{expected_name}.xlsx"
        expected_path = os.path.join(catalog_dir, expected_filename)
        
        # 检查文件是否存在
        if not os.path.exists(expected_path):
            error_msg = f"未找到匹配的Excel文件: {expected_filename}"
            logging.warning(error_msg)
            if hasattr(self.main_window, 'status_bar'):
                self.main_window.status_bar.show_message(error_msg, "warning")
            messagebox.showinfo("提示", error_msg)
            return
            
        # 如果找到了匹配的文件，显示文件信息
        logging.info(f"找到匹配的Excel文件: {expected_path}")
        
        # 获取Excel文件中的所有工作表信息
        try:
            # 使用pandas读取Excel文件
            excel_file = pd.ExcelFile(expected_path, engine='openpyxl')
            sheet_names = excel_file.sheet_names
            
            # 处理每个工作表
            for sheet_name in sheet_names:
                try:
                    # 读取工作表数据
                    df = pd.read_excel(excel_file, sheet_name=sheet_name, engine='openpyxl', header=0)
                    
                    # 将数据添加到文件列表
                    for _, row in df.iterrows():
                        # 获取材料名称、日期和页数
                        material_name = str(row.get('材料名称', '')) if pd.notna(row.get('材料名称')) else ''
                        file_date = str(row.get('日期', '')) if pd.notna(row.get('日期')) else ''
                        page_count = str(int(row.get('页数', ''))) if pd.notna(row.get('页数')) else ''
                        
                        # 插入到列表
                        self.main_window.file_list.insert('', 'end', values=(
                            search_id,
                            search_name,
                            sheet_name,  # 使用工作表名作为类号
                            material_name,
                            expected_filename,  # 显示Excel文件名
                            file_date,
                            page_count,
                            expected_path  # 文件路径
                        ))
                        
                except Exception as e:
                    logging.error(f"处理工作表 {sheet_name} 时出错: {str(e)}")
                    continue
                    
        except Exception as e:
            error_msg = f"读取Excel文件时出错: {str(e)}"
            logging.error(error_msg, exc_info=True)
            messagebox.showerror("错误", error_msg)
            return
            
        # 更新状态栏
        if hasattr(self.main_window, 'status_bar'):
            item_count = len(self.main_window.file_list.get_children())
            if item_count > 0:
                self.main_window.status_bar.show_message(f"找到 {item_count} 条记录", "info")
            else:
                self.main_window.status_bar.show_message("未找到匹配的记录", "warning")
    
    def extract_category_num(self, filename):
        """从文件名中提取分类号"""
        # 去掉扩展名
        name = os.path.splitext(filename)[0]
        
        # 分类号通常是数字或数字-数字的格式
        match = re.match(r'^(\d+(-\d+)?)', name)
        if match:
            return match.group(1)
        return None
    
    def open_install_directory(self):
        """打开程序安装目录"""
        install_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self._open_directory(install_dir)
    
    def open_archive_directory(self):
        """打开档案文件目录"""
        # 如果没有设置导入目录，则使用默认目录
        if not self.main_window.import_root_dir or not os.path.exists(self.main_window.import_root_dir):
            # 使用用户主目录作为默认目录
            default_dir = os.path.expanduser('~')
            # 让用户选择目录
            selected_dir = filedialog.askdirectory(
                title="选择档案文件目录",
                initialdir=default_dir
            )
            if not selected_dir:  # 用户取消了选择
                return
            # 更新导入目录
            self.main_window.import_root_dir = selected_dir
            self.import_root_dir = selected_dir
            # 保存设置
            self.main_window.save_settings()
        
        # 打开目录
        self._open_directory(self.main_window.import_root_dir)
    
    def open_database_location(self):
        """打开数据库位置"""
        if not self.db or not hasattr(self.db, 'db_path'):
            messagebox.showwarning("警告", "数据库未初始化")
            return
        db_dir = os.path.dirname(self.db.db_path)
        self._open_directory(db_dir)
    
    def _open_directory(self, directory):
        """打开指定目录"""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(directory)
            elif os.name == 'posix':  # macOS, Linux
                subprocess.call(('xdg-open', directory))
            logging.info(f"打开目录: {directory}")
        except Exception as e:
            logging.error(f"打开目录失败: {str(e)}")
            messagebox.showerror("错误", f"打开目录失败: {str(e)}")

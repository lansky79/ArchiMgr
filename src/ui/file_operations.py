import os
import logging
import re
import shutil
import subprocess
from tkinter import filedialog, messagebox
import pandas as pd

from utils.excel_utils import get_excel_info, ExcelFileNotFound

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
        """搜索人员档案（支持分类过滤）
        
        搜索规则：
        1. 如果只输入姓名，搜索所有匹配的姓名
        2. 如果只输入编号，搜索所有匹配的编号
        3. 如果同时输入姓名和编号，进行精确匹配
        4. 如果姓名匹配到多条记录，要求用户输入编号进行精确匹配
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
            messagebox.showwarning("警告", "请先导入文件或档案")
            return
            
        # 如果搜索条件为空，提示用户
        if not search_name and not search_id:
            messagebox.showwarning("警告", "请输入姓名或编号")
            return
            
        logging.info(f"开始搜索: 姓名='{search_name}', 编号='{search_id}'")
        
        # 清空当前列表
        self.main_window.file_list.delete(*self.main_window.file_list.get_children())

        # 在导入目录中搜索
        import_root_dir = self.main_window.import_root_dir
        if not import_root_dir or not os.path.exists(import_root_dir):
            error_msg = f"导入目录不存在: {import_root_dir}"
            logging.error(error_msg)
            messagebox.showerror("错误", "请先设置有效的导入目录")
            self.main_window.status_bar.show_message("错误: 请先设置导入目录", "error")
            return

        logging.info(f"在目录中搜索: {import_root_dir}")
        
        # 获取所有Excel文件
        all_excel_files = []
        try:
            for root, dirs, files in os.walk(import_root_dir):
                all_excel_files.extend(
                    os.path.join(root, f) for f in files 
                    if f.lower().endswith('.xlsx') and not f.startswith('~')
                )
            logging.info(f"找到 {len(all_excel_files)} 个Excel文件")
        except Exception as e:
            error_msg = f"遍历目录时出错: {str(e)}"
            logging.error(error_msg)
            messagebox.showerror("错误", error_msg)
            self.main_window.status_bar.show_message("搜索出错", "error")
            return

        # 搜索匹配的文件
        matched_files = []
        search_name_lower = search_name.lower() if search_name else ""
        search_id_lower = search_id.lower() if search_id else ""
        
        # 获取所有Excel文件的基本信息
        excel_files = []
        for file_path in all_excel_files:
            try:
                file_name = os.path.basename(file_path)
                file_name_without_ext = os.path.splitext(file_name)[0]
                excel_files.append({
                    'path': file_path,
                    'name': file_name,
                    'name_without_ext': file_name_without_ext,
                    'name_lower': file_name_without_ext.lower()
                })
            except Exception as e:
                logging.error(f"处理文件 {file_path} 时出错: {e}")
        
        # 1. 如果同时提供了编号和姓名
        if search_id and search_name:
            # 构建预期的文件名（不包含扩展名）
            expected_name = f"{search_id}{search_name}"
            expected_name_lower = expected_name.lower()
            
            # 检查是否有完全匹配的记录
            for file_info in excel_files:
                # 检查文件名是否完全匹配（不区分大小写）
                if file_info['name_lower'] == expected_name_lower:
                    matched_files = [file_info['path']]  # 清空之前的匹配，只保留完全匹配
                    logging.info(f"完全匹配: {file_info['path']}")
                    break
            else:
                # 如果没有完全匹配的记录，显示警告
                error_msg = f"未找到完全匹配的记录: {search_id}{search_name}.xlsx"
                logging.warning(error_msg)
                if hasattr(self.main_window, 'status_bar'):
                    self.main_window.status_bar.show_message(error_msg, "warning")
                return
                
        # 2. 如果只提供了编号
        elif search_id:
            for file_info in excel_files:
                # 检查文件名是否完全匹配编号（不区分大小写）
                if file_info['name_lower'] == search_id_lower:
                    matched_files = [file_info['path']]  # 清空之前的匹配，只保留完全匹配
                    logging.info(f"编号完全匹配: {file_info['path']}")
                    break
            else:
                # 如果没有完全匹配的记录，显示警告
                error_msg = f"未找到编号为 '{search_id}' 的记录"
                logging.warning(error_msg)
                if hasattr(self.main_window, 'status_bar'):
                    self.main_window.status_bar.show_message(error_msg, "warning")
                return
                
        # 3. 如果只提供了姓名
        elif search_name:
            logging.info(f"开始姓名搜索: {search_name}")
            # 获取当前选中的分类
            selected_category = None
            if hasattr(self.main_window, 'category_tree'):
                selection = self.main_window.category_tree.selection()
                if selection:
                    selected_category = self.main_window.category_tree.item(selection[0])['text']
            
            # 搜索匹配的文件
            matched_files = []
            for file_path in all_excel_files:
                file_name = os.path.splitext(os.path.basename(file_path))[0].lower()
                if search_name_lower in file_name:
                    # 如果选择了分类，检查文件是否在选中的分类目录下
                    if selected_category:
                        file_dir = os.path.dirname(file_path)
                        parent_dir = os.path.dirname(file_dir)
                        if os.path.basename(parent_dir) == selected_category:
                            matched_files.append(file_path)
                    else:
                        matched_files.append(file_path)
            
            logging.info(f"找到 {len(matched_files)} 个姓名匹配项")
        
        # 检查文件对应关系
        logging.info(f"最终匹配文件列表: {matched_files}")
        if matched_files:
            # 获取所有匹配的文件名（不包含扩展名）
            excel_names = [os.path.splitext(os.path.basename(f))[0] for f in matched_files]
            
            # 检查是否需要完全匹配
            if search_id and search_name:
                expected_name = f"{search_id}{search_name}"
                exact_matches = [file_path for name, file_path in zip(excel_names, matched_files) 
                               if name == expected_name]
                
                if not exact_matches:
                    error_msg = f"未找到完全匹配的文件: {expected_name}.xlsx"
                    logging.warning(error_msg)
                    if hasattr(self.main_window, 'status_bar'):
                        self.main_window.status_bar.show_message(error_msg, "warning")
                    return
                    
                # 只保留完全匹配的文件
                matched_files = exact_matches
            
            # 更新文件列表
            if matched_files:
                self.main_window.file_list.delete(*self.main_window.file_list.get_children())
                for file_path in matched_files:
                    file_name = os.path.basename(file_path)
                    self.main_window.file_list.insert('', 'end', values=(file_name, file_path))
                
                # 更新状态栏（只在最后更新一次）
                if hasattr(self.main_window, 'status_var'):
                    self.main_window.status_var.set(f"找到 {len(matched_files)} 个匹配的文件")
                
                # 如果是通过姓名搜索且有匹配结果，直接返回
                if search_name and not search_id:
                    return
            
            # 检查PDF图片文件夹
            if not matched_files:  # 如果没有匹配的文件，直接返回
                logging.warning("没有找到匹配的文件")
                if hasattr(self.main_window, 'status_var'):
                    self.main_window.status_var.set("没有找到匹配的文件")
                return
                
            excel_file = matched_files[0]  # 取第一个匹配的文件
            excel_name = os.path.basename(excel_file)
            excel_name_without_ext = os.path.splitext(excel_name)[0]
            
            # 获取Excel文件所在目录的父目录（假设结构为：.../目录/xxx.xlsx）
            excel_dir = os.path.dirname(excel_file)
            parent_dir = os.path.dirname(excel_dir)
            
            # 构建预期的PDF图片文件夹路径
            expected_pdf_dir = os.path.join(parent_dir, "pdf图片", excel_name_without_ext)
            
            # 检查PDF图片文件夹是否存在
            if not os.path.exists(expected_pdf_dir):
                error_msg = f"未找到与Excel文件匹配的PDF图片文件夹: {excel_name_without_ext}"
                logging.warning(error_msg)
                if hasattr(self.main_window, 'status_bar'):
                    self.main_window.status_bar.show_message(error_msg, "warning")
                return
                
            # 检查PDF图片文件夹是否为空
            try:
                pdf_files = [f for f in os.listdir(expected_pdf_dir) 
                           if f.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png'))]
                if not pdf_files:
                    error_msg = f"PDF图片文件夹为空: {excel_name_without_ext}"
                    logging.warning(error_msg)
                    if hasattr(self.main_window, 'status_bar'):
                        self.main_window.status_bar.show_message(error_msg, "warning")
                    return
                logging.info(f"找到 {len(pdf_files)} 个PDF/图片文件在 {expected_pdf_dir}")
            except Exception as e:
                error_msg = f"访问PDF图片文件夹时出错: {str(e)}"
                logging.error(error_msg)
                if hasattr(self.main_window, 'status_bar'):
                    self.main_window.status_bar.show_message(error_msg, "error")
                return
        
        # 去重
        matched_files = list(dict.fromkeys(matched_files))
        
        # 更新文件列表
        if matched_files:
            for file_path in matched_files:
                self.main_window.file_list.insert("", "end", values=(file_path,))
            
            msg = f"找到 {len(matched_files)} 个匹配的文件"
            logging.info(msg)
            self.main_window.status_bar.show_message(msg, "info")
        else:
            msg = f"未找到匹配的文件 (编号: '{search_id}', 姓名: '{search_name}')"
            logging.warning(msg)
            self.main_window.status_bar.show_message(msg, "warning")
        # 更新文件列表
        if matched_files:
            # 更新状态栏显示搜索结果数量
            if hasattr(self.main_window, 'search_result_var'):
                self.main_window.search_result_var.set(f"搜索结果: {len(matched_files)} 个文件")
            
            # 显示搜索结果
            logging.info(f"搜索完成，共找到 {len(matched_files)} 个匹配的文件")
        else:
            # 如果没有找到匹配的文件，清空结果
            if hasattr(self.main_window, 'search_result_var'):
                self.main_window.search_result_var.set("未找到匹配的文件")
            logging.info("搜索完成，未找到匹配的文件")
    
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
        if not self.main_window.import_root_dir:
            messagebox.showwarning("警告", "请先导入文件或档案")
            return
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

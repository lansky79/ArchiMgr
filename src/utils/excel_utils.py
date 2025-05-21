import os
import logging
import sys

# 确保 openpyxl 可用
try:
    import openpyxl
except ImportError:
    print("警告: 未找到 openpyxl 模块，Excel 功能可能无法正常工作")
    logging.warning("未找到 openpyxl 模块，Excel 功能可能无法正常工作")

# 导入 pandas
try:
    import pandas as pd
    # 不要全局设置引擎，而是在每次调用时指定
except ImportError as e:
    print(f"警告: {str(e)}")
    logging.warning(f"导入 pandas 失败: {str(e)}")

class ExcelFileNotFound(Exception):
    pass

def get_excel_info(import_root_dir, person_name, person_id, class_code):
    """
    从Excel获取文件相关信息。
    :param import_root_dir: Excel文件根目录
    :param person_name: 人名
    :param person_id: 编号
    :param class_code: 类号
    :return: (material_name, file_date, page_count)
    :raises ExcelFileNotFound: 未找到匹配的Excel文件
    """
    material_name = ""
    file_date = ""
    page_count = ""

    # 解析sheet名
    class_parts = class_code.split('-')
    main_code = class_parts[0]
    sheet_code = main_code
    if main_code in ['4', '9'] and len(class_parts) >= 2:
        sheet_code = f"{main_code}-{class_parts[1]}"
    sheet_map = {
        '1': '一', '2': '二', '3': '三',
        '4-1': '四-1', '4-2': '四-2', '4-3': '四-3', '4-4': '四-4',
        '5': '五', '6': '六', '7': '七', '8': '八',
        '9-1': '九-1', '9-2': '九-2', '9-3': '九-3', '9-4': '九-4',
        '10': '十'
    }
    sheet_name = sheet_map.get(sheet_code)
    if not sheet_name:
        return material_name, file_date, page_count

    # 搜索Excel文件，优先编号+姓名精确匹配
    excel_file_path = None
    logging.info(f"开始搜索Excel文件 - 目录: {import_root_dir}")
    logging.info(f"搜索条件 - 编号: '{person_id}', 姓名: '{person_name}', 类号: '{class_code}'")
    
    # 首先尝试精确匹配
    for root, dirs, files in os.walk(import_root_dir):
        excel_files = [f for f in files if f.lower().endswith('.xlsx') and not f.startswith('~')]
        
        for file in excel_files:
            file_path = os.path.join(root, file)
            file_name_without_ext = os.path.splitext(file)[0]
            
            # 记录调试信息
            logging.debug(f"检查文件: {file_path}")
            
            # 尝试不同的匹配模式
            # 1. 检查文件名是否包含编号或姓名
            if (person_id and person_id in file_name_without_ext) or \
               (person_name and person_name in file_name_without_ext):
                logging.info(f"找到匹配的Excel文件(包含编号/姓名): {file_path}")
                excel_file_path = file_path
                break
                
            # 2. 检查文件名是否与编号或姓名相同（不区分大小写）
            if (person_id and person_id.lower() == file_name_without_ext.lower()) or \
               (person_name and person_name.lower() == file_name_without_ext.lower()):
                logging.info(f"找到匹配的Excel文件(完全匹配): {file_path}")
                excel_file_path = file_path
                break
                
            # 3. 检查文件名是否以下划线分隔，并且包含编号或姓名
            parts = file_name_without_ext.split('_')
            if (person_id and person_id in parts) or \
               (person_name and person_name in parts):
                logging.info(f"找到匹配的Excel文件(部分匹配): {file_path}")
                excel_file_path = file_path
                break
                
            # 4. 检查文件名是否包含编号或姓名的部分匹配（不区分大小写）
            if (person_id and any(part.lower() == person_id.lower() for part in parts)) or \
               (person_name and any(part.lower() == person_name.lower() for part in parts)):
                logging.info(f"找到匹配的Excel文件(部分不区分大小写匹配): {file_path}")
                excel_file_path = file_path
                break
                
        if excel_file_path:
            break
    
    # 如果还没找到，尝试更宽松的匹配
    if not excel_file_path:
        logging.info("未找到精确匹配的Excel文件，尝试更宽松的匹配...")
        for root, dirs, files in os.walk(import_root_dir):
            excel_files = [f for f in files if f.lower().endswith('.xlsx') and not f.startswith('~')]
            
            for file in excel_files:
                file_path = os.path.join(root, file)
                file_name_without_ext = os.path.splitext(file)[0].lower()
                
                # 检查是否包含编号或姓名的部分内容
                if (person_id and person_id.lower() in file_name_without_ext) or \
                   (person_name and person_name.lower() in file_name_without_ext):
                    logging.info(f"找到部分匹配的Excel文件: {file_path}")
                    excel_file_path = file_path
                    break
            
            if excel_file_path:
                break
    if not excel_file_path:
        raise ExcelFileNotFound(f"未找到匹配的Excel文件: {person_name}")

    # 读取sheet，明确指定 engine='openpyxl'
    try:
        excel = pd.ExcelFile(excel_file_path, engine='openpyxl')
        if sheet_name not in excel.sheet_names:
            # 尝试模糊sheet名
            candidates = [s for s in excel.sheet_names if sheet_name in s]
            if candidates:
                sheet_name = candidates[0]
                logging.info(f"使用模糊匹配的sheet名: {sheet_name}")
            else:
                return material_name, file_date, page_count
                
        df = pd.read_excel(excel_file_path, sheet_name=sheet_name, engine='openpyxl')
        if df.empty:
            return material_name, file_date, page_count
    except Exception as e:
        logging.error(f"读取Excel文件失败: {str(e)}")
        return material_name, file_date, page_count
    # 精确查找A列
    found = False
    for i, value in enumerate(df.iloc[:, 0]):
        if str(value).strip() == class_code:
            row = df.iloc[i]
            material_name = str(row.iloc[1]) if len(row) > 1 and pd.notna(row.iloc[1]) else ""
            # 日期
            if len(row) > 4:
                year = str(int(row.iloc[2])) if pd.notna(row.iloc[2]) else ""
                month = str(int(row.iloc[3])) if pd.notna(row.iloc[3]) else ""
                day = str(int(row.iloc[4])) if pd.notna(row.iloc[4]) else ""
                if year and month and day:
                    file_date = f"{year}-{month}-{day}"
            # 页数
            if len(row) > 5:
                page_value = row.iloc[5]
                page_count = str(int(page_value)) if pd.notna(page_value) else ""
            found = True
            break
    return material_name, file_date, page_count

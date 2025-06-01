#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
修复src/main.py中的导入问题
"""

import os
import sys
import re

def fix_imports():
    """修复main.py中的导入问题"""
    main_file = os.path.join('src', 'main.py')
    backup_file = os.path.join('src', 'main.py.bak')
    
    # 备份原始文件
    if os.path.exists(main_file):
        print(f"备份原始文件到 {backup_file}")
        with open(main_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(content)
    else:
        print(f"错误：找不到文件 {main_file}")
        return False
    
    # 修改导入语句
    print("修改导入语句...")
    new_content = re.sub(
        r'from utils\.paths import',
        'from src.utils.paths import',
        content
    )
    
    # 修改其他导入
    new_content = re.sub(
        r'from models\.database import',
        'from src.models.database import',
        new_content
    )
    
    new_content = re.sub(
        r'from ui\.main_window import',
        'from src.ui.main_window import',
        new_content
    )
    
    new_content = re.sub(
        r'from config\.logger import',
        'from src.config.logger import',
        new_content
    )
    
    # 写入修改后的文件
    with open(main_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"已修复 {main_file} 中的导入语句")
    return True

if __name__ == "__main__":
    print("开始修复导入问题...")
    if fix_imports():
        print("导入问题修复完成！")
        print("请尝试运行 python src/main.py")
    else:
        print("修复失败！")
    
    input("按回车键退出...") 
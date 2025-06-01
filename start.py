#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
档案管理系统启动脚本
用于修复导入路径问题
"""

import os
import sys
import logging

# 设置正确的导入路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 添加src目录到路径
src_dir = os.path.join(current_dir, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

print(f"当前工作目录: {os.getcwd()}")
print(f"Python路径: {sys.executable}")
print(f"系统路径:")
for p in sys.path:
    print(f"  {p}")

try:
    # 导入主模块并运行
    from src.main import main
    print("成功导入主模块，开始运行程序...")
    main()
except ImportError as e:
    print(f"导入错误: {e}")
    print("尝试修复导入问题...")
    
    # 尝试修复特定的导入问题
    if "utils.paths" in str(e):
        print("检测到utils.paths导入问题，尝试修复...")
        try:
            # 修改导入语句
            import src.utils.paths
            # 将模块添加到sys.modules中
            sys.modules['utils.paths'] = src.utils.paths
            print("已修复utils.paths导入问题")
            
            # 重新尝试导入主模块
            from src.main import main
            print("成功导入主模块，开始运行程序...")
            main()
        except Exception as fix_error:
            print(f"修复导入问题失败: {fix_error}")
    else:
        print("无法自动修复导入问题")
    
    input("按回车键退出...")
except Exception as e:
    print(f"运行程序时出错: {e}")
    import traceback
    traceback.print_exc()
    input("按回车键退出...") 
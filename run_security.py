#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
档案安全模块启动脚本
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
    # 导入安全模块并运行
    print("正在启动档案安全模块...")
    from src.security_launcher import main
    main()
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保所有依赖项已正确安装")
    input("按回车键退出...")
except Exception as e:
    print(f"运行程序时出错: {e}")
    import traceback
    traceback.print_exc()
    input("按回车键退出...") 
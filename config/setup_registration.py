#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

def create_valid_registration():
    """创建有效注册信息文件"""
    try:
        # 确保配置目录存在
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_dir = script_dir  # 脚本就在config目录下
        
        # 有效注册信息
        reg_code = "sourcestride123"  # 注册码
        org_name = "sourcestride"  # 单位名称
        
        # 组合并加密注册信息
        reg_info = f"{reg_code}|{org_name}"
        encrypted = ''.join(chr(ord(c) + 1) for c in reg_info)
        
        # 写入有效注册信息文件
        valid_reg_file = os.path.join(config_dir, 'valid_registration.dat')
        with open(valid_reg_file, 'w', encoding='utf-8') as f:
            f.write(encrypted)
            
        print(f"有效注册信息文件已创建: {valid_reg_file}")
        print(f"注册码: {reg_code}")
        print(f"单位名称: {org_name}")
        return True
        
    except Exception as e:
        print(f"创建有效注册信息文件失败: {e}")
        return False

if __name__ == "__main__":
    if create_valid_registration():
        print("设置成功！")
        sys.exit(0)
    else:
        print("设置失败！")
        sys.exit(1) 
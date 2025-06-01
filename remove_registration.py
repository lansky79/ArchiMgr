#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import shutil

def remove_registration():
    """删除所有注册信息文件"""
    try:
        # 获取配置目录路径
        config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config')
        
        # 需要清空的注册文件列表
        registration_files = [
            'registration.dat',
            'valid_registration.dat',
            'registration.txt',
            'valid_reg.dat'
        ]
        
        # 清空或删除文件
        for filename in registration_files:
            file_path = os.path.join(config_dir, filename)
            if os.path.exists(file_path):
                # 方法1: 清空文件内容
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('')
                print(f"已清空文件: {filename}")
                
                # 方法2: 也可以选择直接删除文件
                # os.remove(file_path)
                # print(f"已删除文件: {filename}")
        
        print("所有注册信息已清除！程序将以未注册状态启动。")
        return True
        
    except Exception as e:
        print(f"清除注册信息失败: {e}")
        return False

if __name__ == "__main__":
    if remove_registration():
        print("操作成功完成！")
        sys.exit(0)
    else:
        print("操作失败！")
        sys.exit(1) 
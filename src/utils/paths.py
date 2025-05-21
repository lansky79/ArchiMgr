#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import platform
import logging

def get_app_name():
    """返回应用程序名称"""
    return "档案检索系统"

def get_application_path():
    """获取应用程序安装路径"""
    if getattr(sys, 'frozen', False):
        # 打包后的环境
        return os.path.dirname(sys.executable)
    else:
        # 开发环境
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_user_data_dir():
    """获取用户数据目录，兼容不同Windows版本"""
    app_name = get_app_name()
    
    # 检测操作系统
    system = platform.system()
    if system != "Windows":
        logging.warning(f"不支持的操作系统: {system}，使用默认路径")
    
    # 获取 AppData 路径
    appdata = os.environ.get('APPDATA')
    if not appdata:
        # 备用方案
        appdata = os.path.expanduser('~\\AppData\\Roaming')
        if not os.path.exists(appdata):
            # 极端情况，使用用户主目录
            appdata = os.path.expanduser('~')
            logging.warning(f"无法找到 AppData 目录，使用用户主目录: {appdata}")
    
    return os.path.join(appdata, app_name)

def get_logs_dir():
    """获取日志目录"""
    logs_dir = os.path.join(get_user_data_dir(), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    return logs_dir

def get_database_dir():
    """获取数据库目录"""
    db_dir = os.path.join(get_user_data_dir(), 'database')
    os.makedirs(db_dir, exist_ok=True)
    return db_dir

def get_database_path():
    """获取数据库文件路径"""
    return os.path.join(get_database_dir(), 'archimgr.db')

def get_temp_dir():
    """获取临时文件目录"""
    temp_dir = os.path.join(get_user_data_dir(), 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir

def get_config_dir():
    """获取配置文件目录"""
    config_dir = os.path.join(get_user_data_dir(), 'config')
    os.makedirs(config_dir, exist_ok=True)
    return config_dir

def get_resources_path():
    """获取资源文件路径，这些是只读的，保留在安装目录"""
    if getattr(sys, 'frozen', False):
        # 打包后的环境
        # 首先检查应用程序目录下的resources
        app_resources = os.path.join(get_application_path(), 'resources')
        if os.path.exists(app_resources):
            return app_resources
        # 然后检查应用程序目录/src/resources
        src_resources = os.path.join(get_application_path(), 'src', 'resources')
        if os.path.exists(src_resources):
            return src_resources
        # 如果都找不到，返回默认路径
        return os.path.join(get_application_path(), 'resources')
    else:
        # 开发环境
        return os.path.join(get_application_path(), 'resources')

def get_icon_path():
    """获取应用图标路径"""
    # 尝试不同的可能位置
    possible_paths = [
        os.path.join(get_resources_path(), 'app.ico'),
        os.path.join(get_application_path(), 'resources', 'app.ico'),
        os.path.join(get_application_path(), 'src', 'resources', 'app.ico')
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # 如果都找不到，返回默认路径
    return os.path.join(get_resources_path(), 'app.ico')

def get_exports_dir():
    """获取导出文件目录，默认放在用户的文档目录下"""
    try:
        # 尝试获取用户文档目录
        documents = os.path.join(os.path.expanduser('~'), 'Documents')
        if not os.path.exists(documents):
            # 备用方案
            documents = os.path.expanduser('~')
        
        exports_dir = os.path.join(documents, get_app_name(), 'exports')
        os.makedirs(exports_dir, exist_ok=True)
        return exports_dir
    except Exception as e:
        # 如果出错，使用应用数据目录
        logging.warning(f"无法访问用户文档目录，使用应用数据目录: {str(e)}")
        exports_dir = os.path.join(get_user_data_dir(), 'exports')
        os.makedirs(exports_dir, exist_ok=True)
        return exports_dir

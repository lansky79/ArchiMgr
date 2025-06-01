# -*- coding: utf-8 -*-
"""
配置工具模块

提供配置文件的加载、保存和管理功能。
"""

import os
import json
import logging

# 设置日志记录器
logger = logging.getLogger(__name__)

def load_config(config_path, default_config=None):
    """
    加载配置文件
    
    参数:
        config_path (str): 配置文件路径
        default_config (dict): 默认配置，当文件不存在时使用
        
    返回:
        dict: 配置数据
    """
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"已加载配置文件: {config_path}")
            return config
        elif default_config is not None:
            logger.warning(f"配置文件不存在，使用默认配置: {config_path}")
            # 自动保存默认配置
            save_config(config_path, default_config)
            return default_config
        else:
            logger.warning(f"配置文件不存在且未提供默认配置: {config_path}")
            return {}
    except Exception as e:
        logger.error(f"加载配置文件时出错: {e}")
        if default_config is not None:
            return default_config
        return {}

def save_config(config_path, config_data):
    """
    保存配置文件
    
    参数:
        config_path (str): 配置文件路径
        config_data (dict): 要保存的配置数据
        
    返回:
        bool: 保存成功返回True，否则返回False
    """
    try:
        # 确保目录存在
        config_dir = os.path.dirname(config_path)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
            
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
        logger.info(f"已保存配置文件: {config_path}")
        return True
    except Exception as e:
        logger.error(f"保存配置文件时出错: {e}")
        return False

def get_app_dir(app_name="archimgr", dir_type="config"):
    """
    获取应用目录路径
    
    参数:
        app_name (str): 应用名称
        dir_type (str): 目录类型，如 'config', 'data', 'logs'
        
    返回:
        str: 目录路径
    """
    # 根据操作系统确定基础目录
    if os.name == 'nt':  # Windows
        base_dir = os.environ.get('APPDATA', os.path.expanduser('~'))
        app_dir = os.path.join(base_dir, app_name)
    else:  # Unix/Linux/Mac
        if dir_type == 'config':
            base_dir = os.path.expanduser('~/.config')
        else:
            base_dir = os.path.expanduser('~/.local/share')
        app_dir = os.path.join(base_dir, app_name)
    
    # 创建完整路径
    full_dir = os.path.join(app_dir, dir_type) if dir_type != 'config' else app_dir
    os.makedirs(full_dir, exist_ok=True)
    
    return full_dir

def merge_configs(base_config, override_config):
    """
    合并两个配置
    
    参数:
        base_config (dict): 基础配置
        override_config (dict): 覆盖配置
        
    返回:
        dict: 合并后的配置
    """
    result = base_config.copy()
    
    for key, value in override_config.items():
        # 如果是嵌套字典，递归合并
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value
            
    return result 
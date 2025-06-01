#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
安全模块工具函数 - 提供文件哈希、元数据获取等功能
"""

import os
import hashlib
import logging
import time
from datetime import datetime

def calculate_file_hash(file_path, algorithm='sha256', chunk_size=8192):
    """
    计算文件的哈希值
    
    参数:
        file_path (str): 文件路径
        algorithm (str): 哈希算法，支持 md5, sha1, sha256
        chunk_size (int): 读取文件的块大小
        
    返回:
        str: 文件的哈希值，如果出错则返回 None
    """
    logger = logging.getLogger('security.utils')
    
    if not os.path.isfile(file_path):
        logger.error(f"文件不存在: {file_path}")
        return None
    
    try:
        # 选择哈希算法
        if algorithm == 'md5':
            hasher = hashlib.md5()
        elif algorithm == 'sha1':
            hasher = hashlib.sha1()
        else:
            hasher = hashlib.sha256()
        
        # 分块读取文件并更新哈希
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(chunk_size), b''):
                hasher.update(chunk)
        
        # 返回十六进制哈希值
        return hasher.hexdigest()
    
    except Exception as e:
        logger.error(f"计算文件哈希时出错 ({file_path}): {str(e)}")
        return None

def get_file_metadata(file_path):
    """
    获取文件元数据
    
    参数:
        file_path (str): 文件路径
        
    返回:
        dict: 包含文件元数据的字典
    """
    logger = logging.getLogger('security.utils')
    
    if not os.path.isfile(file_path):
        logger.error(f"文件不存在: {file_path}")
        return None
    
    try:
        # 获取基本文件信息
        stat = os.stat(file_path)
        
        # 返回元数据字典
        return {
            'size': stat.st_size,
            'modified_time': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
            'created_time': datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
            'accessed_time': datetime.fromtimestamp(stat.st_atime).strftime('%Y-%m-%d %H:%M:%S')
        }
    
    except Exception as e:
        logger.error(f"获取文件元数据时出错 ({file_path}): {str(e)}")
        return {
            'size': 0,
            'modified_time': '',
            'created_time': '',
            'accessed_time': ''
        }

def verify_file_hash(file_path, expected_hash, algorithm='sha256'):
    """
    验证文件哈希值是否匹配
    
    参数:
        file_path (str): 文件路径
        expected_hash (str): 期望的哈希值
        algorithm (str): 哈希算法
        
    返回:
        bool: 哈希值是否匹配
    """
    current_hash = calculate_file_hash(file_path, algorithm)
    return current_hash == expected_hash

def format_size(size_bytes):
    """
    格式化文件大小
    
    参数:
        size_bytes (int): 文件大小（字节）
        
    返回:
        str: 格式化后的文件大小
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes/1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes/(1024*1024):.2f} MB"
    else:
        return f"{size_bytes/(1024*1024*1024):.2f} GB" 
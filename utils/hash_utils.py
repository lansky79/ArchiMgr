# -*- coding: utf-8 -*-
"""
哈希计算工具模块

提供文件哈希计算和验证功能，用于档案完整性检查。
"""

import hashlib
import os
import logging

# 设置日志记录器
logger = logging.getLogger(__name__)

def calculate_file_hash(file_path, algorithm='sha256', chunk_size=4096):
    """
    计算文件的哈希值
    
    参数:
        file_path (str): 文件路径
        algorithm (str): 哈希算法，支持 'md5', 'sha1', 'sha256'
        chunk_size (int): 读取文件的块大小
        
    返回:
        str: 文件的哈希值，如果出错则返回None
    """
    try:
        if not os.path.exists(file_path):
            logger.error(f"文件不存在: {file_path}")
            return None
            
        if algorithm == 'md5':
            hash_obj = hashlib.md5()
        elif algorithm == 'sha1':
            hash_obj = hashlib.sha1()
        elif algorithm == 'sha256':
            hash_obj = hashlib.sha256()
        else:
            raise ValueError(f"不支持的哈希算法: {algorithm}")
        
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(chunk_size), b""):
                hash_obj.update(byte_block)
        
        return hash_obj.hexdigest()
    except Exception as e:
        logger.error(f"计算文件哈希值时出错: {e}")
        return None

def verify_file_hash(file_path, expected_hash, algorithm='sha256'):
    """
    验证文件哈希值是否匹配
    
    参数:
        file_path (str): 文件路径
        expected_hash (str): 期望的哈希值
        algorithm (str): 哈希算法，支持 'md5', 'sha1', 'sha256'
        
    返回:
        bool: 哈希值匹配返回True，否则返回False
    """
    actual_hash = calculate_file_hash(file_path, algorithm)
    if actual_hash is None:
        return False
    return actual_hash.lower() == expected_hash.lower()

def get_file_info(file_path):
    """
    获取文件基本信息
    
    参数:
        file_path (str): 文件路径
        
    返回:
        dict: 包含文件大小、修改时间等信息的字典
    """
    try:
        if not os.path.exists(file_path):
            return None
            
        stats = os.stat(file_path)
        return {
            "size": stats.st_size,
            "modified_time": stats.st_mtime,
            "created_time": stats.st_ctime,
            "extension": os.path.splitext(file_path)[1].lower()
        }
    except Exception as e:
        logger.error(f"获取文件信息时出错: {e}")
        return None 
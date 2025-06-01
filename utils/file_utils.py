# -*- coding: utf-8 -*-
"""
文件工具模块

提供文件处理、比较和扫描功能。
"""

import os
import shutil
import datetime
import logging
import fnmatch
from PIL import Image, ImageChops

# 设置日志记录器
logger = logging.getLogger(__name__)

# 支持的文件类型
PDF_EXTENSIONS = ['.pdf']
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.tif', '.tiff', '.bmp', '.gif']
DOCUMENT_EXTENSIONS = ['.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt']
SUPPORTED_EXTENSIONS = PDF_EXTENSIONS + IMAGE_EXTENSIONS + DOCUMENT_EXTENSIONS

def is_supported_file(file_path, extensions=None):
    """
    检查文件是否为支持的类型
    
    参数:
        file_path (str): 文件路径
        extensions (list): 支持的扩展名列表，如果为None则使用默认列表
        
    返回:
        bool: 如果文件类型受支持则返回True，否则返回False
    """
    if extensions is None:
        extensions = SUPPORTED_EXTENSIONS
        
    ext = os.path.splitext(file_path)[1].lower()
    return ext in extensions

def safe_copy_file(src, dst, backup=True):
    """
    安全复制文件，可选创建备份
    
    参数:
        src (str): 源文件路径
        dst (str): 目标文件路径
        backup (bool): 是否创建备份
        
    返回:
        bool: 操作成功返回True，否则返回False
    """
    try:
        # 确保目标目录存在
        dst_dir = os.path.dirname(dst)
        if dst_dir and not os.path.exists(dst_dir):
            os.makedirs(dst_dir, exist_ok=True)
        
        # 如果目标文件已存在且需要备份
        if os.path.exists(dst) and backup:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{dst}.{timestamp}.bak"
            shutil.copy2(dst, backup_path)
            logger.info(f"已创建备份: {backup_path}")
        
        # 复制文件
        shutil.copy2(src, dst)
        logger.info(f"已复制文件: {src} -> {dst}")
        return True
    except Exception as e:
        logger.error(f"复制文件时出错: {e}")
        return False

def scan_directory(directory, extensions=None, recursive=True):
    """
    扫描目录中的文件
    
    参数:
        directory (str): 要扫描的目录
        extensions (list): 要包含的文件扩展名
        recursive (bool): 是否递归扫描子目录
        
    返回:
        list: 找到的文件路径列表
    """
    found_files = []
    
    try:
        if not os.path.exists(directory) or not os.path.isdir(directory):
            logger.error(f"目录不存在或不是有效目录: {directory}")
            return found_files
            
        # 递归遍历或仅扫描顶层目录
        if recursive:
            for root, _, files in os.walk(directory):
                for filename in files:
                    file_path = os.path.join(root, filename)
                    if extensions is None or is_supported_file(file_path, extensions):
                        found_files.append(file_path)
        else:
            for item in os.listdir(directory):
                file_path = os.path.join(directory, item)
                if os.path.isfile(file_path) and (extensions is None or is_supported_file(file_path, extensions)):
                    found_files.append(file_path)
    except Exception as e:
        logger.error(f"扫描目录时出错: {e}")
    
    return found_files

def compare_images(img1_path, img2_path):
    """
    比较两张图片是否相同
    
    参数:
        img1_path (str): 第一张图片路径
        img2_path (str): 第二张图片路径
        
    返回:
        dict: 比较结果，包含是否相同、差异类型等信息
    """
    try:
        img1 = Image.open(img1_path).convert('RGB')
        img2 = Image.open(img2_path).convert('RGB')
        
        # 检查尺寸是否相同
        if img1.size != img2.size:
            return {
                "identical": False,
                "diff_type": "size",
                "details": f"尺寸不同: {img1.size} vs {img2.size}"
            }
        
        # 计算差异
        diff = ImageChops.difference(img1, img2)
        
        # 检查是否有差异（所有像素值是否为0）
        extrema = diff.getextrema()
        max_diff = max([ex[1] for ex in extrema])
        
        if max_diff == 0:
            return {"identical": True}
        else:
            return {
                "identical": False,
                "diff_type": "content",
                "max_diff": max_diff
            }
    except Exception as e:
        logger.error(f"比较图片时出错: {e}")
        return {
            "identical": False,
            "diff_type": "error",
            "details": str(e)
        }

def get_relative_path(file_path, base_dir):
    """
    获取文件相对于基础目录的路径
    
    参数:
        file_path (str): 文件的绝对路径
        base_dir (str): 基础目录
        
    返回:
        str: 相对路径
    """
    try:
        return os.path.relpath(file_path, base_dir)
    except Exception as e:
        logger.error(f"获取相对路径时出错: {e}")
        return file_path

def filter_files(file_list, patterns):
    """
    根据通配符模式过滤文件列表
    
    参数:
        file_list (list): 文件路径列表
        patterns (list): 通配符模式列表
        
    返回:
        list: 过滤后的文件列表
    """
    if not patterns:
        return file_list
        
    result = []
    for file_path in file_list:
        # 获取文件名，用于匹配
        filename = os.path.basename(file_path)
        
        # 检查是否匹配任何模式
        for pattern in patterns:
            if fnmatch.fnmatch(filename, pattern):
                result.append(file_path)
                break
                
    return result 
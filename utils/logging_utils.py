# -*- coding: utf-8 -*-
"""
日志工具模块

提供日志记录和管理功能。
"""

import os
import logging
from logging.handlers import RotatingFileHandler
import datetime
from .config_utils import get_app_dir

# 默认日志格式
DEFAULT_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

def setup_logger(name=None, log_file=None, level=logging.INFO, log_format=None):
    """
    设置日志记录器
    
    参数:
        name (str): 日志记录器名称，默认为根记录器
        log_file (str): 日志文件路径，如果为None则只输出到控制台
        level (int): 日志级别
        log_format (str): 日志格式
        
    返回:
        logging.Logger: 配置好的日志记录器
    """
    # 获取日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 设置日志格式
    formatter = logging.Formatter(log_format or DEFAULT_LOG_FORMAT)
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 如果指定了日志文件，添加文件处理器
    if log_file:
        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
            
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_default_logger(name, app_name="archimgr"):
    """
    获取默认配置的日志记录器
    
    参数:
        name (str): 日志记录器名称
        app_name (str): 应用名称
        
    返回:
        logging.Logger: 配置好的日志记录器
    """
    # 获取日志目录
    log_dir = get_app_dir(app_name, "logs")
    
    # 生成日志文件名
    today = datetime.datetime.now().strftime("%Y%m%d")
    log_file = os.path.join(log_dir, f"{name}_{today}.log")
    
    return setup_logger(name, log_file)

def log_function_call(logger, func_name, args=None, kwargs=None):
    """
    记录函数调用信息
    
    参数:
        logger (logging.Logger): 日志记录器
        func_name (str): 函数名
        args (tuple): 位置参数
        kwargs (dict): 关键字参数
    """
    args_str = str(args) if args else "()"
    kwargs_str = str(kwargs) if kwargs else "{}"
    logger.debug(f"调用函数: {func_name} args={args_str} kwargs={kwargs_str}")

def log_exception(logger, e, context=None):
    """
    记录异常信息
    
    参数:
        logger (logging.Logger): 日志记录器
        e (Exception): 异常对象
        context (str): 上下文信息
    """
    if context:
        logger.exception(f"{context}: {str(e)}")
    else:
        logger.exception(str(e)) 
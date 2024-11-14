import os
import logging
from datetime import datetime

def setup_logging():
    """设置日志配置"""
    # 创建 logs 目录
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # 生成日志文件名（包含日期）
    log_filename = f'logs/debug_{datetime.now().strftime("%Y%m%d")}.log'
    
    # 配置日志格式
    log_format = '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    
    # 文件处理器 - 记录所有日志
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_format))
    
    # 控制台处理器 - 只记录 INFO 及以上级别
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format))
    
    # 配置根日志记录器
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # 记录启动日志
    logging.info("程序启动")
    logging.debug("日志系统初始化完成")

# 导出 setup_logging 函数
__all__ = ['setup_logging'] 
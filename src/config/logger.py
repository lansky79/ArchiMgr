import os
import logging
from datetime import datetime

def setup_logger():
    """设置日志记录器"""
    # 创建日志目录
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # 设置日志格式
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # 创建日志文件名
    log_file = os.path.join(log_dir, f'archimgr_{datetime.now().strftime("%Y%m%d")}.log')
    
    # 配置根日志记录器
    logging.basicConfig(
        level=logging.DEBUG,  # 设置为DEBUG级别以捕获更多信息
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()  # 同时输出到控制台
        ]
    )
    
    logging.info("日志系统初始化完成")

# 导出 setup_logger 函数
__all__ = ['setup_logger'] 
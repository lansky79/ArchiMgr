import os
import logging
from datetime import datetime
from src.utils.paths import get_logs_dir

def setup_logger():
    """设置日志记录器"""
    # 使用路径管理模块获取日志目录
    log_dir = get_logs_dir()
    
    # 设置日志格式
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # 创建日志文件名 - 商用版使用更简洁的命名
    log_file = os.path.join(log_dir, f'app_{datetime.now().strftime("%Y%m%d")}.log')
    
    # 配置根日志记录器 - 商用版使用INFO级别
    logging.basicConfig(
        level=logging.INFO,  # 商用版使用INFO级别，减少调试信息
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
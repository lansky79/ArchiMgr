#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
预加载必要的模块，确保它们在打包后的应用程序中可用
"""

import sys
import os
import logging

def preload_modules():
    """预加载必要的模块"""
    try:
        # 预加载 openpyxl
        import openpyxl
        logging.info("成功加载 openpyxl 模块")
        
        # 预加载 pandas
        import pandas as pd
        # 确保 pandas 可以访问 openpyxl
        # 但不要全局设置引擎，因为这可能导致错误
        logging.info("成功加载 pandas")
        
        return True
    except ImportError as e:
        logging.error(f"预加载模块失败: {str(e)}")
        return False

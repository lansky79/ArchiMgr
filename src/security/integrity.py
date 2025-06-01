#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
档案完整性检查模块 - 提供档案文件完整性检查功能
"""

import os
import json
import logging
import hashlib
import time
from datetime import datetime
import threading
from pathlib import Path

# 导入工具模块
try:
    from src.security.utils import calculate_file_hash, get_file_metadata
except ImportError:
    # 打包环境
    from security.utils import calculate_file_hash, get_file_metadata

class IntegrityChecker:
    """档案完整性检查类"""
    
    def __init__(self, archives_dir=None, database_path=None):
        """
        初始化档案完整性检查器
        
        参数:
            archives_dir (str): 档案文件目录
            database_path (str): 完整性数据库文件路径
        """
        # 设置档案目录
        self.archives_dir = archives_dir
        
        # 设置数据库路径
        if database_path:
            self.database_path = database_path
        else:
            config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'config')
            os.makedirs(config_dir, exist_ok=True)
            self.database_path = os.path.join(config_dir, 'integrity_db.json')
        
        # 确保数据库目录存在
        os.makedirs(os.path.dirname(self.database_path), exist_ok=True)
        
        # 支持的文件扩展名
        self.supported_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.tif', '.tiff', '.doc', '.docx', '.xls', '.xlsx']
        
        # 日志记录器
        self.logger = logging.getLogger('security.integrity')
        
        # 内部状态
        self._is_running = False
        self._progress = 0
        self._total_files = 0
        self._current_file = ""
        self._abort_flag = False
        
        # 线程锁
        self._lock = threading.Lock()
    
    def get_progress(self):
        """获取当前进度"""
        with self._lock:
            return {
                'is_running': self._is_running,
                'progress': self._progress,
                'total_files': self._total_files,
                'current_file': self._current_file
            }
    
    def abort(self):
        """中止当前操作"""
        with self._lock:
            self._abort_flag = True
    
    def build_database(self, callback=None):
        """
        构建完整性数据库
        
        参数:
            callback: 进度回调函数，接收进度百分比和当前文件路径
        
        返回:
            bool: 操作是否成功
        """
        if not self.archives_dir or not os.path.isdir(self.archives_dir):
            self.logger.error(f"档案目录无效: {self.archives_dir}")
            return False
        
        try:
            with self._lock:
                self._is_running = True
                self._progress = 0
                self._abort_flag = False
            
            start_time = time.time()
            self.logger.info(f"开始构建完整性数据库，档案目录: {self.archives_dir}")
            
            # 扫描所有文件
            all_files = []
            for root, _, files in os.walk(self.archives_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    if self._should_process_file(file_path):
                        all_files.append(file_path)
            
            with self._lock:
                self._total_files = len(all_files)
            
            self.logger.info(f"找到 {len(all_files)} 个档案文件")
            
            # 准备数据库
            database = {
                'created_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'archives_dir': self.archives_dir,
                'file_count': len(all_files),
                'files': {}
            }
            
            # 处理每个文件
            for i, file_path in enumerate(all_files):
                # 检查是否需要中止
                with self._lock:
                    if self._abort_flag:
                        self.logger.info("操作被用户中止")
                        return False
                    self._current_file = file_path
                    self._progress = (i / len(all_files)) * 100 if all_files else 100
                
                try:
                    # 计算文件哈希
                    file_hash = calculate_file_hash(file_path)
                    
                    # 获取文件元数据
                    metadata = get_file_metadata(file_path)
                    
                    # 将相对路径存储到数据库
                    rel_path = os.path.relpath(file_path, self.archives_dir)
                    
                    # 保存到数据库
                    database['files'][rel_path] = {
                        'hash': file_hash,
                        'size': metadata['size'],
                        'modified_time': metadata['modified_time'],
                        'created_time': metadata['created_time'],
                        'checked_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    # 调用回调函数
                    if callback:
                        callback(self._progress, file_path)
                        
                except Exception as e:
                    self.logger.error(f"处理文件 {file_path} 时出错: {str(e)}")
            
            # 保存数据库
            with open(self.database_path, 'w', encoding='utf-8') as f:
                json.dump(database, f, ensure_ascii=False, indent=2)
            
            elapsed_time = time.time() - start_time
            self.logger.info(f"完整性数据库构建完成，用时 {elapsed_time:.2f} 秒")
            
            return True
            
        except Exception as e:
            self.logger.exception(f"构建完整性数据库时出错: {str(e)}")
            return False
        finally:
            with self._lock:
                self._is_running = False
                self._progress = 100
    
    def verify_integrity(self, callback=None, generate_report=True):
        """
        验证档案完整性
        
        参数:
            callback: 进度回调函数
            generate_report: 是否生成报告
            
        返回:
            dict: 包含验证结果的字典
        """
        if not os.path.exists(self.database_path):
            self.logger.error(f"完整性数据库不存在: {self.database_path}")
            return {'status': 'error', 'message': '完整性数据库不存在'}
        
        try:
            with self._lock:
                self._is_running = True
                self._progress = 0
                self._abort_flag = False
            
            start_time = time.time()
            self.logger.info("开始验证档案完整性")
            
            # 加载数据库
            with open(self.database_path, 'r', encoding='utf-8') as f:
                database = json.load(f)
            
            archives_dir = database.get('archives_dir', self.archives_dir)
            if not archives_dir or not os.path.isdir(archives_dir):
                self.logger.error(f"数据库中的档案目录无效: {archives_dir}")
                return {'status': 'error', 'message': '档案目录无效'}
            
            # 初始化结果
            result = {
                'status': 'success',
                'verified_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'database_time': database.get('created_time', 'unknown'),
                'archives_dir': archives_dir,
                'total_files': database.get('file_count', 0),
                'verified_files': 0,
                'modified_files': [],
                'missing_files': [],
                'new_files': []
            }
            
            # 获取所有当前文件
            current_files = set()
            for root, _, files in os.walk(archives_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    if self._should_process_file(file_path):
                        rel_path = os.path.relpath(file_path, archives_dir)
                        current_files.add(rel_path)
            
            # 处理数据库中的文件
            db_files = list(database.get('files', {}).keys())
            
            with self._lock:
                self._total_files = len(db_files)
            
            for i, rel_path in enumerate(db_files):
                # 检查是否需要中止
                with self._lock:
                    if self._abort_flag:
                        self.logger.info("操作被用户中止")
                        return {'status': 'aborted', 'message': '操作被用户中止'}
                    self._progress = (i / len(db_files)) * 100 if db_files else 100
                
                # 构造完整路径
                file_path = os.path.join(archives_dir, rel_path)
                
                with self._lock:
                    self._current_file = file_path
                
                # 调用回调函数
                if callback:
                    callback(self._progress, file_path)
                
                # 检查文件是否存在
                if not os.path.exists(file_path):
                    self.logger.warning(f"文件丢失: {rel_path}")
                    result['missing_files'].append(rel_path)
                    continue
                
                try:
                    # 获取数据库中的哈希值
                    db_hash = database['files'][rel_path]['hash']
                    
                    # 计算当前哈希值
                    current_hash = calculate_file_hash(file_path)
                    
                    # 比较哈希值
                    if current_hash != db_hash:
                        self.logger.warning(f"文件已修改: {rel_path}")
                        result['modified_files'].append(rel_path)
                    else:
                        result['verified_files'] += 1
                        
                except Exception as e:
                    self.logger.error(f"验证文件 {file_path} 时出错: {str(e)}")
            
            # 查找新文件
            db_file_set = set(db_files)
            for rel_path in current_files:
                if rel_path not in db_file_set:
                    result['new_files'].append(rel_path)
                    self.logger.info(f"发现新文件: {rel_path}")
            
            # 生成报告
            if generate_report:
                report_path = os.path.join(os.path.dirname(self.database_path), 'integrity_report.json')
                with open(report_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                self.logger.info(f"完整性报告已保存到: {report_path}")
            
            elapsed_time = time.time() - start_time
            self.logger.info(f"档案完整性验证完成，用时 {elapsed_time:.2f} 秒")
            
            return result
            
        except Exception as e:
            self.logger.exception(f"验证档案完整性时出错: {str(e)}")
            return {'status': 'error', 'message': str(e)}
        finally:
            with self._lock:
                self._is_running = False
                self._progress = 100
    
    def update_database(self, callback=None):
        """
        更新完整性数据库
        
        参数:
            callback: 进度回调函数
            
        返回:
            bool: 操作是否成功
        """
        if not os.path.exists(self.database_path):
            self.logger.error(f"完整性数据库不存在: {self.database_path}")
            return False
        
        try:
            with self._lock:
                self._is_running = True
                self._progress = 0
                self._abort_flag = False
            
            start_time = time.time()
            self.logger.info("开始更新完整性数据库")
            
            # 加载数据库
            with open(self.database_path, 'r', encoding='utf-8') as f:
                database = json.load(f)
            
            archives_dir = database.get('archives_dir', self.archives_dir)
            if not archives_dir or not os.path.isdir(archives_dir):
                self.logger.error(f"数据库中的档案目录无效: {archives_dir}")
                return False
            
            # 获取所有当前文件
            current_files = []
            for root, _, files in os.walk(archives_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    if self._should_process_file(file_path):
                        rel_path = os.path.relpath(file_path, archives_dir)
                        current_files.append((rel_path, file_path))
            
            with self._lock:
                self._total_files = len(current_files)
            
            # 更新数据库
            db_files = set(database.get('files', {}).keys())
            updated_db = {
                'created_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'archives_dir': archives_dir,
                'file_count': len(current_files),
                'files': {}
            }
            
            # 处理每个文件
            for i, (rel_path, file_path) in enumerate(current_files):
                # 检查是否需要中止
                with self._lock:
                    if self._abort_flag:
                        self.logger.info("操作被用户中止")
                        return False
                    self._current_file = file_path
                    self._progress = (i / len(current_files)) * 100 if current_files else 100
                
                # 调用回调函数
                if callback:
                    callback(self._progress, file_path)
                
                try:
                    # 如果文件在数据库中且未修改，则复用数据
                    if rel_path in db_files:
                        old_hash = database['files'][rel_path]['hash']
                        current_hash = calculate_file_hash(file_path)
                        
                        if old_hash == current_hash:
                            # 复用旧数据
                            updated_db['files'][rel_path] = database['files'][rel_path]
                            updated_db['files'][rel_path]['checked_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            continue
                    
                    # 计算新哈希值和元数据
                    file_hash = calculate_file_hash(file_path)
                    metadata = get_file_metadata(file_path)
                    
                    # 保存到数据库
                    updated_db['files'][rel_path] = {
                        'hash': file_hash,
                        'size': metadata['size'],
                        'modified_time': metadata['modified_time'],
                        'created_time': metadata['created_time'],
                        'checked_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                except Exception as e:
                    self.logger.error(f"处理文件 {file_path} 时出错: {str(e)}")
            
            # 备份旧数据库
            backup_path = f"{self.database_path}.bak"
            import shutil
            shutil.copy2(self.database_path, backup_path)
            self.logger.info(f"已备份旧数据库到: {backup_path}")
            
            # 保存更新后的数据库
            with open(self.database_path, 'w', encoding='utf-8') as f:
                json.dump(updated_db, f, ensure_ascii=False, indent=2)
            
            elapsed_time = time.time() - start_time
            self.logger.info(f"完整性数据库更新完成，用时 {elapsed_time:.2f} 秒")
            
            return True
            
        except Exception as e:
            self.logger.exception(f"更新完整性数据库时出错: {str(e)}")
            return False
        finally:
            with self._lock:
                self._is_running = False
                self._progress = 100
    
    def _should_process_file(self, file_path):
        """判断是否应该处理该文件"""
        if not os.path.isfile(file_path):
            return False
        
        # 检查文件扩展名
        ext = os.path.splitext(file_path)[1].lower()
        return ext in self.supported_extensions 
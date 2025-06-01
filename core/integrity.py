# -*- coding: utf-8 -*-
"""
档案完整性检查模块

提供档案文件完整性检查、验证和管理功能。
"""

import os
import json
import datetime
import time
import logging
from ..utils.hash_utils import calculate_file_hash, get_file_info
from ..utils.file_utils import scan_directory, get_relative_path
from ..utils.logging_utils import log_function_call, log_exception

# 设置日志记录器
logger = logging.getLogger(__name__)

class IntegrityChecker:
    """档案完整性检查器"""
    
    def __init__(self, archives_dir, database_path):
        """
        初始化完整性检查器
        
        参数:
            archives_dir (str): 档案目录路径
            database_path (str): 完整性数据库文件路径
        """
        self.archives_dir = archives_dir
        self.database_path = database_path
        
        # 支持的文件扩展名（主要是图片和PDF）
        self.supported_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.tif', '.tiff', '.bmp']
        
        # 确保数据库目录存在
        database_dir = os.path.dirname(database_path)
        if database_dir and not os.path.exists(database_dir):
            os.makedirs(database_dir, exist_ok=True)
    
    def build_database(self):
        """
        构建完整性数据库
        
        返回:
            int: 处理的文件数量
        """
        log_function_call(logger, "build_database")
        
        try:
            # 创建数据库结构
            database = {
                "created_at": datetime.datetime.now().isoformat(),
                "last_updated": datetime.datetime.now().isoformat(),
                "archives_dir": self.archives_dir,
                "files": {}
            }
            
            # 扫描档案文件
            logger.info(f"开始扫描档案目录: {self.archives_dir}")
            files = scan_directory(self.archives_dir, self.supported_extensions)
            logger.info(f"找到 {len(files)} 个档案文件")
            
            # 计算每个文件的哈希值
            for i, file_path in enumerate(files):
                # 获取相对路径（作为键）
                rel_path = get_relative_path(file_path, self.archives_dir)
                
                # 计算哈希值
                file_hash = calculate_file_hash(file_path)
                if file_hash is None:
                    logger.warning(f"跳过文件 {rel_path}，无法计算哈希值")
                    continue
                
                # 获取文件信息
                file_info = get_file_info(file_path)
                
                # 添加到数据库
                database["files"][rel_path] = {
                    "hash": file_hash,
                    "size": file_info["size"],
                    "modified_time": file_info["modified_time"],
                    "created_time": file_info["created_time"],
                    "extension": file_info["extension"],
                    "last_checked": datetime.datetime.now().isoformat()
                }
                
                # 输出进度
                if (i + 1) % 100 == 0 or i + 1 == len(files):
                    logger.info(f"已处理 {i + 1}/{len(files)} 个文件")
            
            # 保存数据库
            with open(self.database_path, 'w', encoding='utf-8') as f:
                json.dump(database, f, ensure_ascii=False, indent=2)
                
            logger.info(f"完整性数据库已保存至: {self.database_path}")
            return len(database["files"])
            
        except Exception as e:
            log_exception(logger, e, "构建完整性数据库时出错")
            raise
    
    def verify_integrity(self, generate_report=True):
        """
        验证档案完整性
        
        参数:
            generate_report (bool): 是否生成报告文件
            
        返回:
            dict: 验证结果
        """
        log_function_call(logger, "verify_integrity", None, {"generate_report": generate_report})
        
        try:
            # 检查数据库是否存在
            if not os.path.exists(self.database_path):
                logger.error(f"完整性数据库不存在: {self.database_path}")
                return None
            
            # 加载数据库
            with open(self.database_path, 'r', encoding='utf-8') as f:
                database = json.load(f)
                
            # 确保档案目录一致
            if database.get("archives_dir") != self.archives_dir:
                logger.warning(f"数据库中的档案目录({database.get('archives_dir')})与当前设置({self.archives_dir})不一致")
            
            # 创建结果结构
            results = {
                "timestamp": datetime.datetime.now().isoformat(),
                "database_created": database.get("created_at"),
                "database_updated": database.get("last_updated"),
                "archives_dir": self.archives_dir,
                "verified_files": 0,
                "modified_files": [],
                "missing_files": [],
                "new_files": []
            }
            
            # 扫描当前文件
            logger.info(f"开始扫描档案目录: {self.archives_dir}")
            current_files = scan_directory(self.archives_dir, self.supported_extensions)
            logger.info(f"找到 {len(current_files)} 个档案文件")
            
            # 记录当前文件的相对路径
            current_rel_paths = set()
            
            # 检查每个当前文件
            for i, file_path in enumerate(current_files):
                # 获取相对路径
                rel_path = get_relative_path(file_path, self.archives_dir)
                current_rel_paths.add(rel_path)
                
                # 检查文件是否在数据库中
                if rel_path in database["files"]:
                    # 文件存在于数据库中，验证哈希值
                    stored_hash = database["files"][rel_path]["hash"]
                    current_hash = calculate_file_hash(file_path)
                    
                    if current_hash is None:
                        logger.warning(f"跳过文件 {rel_path}，无法计算哈希值")
                        continue
                        
                    results["verified_files"] += 1
                    
                    if current_hash != stored_hash:
                        # 哈希值不匹配，文件已被修改
                        logger.warning(f"文件已修改: {rel_path}")
                        
                        # 获取文件信息
                        file_info = get_file_info(file_path)
                        
                        # 添加到修改文件列表
                        results["modified_files"].append({
                            "path": rel_path,
                            "old_hash": stored_hash,
                            "new_hash": current_hash,
                            "old_size": database["files"][rel_path]["size"],
                            "new_size": file_info["size"],
                            "old_modified_time": database["files"][rel_path]["modified_time"],
                            "new_modified_time": file_info["modified_time"]
                        })
                else:
                    # 文件不在数据库中，是新文件
                    logger.info(f"发现新文件: {rel_path}")
                    
                    # 获取文件信息
                    file_info = get_file_info(file_path)
                    current_hash = calculate_file_hash(file_path)
                    
                    # 添加到新文件列表
                    results["new_files"].append({
                        "path": rel_path,
                        "hash": current_hash,
                        "size": file_info["size"],
                        "modified_time": file_info["modified_time"],
                        "created_time": file_info["created_time"]
                    })
                
                # 输出进度
                if (i + 1) % 100 == 0 or i + 1 == len(current_files):
                    logger.info(f"已验证 {i + 1}/{len(current_files)} 个文件")
            
            # 检查缺失的文件
            for rel_path in database["files"]:
                if rel_path not in current_rel_paths:
                    # 文件在数据库中但当前不存在，已丢失
                    logger.warning(f"文件已丢失: {rel_path}")
                    
                    # 添加到丢失文件列表
                    results["missing_files"].append({
                        "path": rel_path,
                        "hash": database["files"][rel_path]["hash"],
                        "size": database["files"][rel_path]["size"],
                        "last_modified_time": database["files"][rel_path]["modified_time"],
                        "last_checked": database["files"][rel_path]["last_checked"]
                    })
            
            # 如果需要，生成报告
            if generate_report:
                report_dir = os.path.dirname(self.database_path)
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                report_path = os.path.join(report_dir, f"integrity_report_{timestamp}.json")
                
                with open(report_path, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                    
                logger.info(f"完整性报告已保存至: {report_path}")
                results["report_path"] = report_path
            
            # 返回结果
            return results
            
        except Exception as e:
            log_exception(logger, e, "验证档案完整性时出错")
            raise
    
    def update_database(self):
        """
        更新完整性数据库
        
        返回:
            dict: 更新结果
        """
        log_function_call(logger, "update_database")
        
        try:
            # 检查数据库是否存在
            if not os.path.exists(self.database_path):
                logger.warning(f"完整性数据库不存在，将创建新数据库: {self.database_path}")
                file_count = self.build_database()
                return {"updated_files": 0, "new_files": file_count, "total_files": file_count}
            
            # 加载数据库
            with open(self.database_path, 'r', encoding='utf-8') as f:
                database = json.load(f)
            
            # 记录更新统计
            stats = {
                "updated_files": 0,
                "new_files": 0,
                "total_files": 0
            }
            
            # 扫描当前文件
            logger.info(f"开始扫描档案目录: {self.archives_dir}")
            current_files = scan_directory(self.archives_dir, self.supported_extensions)
            logger.info(f"找到 {len(current_files)} 个档案文件")
            
            # 更新数据库中的文件
            for i, file_path in enumerate(current_files):
                # 获取相对路径
                rel_path = get_relative_path(file_path, self.archives_dir)
                
                # 获取文件信息
                file_info = get_file_info(file_path)
                current_hash = calculate_file_hash(file_path)
                
                if current_hash is None:
                    logger.warning(f"跳过文件 {rel_path}，无法计算哈希值")
                    continue
                
                # 检查文件是否在数据库中
                if rel_path in database["files"]:
                    # 文件存在于数据库中，检查哈希值是否变化
                    stored_hash = database["files"][rel_path]["hash"]
                    
                    if current_hash != stored_hash:
                        # 哈希值已变化，更新记录
                        logger.info(f"更新文件记录: {rel_path}")
                        database["files"][rel_path] = {
                            "hash": current_hash,
                            "size": file_info["size"],
                            "modified_time": file_info["modified_time"],
                            "created_time": file_info["created_time"],
                            "extension": file_info["extension"],
                            "last_checked": datetime.datetime.now().isoformat(),
                            "previous_hash": stored_hash
                        }
                        stats["updated_files"] += 1
                    else:
                        # 哈希值未变化，仅更新检查时间
                        database["files"][rel_path]["last_checked"] = datetime.datetime.now().isoformat()
                else:
                    # 新文件，添加到数据库
                    logger.info(f"添加新文件记录: {rel_path}")
                    database["files"][rel_path] = {
                        "hash": current_hash,
                        "size": file_info["size"],
                        "modified_time": file_info["modified_time"],
                        "created_time": file_info["created_time"],
                        "extension": file_info["extension"],
                        "last_checked": datetime.datetime.now().isoformat()
                    }
                    stats["new_files"] += 1
                
                # 输出进度
                if (i + 1) % 100 == 0 or i + 1 == len(current_files):
                    logger.info(f"已处理 {i + 1}/{len(current_files)} 个文件")
            
            # 更新数据库信息
            database["last_updated"] = datetime.datetime.now().isoformat()
            database["archives_dir"] = self.archives_dir
            
            # 保存数据库
            with open(self.database_path, 'w', encoding='utf-8') as f:
                json.dump(database, f, ensure_ascii=False, indent=2)
                
            logger.info(f"完整性数据库已更新: {self.database_path}")
            
            # 更新总文件数
            stats["total_files"] = len(database["files"])
            
            return stats
            
        except Exception as e:
            log_exception(logger, e, "更新完整性数据库时出错")
            raise 
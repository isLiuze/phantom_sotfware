# src/utils/file_utils.py

import os
import json
import shutil
from typing import Dict, Any, Optional
from datetime import datetime

class FileUtils:
    """文件操作工具类"""
    
    @staticmethod
    def ensure_directory(directory_path: str) -> None:
        """确保目录存在，如果不存在则创建"""
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
    
    @staticmethod
    def backup_file(file_path: str, backup_dir: str = None) -> str:
        """
        备份文件
        
        Args:
            file_path: 要备份的文件路径
            backup_dir: 备份目录，如果为None则在原文件目录创建backup子目录
            
        Returns:
            备份文件的路径
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        if backup_dir is None:
            backup_dir = os.path.join(os.path.dirname(file_path), "backup")
        
        FileUtils.ensure_directory(backup_dir)
        
        # 生成备份文件名（添加时间戳）
        filename = os.path.basename(file_path)
        name, ext = os.path.splitext(filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{name}_backup_{timestamp}{ext}"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # 复制文件
        shutil.copy2(file_path, backup_path)
        return backup_path
    
    @staticmethod
    def read_json_file(file_path: str) -> Optional[Dict[str, Any]]:
        """
        读取JSON文件
        
        Args:
            file_path: JSON文件路径
            
        Returns:
            解析后的字典，如果失败返回None
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError) as e:
            print(f"读取JSON文件失败 {file_path}: {e}")
            return None
    
    @staticmethod
    def write_json_file(file_path: str, data: Dict[str, Any], backup: bool = True) -> bool:
        """
        写入JSON文件
        
        Args:
            file_path: JSON文件路径
            data: 要写入的数据
            backup: 是否在写入前备份原文件
            
        Returns:
            是否成功
        """
        try:
            # 如果文件存在且需要备份
            if backup and os.path.exists(file_path):
                FileUtils.backup_file(file_path)
            
            # 确保目录存在
            FileUtils.ensure_directory(os.path.dirname(file_path))
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"写入JSON文件失败 {file_path}: {e}")
            return False
    
    @staticmethod
    def get_safe_filename(filename: str) -> str:
        """
        获取安全的文件名（移除非法字符）
        
        Args:
            filename: 原文件名
            
        Returns:
            安全的文件名
        """
        import re
        # 移除Windows和Unix中的非法字符
        safe_filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # 移除连续的空格
        safe_filename = re.sub(r'\s+', '_', safe_filename.strip())
        return safe_filename or "unnamed_file"
    
    @staticmethod
    def get_file_size(file_path: str) -> int:
        """
        获取文件大小（字节）
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件大小，如果文件不存在返回0
        """
        try:
            return os.path.getsize(file_path)
        except OSError:
            return 0
    
    @staticmethod
    def is_file_writable(file_path: str) -> bool:
        """
        检查文件是否可写
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否可写
        """
        try:
            if os.path.exists(file_path):
                return os.access(file_path, os.W_OK)
            else:
                # 检查目录是否可写
                directory = os.path.dirname(file_path)
                return os.access(directory, os.W_OK)
        except OSError:
            return False 
# src/core/validators.py

import re
from typing import Tuple, Any
from datetime import datetime

class Validator:
    """基础验证器类"""
    
    @staticmethod
    def is_not_empty(value: str) -> Tuple[bool, str]:
        """验证字符串不为空"""
        if not value or not value.strip():
            return False, "此字段不能为空"
        return True, ""
    
    @staticmethod
    def is_positive_number(value: str) -> Tuple[bool, str]:
        """验证正数"""
        try:
            num = float(value)
            if num <= 0:
                return False, "必须是正数"
            return True, ""
        except ValueError:
            return False, "必须是有效数字"
    
    @staticmethod
    def is_non_negative_number(value: str) -> Tuple[bool, str]:
        """验证非负数"""
        try:
            num = float(value)
            if num < 0:
                return False, "不能是负数"
            return True, ""
        except ValueError:
            return False, "必须是有效数字"
    
    @staticmethod
    def is_valid_date(date_str: str) -> Tuple[bool, str]:
        """验证日期格式 YYYY-MM-DD"""
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True, ""
        except ValueError:
            return False, "日期格式无效，请使用 YYYY-MM-DD 格式"
    
    @staticmethod
    def is_valid_time(time_str: str) -> Tuple[bool, str]:
        """验证时间格式 HH:MM"""
        pattern = r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$'
        if not re.match(pattern, time_str):
            return False, "时间格式无效，请使用 HH:MM 格式"
        return True, ""
    
    @staticmethod
    def is_in_range(value: str, min_val: float, max_val: float) -> Tuple[bool, str]:
        """验证数值在指定范围内"""
        try:
            num = float(value)
            if num < min_val or num > max_val:
                return False, f"值必须在 {min_val} 到 {max_val} 之间"
            return True, ""
        except ValueError:
            return False, "必须是有效数字"
    
    @staticmethod
    def max_length(value: str, max_len: int) -> Tuple[bool, str]:
        """验证字符串最大长度"""
        if len(value) > max_len:
            return False, f"长度不能超过 {max_len} 个字符"
        return True, ""

class ActivityValidator(Validator):
    """活度专用验证器"""
    
    @staticmethod
    def validate_activity(activity: str) -> Tuple[bool, str]:
        """验证活度值"""
        # 先验证是否为空
        is_valid, message = Validator.is_not_empty(activity)
        if not is_valid:
            return is_valid, message
        
        # 验证是否为正数
        is_valid, message = Validator.is_positive_number(activity)
        if not is_valid:
            return is_valid, message
        
        # 验证范围（0.001 到 10000 MBq）
        return Validator.is_in_range(activity, 0.001, 10000)

class ExperimentValidator(Validator):
    """实验专用验证器"""
    
    @staticmethod
    def validate_name(name: str) -> Tuple[bool, str]:
        """验证实验名称"""
        # 验证非空
        is_valid, message = Validator.is_not_empty(name)
        if not is_valid:
            return is_valid, message
        
        # 验证长度
        return Validator.max_length(name, 100)
    
    @staticmethod
    def validate_center(center: str) -> Tuple[bool, str]:
        """验证中心名称"""
        # 验证非空
        is_valid, message = Validator.is_not_empty(center)
        if not is_valid:
            return is_valid, message
        
        # 验证长度
        return Validator.max_length(center, 100)
    
    @staticmethod
    def validate_volume(volume: str) -> Tuple[bool, str]:
        """验证体积"""
        if not volume or not volume.strip():
            return True, ""  # 体积可以为空
        
        # 验证非负数
        is_valid, message = Validator.is_non_negative_number(volume)
        if not is_valid:
            return is_valid, message
        
        # 验证范围（0 到 1000 L）
        return Validator.is_in_range(volume, 0, 1000) 
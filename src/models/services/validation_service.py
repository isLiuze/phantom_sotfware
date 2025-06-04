# src/models/services/validation_service.py

import re
from typing import List, Tuple, Dict, Any
from datetime import datetime
from ..entities.experiment import Experiment

class ValidationService:
    """数据验证服务类"""
    
    @staticmethod
    def validate_experiment(experiment: Experiment) -> Tuple[bool, List[str]]:
        """验证实验数据的完整性和有效性"""
        errors = []
        
        # 验证必填字段
        if not experiment.name or not experiment.name.strip():
            errors.append("实验名称不能为空")
        
        if not experiment.center or not experiment.center.strip():
            errors.append("中心名称不能为空")
        
        if not experiment.date or not experiment.date.strip():
            errors.append("实验日期不能为空")
        
        if not experiment.model_type or not experiment.model_type.strip():
            errors.append("体模类型不能为空")
        
        # 验证日期格式
        if experiment.date:
            if not ValidationService._is_valid_date_format(experiment.date):
                errors.append("日期格式无效，请使用 YYYY-MM-DD 格式")
        
        # 验证参数
        params_errors = ValidationService._validate_parameters(experiment.parameters)
        errors.extend(params_errors)
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _is_valid_date_format(date_str: str) -> bool:
        """验证日期格式是否为 YYYY-MM-DD"""
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False
    
    @staticmethod
    def _validate_parameters(parameters: Dict[str, Any]) -> List[str]:
        """验证实验参数"""
        errors = []
        
        # 验证体积
        volume = parameters.get("volume", 0)
        if volume is not None:
            try:
                volume_float = float(volume)
                if volume_float < 0:
                    errors.append("容器体积不能为负数")
            except (ValueError, TypeError):
                errors.append("容器体积必须是有效数字")
        
        # 验证目标活度
        target_activity = parameters.get("target_activity", 0)
        if target_activity is not None:
            try:
                activity_float = float(target_activity)
                if activity_float < 0:
                    errors.append("目标活度不能为负数")
            except (ValueError, TypeError):
                errors.append("目标活度必须是有效数字")
        
        # 验证机器时间差
        machine_time_diff = parameters.get("machine_time_diff", 0)
        if machine_time_diff is not None:
            try:
                float(machine_time_diff)
            except (ValueError, TypeError):
                errors.append("机器时间差必须是有效数字")
        
        return errors
    
    @staticmethod
    def validate_activity_value(activity: str) -> Tuple[bool, str]:
        """验证活度值"""
        if not activity or not activity.strip():
            return False, "活度值不能为空"
        
        try:
            activity_float = float(activity)
            if activity_float < 0:
                return False, "活度值不能为负数"
            if activity_float > 10000:  # 设定一个合理的上限
                return False, "活度值过大，请检查输入"
            return True, ""
        except ValueError:
            return False, "活度值必须是有效数字"
    
    @staticmethod
    def validate_time_format(time_str: str) -> Tuple[bool, str]:
        """验证时间格式 HH:MM"""
        if not time_str or not time_str.strip():
            return False, "时间不能为空"
        
        pattern = r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$'
        if not re.match(pattern, time_str):
            return False, "时间格式无效，请使用 HH:MM 格式"
        
        return True, "" 
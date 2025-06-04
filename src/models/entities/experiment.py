# src/models/entities/experiment.py

import uuid
from datetime import datetime
import pytz

class Experiment:
    def __init__(self, name, center, model_type, created_at=None, parameters=None, experiment_id=None, id=None):
        # 兼容新旧字段命名
        self.experiment_id = experiment_id or id or str(uuid.uuid4())
        self.id = self.experiment_id  # 兼容性别名
        self.name = name
        self.center = center
        self.model_type = model_type
        
        # 处理created_at，确保返回datetime对象
        if isinstance(created_at, datetime):
            self.created_at = created_at
        elif isinstance(created_at, str):
            self.created_at = self._parse_datetime_from_string(created_at)
        else:
            self.created_at = self._get_current_beijing_time()
            
        # 生成date字段（从created_at提取日期）
        self.date = self.created_at.strftime("%Y-%m-%d")
        
        self.parameters = parameters or {}
        
        # 确保parameters包含必要的默认字段
        self.parameters.setdefault("remark", "")
        self.parameters.setdefault("isotope", "Ga-68")
        self.parameters.setdefault("device_model", "")
        self.parameters.setdefault("activity_unit", "mCi")

    def _get_current_beijing_time(self):
        """获取当前北京时间"""
        tz = pytz.timezone("Asia/Shanghai")
        return datetime.now(tz)

    def _parse_datetime_from_string(self, date_str):
        """从字符串解析datetime对象"""
        tz = pytz.timezone("Asia/Shanghai")
        try:
            # 尝试解析ISO格式 "2025-05-31T23:55:21"
            dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")
            return tz.localize(dt)
        except ValueError:
            try:
                # 尝试解析日期格式 "2025-05-12"
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                return tz.localize(dt)
            except ValueError:
                # 解析失败，返回当前时间
                return self._get_current_beijing_time()

    @classmethod
    def from_dict(cls, data):
        """从字典创建Experiment对象"""
        experiment = cls(
            name=data.get("name", ""),
            center=data.get("center", ""),
            model_type=data.get("model_type", ""),
            created_at=data.get("created_at"),
            parameters=data.get("parameters", {}),
            experiment_id=data.get("id") or data.get("experiment_id")  # 兼容两种字段名
        )
        
        # 兼容旧数据：如果date在顶层数据中，使用它
        if "date" in data:
            try:
                # 尝试从日期字符串重新解析created_at
                date_str = data["date"]
                if date_str:
                    dt = datetime.strptime(date_str, "%Y-%m-%d")
                    tz = pytz.timezone("Asia/Shanghai")
                    experiment.created_at = tz.localize(dt)
                    experiment.date = date_str
            except ValueError:
                pass
        
        # 兼容旧数据：如果remark在顶层，迁移到parameters中
        if "remark" in data and "remark" not in experiment.parameters:
            experiment.parameters["remark"] = data["remark"]
            
        return experiment

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.experiment_id,
            "name": self.name,
            "center": self.center,
            "date": self.date,
            "model_type": self.model_type,
            "created_at": self.created_at.strftime("%Y-%m-%dT%H:%M:%S") if isinstance(self.created_at, datetime) else self.created_at,
            "parameters": self.parameters
        } 
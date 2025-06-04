# src/config/settings.py

import os
import json
from typing import Dict, Any, Optional
from ..utils.file_utils import FileUtils

class AppSettings:
    """应用程序设置管理类"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = os.path.join(os.getcwd(), config_file)
        self._settings = self._load_default_settings()
        self.load_settings()
    
    def _load_default_settings(self) -> Dict[str, Any]:
        """加载默认设置"""
        return {
            "window": {
                "width": 1600,
                "height": 900,
                "maximized": False,
                "position": {"x": 100, "y": 100}
            },
            "ui": {
                "theme": "modern",
                "font_size": 12,
                "language": "zh_CN"
            },
            "experiment": {
                "default_isotope": "Ga-68",
                "default_activity_unit": "MBq",
                "auto_save": True,
                "backup_count": 10
            },
            "calculation": {
                "decimal_places": 2,
                "show_intermediate_steps": True,
                "auto_refresh_interval": 5  # 秒
            },
            "export": {
                "default_format": "csv",
                "include_timestamp": True,
                "export_path": "exports"
            },
            "recent_files": [],
            "recent_experiments": []
        }
    
    def load_settings(self) -> None:
        """从文件加载设置"""
        settings_data = FileUtils.read_json_file(self.config_file)
        if settings_data:
            self._merge_settings(settings_data)
    
    def save_settings(self) -> bool:
        """保存设置到文件"""
        return FileUtils.write_json_file(self.config_file, self._settings, backup=False)
    
    def _merge_settings(self, new_settings: Dict[str, Any]) -> None:
        """合并新设置，保留默认值"""
        def merge_dict(default: dict, new: dict) -> dict:
            for key, value in new.items():
                if key in default:
                    if isinstance(default[key], dict) and isinstance(value, dict):
                        merge_dict(default[key], value)
                    else:
                        default[key] = value
                else:
                    default[key] = value
            return default
        
        merge_dict(self._settings, new_settings)
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取设置值，支持点分隔的嵌套键"""
        keys = key.split('.')
        value = self._settings
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """设置值，支持点分隔的嵌套键"""
        keys = key.split('.')
        target = self._settings
        
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        
        target[keys[-1]] = value
    
    def get_window_settings(self) -> Dict[str, Any]:
        """获取窗口设置"""
        return self.get("window", {})
    
    def set_window_settings(self, width: int, height: int, maximized: bool, x: int, y: int) -> None:
        """设置窗口设置"""
        self.set("window.width", width)
        self.set("window.height", height)
        self.set("window.maximized", maximized)
        self.set("window.position.x", x)
        self.set("window.position.y", y)
    
    def add_recent_experiment(self, experiment_id: str, experiment_name: str) -> None:
        """添加最近实验"""
        recent = self.get("recent_experiments", [])
        
        # 移除已存在的记录
        recent = [item for item in recent if item.get("id") != experiment_id]
        
        # 添加到开头
        recent.insert(0, {
            "id": experiment_id,
            "name": experiment_name,
            "timestamp": FileUtils.get_current_timestamp()
        })
        
        # 限制数量
        max_recent = 10
        if len(recent) > max_recent:
            recent = recent[:max_recent]
        
        self.set("recent_experiments", recent)
    
    def get_recent_experiments(self) -> list:
        """获取最近实验列表"""
        return self.get("recent_experiments", [])
    
    def clear_recent_experiments(self) -> None:
        """清空最近实验列表"""
        self.set("recent_experiments", [])

# 全局设置实例
app_settings = AppSettings() 
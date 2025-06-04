# src/models/services/export_service.py

import csv
import os
from typing import List
from ..entities.experiment import Experiment
from ...utils.time_utils import get_current_beijing_time

class ExportService:
    """数据导出服务类"""
    
    @staticmethod
    def export_experiments_to_csv(experiments: List[Experiment], filename: str = None) -> str:
        """导出实验数据到 CSV"""
        if filename is None:
            timestamp = get_current_beijing_time().strftime("%Y%m%d_%H%M%S")
            filename = f"experiments_{timestamp}.csv"
        
        try:
            with open(filename, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "实验名称", "中心", "日期", "体模类型", "容器体积 (L)",
                    "目标活度 (MBq)", "机器时间差 (秒)", "设备型号", "备注"
                ])
                for exp in experiments:
                    writer.writerow([
                        exp.name,
                        exp.center,
                        exp.date,
                        exp.model_type,
                        exp.parameters.get("volume", 0.0),
                        exp.parameters.get("target_activity", 0.0),
                        exp.parameters.get("machine_time_diff", 0.0),
                        exp.parameters.get("device_model", ""),
                        exp.parameters.get("remark", "")
                    ])
            return filename
        except Exception as e:
            print(f"导出 CSV 失败: {e}")
            raise
    
    @staticmethod
    def export_experiment_report(experiment: Experiment, filename: str = None) -> str:
        """导出单个实验的详细报告"""
        if filename is None:
            timestamp = get_current_beijing_time().strftime("%Y%m%d_%H%M%S")
            filename = f"experiment_report_{experiment.name}_{timestamp}.txt"
        
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"实验报告\n")
                f.write(f"=" * 50 + "\n")
                f.write(f"实验名称: {experiment.name}\n")
                f.write(f"中心名称: {experiment.center}\n")
                f.write(f"实验日期: {experiment.date}\n")
                f.write(f"体模类型: {experiment.model_type}\n")
                f.write(f"创建时间: {experiment.created_at}\n")
                f.write(f"\n参数详情:\n")
                f.write(f"-" * 30 + "\n")
                for key, value in experiment.parameters.items():
                    f.write(f"{key}: {value}\n")
            return filename
        except Exception as e:
            print(f"导出报告失败: {e}")
            raise 
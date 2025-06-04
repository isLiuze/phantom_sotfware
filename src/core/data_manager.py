# src/core/data_manager.py

import os
import glob
import json
import logging
import re
from src.models.entities.experiment import Experiment

logger = logging.getLogger(__name__)

class DataManager:
    def __init__(self):
        """
        初始化 DataManager，确保 experiments 目录存在，用来存放所有 JSON 文件。
        """
        # 使用绝对路径确保在正确位置
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        self.data_dir = os.path.join(project_root, "experiments")
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            logger.info(f"创建实验数据目录: {self.data_dir}")

    def _sanitize(self, text: str) -> str:
        """
        将任意字符串转换为文件名安全形式：替换非法字符，并把空白换成下划线。
        """
        if not isinstance(text, str):
            return "_"
        clean = re.sub(r'[<>:"/\\|?*]', '_', text)    # Windows/Unix 禁用字符替换为 _
        clean = re.sub(r'\s+', '_', clean.strip())     # 连续空格替换为单个 _
        return clean or "_"

    def load_experiments(self) -> list:
        """
        扫描 data_dir 目录下所有 .json 文件，将其解析为 Experiment 对象并返回列表。
        同时，将该文件路径保存在 exp._file_path 中，便于后续直接删除/覆盖。
        """
        experiments = []
        pattern = os.path.join(self.data_dir, "*.json")
        logger.info(f"加载 JSON 文件，模式: {pattern}")

        for file_path in glob.glob(pattern):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                logger.error(f"读取或解析失败: {file_path}，错误: {e}")
                continue

            # 检查字段完整性（兼容新旧字段名）
            required_fields = ["name", "center", "model_type", "parameters"]
            if "date" not in data and "created_at" in data:
                data["date"] = data["created_at"]
            elif "created_at" not in data and "date" in data:
                data["created_at"] = data["date"]
                
            if not all(k in data for k in required_fields):
                logger.warning(f"文件缺少必要字段，跳过: {file_path}")
                continue

            try:
                exp = Experiment.from_dict(data)
            except Exception as e:
                logger.error(f"Experiment.from_dict 失败: {file_path}，错误: {e}")
                continue

            # 将文件路径记录在 Experiment 对象里
            exp._file_path = file_path
            experiments.append(exp)
            logger.info(f"成功加载实验: {file_path}，name={exp.name}")

        logger.info(f"共加载 {len(experiments)} 个实验")
        return experiments

    def save_experiment(self, experiment: Experiment) -> None:
        """
        保存（新建或更新）一个 Experiment：
        1. 如果 experiment._file_path 存在且文件存在，则先删除旧文件（覆盖式保存）。
        2. 根据 experiment.name, center, date, model_type 生成新的文件名。
        3. 将 experiment.to_dict() 写入新文件，并把新文件路径赋值给 exp._file_path。
        """
        # 1. 如果对象已有 _file_path（旧文件路径），则删除它以便覆盖
        old_path = getattr(experiment, "_file_path", None)
        if isinstance(old_path, str) and os.path.isfile(old_path):
            try:
                os.remove(old_path)
                logger.debug(f"删除旧实验文件: {old_path}")
            except Exception as e:
                logger.error(f"删除旧文件失败: {old_path}，错误: {e}")

        # 2. 构造新文件名基础
        date_str = experiment.date if hasattr(experiment, 'date') else str(experiment.created_at)[:10]
        base_name = (
            f"{self._sanitize(experiment.name)}_"
            f"{self._sanitize(experiment.center)}_"
            f"{self._sanitize(date_str)}_"
            f"{self._sanitize(experiment.model_type)}"
        )
        filename = f"{base_name}.json"
        full_path = os.path.join(self.data_dir, filename)

        # 如果目标路径被占用，在末尾加后缀 "_1", "_2" ...
        suffix = 1
        while os.path.exists(full_path):
            filename = f"{base_name}_{suffix}.json"
            full_path = os.path.join(self.data_dir, filename)
            suffix += 1

        # 3. 写入 JSON 文件
        payload = experiment.to_dict()
        try:
            with open(full_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            logger.info(f"保存实验: {full_path}")
            # 更新 experiment._file_path
            experiment._file_path = full_path
        except Exception as e:
            logger.error(f"保存失败: {full_path}，错误: {e}")
            raise

    def delete_experiment(self, experiment: Experiment) -> None:
        """
        删除某个 Experiment 对应的 JSON 文件：
        直接读取 exp._file_path，若文件存在，则删除；否则仅发出警告。
        """
        path = getattr(experiment, "_file_path", None)
        if isinstance(path, str) and os.path.isfile(path):
            try:
                os.remove(path)
                logger.info(f"已删除实验文件: {path}")
            except Exception as e:
                logger.error(f"删除文件失败: {path}，错误: {e}")
                raise
        else:
            logger.warning(f"无法删除: 找不到 experiment._file_path={path}")

    def save_all_data(self, experiments=None):
        """保存所有实验数据"""
        if experiments is None:
            # 如果没有传入experiments参数，从文件加载当前的实验
            experiments = self.load_experiments()
            
        for experiment in experiments:
            try:
                self.save_experiment(experiment)
            except Exception as e:
                logger.error(f"保存实验失败 {experiment.name}: {e}")

    def get_experiments(self):
        """获取所有实验数据"""
        return self.load_experiments() 
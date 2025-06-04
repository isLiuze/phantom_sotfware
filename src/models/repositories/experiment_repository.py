# src/models/repositories/experiment_repository.py

import os
import glob
import json
import logging
import re
from typing import List, Optional
from .base_repository import BaseRepository
from ..entities.experiment import Experiment

logger = logging.getLogger(__name__)

class ExperimentRepository(BaseRepository[Experiment]):
    def __init__(self):
        """
        初始化 ExperimentRepository，确保 experiments 目录存在，用来存放所有 JSON 文件。
        """
        # 获取当前文件的目录，然后向上找到TiMo_app_v2根目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # current_dir是 .../TiMo_app_v2/src/models/repositories
        # 需要向上3级到达 TiMo_app_v2
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        self.data_dir = os.path.join(project_root, "experiments")
        
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            logger.info(f"创建实验数据目录: {self.data_dir}")
        else:
            logger.info(f"使用实验数据目录: {self.data_dir}")

    def _sanitize(self, text: str) -> str:
        """
        将任意字符串转换为文件名安全形式：替换非法字符，并把空白换成下划线。
        """
        if not isinstance(text, str):
            return "_"
        clean = re.sub(r'[<>:"/\\|?*]', '_', text)    # Windows/Unix 禁用字符替换为 _
        clean = re.sub(r'\s+', '_', clean.strip())     # 连续空格替换为单个 _
        return clean or "_"

    def get_all(self) -> List[Experiment]:
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

            # 检查字段完整性
            if not all(k in data for k in ("name", "center", "date", "model_type", "parameters")):
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

    def get_by_id(self, id: str) -> Optional[Experiment]:
        """根据ID获取实验"""
        experiments = self.get_all()
        for exp in experiments:
            if exp.id == id:
                return exp
        return None

    def save(self, experiment: Experiment) -> None:
        """
        保存（新建或更新）一个 Experiment：
        1. 如果 experiment._file_path 存在且文件存在，则先删除旧文件（覆盖式保存）。
        2. 根据 experiment.name, center, date, model_type 生成新的文件名 "{sanitize(name)}_{sanitize(center)}_{sanitize(date)}_{sanitize(model_type)}.json"。
           若该文件名已存在（不同的全路径），自动在末尾追加 "_1"、"_2"… 以防冲突。
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
        base_name = (
            f"{self._sanitize(experiment.name)}_"
            f"{self._sanitize(experiment.center)}_"
            f"{self._sanitize(experiment.date)}_"
            f"{self._sanitize(experiment.model_type)}"
        )
        filename = f"{base_name}.json"
        full_path = os.path.join(self.data_dir, filename)

        # 如果目标路径被占用（可能是刚才删的不彻底或其他同名实验），在末尾加后缀 "_1", "_2" ...
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

    def delete(self, experiment: Experiment) -> None:
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

    def delete_by_id(self, id: str) -> None:
        """根据ID删除实验"""
        experiment = self.get_by_id(id)
        if experiment:
            self.delete(experiment)

    def get_all_experiments(self) -> List[Experiment]:
        """获取所有实验 - 提供与MainViewModel兼容的方法名"""
        return self.get_all()
    
    def save_experiment(self, experiment: Experiment) -> None:
        """保存实验 - 提供与MainViewModel兼容的方法名"""
        self.save(experiment)
    
    def delete_experiment(self, experiment_id: str) -> None:
        """删除实验 - 提供与MainViewModel兼容的方法名"""
        self.delete_by_id(experiment_id) 
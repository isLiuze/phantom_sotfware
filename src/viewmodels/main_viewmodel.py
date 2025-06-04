# src/viewmodels/main_viewmodel.py

from PyQt5.QtCore import QObject, pyqtSignal
from typing import Optional, List, Dict, Any, Callable
from ..core.bindings import Property
from ..models.repositories.experiment_repository import ExperimentRepository
from ..models.services.export_service import ExportService
from ..models.entities.experiment import Experiment
from ..utils.time_utils import get_current_beijing_time
import logging
import os
from datetime import datetime


class MainViewModel(QObject):
    """主视图模型 - 管理应用程序的全局状态和业务逻辑"""
    
    # 信号
    error_occurred = pyqtSignal(str)
    status_changed = pyqtSignal(str, int)  # 消息, 超时时间
    experiments_loaded = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        
        # 创建依赖服务
        self.experiment_repository = ExperimentRepository()
        self.export_service = ExportService()
        
        # 可绑定属性
        self.is_busy = Property(False)
        self.current_file = Property("")
        self.has_unsaved_changes = Property(False)
        self.selected_experiment = Property(None)
        self.experiment_count = Property(0)
        self.can_undo = Property(False)
        self.can_redo = Property(False)
        
        # 状态
        self._command_history = []
        self._command_index = -1
        self._experiments = []
        
        # 加载实验数据
        self.load_experiments()
    
    def bind_property(self, property_name: str, callback: Callable):
        """绑定属性更改回调"""
        if hasattr(self, property_name):
            prop = getattr(self, property_name)
            if hasattr(prop, 'bind_to'):
                prop.bind_to(callback)
    
    def get_property_value(self, property_name: str, default=None):
        """获取属性值"""
        if hasattr(self, property_name):
            prop = getattr(self, property_name)
            if hasattr(prop, 'value'):
                return prop.value
        return default
    
    # 文件操作
    def new_project(self):
        """新建项目"""
        self.status_changed.emit("创建新项目", 2000)
    
    def open_project(self):
        """打开项目"""
        self.status_changed.emit("打开项目", 2000)
    
    def save_project(self):
        """保存项目"""
        self.status_changed.emit("保存项目", 2000)
        self.has_unsaved_changes.value = False
    
    def save_as(self):
        """项目另存为"""
        self.status_changed.emit("项目另存为", 2000)
        self.has_unsaved_changes.value = False
    
    def open_recent_file(self, file_path: str):
        """打开最近文件"""
        self.status_changed.emit(f"打开最近文件: {file_path}", 2000)
    
    # 编辑操作
    def undo(self):
        """撤销"""
        if self._command_index > 0:
            self._command_index -= 1
            # 执行撤销操作
            self.status_changed.emit("撤销操作", 2000)
            self._update_undo_redo_state()
    
    def redo(self):
        """重做"""
        if self._command_index < len(self._command_history) - 1:
            self._command_index += 1
            # 执行重做操作
            self.status_changed.emit("重做操作", 2000)
            self._update_undo_redo_state()
    
    def _update_undo_redo_state(self):
        """更新撤销/重做状态"""
        self.can_undo.value = self._command_index > 0
        self.can_redo.value = self._command_index < len(self._command_history) - 1
    
    # 实验操作
    def add_experiment(self):
        """添加实验"""
        self.status_changed.emit("添加新实验", 2000)
    
    def edit_experiment(self):
        """编辑当前选中的实验"""
        if self.selected_experiment.value:
            self.status_changed.emit(f"编辑实验: {self.selected_experiment.value.name}", 2000)
    
    def delete_experiment(self, experiment_id: str):
        """删除实验"""
        try:
            # 从仓库中删除
            self.experiment_repository.delete_experiment(experiment_id)
            
            # 从内存中删除
            self._experiments = [exp for exp in self._experiments if exp.experiment_id != experiment_id]
            self.experiment_count.value = len(self._experiments)
            
            # 标记为未保存
            self.has_unsaved_changes.value = True
            
            self.status_changed.emit("删除实验成功", 2000)
            return True
        except Exception as e:
            self.error_occurred.emit(f"删除实验失败: {str(e)}")
            return False
    
    def duplicate_experiment(self):
        """复制当前选中的实验"""
        if self.selected_experiment.value:
            self.status_changed.emit(f"复制实验: {self.selected_experiment.value.name}", 2000)
    
    def export_experiment(self):
        """导出当前选中的实验"""
        if self.selected_experiment.value:
            self.status_changed.emit(f"导出实验: {self.selected_experiment.value.name}", 2000)
    
    def export_all_experiments(self):
        """导出所有实验"""
        self.status_changed.emit("导出所有实验", 2000)
    
    def create_experiment(self, experiment_data: Dict[str, Any]) -> Optional[Experiment]:
        """创建新实验"""
        try:
            # 创建实验对象
            experiment = Experiment(
                name=experiment_data.get("name", ""),
                center=experiment_data.get("center", ""),
                model_type=experiment_data.get("model_type", ""),
                created_at=get_current_beijing_time()
            )
            
            # 设置参数
            experiment.parameters.update({
                "remark": experiment_data.get("remark", ""),
                "isotope": "Ga-68",
                "volume": 0.0,
                "target_activity": 0.0,
                "machine_time_diff": 0.0,
                "device_model": "",
                "activity_unit": "mCi"
            })
            
            # 添加到仓库
            self.experiment_repository.save_experiment(experiment)
            
            # 更新内部状态
            self._experiments.append(experiment)
            self.experiment_count.value = len(self._experiments)
            
            # 标记为未保存
            self.has_unsaved_changes.value = True
            
            # 通知UI
            self.status_changed.emit(f"已创建实验: {experiment.name}", 2000)
            
            return experiment
        except Exception as e:
            self.error_occurred.emit(f"创建实验失败: {str(e)}")
            logging.error(f"创建实验失败: {e}")
            return None
    
    def get_experiments(self) -> List[Experiment]:
        """获取所有实验列表"""
        return self._experiments.copy()
    
    def save_all_data(self):
        """保存所有数据"""
        try:
            # 保存所有实验
            for experiment in self._experiments:
                self.experiment_repository.save_experiment(experiment)
            
            self.has_unsaved_changes.value = False
            self.status_changed.emit("数据保存成功", 2000)
            
        except Exception as e:
            self.error_occurred.emit(f"保存数据失败: {str(e)}")
            logging.error(f"保存数据失败: {e}")
    
    def get_current_time_str(self):
        """获取当前时间字符串"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 视图操作
    def refresh(self):
        """刷新数据"""
        self.status_changed.emit("正在刷新数据...")
        # 重新加载实验数据的逻辑
        self.status_changed.emit("数据刷新完成")
    
    def change_theme(self, theme_name: str):
        """更改主题"""
        self.status_changed.emit(f"已切换到主题: {theme_name}", 2000)
    
    # 工具操作
    def show_activity_calculator(self):
        """显示活度计算器"""
        self.status_changed.emit("打开活度计算器", 2000)
    
    def show_nuclide_info(self):
        """显示核素信息"""
        self.status_changed.emit("打开核素信息", 2000)
    
    def show_import_wizard(self):
        """显示导入向导"""
        self.status_changed.emit("打开导入向导", 2000)
    
    def show_batch_processor(self):
        """显示批处理工具"""
        self.status_changed.emit("打开批处理工具", 2000)
    
    def show_settings(self):
        """显示设置"""
        self.status_changed.emit("打开设置", 2000)
    
    # 帮助操作
    def show_help(self):
        """显示帮助"""
        self.status_changed.emit("打开帮助", 2000)
    
    def show_shortcuts(self):
        """显示快捷键"""
        self.status_changed.emit("显示快捷键", 2000)
    
    def check_updates(self):
        """检查更新"""
        self.status_changed.emit("检查更新", 2000)
    
    def show_about(self):
        """显示关于"""
        self.status_changed.emit("关于应用", 2000)
    
    # 数据加载
    def load_experiments(self):
        """加载实验数据"""
        try:
            self.is_busy.value = True
            
            # 从仓库加载所有实验
            self._experiments = self.experiment_repository.get_all_experiments()
            self.experiment_count.value = len(self._experiments)
            
            # 发送信号
            self.experiments_loaded.emit(self._experiments)
            
            logging.info(f"加载了 {len(self._experiments)} 个实验")
            
        except Exception as e:
            self.error_occurred.emit(f"加载实验失败: {str(e)}")
            logging.error(f"加载实验失败: {e}")
            self._experiments = []
            
        finally:
            self.is_busy.value = False
    
    # 清理
    def cleanup(self):
        """清理资源"""
        self.status_changed.emit("正在清理资源...")
        # 清理逻辑
        self.status_changed.emit("资源清理完成")
    
    def exit(self):
        """退出应用"""
        self.cleanup()
        self.status_changed.emit("正在退出应用", 1000)

    def set_experiments(self, experiments):
        """设置实验列表"""
        self._experiments = experiments
        self.experiments_loaded.emit(experiments)

    def refresh(self):
        """刷新数据"""
        self.status_changed.emit("正在刷新数据...")
        # 重新加载实验数据的逻辑
        self.status_changed.emit("数据刷新完成")
        
    def cleanup(self):
        """清理资源"""
        self.status_changed.emit("正在清理资源...")
        # 清理逻辑
        self.status_changed.emit("资源清理完成") 
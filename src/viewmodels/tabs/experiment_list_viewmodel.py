from PyQt5.QtCore import QObject, pyqtSignal
from typing import List, Optional, Dict
from ...core.bindings import Property, ObservableList
from ...models.entities.experiment import Experiment
from ...models.repositories.experiment_repository import ExperimentRepository
from ...models.services.export_service import ExportService


class ExperimentListViewModel(QObject):
    """实验列表标签页的ViewModel"""
    
    # 信号
    experiment_selected = pyqtSignal(object)
    filter_changed = pyqtSignal()
    status_message = pyqtSignal(str, int)  # 消息, 超时(ms)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, experiment_repository: ExperimentRepository, export_service: ExportService):
        super().__init__()
        self.experiment_repository = experiment_repository
        self.export_service = export_service
        
        # 数据属性
        self.experiments = ObservableList()
        self.selected_experiment = Property(None)
        self.search_text = Property("")
        self.filter_nuclide = Property("全部")
        
        # 状态属性
        self.is_loading = Property(False)
        self.total_experiments = Property(0)
        self.filtered_count = Property(0)
        
        # 绑定搜索和筛选
        self._bind_filtering()
        
        # 初始化加载
        self.refresh_experiments()
    
    def _bind_filtering(self):
        """绑定搜索和筛选功能"""
        # 属性变化时应用过滤
        self.search_text.bind_to(lambda _: self._apply_filter())
        self.filter_nuclide.bind_to(lambda _: self._apply_filter())
    
    def _apply_filter(self):
        """应用过滤条件"""
        try:
            all_experiments = list(self.experiments)
            filtered = all_experiments
            
            # 应用搜索过滤
            if self.search_text.value and self.search_text.value.strip():
                search_term = self.search_text.value.strip().lower()
                filtered = [exp for exp in filtered 
                          if self._experiment_matches_search(exp, search_term)]
            
            # 应用核素过滤
            if self.filter_nuclide.value and self.filter_nuclide.value != "全部":
                filtered = [exp for exp in filtered 
                          if exp.parameters.get("isotope") == self.filter_nuclide.value]
            
            # 更新计数
            self.filtered_count.value = len(filtered)
            
            # 触发过滤变化事件
            self.filter_changed.emit()
            
            return filtered
        except Exception as e:
            self.error_occurred.emit(f"应用过滤失败: {str(e)}")
            return all_experiments
    
    def _experiment_matches_search(self, experiment: Experiment, search_term: str) -> bool:
        """检查实验是否匹配搜索条件"""
        if not search_term:
            return True
        
        # 搜索实验名称、中心名称、核素等字段
        searchable_fields = [
            experiment.name.lower(),
            experiment.center.lower(),
            experiment.model_type.lower(),
            str(experiment.parameters.get("isotope", "")).lower(),
            str(experiment.parameters.get("device_model", "")).lower(),
            str(experiment.parameters.get("remark", "")).lower()
        ]
        
        return any(search_term in field for field in searchable_fields if field)
    
    def refresh_experiments(self):
        """刷新实验列表"""
        self.is_loading.value = True
        try:
            all_experiments = self.experiment_repository.get_all_experiments()
            
            # 更新列表
            self.experiments.clear()
            for exp in all_experiments:
                self.experiments.append(exp)
            
            # 更新计数
            self.total_experiments.value = len(all_experiments)
            self.filtered_count.value = len(all_experiments)
            
            # 应用过滤
            if self.search_text.value or self.filter_nuclide.value != "全部":
                self._apply_filter()
                
            # 发送状态消息
            self.status_message.emit(f"已加载 {len(all_experiments)} 个实验", 2000)
            
        except Exception as e:
            self.error_occurred.emit(f"刷新实验列表失败: {str(e)}")
        finally:
            self.is_loading.value = False
    
    def get_filtered_experiments(self) -> List[Experiment]:
        """获取过滤后的实验列表"""
        return self._apply_filter()
    
    def get_available_nuclides(self) -> List[str]:
        """获取所有实验中使用的核素列表"""
        nuclides = set()
        for experiment in self.experiments:
            isotope = experiment.parameters.get("isotope")
            if isotope:
                nuclides.add(isotope)
        return ["全部"] + sorted(list(nuclides))
    
    # 数据操作方法
    def _add_experiment(self):
        """添加新实验"""
        self.status_message.emit("添加新实验功能尚未实现", 2000)
    
    def _edit_experiment(self):
        """编辑选中的实验"""
        if self.selected_experiment.value:
            self.status_message.emit(f"编辑实验: {self.selected_experiment.value.name}", 2000)
    
    def _delete_experiment(self):
        """删除选中的实验"""
        if self.selected_experiment.value:
            self.status_message.emit(f"删除实验: {self.selected_experiment.value.name}", 2000)
    
    def _confirm_delete_experiment(self, experiment: Experiment):
        """确认删除实验"""
        try:
            self.experiment_repository.delete_experiment(experiment.id)
            # 从列表中移除
            for i, exp in enumerate(self.experiments):
                if exp.id == experiment.id:
                    self.experiments.remove(exp)
                    break
            
            # 更新计数
            self.total_experiments.value = len(self.experiments)
            self._apply_filter()
            
            # 重置选中项
            if self.selected_experiment.value and self.selected_experiment.value.id == experiment.id:
                self.selected_experiment.value = None
            
            self.status_message.emit(f"已删除实验: {experiment.name}", 2000)
        except Exception as e:
            self.error_occurred.emit(f"删除实验失败: {str(e)}")
    
    def _duplicate_experiment(self):
        """复制选中的实验"""
        if self.selected_experiment.value:
            self.status_message.emit("复制实验功能尚未实现", 2000)
    
    def _export_experiment(self):
        """导出选中的实验"""
        if self.selected_experiment.value:
            self.status_message.emit("导出实验功能尚未实现", 2000)
    
    def _export_all_experiments(self):
        """导出所有实验"""
        if self.experiments:
            self.status_message.emit("导出所有实验功能尚未实现", 2000)
        else:
            self.status_message.emit("没有可导出的实验", 2000) 
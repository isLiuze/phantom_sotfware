from typing import Optional, List
from datetime import datetime
from ...core.bindings import Property, Command
from ...core.validators import ExperimentValidator
from ...core.events import EventBus
from ...models.entities.experiment import Experiment
from ...models.entities.syringe import Syringe
from ...models.entities.activity_preset import ActivityPreset
from ...models.services.validation_service import ValidationService
from ..base_viewmodel import BaseViewModel


class AddExperimentViewModel(BaseViewModel):
    """添加实验对话框的ViewModel"""
    
    def __init__(self, validation_service: ValidationService):
        super().__init__()
        self.validation_service = validation_service
        
        # 输入字段属性
        self.experiment_name = Property("")
        self.nuclide = Property("F-18")
        self.phantom_type = Property("圆柱模体")
        self.description = Property("")
        
        # 验证状态
        self.is_valid = Property(False)
        self.validation_errors = Property({})
        
        # 命令
        self.confirm_command = Command(self._confirm_experiment)
        self.cancel_command = Command(self._cancel)
        
        # 绑定验证
        self._bind_validation()
    
    def _bind_validation(self):
        """绑定输入验证"""
        def validate():
            errors = {}
            
            # 验证实验名称
            if not self.experiment_name.value.strip():
                errors['experiment_name'] = "实验名称不能为空"
            elif len(self.experiment_name.value.strip()) < 2:
                errors['experiment_name'] = "实验名称至少需要2个字符"
            
            # 验证核素
            if not self.nuclide.value:
                errors['nuclide'] = "请选择核素"
            
            # 验证模体类型
            if not self.phantom_type.value:
                errors['phantom_type'] = "请选择模体类型"
            
            self.validation_errors.value = errors
            self.is_valid.value = len(errors) == 0
        
        # 绑定输入字段变化
        self.experiment_name.changed.connect(validate)
        self.nuclide.changed.connect(validate)
        self.phantom_type.changed.connect(validate)
        
        # 初始验证
        validate()
    
    def _confirm_experiment(self):
        """确认创建实验"""
        if not self.is_valid.value:
            return
        
        try:
            # 创建实验对象
            experiment = Experiment(
                name=self.experiment_name.value.strip(),
                nuclide=self.nuclide.value,
                phantom_type=self.phantom_type.value,
                description=self.description.value.strip(),
                created_time=datetime.now(),
                syringes=[]
            )
            
            # 触发实验创建事件
            EventBus.emit('experiment_created', experiment)
            EventBus.emit('dialog_close', True)
            
        except Exception as e:
            self.validation_errors.value = {'general': str(e)}
    
    def _cancel(self):
        """取消操作"""
        EventBus.emit('dialog_close', False)
    
    def get_available_nuclides(self) -> List[str]:
        """获取可用核素列表"""
        from ...core.constants import NUCLIDE_HALF_LIVES
        return list(NUCLIDE_HALF_LIVES.keys())
    
    def get_available_phantom_types(self) -> List[str]:
        """获取可用模体类型"""
        return ["圆柱模体", "椭圆模体", "人体模体", "自定义模体"]
    
    def reset_form(self):
        """重置表单"""
        self.experiment_name.value = ""
        self.nuclide.value = "F-18"
        self.phantom_type.value = "圆柱模体"
        self.description.value = "" 
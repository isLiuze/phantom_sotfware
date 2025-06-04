from typing import Optional, List
from datetime import datetime, timedelta
from ...core.bindings import Property, Command
from ...core.events import EventBus
from ...models.entities.syringe import Syringe
from ...models.services.activity_service import ActivityService
from ..base_viewmodel import BaseViewModel


class AddSyringeViewModel(BaseViewModel):
    """添加分针对话框的ViewModel"""
    
    def __init__(self, activity_service: ActivityService, experiment_nuclide: str):
        super().__init__()
        self.activity_service = activity_service
        self.experiment_nuclide = experiment_nuclide
        
        # 输入字段属性
        self.syringe_number = Property("")
        self.initial_activity = Property("")
        self.initial_time = Property(datetime.now())
        self.unit = Property("MBq")
        self.target_time = Property(datetime.now() + timedelta(hours=1))
        
        # 计算结果
        self.calculated_activity = Property("")
        self.decay_factor = Property("")
        
        # 验证状态
        self.is_valid = Property(False)
        self.validation_errors = Property({})
        
        # 命令
        self.calculate_command = Command(self._calculate_activity)
        self.confirm_command = Command(self._confirm_syringe)
        self.cancel_command = Command(self._cancel)
        
        # 绑定验证和自动计算
        self._bind_validation()
        self._bind_auto_calculation()
    
    def _bind_validation(self):
        """绑定输入验证"""
        def validate():
            errors = {}
            
            # 验证分针编号
            if not self.syringe_number.value.strip():
                errors['syringe_number'] = "分针编号不能为空"
            
            # 验证初始活度
            try:
                activity = float(self.initial_activity.value)
                if activity <= 0:
                    errors['initial_activity'] = "初始活度必须大于0"
            except ValueError:
                if self.initial_activity.value.strip():
                    errors['initial_activity'] = "请输入有效的数值"
                else:
                    errors['initial_activity'] = "初始活度不能为空"
            
            # 验证时间
            if self.target_time.value <= self.initial_time.value:
                errors['target_time'] = "目标时间必须晚于初始时间"
            
            self.validation_errors.value = errors
            self.is_valid.value = len(errors) == 0
        
        # 绑定输入字段变化
        self.syringe_number.changed.connect(validate)
        self.initial_activity.changed.connect(validate)
        self.initial_time.changed.connect(validate)
        self.target_time.changed.connect(validate)
        
        # 初始验证
        validate()
    
    def _bind_auto_calculation(self):
        """绑定自动计算"""
        def auto_calculate():
            if (self.initial_activity.value and 
                self.initial_time.value and 
                self.target_time.value and
                self.target_time.value > self.initial_time.value):
                self._calculate_activity()
        
        self.initial_activity.changed.connect(auto_calculate)
        self.initial_time.changed.connect(auto_calculate)
        self.target_time.changed.connect(auto_calculate)
        self.unit.changed.connect(auto_calculate)
    
    def _calculate_activity(self):
        """计算目标时间的活度"""
        try:
            initial_activity = float(self.initial_activity.value)
            
            # 计算衰减后的活度
            result = self.activity_service.calculate_decay(
                initial_activity=initial_activity,
                initial_time=self.initial_time.value,
                target_time=self.target_time.value,
                nuclide=self.experiment_nuclide,
                unit=self.unit.value
            )
            
            self.calculated_activity.value = f"{result['final_activity']:.2f}"
            self.decay_factor.value = f"{result['decay_factor']:.4f}"
            
        except Exception as e:
            self.calculated_activity.value = "计算错误"
            self.decay_factor.value = "计算错误"
    
    def _confirm_syringe(self):
        """确认添加分针"""
        if not self.is_valid.value:
            return
        
        try:
            # 创建分针对象
            syringe = Syringe(
                number=self.syringe_number.value.strip(),
                initial_activity=float(self.initial_activity.value),
                initial_time=self.initial_time.value,
                unit=self.unit.value,
                target_time=self.target_time.value,
                calculated_activity=float(self.calculated_activity.value) if self.calculated_activity.value != "计算错误" else 0
            )
            
            # 触发分针创建事件
            EventBus.emit('syringe_created', syringe)
            EventBus.emit('dialog_close', True)
            
        except Exception as e:
            self.validation_errors.value = {'general': str(e)}
    
    def _cancel(self):
        """取消操作"""
        EventBus.emit('dialog_close', False)
    
    def get_available_units(self) -> List[str]:
        """获取可用单位列表"""
        from ...core.constants import ACTIVITY_UNITS
        return list(ACTIVITY_UNITS.keys())
    
    def set_preset_time_offset(self, hours: int):
        """设置预设时间偏移"""
        self.target_time.value = self.initial_time.value + timedelta(hours=hours)
    
    def reset_form(self):
        """重置表单"""
        self.syringe_number.value = ""
        self.initial_activity.value = ""
        self.initial_time.value = datetime.now()
        self.target_time.value = datetime.now() + timedelta(hours=1)
        self.calculated_activity.value = ""
        self.decay_factor.value = "" 
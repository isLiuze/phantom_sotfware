from PyQt5.QtCore import QObject, pyqtSignal
from typing import Any, Dict, List
from ..core.bindings import Property, ObservableList
from ..core.events import event_bus, Events

class BaseViewModel(QObject):
    """ViewModel基类，提供数据绑定和事件处理"""
    
    # 通用信号
    property_changed = pyqtSignal(str, object)  # property_name, new_value
    command_executed = pyqtSignal(str, object)  # command_name, result
    error_occurred = pyqtSignal(str)  # error_message
    status_changed = pyqtSignal(str)  # status_message
    
    def __init__(self):
        super().__init__()
        self._properties: Dict[str, Property] = {}
        self._is_busy = Property(False)
        
        # 连接到全局事件总线
        self._connect_events()
    
    def _connect_events(self):
        """连接全局事件"""
        event_bus.error_occurred.connect(self.error_occurred.emit)
        event_bus.status_message.connect(self.status_changed.emit)
    
    def create_property(self, name: str, initial_value: Any = None) -> Property:
        """创建一个新的可观察属性"""
        prop = Property(initial_value)
        prop.value_changed.connect(lambda value: self.property_changed.emit(name, value))
        self._properties[name] = prop
        return prop
    
    def get_property(self, name: str) -> Property:
        """获取属性"""
        if name not in self._properties:
            raise ValueError(f"Property '{name}' not found")
        return self._properties[name]
    
    def set_property_value(self, name: str, value: Any):
        """设置属性值"""
        if name in self._properties:
            self._properties[name].value = value
        else:
            self.create_property(name, value)
    
    def get_property_value(self, name: str, default: Any = None) -> Any:
        """获取属性值"""
        if name in self._properties:
            return self._properties[name].value
        return default
    
    @property
    def is_busy(self) -> bool:
        """是否忙碌状态"""
        return self._is_busy.value
    
    @is_busy.setter
    def is_busy(self, value: bool):
        """设置忙碌状态"""
        self._is_busy.value = value
    
    def bind_property(self, property_name: str, callback):
        """绑定属性变化回调"""
        if property_name in self._properties:
            self._properties[property_name].bind_to(callback)
    
    def execute_command(self, command_name: str, *args, **kwargs):
        """执行命令的基础方法"""
        try:
            self.is_busy = True
            result = self._execute_command_impl(command_name, *args, **kwargs)
            self.command_executed.emit(command_name, result)
            return result
        except Exception as e:
            error_msg = f"执行命令 '{command_name}' 时发生错误: {str(e)}"
            self.error_occurred.emit(error_msg)
            raise
        finally:
            self.is_busy = False
    
    def _execute_command_impl(self, command_name: str, *args, **kwargs):
        """子类应该重写此方法来实现具体的命令"""
        raise NotImplementedError(f"Command '{command_name}' not implemented")
    
    def emit_status(self, message: str):
        """发送状态消息"""
        self.status_changed.emit(message)
        event_bus.status_message.emit(message)
    
    def emit_error(self, error_message: str):
        """发送错误消息"""
        self.error_occurred.emit(error_message)
        event_bus.error_occurred.emit(error_message)
    
    def cleanup(self):
        """清理资源"""
        for prop in self._properties.values():
            prop.deleteLater()
        self._properties.clear() 
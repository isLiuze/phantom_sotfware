# src/core/events.py

from PyQt5.QtCore import QObject, pyqtSignal
from typing import Dict, List, Callable, Any

class EventBus(QObject):
    """事件总线，用于组件间通信"""
    
    # 定义常用事件信号
    experiment_created = pyqtSignal(object)  # experiment
    experiment_updated = pyqtSignal(object)  # experiment
    experiment_deleted = pyqtSignal(object)  # experiment
    experiment_selected = pyqtSignal(object)  # experiment
    
    activity_calculated = pyqtSignal(dict)  # calculation_result
    
    status_message = pyqtSignal(str)  # message
    error_occurred = pyqtSignal(str)  # error_message
    
    def __init__(self):
        super().__init__()
        self._event_handlers: Dict[str, List[Callable]] = {}
    
    def subscribe(self, event_name: str, handler: Callable):
        """订阅事件"""
        if event_name not in self._event_handlers:
            self._event_handlers[event_name] = []
        self._event_handlers[event_name].append(handler)
    
    def unsubscribe(self, event_name: str, handler: Callable):
        """取消订阅事件"""
        if event_name in self._event_handlers:
            if handler in self._event_handlers[event_name]:
                self._event_handlers[event_name].remove(handler)
    
    def publish(self, event_name: str, data: Any = None):
        """发布事件"""
        if event_name in self._event_handlers:
            for handler in self._event_handlers[event_name]:
                try:
                    if data is not None:
                        handler(data)
                    else:
                        handler()
                except Exception as e:
                    print(f"Error in event handler for {event_name}: {e}")
    
    def clear_handlers(self, event_name: str = None):
        """清除事件处理器"""
        if event_name:
            if event_name in self._event_handlers:
                self._event_handlers[event_name].clear()
        else:
            self._event_handlers.clear()

# 全局事件总线实例
event_bus = EventBus()

# 事件名称常量
class Events:
    EXPERIMENT_CREATED = "experiment_created"
    EXPERIMENT_UPDATED = "experiment_updated"
    EXPERIMENT_DELETED = "experiment_deleted"
    EXPERIMENT_SELECTED = "experiment_selected"
    
    ACTIVITY_CALCULATED = "activity_calculated"
    
    STATUS_MESSAGE = "status_message"
    ERROR_OCCURRED = "error_occurred"
    
    # 视图事件
    VIEW_CHANGED = "view_changed"
    TAB_OPENED = "tab_opened"
    TAB_CLOSED = "tab_closed" 
from PyQt5.QtCore import QObject, pyqtSignal
from typing import Any, Callable, Dict, List

class Property(QObject):
    """可观察的属性类，支持数据绑定"""
    
    value_changed = pyqtSignal(object)
    
    def __init__(self, initial_value: Any = None):
        super().__init__()
        self._value = initial_value
        self._observers: List[Callable] = []
    
    @property
    def value(self) -> Any:
        return self._value
    
    @value.setter
    def value(self, new_value: Any):
        if self._value != new_value:
            old_value = self._value
            self._value = new_value
            self.value_changed.emit(new_value)
            self._notify_observers(old_value, new_value)
    
    def bind_to(self, callback: Callable[[Any], None]):
        """绑定值变化回调"""
        self._observers.append(callback)
        # 立即调用一次以设置初始值
        callback(self._value)
    
    def _notify_observers(self, old_value: Any, new_value: Any):
        """通知所有观察者"""
        for observer in self._observers:
            try:
                observer(new_value)
            except Exception as e:
                print(f"Observer callback error: {e}")

class ObservableList(QObject):
    """可观察的列表类"""
    
    item_added = pyqtSignal(object, int)  # item, index
    item_removed = pyqtSignal(object, int)  # item, index
    item_changed = pyqtSignal(object, int)  # item, index
    list_cleared = pyqtSignal()
    
    def __init__(self, initial_items: List[Any] = None):
        super().__init__()
        self._items = initial_items or []
    
    def append(self, item: Any):
        """添加项目"""
        self._items.append(item)
        self.item_added.emit(item, len(self._items) - 1)
    
    def remove(self, item: Any):
        """移除项目"""
        if item in self._items:
            index = self._items.index(item)
            self._items.remove(item)
            self.item_removed.emit(item, index)
    
    def remove_at(self, index: int):
        """根据索引移除项目"""
        if 0 <= index < len(self._items):
            item = self._items.pop(index)
            self.item_removed.emit(item, index)
    
    def clear(self):
        """清空列表"""
        self._items.clear()
        self.list_cleared.emit()
    
    def __getitem__(self, index: int):
        return self._items[index]
    
    def __len__(self):
        return len(self._items)
    
    def __iter__(self):
        return iter(self._items)
    
    @property
    def items(self) -> List[Any]:
        return self._items.copy()

class Command(QObject):
    """命令类，支持撤销/重做"""
    
    executed = pyqtSignal()
    
    def __init__(self, execute_func: Callable, undo_func: Callable = None, description: str = ""):
        super().__init__()
        self.execute_func = execute_func
        self.undo_func = undo_func
        self.description = description
    
    def execute(self):
        """执行命令"""
        if self.execute_func:
            self.execute_func()
            self.executed.emit()
    
    def undo(self):
        """撤销命令"""
        if self.undo_func:
            self.undo_func() 
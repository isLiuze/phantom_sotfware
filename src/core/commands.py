from abc import ABC, abstractmethod
from typing import Any, Optional

class Command(ABC):
    """命令接口"""
    
    @abstractmethod
    def execute(self) -> Any:
        """执行命令"""
        pass
    
    @abstractmethod
    def undo(self) -> Any:
        """撤销命令"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """命令描述"""
        pass

class CreateExperimentCommand(Command):
    """创建实验命令"""
    
    def __init__(self, repository, experiment):
        self.repository = repository
        self.experiment = experiment
        self._executed = False
    
    def execute(self):
        if not self._executed:
            self.repository.save(self.experiment)
            self._executed = True
        return self.experiment
    
    def undo(self):
        if self._executed:
            self.repository.delete(self.experiment)
            self._executed = False
    
    @property
    def description(self) -> str:
        return f"创建实验: {self.experiment.name}"

class UpdateExperimentCommand(Command):
    """更新实验命令"""
    
    def __init__(self, repository, experiment, old_experiment_data):
        self.repository = repository
        self.experiment = experiment
        self.old_experiment_data = old_experiment_data
        self._executed = False
    
    def execute(self):
        if not self._executed:
            self.repository.save(self.experiment)
            self._executed = True
        return self.experiment
    
    def undo(self):
        if self._executed:
            # 恢复旧数据
            self.experiment.name = self.old_experiment_data['name']
            self.experiment.center = self.old_experiment_data['center']
            self.experiment.date = self.old_experiment_data['date']
            self.experiment.model_type = self.old_experiment_data['model_type']
            self.experiment.parameters = self.old_experiment_data['parameters'].copy()
            self.repository.save(self.experiment)
            self._executed = False
    
    @property
    def description(self) -> str:
        return f"更新实验: {self.experiment.name}"

class DeleteExperimentCommand(Command):
    """删除实验命令"""
    
    def __init__(self, repository, experiment):
        self.repository = repository
        self.experiment = experiment
        self._executed = False
    
    def execute(self):
        if not self._executed:
            self.repository.delete(self.experiment)
            self._executed = True
    
    def undo(self):
        if self._executed:
            self.repository.save(self.experiment)
            self._executed = False
    
    @property
    def description(self) -> str:
        return f"删除实验: {self.experiment.name}"

class CommandHistory:
    """命令历史管理器"""
    
    def __init__(self, max_history: int = 50):
        self.max_history = max_history
        self.history = []
        self.current_index = -1
    
    def execute_command(self, command: Command) -> Any:
        """执行命令并添加到历史"""
        result = command.execute()
        
        # 如果当前不在历史的最新位置，删除后面的历史
        if self.current_index < len(self.history) - 1:
            self.history = self.history[:self.current_index + 1]
        
        # 添加新命令
        self.history.append(command)
        self.current_index += 1
        
        # 限制历史大小
        if len(self.history) > self.max_history:
            self.history.pop(0)
            self.current_index -= 1
        
        return result
    
    def undo(self) -> bool:
        """撤销上一个命令"""
        if self.can_undo():
            command = self.history[self.current_index]
            command.undo()
            self.current_index -= 1
            return True
        return False
    
    def redo(self) -> bool:
        """重做下一个命令"""
        if self.can_redo():
            self.current_index += 1
            command = self.history[self.current_index]
            command.execute()
            return True
        return False
    
    def can_undo(self) -> bool:
        """是否可以撤销"""
        return self.current_index >= 0
    
    def can_redo(self) -> bool:
        """是否可以重做"""
        return self.current_index < len(self.history) - 1
    
    def clear(self):
        """清空历史"""
        self.history.clear()
        self.current_index = -1 
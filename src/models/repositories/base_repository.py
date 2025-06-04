from abc import ABC, abstractmethod
from typing import List, Optional, TypeVar, Generic

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    """仓库基类，定义通用的数据访问接口"""
    
    @abstractmethod
    def get_all(self) -> List[T]:
        """获取所有实体"""
        pass
    
    @abstractmethod
    def get_by_id(self, id: str) -> Optional[T]:
        """根据ID获取实体"""
        pass
    
    @abstractmethod
    def save(self, entity: T) -> None:
        """保存实体"""
        pass
    
    @abstractmethod
    def delete(self, entity: T) -> None:
        """删除实体"""
        pass
    
    @abstractmethod
    def delete_by_id(self, id: str) -> None:
        """根据ID删除实体"""
        pass 
from ..entities.nuclide import (
    calculate_decayed_activity,
    calculate_initial_activity, 
    calculate_time_to_target,
    convert_activity_unit
)

class ActivityService:
    """活度计算服务类"""
    
    @staticmethod
    def calculate_decayed_activity(initial_activity: float, time_minutes: float, isotope: str) -> float:
        """计算衰减后的活度"""
        return calculate_decayed_activity(initial_activity, time_minutes, isotope)
    
    @staticmethod
    def calculate_initial_activity(target_activity: float, time_minutes: float, isotope: str) -> float:
        """计算为达到目标活度所需的初始活度"""
        return calculate_initial_activity(target_activity, time_minutes, isotope)
    
    @staticmethod
    def calculate_time_to_target(initial_activity: float, target_activity: float, isotope: str) -> float:
        """计算达到目标活度所需的时间（分钟）"""
        return calculate_time_to_target(initial_activity, target_activity, isotope)
    
    @staticmethod
    def convert_activity_unit(activity: float, from_unit: str, to_unit: str) -> float:
        """转换活度单位"""
        return convert_activity_unit(activity, from_unit, to_unit)
    
    @staticmethod
    def calculate_activity_at_time(initial_activity: float, initial_time: str, 
                                  target_time: str, isotope: str) -> float:
        """计算指定时间点的活度"""
        from ...utils.time_utils import calculate_time_difference
        
        time_diff_minutes = calculate_time_difference(initial_time, target_time)
        return calculate_decayed_activity(initial_activity, time_diff_minutes, isotope) 
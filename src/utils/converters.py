# src/utils/converters.py

from ..core.constants import ACTIVITY_UNITS

class UnitConverter:
    """单位转换工具类"""
    
    @staticmethod
    def convert_activity(value: float, from_unit: str, to_unit: str) -> float:
        """
        转换活度单位
        
        Args:
            value: 活度值
            from_unit: 源单位
            to_unit: 目标单位
            
        Returns:
            转换后的活度值
        """
        # 查找转换因子
        from_factor = None
        to_factor = None
        
        for unit, factor in ACTIVITY_UNITS:
            if unit == from_unit:
                from_factor = factor
            if unit == to_unit:
                to_factor = factor
        
        if from_factor is None:
            raise ValueError(f"不支持的源单位: {from_unit}")
        if to_factor is None:
            raise ValueError(f"不支持的目标单位: {to_unit}")
        
        # 先转换为MBq，再转换为目标单位
        mbq_value = value * from_factor
        return mbq_value / to_factor
    
    @staticmethod
    def get_supported_activity_units() -> list:
        """获取支持的活度单位列表"""
        return [unit for unit, _ in ACTIVITY_UNITS]
    
    @staticmethod
    def format_activity_with_unit(value: float, unit: str, decimals: int = 2) -> str:
        """
        格式化活度值并添加单位
        
        Args:
            value: 活度值
            unit: 单位
            decimals: 小数位数
            
        Returns:
            格式化后的字符串
        """
        return f"{value:.{decimals}f} {unit}"

class TimeConverter:
    """时间转换工具类"""
    
    @staticmethod
    def minutes_to_hours_minutes(minutes: float) -> tuple:
        """
        将分钟转换为小时和分钟
        
        Args:
            minutes: 总分钟数
            
        Returns:
            (小时, 分钟) 元组
        """
        hours = int(minutes // 60)
        remaining_minutes = int(minutes % 60)
        return hours, remaining_minutes
    
    @staticmethod
    def format_duration(minutes: float) -> str:
        """
        格式化时长为易读格式
        
        Args:
            minutes: 分钟数
            
        Returns:
            格式化后的时长字符串
        """
        if minutes < 60:
            return f"{minutes:.1f} 分钟"
        
        hours, mins = TimeConverter.minutes_to_hours_minutes(minutes)
        if hours > 0 and mins > 0:
            return f"{hours} 小时 {mins} 分钟"
        elif hours > 0:
            return f"{hours} 小时"
        else:
            return f"{mins} 分钟" 
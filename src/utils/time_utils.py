from datetime import datetime, timedelta
import pytz

def get_current_beijing_time():
    """获取当前北京时间"""
    tz = pytz.timezone("Asia/Shanghai")
    return datetime.now(tz)

def format_datetime(dt, format_str="%Y-%m-%d %H:%M:%S"):
    """格式化日期时间"""
    return dt.strftime(format_str)

def calculate_time_difference(start_time, end_time):
    """计算两个时间之间的差异，返回分钟数"""
    if isinstance(start_time, str):
        start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
    if isinstance(end_time, str):
        end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
    
    diff = end_time - start_time
    return diff.total_seconds() / 60  # 返回分钟数

def add_minutes(dt, minutes):
    """向日期时间添加分钟数"""
    return dt + timedelta(minutes=minutes) 
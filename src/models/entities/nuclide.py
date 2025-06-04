# src/models/entities/nuclide.py

import numpy as np
from datetime import datetime, timedelta
from ...core.constants import HALF_LIFE_TABLE
from ...utils.time_utils import calculate_time_difference

def calculate_decayed_activity(initial_activity, time_minutes, isotope):
    """
    计算核素衰减后的活度
    
    参数:
    initial_activity: 初始活度
    time_minutes: 衰减时间（分钟）
    isotope: 核素名称
    
    返回:
    衰减后的活度
    """
    try:
        half_life = HALF_LIFE_TABLE[isotope]
        decay_constant = np.log(2) / half_life
        return initial_activity * np.exp(-decay_constant * time_minutes)
    except KeyError:
        raise ValueError(f"未知核素: {isotope}")

def calculate_initial_activity(target_activity, time_minutes, isotope):
    """
    计算为了达到目标活度需要的初始活度
    
    参数:
    target_activity: 目标活度
    time_minutes: 衰减时间（分钟）
    isotope: 核素名称
    
    返回:
    所需的初始活度
    """
    try:
        half_life = HALF_LIFE_TABLE[isotope]
        decay_constant = np.log(2) / half_life
        return target_activity / np.exp(-decay_constant * time_minutes)
    except KeyError:
        raise ValueError(f"未知核素: {isotope}")

def calculate_time_to_target(initial_activity, target_activity, isotope):
    """
    计算达到目标活度所需的时间（分钟）
    
    参数:
    initial_activity: 初始活度
    target_activity: 目标活度
    isotope: 核素名称
    
    返回:
    达到目标活度所需的时间（分钟）
    """
    if initial_activity <= target_activity:
        return 0  # 如果初始活度小于目标活度，无法通过衰减达到
    
    try:
        half_life = HALF_LIFE_TABLE[isotope]
        decay_constant = np.log(2) / half_life
        return np.log(initial_activity / target_activity) / decay_constant
    except KeyError:
        raise ValueError(f"未知核素: {isotope}")

def convert_activity_unit(activity, from_unit, to_unit):
    """
    在不同活度单位之间转换
    
    参数:
    activity: 活度值
    from_unit: 源单位（"MBq", "mCi", "kBq", "Bq"）
    to_unit: 目标单位（"MBq", "mCi", "kBq", "Bq"）
    
    返回:
    转换后的活度值
    """
    from ...core.constants import ACTIVITY_UNITS
    
    # 查找转换因子
    from_factor = next((factor for unit, factor in ACTIVITY_UNITS if unit == from_unit), None)
    to_factor = next((factor for unit, factor in ACTIVITY_UNITS if unit == to_unit), None)
    
    if from_factor is None or to_factor is None:
        raise ValueError(f"不支持的单位转换: {from_unit} -> {to_unit}")
    
    # 转换为MBq，再转换为目标单位
    mbq_value = activity * from_factor
    return mbq_value / to_factor 
# src/core/constants.py

"""项目常量定义"""

# 核素半衰期表（单位：分钟）
HALF_LIFE_TABLE = {
    "Ga-68": 67.71,
    "F-18": 109.8,
    "C-11": 20.39,
    "N-13": 9.97,
    "O-15": 2.04,
    "Rb-82": 1.27,
    "I-124": 6026.4,
    "Cu-64": 762.9,
    "Zr-89": 4699.2,
    "Y-90": 3842.4,
    "Lu-177": 951264.0,
    "Ac-225": 14256.0
}

# 核素列表（从HALF_LIFE_TABLE提取）
ISOTOPE_LIST = list(HALF_LIFE_TABLE.keys())

# 活度单位转换表（相对于MBq的转换因子）
ACTIVITY_UNITS = [
    ("MBq", 1.0),
    ("mCi", 37.0),
    ("kBq", 0.001),
    ("Bq", 0.000001),
    ("GBq", 1000.0),
    ("Ci", 37000.0),
    ("µCi", 0.037)
]

# 体模类型
PHANTOM_TYPES = [
    "Jaszczak",
    "NEMA IQ",
    "Hoffman Brain",
    "Cardiac Phantom",
    "Derenzo",
    "Flood Source",
    "Line Source",
    "Point Source",
    "Uniform Cylinder",
    "ACR PET",
    "自定义"
]

# 设备型号
DEVICE_MODELS = [
    "Siemens Biograph mCT",
    "Siemens Biograph Vision",
    "GE Discovery MI",
    "GE Discovery IQ",
    "Philips Vereos",
    "Philips Gemini TF",
    "Philips Ingenuity TF",
    "Canon Celesteion",
    "United Imaging uEXPLORER",
    "United Imaging uMI 780",
    "其他"
]

# 容器类型
CONTAINER_TYPES = [
    "标准注射器",
    "大注射器",
    "小瓶",
    "大容器",
    "其他"
]

# 容器体积预设（单位：mL）
CONTAINER_VOLUMES = {
    "标准注射器": 10.0,
    "大注射器": 20.0,
    "小瓶": 5.0,
    "大容器": 100.0,
    "其他": 0.0
}

# 数据文件夹
DATA_FOLDERS = {
    "experiments": "data/experiments",
    "exports": "data/exports",
    "logs": "data/logs",
    "temp": "data/temp"
}

# 文件格式
FILE_FORMATS = {
    "experiment": ".json",
    "export": ".csv",
    "backup": ".bak"
}

# 默认配置
DEFAULT_CONFIG = {
    "default_isotope": "Ga-68",
    "default_activity_unit": "MBq",
    "default_volume": 0.0,
    "auto_save": True,
    "auto_save_interval": 60,  # 秒
    "backup_count": 5,
    "theme": "modern"
}

# 表格列配置
TABLE_COLUMNS = {
    "experiment_list": [
        {"name": "实验名称", "width": 200},
        {"name": "中心名称", "width": 150},
        {"name": "日期", "width": 100},
        {"name": "模体类型", "width": 120},
        {"name": "核素", "width": 80},
        {"name": "设备型号", "width": 150},
        {"name": "备注", "width": 200}
    ]
}

# 验证规则
VALIDATION_RULES = {
    "experiment_name": {
        "min_length": 1,
        "max_length": 100,
        "required": True
    },
    "center_name": {
        "min_length": 1,
        "max_length": 100,
        "required": True
    },
    "activity": {
        "min_value": 0.0,
        "max_value": 10000.0,
        "decimal_places": 3
    },
    "volume": {
        "min_value": 0.0,
        "max_value": 1000.0,
        "decimal_places": 3
    }
}

# 样式配置
STYLE_CONFIG = {
    "primary_color": "#1976d2",
    "success_color": "#43a047",
    "warning_color": "#ff9800",
    "danger_color": "#e53935",
    "info_color": "#17a2b8",
    "secondary_color": "#6c757d"
}

# 应用信息
APP_INFO = {
    "name": "TiMo PET 模体实验管理系统",
    "version": "2.0.0",
    "description": "PET模体实验数据管理与分析系统",
    "author": "TiMo团队",
    "license": "MIT",
    "website": "https://github.com/timo-team/timo-app"
} 
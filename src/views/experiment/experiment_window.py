# src/ui/experiment_window.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QLineEdit, QComboBox, QPushButton, QMessageBox, QTabWidget, QDateTimeEdit,
    QFrame, QScrollArea, QSizePolicy
)
from PyQt5.QtGui import QDoubleValidator, QRegExpValidator, QFont
from PyQt5.QtCore import Qt, QTimer, QRegExp, pyqtSignal, QDateTime, QSignalBlocker
from ...core.constants import HALF_LIFE_TABLE, ACTIVITY_UNITS, DEVICE_MODELS
from ...utils.time_utils import get_current_beijing_time, format_datetime
from .experiment_tabs.activity_tab import ActivityTab
from .experiment_tabs.phantom_activity_tab import PhantomActivityTab
from .experiment_tabs.sequence_rebuild_tab import SequenceRebuildTab
from .experiment_tabs.phantom_analysis_tab import PhantomAnalysisTab
from ...models.nuclide import calculate_decayed_activity
from datetime import datetime, timedelta
import pytz
import numpy as np
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class ExperimentWindow(QWidget):
    # 实验更新信号
    experiment_updated = pyqtSignal(object)

    def __init__(self, experiment, parent=None):
        super().__init__(parent)
        self.experiment = experiment
        self.main_window = parent
        
        # 设置默认活度单位为mCi
        self.activity_unit = self.experiment.parameters.get("activity_unit", "mCi")
        if "activity_unit" not in self.experiment.parameters:
            self.experiment.parameters["activity_unit"] = "mCi"
            
        self.scan_time = self._parse_time(self.experiment.parameters.get("scan_time", ""))
        
        # 确保 parameters 中有默认字段
        self.experiment.parameters.setdefault("isotope", "Ga-68")
        self.experiment.parameters.setdefault("volume", 0.0)
        self.experiment.parameters.setdefault("target_activity", 0.0)
        self.experiment.parameters.setdefault("machine_time_diff", 0.0)
        self.experiment.parameters.setdefault("device_model", "")
        self.experiment.parameters.setdefault("remark", "")
        
        self._init_ui()
        self._start_timer()
        logging.info(f"初始化实验窗口: 单位={self.activity_unit}")

    def _init_ui(self):
        # 整个窗口的主垂直布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 添加标题
        title_label = QLabel(f"{self.experiment.name} - {self.experiment.center}")
        title_label.setObjectName("header")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)

        # ———— 第一部分：上方内容区（左侧参数 + 右侧标签页） ————
        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)

        # 左侧：实验参数组 - 使用滚动区域
        param_scroll = QScrollArea()
        param_scroll.setWidgetResizable(True)
        param_scroll.setFrameShape(QFrame.NoFrame)
        param_scroll.setFixedWidth(400)  # 固定宽度
        
        param_container = QWidget()
        param_layout = QVBoxLayout(param_container)
        param_layout.setContentsMargins(0, 0, 0, 0)
        
        left_group = QGroupBox("实验参数")
        left_group.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)  # 固定宽度策略
        left_layout = QGridLayout()
        left_layout.setSpacing(10)
        left_group.setLayout(left_layout)

        # 准备实验参数控件 - 扫描时刻活度从mCi转换显示
        target_mci = self.experiment.parameters.get("target_activity", 0.0)
        disp_target = self.convert_activity(target_mci, "mCi", self.activity_unit) or 0.0
        current_remark = self.experiment.parameters.get("remark", "")

        # 创建输入控件
        self.name_input = QLineEdit(self.experiment.name)
        self.center_name = QLineEdit(self.experiment.center)
        self.phantom_display = QLineEdit(self.experiment.model_type)
        self.phantom_display.setReadOnly(True)
        self.volume = QLineEdit(str(self.experiment.parameters.get("volume", 0.0)))
        self.isotope = QComboBox()
        self.isotope.addItems(list(HALF_LIFE_TABLE.keys()))
        self.isotope.setCurrentText(self.experiment.parameters.get("isotope", "Ga-68"))
        
        self.half_display = QLineEdit()
        self.half_display.setReadOnly(True)
        
        self.device_model = QComboBox()
        self.device_model.addItems(DEVICE_MODELS)
        self.device_model.setCurrentText(self.experiment.parameters.get("device_model", ""))
        self.machine_time_diff = QLineEdit(str(self.experiment.parameters.get("machine_time_diff", 0.0)))
        self.target_activity = QLineEdit("" if disp_target == 0.0 else f"{disp_target:.3f}")
        self.unit_combo = QComboBox()
        self.unit_combo.addItems([u for u, _ in ACTIVITY_UNITS])
        self.unit_combo.setCurrentText(self.activity_unit)
        self.remark = QLineEdit(current_remark)

        # 添加参数到布局
        params = [
            ("实验名称:", self.name_input),
            ("中心名称:", self.center_name),
            ("模体类型:", self.phantom_display),
            ("模体体积 (L):", self.volume),
            ("核素:", None),  # 特殊处理
            ("设备型号:", self.device_model),
            ("机器时间差 (s):", self.machine_time_diff),
            (f"扫描时刻活度 ({self.activity_unit}):", self.target_activity),
            ("活度单位:", self.unit_combo),
            ("备注:", self.remark)
        ]

        row = 0
        self.target_label = None
        for label_text, widget in params:
            if label_text == "核素:":
                # 核素特殊布局
                iso_lab = QLabel("核素:")
                iso_lab.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.update_half_life()

                hl_box = QHBoxLayout()
                hl_box.addWidget(self.isotope)
                hl_box.addWidget(QLabel("半衰期:"))
                hl_box.addWidget(self.half_display)
                hl_box.setSpacing(5)

                left_layout.addWidget(iso_lab, row, 0)
                left_layout.addLayout(hl_box, row, 1)

                # 连接信号
                self.isotope.currentTextChanged.connect(self.update_half_life)
                self.isotope.currentTextChanged.connect(self.save_parameters)
            else:
                lbl = QLabel(label_text)
                lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                left_layout.addWidget(lbl, row, 0)
                left_layout.addWidget(widget, row, 1)

                if isinstance(widget, QLineEdit):
                    widget.setPlaceholderText("请输入...")

                if label_text.startswith("扫描时刻活度"):
                    self.target_label = lbl
                    # 为扫描时刻活度设置根据单位的验证器
                    if self.activity_unit == "mCi":
                        validator = QDoubleValidator(0.0, 1000.0, 3)
                    else:
                        validator = QDoubleValidator(0.0, 100000.0, 3)
                    validator.setNotation(QDoubleValidator.StandardNotation)
                    widget.setValidator(validator)
                    # 连接信号
                    widget.textChanged.connect(self.on_target_activity_changed)
                elif isinstance(widget, QComboBox):
                    widget.currentTextChanged.connect(self.save_parameters)
                else:
                    # 数值输入框验证
                    if label_text in ["模体体积 (L):", "机器时间差 (s):"]:
                        validator = QDoubleValidator(-1000.0, 1000.0, 3)
                        validator.setNotation(QDoubleValidator.StandardNotation)
                        widget.setValidator(validator)
                    
                    if isinstance(widget, QLineEdit) and not widget.isReadOnly():
                        widget.textChanged.connect(self.save_parameters)

            row += 1

        # 单位切换信号
        self.unit_combo.currentTextChanged.connect(self.on_unit_changed)

        param_layout.addWidget(left_group)
        param_scroll.setWidget(param_container)
        content_layout.addWidget(param_scroll, 1)  # 参数区域占比1

        # 右侧：创建 TabWidget
        self.tab_widget = QTabWidget()
        self.activity_tab = ActivityTab(self.experiment, self)
        self.phantom_activity_tab = PhantomActivityTab(self.experiment, self)
        self.sequence_rebuild_tab = SequenceRebuildTab(self.experiment, self)
        self.phantom_analysis_tab = PhantomAnalysisTab(self.experiment, self)
        self.tab_widget.addTab(self.activity_tab, "📊 活度预设")
        self.tab_widget.addTab(self.phantom_activity_tab, "💉 模体活度记录")
        self.tab_widget.addTab(self.sequence_rebuild_tab, "🔧 序列重建设置")
        self.tab_widget.addTab(self.phantom_analysis_tab, "🔬 模体数据分析")

        # "时间" 标签，挂到 TabBar 的右上角
        self.time_display_top = QLabel("加载中...")
        self.time_display_top.setObjectName("time_display")
        self.time_display_top.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.tab_widget.setCornerWidget(self.time_display_top, Qt.TopRightCorner)

        content_layout.addWidget(self.tab_widget, 2)  # 标签页区域占比2

        main_layout.addLayout(content_layout)

    def _parse_time(self, time_str):
        """解析时间字符串为QDateTime对象"""
        if not time_str:
            return None
            
        try:
            if isinstance(time_str, str):
                # 尝试解析ISO格式时间字符串
                dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                # 转换为北京时间
                beijing_tz = pytz.timezone('Asia/Shanghai')
                if dt.tzinfo is None:
                    dt = beijing_tz.localize(dt)
                else:
                    dt = dt.astimezone(beijing_tz)
                return QDateTime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
            elif isinstance(time_str, (int, float)):
                # 尝试解析时间戳
                dt = datetime.fromtimestamp(time_str, pytz.timezone('Asia/Shanghai'))
                return QDateTime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        except (ValueError, OSError) as e:
            logging.error(f"时间解析错误: {e}")
            
        return None

    def _save_experiment(self):
        """保存实验数据到数据库"""
        try:
            # 获取父窗口的数据管理器
            if self.main_window and hasattr(self.main_window, "data_manager"):
                self.main_window.data_manager.save_experiment(self.experiment)
                # 发出更新信号
                self.experiment_updated.emit(self.experiment)
        except Exception as e:
            logging.error(f"保存实验失败: {e}")

    def _start_timer(self):
        """启动定时器，每秒更新一次时间和活度"""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)  # 1000ms = 1s

    def update_time(self):
        """更新时间显示"""
        current_time = get_current_beijing_time()
        formatted_time = format_datetime(current_time)
        self.time_display_top.setText(f"北京时间: {formatted_time}")

    def update_half_life(self):
        """更新半衰期显示"""
        isotope = self.isotope.currentText()
        half_life = HALF_LIFE_TABLE.get(isotope, 0)
        self.half_display.setText(f"{half_life:.2f} 分钟")

    def on_unit_changed(self, new_unit):
        """处理活度单位变化"""
        if new_unit == self.activity_unit:
            return
            
        old_unit = self.activity_unit
        self.activity_unit = new_unit
        
        # 更新标签
        if self.target_label:
            self.target_label.setText(f"扫描时刻活度 ({new_unit}):")
            
        # 转换目标活度显示
        target_text = self.target_activity.text().strip()
        if target_text:
            try:
                target_value = float(target_text)
                converted_value = self.convert_activity(target_value, old_unit, new_unit)
                self.target_activity.setText(f"{converted_value:.3f}")
            except ValueError:
                pass
                
        # 保存单位设置
        self.experiment.parameters["activity_unit"] = new_unit
        self._save_experiment()
        
        # 通知活度标签页单位变化
        if hasattr(self.activity_tab, "update_activity_unit"):
            self.activity_tab.update_activity_unit(new_unit)
            
        # 通知模体活度记录标签页单位变化
        if hasattr(self.phantom_activity_tab, "update_activity_unit"):
            self.phantom_activity_tab.update_activity_unit(new_unit)

    def get_unit_factor(self, unit):
        """获取单位转换因子"""
        for u, factor in ACTIVITY_UNITS:
            if u == unit:
                return factor
        return 1.0  # 默认为 MBq

    def convert_activity(self, value, from_unit=None, to_unit=None):
        """在不同活度单位之间转换"""
        if value is None or from_unit is None or to_unit is None:
            return None
            
        if from_unit == to_unit:
            return value
            
        # 转换为 MBq
        from_factor = self.get_unit_factor(from_unit)
        to_factor = self.get_unit_factor(to_unit)
        
        return value * from_factor / to_factor

    def save_parameters(self):
        """保存参数到实验对象"""
        # 阻止循环更新
        with QSignalBlocker(self.name_input), QSignalBlocker(self.center_name):
            # 更新实验基本信息
            self.experiment.name = self.name_input.text()
            self.experiment.center = self.center_name.text()
            
            # 更新参数
            try:
                volume = float(self.volume.text()) if self.volume.text() else 0.0
                self.experiment.parameters["volume"] = volume
            except ValueError:
                pass
                
            try:
                machine_time_diff = float(self.machine_time_diff.text()) if self.machine_time_diff.text() else 0.0
                self.experiment.parameters["machine_time_diff"] = machine_time_diff
            except ValueError:
                pass
                
            try:
                target_activity = float(self.target_activity.text()) if self.target_activity.text() else 0.0
                # 保存为 mCi（标准单位）
                self.experiment.parameters["target_activity"] = self.convert_activity(
                    target_activity, self.activity_unit, "mCi"
                )
            except ValueError:
                pass
                
            # 更新其他参数
            self.experiment.parameters["isotope"] = self.isotope.currentText()
            self.experiment.parameters["device_model"] = self.device_model.currentText()
            self.experiment.parameters["remark"] = self.remark.text()
            
            # 保存到数据库
            self._save_experiment()

    def on_target_activity_changed(self):
        """处理目标活度变化"""
        target_text = self.target_activity.text().strip()
        if not target_text:
            return
            
        try:
            target_activity = float(target_text)
            # 转换为 mCi 保存
            mci_value = self.convert_activity(target_activity, self.activity_unit, "mCi")
            self.experiment.parameters["target_activity"] = mci_value
            self._save_experiment()
        except ValueError:
            pass 
from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QComboBox, QPushButton, QHBoxLayout, QMessageBox, QLabel, QSizePolicy, QWidget
from PyQt5.QtGui import QDoubleValidator
from ...models.nuclide import calculate_decayed_activity
from ...core.constants import HALF_LIFE_TABLE, ACTIVITY_UNITS
from ...utils.time_utils import get_current_beijing_time
from datetime import datetime
import pytz

class ActivityCalculatorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("活度计算器")
        self.current_unit = "MBq"
        self.setFixedSize(600, 500)
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

        # 标题
        title = QLabel("活度计算器")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #1976d2;
                padding-bottom: 10px;
            }
        """)
        layout.addRow(title)

        self.activity_input = QLineEdit()
        self.activity_input.setValidator(QDoubleValidator(0.0, 10000.0, 3))
        self.activity_input.setPlaceholderText("请输入初始活度...")
        layout.addRow("初始活度:", self.activity_input)

        self.unit_combo = QComboBox()
        self.unit_combo.addItems([u[0] for u in ACTIVITY_UNITS])
        self.unit_combo.setCurrentText("MBq")
        self.unit_combo.currentTextChanged.connect(self.on_unit_changed)
        layout.addRow("单位:", self.unit_combo)

        self.isotope = QComboBox()
        self.isotope.addItems(list(HALF_LIFE_TABLE.keys()))
        self.isotope.setCurrentText("Ga-68")

        
        self.half_life_display = QLineEdit()
        self.half_life_display.setReadOnly(True)

        
        self.update_half_life()
        
        isotope_widget = QWidget()
        # isotope_widget.setFixedHeight(30)
        isotope_layout = QHBoxLayout(isotope_widget)
        isotope_layout.setContentsMargins(0, 0, 0, 0)
        isotope_layout.setSpacing(10)
        isotope_layout.addWidget(self.isotope)
        isotope_layout.addWidget(self.half_life_display)
        isotope_layout.addStretch()
        
        layout.addRow("核素:", isotope_widget)

        self.current_time_input = QLineEdit()
        self.current_time_input.setText(get_current_beijing_time().strftime("%Y/%m/%d-%H:%M:%S"))
        self.current_time_input.setPlaceholderText("YYYY/MM/DD-HH:MM:SS")
        layout.addRow("当前时间:", self.current_time_input)

        self.target_time_input = QLineEdit()
        self.target_time_input.setText(get_current_beijing_time().strftime("%Y/%m/%d-%H:%M:%S"))
        self.target_time_input.setPlaceholderText("YYYY/MM/DD-HH:MM:SS")
        layout.addRow("目标时间:", self.target_time_input)

        self.time_diff_input = QLineEdit("0.0")
        self.time_diff_input.setValidator(QDoubleValidator(-10000.0, 10000.0, 3))
        layout.addRow("时间差 (分钟):", self.time_diff_input)

        self.result_display = QLineEdit()
        self.result_display.setReadOnly(True)
        self.result_display.setPlaceholderText(f"衰减后活度 ({self.current_unit})")
        layout.addRow("衰减后活度:", self.result_display)

        button_layout = QHBoxLayout()
        calc_by_diff_button = QPushButton("按时间差计算")
        calc_by_diff_button.setObjectName("success")
        calc_by_date_button = QPushButton("按日期计算")
        calc_by_date_button.setObjectName("success")
        button_layout.addWidget(calc_by_diff_button)
        button_layout.addWidget(calc_by_date_button)
        layout.addRow(button_layout)

        calc_by_diff_button.clicked.connect(self.calculate_by_diff)
        calc_by_date_button.clicked.connect(self.calculate_by_date)
        self.isotope.currentTextChanged.connect(self.update_half_life)
        self.current_time_input.textChanged.connect(self.update_time_diff)
        self.target_time_input.textChanged.connect(self.update_time_diff)

    def on_unit_changed(self, new_unit):
        """单位切换时转换数值"""
        old_unit = self.current_unit
        self.current_unit = new_unit
        
        # 转换输入活度
        if self.activity_input.text():
            try:
                value = float(self.activity_input.text())
                converted = self.convert_activity(value, old_unit, new_unit)
                if converted is not None:
                    self.activity_input.setText(f"{converted:.3f}")
            except ValueError:
                pass
        
        # 转换结果活度
        if self.result_display.text():
            try:
                value = float(self.result_display.text())
                converted = self.convert_activity(value, old_unit, new_unit)
                if converted is not None:
                    self.result_display.setText(f"{converted:.4f}")
            except ValueError:
                pass
        
        # 更新占位符
        self.result_display.setPlaceholderText(f"衰减后活度 ({new_unit})")
        
        # 更新验证器，限制mCi不超过1000
        if new_unit == "mCi":
            self.activity_input.setValidator(QDoubleValidator(0.0, 1000.0, 3))
        else:
            self.activity_input.setValidator(QDoubleValidator(0.0, 10000.0, 3))

    def update_half_life(self):
        iso = self.isotope.currentText()
        hl = HALF_LIFE_TABLE.get(iso, 0)
        self.half_life_display.setText(f"半衰期: {hl:.2f} 分钟")

    def parse_time(self, time_str):
        tz = pytz.timezone("Asia/Shanghai")
        current_date = get_current_beijing_time().strftime("%Y/%m/%d")
        try:
            dt = datetime.strptime(time_str, "%Y/%m/%d-%H:%M:%S")
            return tz.localize(dt)
        except ValueError:
            try:
                dt = datetime.strptime(f"{current_date}-{time_str}", "%Y/%m/%d-%H:%M:%S")
                return tz.localize(dt)
            except ValueError:
                return None

    def update_time_diff(self):
        try:
            current_time = self.parse_time(self.current_time_input.text())
            target_time = self.parse_time(self.target_time_input.text())
            if current_time and target_time:
                time_diff = (target_time - current_time).total_seconds() / 60
                self.time_diff_input.setText(f"{time_diff:.4f}")
        except Exception:
            self.time_diff_input.setText("0.0")

    def get_unit_factor(self, unit):
        for u, f in ACTIVITY_UNITS:
            if u == unit:
                return f
        return 1.0

    def convert_activity(self, value, from_unit, to_unit):
        try:
            base_value = value * self.get_unit_factor(from_unit)
            return base_value / self.get_unit_factor(to_unit)
        except (ValueError, TypeError):
            return None

    def calculate_by_diff(self):
        try:
            initial_activity = float(self.activity_input.text())
            time_diff = float(self.time_diff_input.text())
            isotope = self.isotope.currentText()
            unit = self.unit_combo.currentText()
            
            # 检查mCi限制
            if unit == "mCi" and initial_activity > 1000:
                QMessageBox.warning(self, "警告", "mCi单位下活度不能超过1000")
                return
            
            base_activity = self.convert_activity(initial_activity, unit, "MBq")
            decayed_activity = calculate_decayed_activity(base_activity, time_diff, isotope)
            result = self.convert_activity(decayed_activity, "MBq", unit)
            self.result_display.setText(f"{result:.4f}")
        except ValueError as e:
            QMessageBox.critical(self, "错误", f"计算失败: {str(e)}")
            self.result_display.setText("")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"意外错误: {str(e)}")
            self.result_display.setText("")

    def calculate_by_date(self):
        try:
            initial_activity = float(self.activity_input.text())
            current_time = self.parse_time(self.current_time_input.text())
            target_time = self.parse_time(self.target_time_input.text())
            
            if not current_time or not target_time:
                QMessageBox.warning(self, "警告", "请输入正确的时间格式 (YYYY/MM/DD-HH:MM:SS)")
                return
            
            time_diff = (target_time - current_time).total_seconds() / 60
            isotope = self.isotope.currentText()
            unit = self.unit_combo.currentText()
            
            # 检查mCi限制
            if unit == "mCi" and initial_activity > 1000:
                QMessageBox.warning(self, "警告", "mCi单位下活度不能超过1000")
                return
            
            base_activity = self.convert_activity(initial_activity, unit, "MBq")
            decayed_activity = calculate_decayed_activity(base_activity, time_diff, isotope)
            result = self.convert_activity(decayed_activity, "MBq", unit)
            self.result_display.setText(f"{result:.4f}")
        except ValueError as e:
            QMessageBox.critical(self, "错误", f"计算失败: {str(e)}")
            self.result_display.setText("")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"意外错误: {str(e)}")
            self.result_display.setText("") 
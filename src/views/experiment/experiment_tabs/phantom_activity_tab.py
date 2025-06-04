from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QGroupBox, QLabel, QLineEdit, QPushButton, QMessageBox, QHBoxLayout, QDateTimeEdit, QFrame
from PyQt5.QtGui import QDoubleValidator, QRegExpValidator
from PyQt5.QtCore import Qt, QSignalBlocker, QRegExp, QDateTime, QTimer
from src.models.entities.nuclide import calculate_decayed_activity
from src.utils.time_utils import get_current_beijing_time
from src.core.constants import HALF_LIFE_TABLE
from datetime import datetime, timedelta
import pytz
import logging
import numpy as np

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

class PhantomActivityTab(QWidget):
    def __init__(self, experiment, parent=None):
        super().__init__(parent)
        self.experiment = experiment
        self.parent_widget = parent
        self.syringe_widgets = {}
        self.activity_unit = self.experiment.parameters.get("activity_unit", "mCi")
        self.syringes = self.experiment.parameters.get("syringes", [])
        self.raw_activity_values = {}
        self.refreshing = False
        self._load_syringes()
        self.init_ui()

    def _load_syringes(self):
        """Load syringe data or initialize with default."""
        default_syringe = {
            "name": "分针1",
            "activities": {
                lbl: {"value": 0.0, "time": ""} for lbl in ["本底活度", "注射分针活度", "残余针活度", "残余本底活度"]
            },
            "actual_activity": 0.0
        }
        if not self.syringes:
            self.syringes = [default_syringe]
        self.experiment.parameters["syringes"] = self.syringes
        self._save_experiment()

    def _save_experiment(self):
        """Save experiment data."""
        try:
            if hasattr(self.parent_widget, 'main_window') and hasattr(self.parent_widget.main_window, 'data_manager'):
                self.parent_widget.main_window.data_manager.save_experiment(self.experiment)
        except Exception as e:
            logging.error(f"保存实验失败: {e}")

    def init_ui(self):
        """Initialize the UI layout."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 15, 10, 10)

        # 顶部控制区域（添加分针按钮和总活度计算）
        top_control_layout = QHBoxLayout()
        
        # 添加分针按钮
        self.add_btn = QPushButton("添加分针")
        self.add_btn.clicked.connect(self._on_add_syringe)
        top_control_layout.addWidget(self.add_btn)
        
        # 添加间距
        top_control_layout.addSpacing(30)  # 30像素的间距
        
        # 计算总活度按钮
        self.calc_total_btn = QPushButton("计算总活度")
        self.calc_total_btn.clicked.connect(self.calculate_total_activity)
        top_control_layout.addWidget(self.calc_total_btn)
        
        # 总活度显示标签
        self.total_activity_label = QLabel(f"总活度: 0.00 {self.activity_unit}")
        self.total_activity_label.setMinimumWidth(200)
        top_control_layout.addWidget(self.total_activity_label)
        
        # 详细信息显示标签
        self.detail_info_label = QLabel("")
        self.detail_info_label.setWordWrap(True)  # 允许换行
        self.detail_info_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
                color: #495057;
            }
        """)
        top_control_layout.addWidget(self.detail_info_label)
        
        # 添加弹性空间
        top_control_layout.addStretch()
        
        layout.addLayout(top_control_layout)

        # 分针网格
        self.syringe_grid = QGridLayout()
        self.syringe_grid.setSpacing(10)
        layout.addLayout(self.syringe_grid)
        self._refresh_syringe_widgets()
        
        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
        
        # ———— 底部活度计算区域 ————
        bottom_group = QGroupBox("活度计算")
        self.bottom_layout = QGridLayout()
        self.bottom_layout.setSpacing(15)
        bottom_group.setLayout(self.bottom_layout)

        # 创建活度计算控件
        self.scan_time_edit = QDateTimeEdit()
        self.scan_time_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.scan_time_edit.setCalendarPopup(True)
        
        # 获取扫描时间
        scan_time = self.parent_widget._parse_time(self.experiment.parameters.get("scan_time", ""))
        if scan_time:
            self.scan_time_edit.setDateTime(scan_time)
        else:
            self.scan_time_edit.setDateTime(QDateTime.currentDateTime())
        
        self.scan_time_edit.dateTimeChanged.connect(self._on_scan_time_changed)
        
        self.actual_activity = QLineEdit()
        self.actual_activity.setPlaceholderText(f"输入实际活度 ({self.activity_unit})")
        self.actual_activity.textChanged.connect(self._on_actual_activity_changed)
        
        self.target_activity = QLineEdit()
        self.target_activity.setPlaceholderText(f"输入目标活度 ({self.activity_unit})")
        self.target_activity.textChanged.connect(self._on_target_activity_changed)
        
        self.countdown_display = QLabel("--:--:--")
        self.current_activity_display = QLabel("0.00")
        
        # 添加到布局
        self.bottom_layout.addWidget(QLabel("扫描时间:"), 0, 0)
        self.bottom_layout.addWidget(self.scan_time_edit, 0, 1)
        self.bottom_layout.addWidget(QLabel("倒计时:"), 0, 2)
        self.bottom_layout.addWidget(self.countdown_display, 0, 3)
        
        self.bottom_layout.addWidget(QLabel(f"实际活度 ({self.activity_unit}):"), 1, 0)
        self.bottom_layout.addWidget(self.actual_activity, 1, 1)
        self.bottom_layout.addWidget(QLabel(f"当前活度 ({self.activity_unit}):"), 1, 2)
        self.bottom_layout.addWidget(self.current_activity_display, 1, 3)
        
        self.bottom_layout.addWidget(QLabel(f"目标活度 ({self.activity_unit}):"), 2, 0)
        self.bottom_layout.addWidget(self.target_activity, 2, 1)
        
        # 设置列的拉伸因子
        self.bottom_layout.setColumnStretch(0, 0)  # 标签列不拉伸
        self.bottom_layout.setColumnStretch(1, 1)  # 输入列拉伸
        self.bottom_layout.setColumnStretch(2, 0)  # 标签列不拉伸
        self.bottom_layout.setColumnStretch(3, 1)  # 输入列拉伸
        
        # 加载初始值
        target_mci = self.experiment.parameters.get("target_activity", 0.0)
        disp_target = self.parent_widget.convert_activity(target_mci, "mCi", self.activity_unit) or 0.0
        if disp_target > 0:
            self.target_activity.setText(f"{disp_target:.3f}")
        
        # 设置验证器
        if self.activity_unit == "mCi":
            validator = QDoubleValidator(0.0, 1000.0, 3)
        else:
            validator = QDoubleValidator(0.0, 100000.0, 3)
        validator.setNotation(QDoubleValidator.StandardNotation)
        self.actual_activity.setValidator(validator)
        self.target_activity.setValidator(validator)

        layout.addWidget(bottom_group)
        
        # 启动定时器更新倒计时和当前活度
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_activity_displays)
        self.timer.start(1000)  # 1秒更新一次
        
    def _on_scan_time_changed(self, datetime):
        """处理扫描时间变化"""
        # 保存扫描时间
        self.experiment.parameters["scan_time"] = datetime.toPyDateTime().isoformat()
        self._save_experiment()
        self._update_activity_displays()
        
    def _on_actual_activity_changed(self, text):
        """处理实际活度变化"""
        self._update_activity_displays()
        
        # 如果目标活度也有值，自动计算扫描时间
        if text and self.target_activity.text():
            self._auto_calculate_scan_time()
            
    def _on_target_activity_changed(self, text):
        """处理目标活度变化"""
        # 保存目标活度
        try:
            if text:
                target_activity = float(text)
                # 转换为 mCi 保存
                mci_value = self.parent_widget.convert_activity(target_activity, self.activity_unit, "mCi")
                self.experiment.parameters["target_activity"] = mci_value
                self._save_experiment()
        except ValueError:
            pass
            
        # 如果实际活度也有值，自动计算扫描时间
        if text and self.actual_activity.text():
            self._auto_calculate_scan_time()
            
    def _auto_calculate_scan_time(self):
        """自动计算扫描时间"""
        try:
            target_text = self.target_activity.text().strip()
            actual_text = self.actual_activity.text().strip()
            
            if not target_text or not actual_text:
                return
                
            target_activity = float(target_text)
            actual_activity = float(actual_text)
            
            # 检查活度大小关系
            if actual_activity <= target_activity:
                return
                
            # 获取核素
            isotope = self.parent_widget.isotope.currentText()
            
            # 计算达到目标活度所需的时间（分钟）
            half_life = HALF_LIFE_TABLE.get(isotope, 0)
            if not half_life:
                return
                
            decay_constant = np.log(2) / half_life
            minutes_to_target = np.log(actual_activity / target_activity) / decay_constant
            
            # 计算扫描时间
            current_time = get_current_beijing_time()
            scan_time = current_time + timedelta(minutes=minutes_to_target)
            
            # 更新扫描时间控件（阻止循环触发）
            self.scan_time_edit.blockSignals(True)
            self.scan_time_edit.setDateTime(QDateTime(
                scan_time.year, scan_time.month, scan_time.day,
                scan_time.hour, scan_time.minute, scan_time.second
            ))
            self.scan_time_edit.blockSignals(False)
            
            # 保存扫描时间
            self.experiment.parameters["scan_time"] = scan_time.isoformat()
            self._save_experiment()
            
        except (ValueError, ZeroDivisionError):
            pass
            
    def _update_activity_displays(self):
        """更新倒计时和当前活度显示"""
        # 更新倒计时
        scan_time = self.scan_time_edit.dateTime()
        current_time = get_current_beijing_time()
        
        # 转换QDateTime为datetime对象，并添加时区信息
        scan_dt = scan_time.toPyDateTime()
        beijing_tz = pytz.timezone('Asia/Shanghai')
        scan_dt = beijing_tz.localize(scan_dt)
        
        # 计算时间差
        time_diff = scan_dt - current_time
        
        if time_diff.total_seconds() <= 0:
            # 已过扫描时间
            self.countdown_display.setText("已过期")
            self.countdown_display.setStyleSheet("color: #d32f2f; font-weight: bold;")
        else:
            # 显示倒计时
            hours, remainder = divmod(time_diff.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            # 格式化显示
            countdown_text = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            self.countdown_display.setText(countdown_text)
            self.countdown_display.setStyleSheet("")
            
        # 更新当前活度
        actual_text = self.actual_activity.text().strip()
        if not actual_text:
            self.current_activity_display.setText("0.00")
            return
            
        try:
            actual_activity = float(actual_text)
        except ValueError:
            self.current_activity_display.setText("输入错误")
            return
            
        # 计算时间差（分钟）
        time_diff_minutes = (current_time - scan_dt).total_seconds() / 60
        
        # 获取核素
        isotope = self.parent_widget.isotope.currentText()
        
        # 计算当前活度
        try:
            current_activity = calculate_decayed_activity(actual_activity, time_diff_minutes, isotope)
            self.current_activity_display.setText(f"{current_activity:.3f}")
            
            # 根据活度值设置不同的样式
            if current_activity < 0.1 * actual_activity:  # 低于10%
                self.current_activity_display.setStyleSheet("background-color: #ffebee; color: #c62828;")
            elif current_activity < 0.5 * actual_activity:  # 低于50%
                self.current_activity_display.setStyleSheet("background-color: #fff8e1; color: #ff8f00;")
            else:
                self.current_activity_display.setStyleSheet("")
                
        except Exception as e:
            self.current_activity_display.setText(f"计算错误")
            
    def update_activity_unit(self, new_unit):
        """更新活度单位"""
        if new_unit == self.activity_unit:
            return
            
        old_unit = self.activity_unit
        self.activity_unit = new_unit
        
        # 更新标签
        for idx, widget in self.syringe_widgets.items():
            for label in widget["activity_labels"].values():
                if label.text().endswith(old_unit):
                    label.setText(label.text().replace(old_unit, new_unit))
                    
        # 更新底部活度计算区域的单位
        for i in range(self.bottom_layout.rowCount()):
            item = self.bottom_layout.itemAtPosition(i, 0)
            if item and item.widget():
                label = item.widget()
                if isinstance(label, QLabel) and old_unit in label.text():
                    label.setText(label.text().replace(old_unit, new_unit))
                    
        # 转换实际活度显示
        actual_text = self.actual_activity.text().strip()
        if actual_text:
            try:
                actual_value = float(actual_text)
                converted_value = self.parent_widget.convert_activity(actual_value, old_unit, new_unit)
                self.actual_activity.setText(f"{converted_value:.3f}")
            except ValueError:
                pass
                
        # 转换目标活度显示
        target_text = self.target_activity.text().strip()
        if target_text:
            try:
                target_value = float(target_text)
                converted_value = self.parent_widget.convert_activity(target_value, old_unit, new_unit)
                self.target_activity.setText(f"{converted_value:.3f}")
            except ValueError:
                pass
                
        # 转换当前活度显示
        current_text = self.current_activity_display.text().strip()
        if current_text and current_text not in ["0.00", "输入错误", "计算错误"]:
            try:
                current_value = float(current_text)
                converted_value = self.parent_widget.convert_activity(current_value, old_unit, new_unit)
                self.current_activity_display.setText(f"{converted_value:.3f}")
            except ValueError:
                pass
                
        # 更新验证器
        if new_unit == "MBq" or new_unit == "kBq":
            validator = QDoubleValidator(0.0, 100000.0, 3)
        else:
            validator = QDoubleValidator(0.0, 1000.0, 3)
        validator.setNotation(QDoubleValidator.StandardNotation)
        self.actual_activity.setValidator(validator)
        self.target_activity.setValidator(validator)
        
        # 更新总活度显示
        total_text = self.total_activity_label.text()
        if ":" in total_text:
            value_part = total_text.split(":")[1].strip().split()[0]
            try:
                value = float(value_part)
                converted = self.parent_widget.convert_activity(value, old_unit, new_unit)
                self.total_activity_label.setText(f"总活度: {converted:.2f} {new_unit}")
            except ValueError:
                self.total_activity_label.setText(f"总活度: 0.00 {new_unit}")
        
    def calculate_total_activity(self):
        """计算所有分针的总活度，并将每个分针的活度衰减到最后一根分针的残余时刻"""
        try:
            if not self.syringes:
                return
                
            # 找到最后一根分针的残余时刻
            last_syringe_idx = len(self.syringes) - 1
            last_residual_time_str = self.syringes[last_syringe_idx]["activities"].get("残余针活度", {}).get("time", "")
            
            if not last_residual_time_str:
                QMessageBox.warning(self, "警告", "最后一根分针的残余时间未设置")
                return
                
            # 解析最后一根分针的残余时间
            last_residual_time = self.parent_widget._parse_time(last_residual_time_str)
            if not last_residual_time:
                QMessageBox.warning(self, "警告", "无法解析时间格式")
                return
                
            isotope = self.parent_widget.isotope.currentText()
            total_activity_mci = 0.0
            detail_info = []
            
            # 计算每个分针的活度，并衰减到最后一根分针的残余时刻
            for idx, syringe in enumerate(self.syringes):
                actual_activity_mci = syringe.get("actual_activity", 0.0)
                syringe_name = syringe.get("name", f"分针{idx+1}")
                
                if actual_activity_mci <= 0:
                    detail_info.append(f"{syringe_name}: 无实际活度数据")
                    continue
                    
                # 获取该分针的残余时间
                residual_time_str = syringe["activities"].get("残余针活度", {}).get("time", "")
                if not residual_time_str:
                    detail_info.append(f"{syringe_name}: 残余时间未设置")
                    continue
                    
                residual_time = self.parent_widget._parse_time(residual_time_str)
                if not residual_time:
                    detail_info.append(f"{syringe_name}: 时间格式错误")
                    continue
                    
                # 计算时间差（分钟）
                time_diff_minutes = (last_residual_time - residual_time).total_seconds() / 60
                
                # 转换为MBq进行衰变计算
                actual_activity_mbq = self.parent_widget.convert_activity(actual_activity_mci, "mCi", "MBq")
                decayed_activity_mbq = calculate_decayed_activity(actual_activity_mbq, time_diff_minutes, isotope)
                # 转换回mCi
                decayed_activity_mci = self.parent_widget.convert_activity(decayed_activity_mbq, "MBq", "mCi")
                total_activity_mci += decayed_activity_mci
                
                # 转换为当前单位显示
                actual_display = self.parent_widget.convert_activity(actual_activity_mci, "mCi", self.activity_unit)
                decayed_display = self.parent_widget.convert_activity(decayed_activity_mci, "mCi", self.activity_unit)
                
                detail_info.append(f"{syringe_name}: {actual_display:.2f} → {decayed_display:.2f} {self.activity_unit}")
            
            # 转换为当前单位并显示
            total_activity_display = self.parent_widget.convert_activity(total_activity_mci, "mCi", self.activity_unit)
            self.total_activity_label.setText(f"总活度: {total_activity_display:.2f} {self.activity_unit}")
            
            # 显示详细信息 - 简洁格式
            if detail_info:
                # 简化显示格式，只显示关键信息
                simplified_info = []
                for info in detail_info:
                    if "→" in info:  # 只显示有效的衰变信息
                        simplified_info.append(info)
                
                if simplified_info:
                    detail_text = " | ".join(simplified_info)
                    self.detail_info_label.setText(detail_text)
                else:
                    self.detail_info_label.setText("无有效数据")
            else:
                self.detail_info_label.setText("无数据")
            
            # 保存总活度(mCi)到实验参数
            self.experiment.parameters["total_activity"] = total_activity_mci
            self._save_experiment()
            
        except Exception as e:
            logging.error(f"计算总活度失败: {e}")
            QMessageBox.critical(self, "错误", f"计算总活度失败: {e}")

    def _refresh_syringe_widgets(self):
        """Refresh syringe widgets."""
        if self.refreshing:
            return
        self.refreshing = True
        try:
            # 先清除旧的信号连接
            for idx, widget in self.syringe_widgets.items():
                for inp in widget["activity_inputs"].values():
                    try:
                        inp.textChanged.disconnect()
                        inp.editingFinished.disconnect()
                    except TypeError:
                        pass  # 忽略断开未连接信号的错误
                    
                for tm in widget["time_displays"].values():
                    try:
                        # 对于QDateTimeEdit，是dateTimeChanged信号
                        tm.dateTimeChanged.disconnect()
                    except TypeError:
                        pass  # 忽略断开未连接信号的错误
                        
            # 移除现有控件
            while self.syringe_grid.count():
                item = self.syringe_grid.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            self.syringe_widgets.clear()
            
            # 重新添加
            for i, s in enumerate(self.syringes):
                widget = self._create_syringe_widget(i, s)
                self.syringe_widgets[i] = widget
                self.syringe_grid.addWidget(widget["group"], 0, i)
        finally:
            self.refreshing = False

    def _create_syringe_widget(self, idx, data):
        """Create a widget group for a single syringe."""
        grp = QGroupBox(data.get("name", f"分针{idx+1}"))
        v = QVBoxLayout(grp)

        # 分针名称输入 - 标签和输入框在同一行
        name_layout = QHBoxLayout()
        name_label = QLabel("分针名称:")
        name_label.setFixedWidth(80)  # 固定标签宽度
        name_le = QLineEdit(data.get("name", f"分针{idx+1}"))
        name_le.editingFinished.connect(lambda: self._on_name_changed(idx, name_le.text()))
        name_layout.addWidget(name_label)
        name_layout.addWidget(name_le)
        # 不添加弹性空间，让输入框延伸到最右边
        v.addLayout(name_layout)

         # 主网格：三列：标签 / 活动输入框 / 时间输入框
        grid = QGridLayout(grp)
        grid.setVerticalSpacing(20)
        # 这里改为 13:30 以近似 1.3:3 比例
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 15)
        grid.setColumnStretch(2, 30)

        labels = ["本底活度", "注射分针活度", "残余针活度", "残余本底活度"]
        activity_inputs = {}
        activity_labels = {}
        time_displays = {}

        for i, lbl in enumerate(labels):
            # 第一列：标签
            label = QLabel(f"{lbl} ({self.activity_unit})")
            label.setFixedWidth(170)
            grid.addWidget(label, i, 0)
            activity_labels[lbl] = label

             # 第二列：数值输入，把 placeholder 改为 "请输入..."
            inp = QLineEdit()
            inp.setStyleSheet("""
                QLineEdit {
                    font-size: 14px;
                }
                QLineEdit:placeholder {
                    color: gray;         /* 可选：placeholder 的颜色 */
                    font-size: 10px;     /* 占位符字体改为 10px */
                }
            """)
            inp.setValidator(QDoubleValidator(0.0, 1000.0, 3))
            inp.setPlaceholderText("请输入...")
            with QSignalBlocker(inp):
                # 从mCi值转换为当前单位显示
                mci_val = data["activities"].get(lbl, {"value": 0.0})["value"]
                new_val = self.parent_widget.convert_activity(mci_val, "mCi", self.activity_unit)
                if new_val is not None and new_val > 0:
                    inp.setText(f"{new_val:.3f}")
            inp.textChanged.connect(lambda v, le=inp: self._on_activity_changed(le, v, idx))
            inp.editingFinished.connect(lambda: self._on_activity_finished(idx))
            grid.addWidget(inp, i, 1)
            activity_inputs[lbl] = inp

            # 第三列：使用QDateTimeEdit替代QLineEdit进行时间输入
            tm = QDateTimeEdit()
            tm.setDisplayFormat("yyyy/MM/dd-HH:mm:ss")
            tm.setCalendarPopup(True)
            
            # 设置默认时间或已保存的时间
            time_str = data["activities"].get(lbl, {}).get("time", "")
            if time_str:
                dt = self.parent_widget._parse_time(time_str)
                if dt:
                    tm.setDateTime(QDateTime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second))
            else:
                tm.setDateTime(QDateTime.currentDateTime())
                
            tm.dateTimeChanged.connect(lambda dt, label=lbl: self._on_datetime_changed(idx, label, dt))
            grid.addWidget(tm, i, 2)
            time_displays[lbl] = tm

        # 实际活度显示行
        actual_layout = QHBoxLayout()
        actual_label = QLabel(f"注射时刻活度衰变到残余时刻活度值 ({self.activity_unit})")
        actual_display = QLineEdit()
        actual_display.setReadOnly(True)
        actual_display.setFixedWidth(150)  # 设置固定宽度
        # 从mCi值转换为当前单位显示
        actual_mci = data.get("actual_activity", 0.0)
        new_actual = self.parent_widget.convert_activity(actual_mci, "mCi", self.activity_unit)
        if new_actual is not None:
            actual_display.setText(f"{new_actual:.3f}")
        actual_layout.addWidget(actual_label)
        actual_layout.addWidget(actual_display)

        v.addLayout(grid)
        v.addLayout(actual_layout)

        # 下方按钮行
        hb = QHBoxLayout()
        cb = QPushButton("计算实际活度")
        cb.clicked.connect(lambda: self.calculate_actual(idx))
        db = QPushButton("删除分针")
        # db.setObjectName("danger")  # 使用危险按钮样式
        db.clicked.connect(lambda: self._on_delete_syringe(idx))
        hb.addWidget(cb)
        hb.addWidget(db)
        v.addLayout(hb)

        return {
            "group": grp,
            "name_input": name_le,
            "activity_inputs": activity_inputs,
            "activity_labels": activity_labels,
            "time_displays": time_displays,
            "actual_display": actual_display,
            "actual_label": actual_label
        }

    def _on_add_syringe(self):
        """Add a new syringe."""
        if len(self.syringes) >= 4:
            QMessageBox.warning(self, "警告", "最多支持4个分针！")
            return
        idx = len(self.syringes)
        new_syringe = {
            "name": f"分针{idx+1}",
            "activities": {
                lbl: {"value": 0.0, "time": ""} for lbl in ["本底活度", "注射分针活度", "残余针活度", "残余本底活度"]
            },
            "actual_activity": 0.0
        }
        self.syringes.append(new_syringe)
        self.experiment.parameters["syringes"] = self.syringes
        self._save_experiment()
        self._refresh_syringe_widgets()

    def _on_delete_syringe(self, idx):
        """Delete a syringe."""
        if len(self.syringes) <= 1:
            QMessageBox.warning(self, "警告", "至少保留一个分针！")
            return
        self.syringes.pop(idx)
        self.experiment.parameters["syringes"] = self.syringes
        self._save_experiment()
        self._refresh_syringe_widgets()

    def _on_name_changed(self, idx, name):
        """Update syringe name."""
        if idx < len(self.syringes):
            self.syringes[idx]["name"] = name
            self.experiment.parameters["syringes"] = self.syringes
            self._save_experiment()
            self._refresh_syringe_widgets()

    def _on_activity_changed(self, le, val, idx):
        """Handle activity input change."""
        if idx >= len(self.syringes) or idx not in self.syringe_widgets:
            return
        try:
            v = float(val) if val else 0.0
            # 将当前单位的输入值转换为mCi并保存到JSON
            mci_val = self.parent_widget.convert_activity(v, self.activity_unit, "mCi")
            if mci_val is not None:
                # 找到对应的标签并保存mCi值
                for lbl, inp in self.syringe_widgets[idx]["activity_inputs"].items():
                    if inp == le:
                        self.syringes[idx]["activities"][lbl]["value"] = mci_val
                        break
                self.experiment.parameters["syringes"] = self.syringes
                self._save_experiment()
        except ValueError:
            pass

    def _on_activity_finished(self, idx):
        """Trigger actual activity calculation on editing finished."""
        self.calculate_actual(idx)

    def _on_datetime_changed(self, idx, label, dt):
        """Handle datetime change from QDateTimeEdit."""
        if idx >= len(self.syringes) or idx not in self.syringe_widgets or label not in self.syringes[idx]["activities"]:
            return
            
        # 保存时间为字符串格式
        time_str = dt.toString("yyyy/MM/dd-HH:mm:ss")
        self.syringes[idx]["activities"][label]["time"] = time_str
        self.experiment.parameters["syringes"] = self.syringes
        self._save_experiment()
        self.calculate_actual(idx)

    def calculate_actual(self, idx):
        """Calculate actual activity for a syringe."""
        if idx >= len(self.syringes) or idx not in self.syringe_widgets:
            return
        try:
            syringe = self.syringes[idx]
            activities = syringe["activities"]
            required_activities = ["注射分针活度", "残余针活度"]
            if not all(activities[l]["value"] > 0 for l in required_activities):
                self.syringe_widgets[idx]["actual_display"].setText("请输入必要活度值")
                return
                
            # 确保所有时间都有值
            for lbl in activities:
                time_widget = self.syringe_widgets[idx]["time_displays"][lbl]
                time_str = time_widget.dateTime().toString("yyyy/MM/dd-HH:mm:ss")
                activities[lbl]["time"] = time_str
                
            self.experiment.parameters["syringes"] = self.syringes
            self._save_experiment()

            # 注意：这里的活度值都是mCi单位，需要转换为MBq进行计算
            bg_activity = self.parent_widget.convert_activity(activities["本底活度"]["value"], "mCi", "MBq")
            syringe_activity = self.parent_widget.convert_activity(activities["注射分针活度"]["value"], "mCi", "MBq")
            residual_activity = self.parent_widget.convert_activity(activities["残余针活度"]["value"], "mCi", "MBq")
            residual_bg = self.parent_widget.convert_activity(activities["残余本底活度"]["value"], "mCi", "MBq")
            isotope = self.parent_widget.isotope.currentText()
            
            # 从时间字符串解析时间
            times = {}
            for lbl in activities:
                time_str = activities[lbl]["time"]
                dt = self.parent_widget._parse_time(time_str)
                if dt:
                    times[lbl] = dt
                else:
                    self.syringe_widgets[idx]["actual_display"].setText("时间格式错误")
                    return
                    
            if not all(times.values()):
                self.syringe_widgets[idx]["actual_display"].setText("时间数据不完整")
                return

            moment_2 = times["注射分针活度"]
            moment_4 = times["残余本底活度"]
            M = syringe_activity - bg_activity
            K = calculate_decayed_activity(M, (moment_4 - moment_2).total_seconds() / 60, isotope)
            actual_activity_mbq = K - residual_activity + residual_bg

            if actual_activity_mbq < 0:
                self.syringe_widgets[idx]["actual_display"].setText("计算结果为负值")
                return
            elif actual_activity_mbq > 10000.0:
                self.syringe_widgets[idx]["actual_display"].setText("结果超出范围")
                return

            # 将计算结果转换为mCi保存
            actual_activity_mci = self.parent_widget.convert_activity(actual_activity_mbq, "MBq", "mCi")
            
            # 转换为当前单位显示
            actual_display = self.parent_widget.convert_activity(actual_activity_mci, "mCi", self.activity_unit)
            self.syringe_widgets[idx]["actual_display"].setText(f"{actual_display:.3f}")
            
            # 保存mCi值
            syringe["actual_activity"] = actual_activity_mci
            
            # 更新主界面的活度输入框（转换为当前单位）
            self.parent_widget.act_input.setText(f"{actual_display:.3f}")
            
            # 保存mCi值到实验参数
            self.experiment.parameters["actual_activity"] = actual_activity_mci
            self.experiment.parameters["syringes"] = self.syringes
            self._save_experiment()
            
            # 每次计算完实际活度后，自动更新总活度
            self.calculate_total_activity()
            
        except Exception as e:
            logging.error(f"计算实际活度失败: {e}")
            self.syringe_widgets[idx]["actual_display"].setText(f"计算错误") 
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QLineEdit, QComboBox, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QHeaderView, QSpinBox, QDoubleSpinBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDoubleValidator
import numpy as np
import logging


class ActivityTab(QWidget):
    # 活度数据更新信号
    activity_updated = pyqtSignal(dict)
    
    def __init__(self, experiment, parent=None):
        super().__init__(parent)
        self.experiment = experiment
        self.parent_window = parent
        
        # 活度预设数据（基于图片中的数据）
        self.activity_presets = {
            "Uniform": {
                "times": [0, 20, 40, 60, 90, 110],  # 分钟
                "mci_factors": [1.314, 1.632, 2.064, 2.588, 3.805, 4.816],  # 相对于扫描时刻的倍数
                "mbq_factors": [48.63, 60.39, 76.37, 95.76, 140.79, 178.19],  # 相对于扫描时刻的倍数
                "ideal_concentration": "6.45 kBq/mL (12.2 mCi / 70 kg)",
                "range": "6.10-7.45 kBq/mL"
            },
            "NEMA-IQ空腔": {
                "times": [0, 30, 60, 90, 110, 150],  # 分钟
                "volume": 9800,  # mL
                "activities": [2.25, 2.45, 2.75, 3.11, 3.42, 4.11],  # mCi
                "ideal_concentration": "8.51 kBq/mL (16.1 mCi / 70 kg)",
                "hot_sphere_ratio": "4/1"
            },
            "NEMA-IQ热球": {
                "times": [0, 30, 60, 90, 110, 150],  # 分钟
                "volume": 46.69,  # mL
                "activities": [0.0108, 0.0117, 0.0131, 0.0149, 0.0162, 0.0196],  # mCi
                "ideal_concentration": "8.51 kBq/mL (16.1 mCi / 70 kg)",
                "hot_sphere_ratio": "4/1"
            }
        }
        
        self.init_ui()
        self.load_saved_data()

    def init_ui(self):
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 顶部控制区域
        control_group = QGroupBox("📋 活度预设配置")
        control_layout = QGridLayout()
        
        # 模体类型选择
        control_layout.addWidget(QLabel("模体类型:"), 0, 0)
        self.phantom_type_combo = QComboBox()
        self.phantom_type_combo.addItems(list(self.activity_presets.keys()))
        self.phantom_type_combo.currentTextChanged.connect(self.on_phantom_type_changed)
        control_layout.addWidget(self.phantom_type_combo, 0, 1)
        
        # 扫描时刻活度输入（0min基准值）
        control_layout.addWidget(QLabel("扫描时刻活度:"), 0, 2)
        self.scan_activity_input = QLineEdit()
        self.scan_activity_input.setPlaceholderText("输入0min活度值")
        validator = QDoubleValidator(0.0, 10000.0, 3)
        self.scan_activity_input.setValidator(validator)
        self.scan_activity_input.textChanged.connect(self.calculate_activities)
        control_layout.addWidget(self.scan_activity_input, 0, 3)
        
        # 活度单位显示（只显示，不可修改）
        control_layout.addWidget(QLabel("单位:"), 0, 4)
        self.unit_display = QLabel()
        self.unit_display.setStyleSheet("QLabel { border: 1px solid #ccc; padding: 5px; background-color: #f9f9f9; }")
        control_layout.addWidget(self.unit_display, 0, 5)
        
        # 计算按钮
        self.calculate_btn = QPushButton("📊 计算活度序列")
        self.calculate_btn.setObjectName("primary")
        self.calculate_btn.clicked.connect(self.calculate_activities)
        control_layout.addWidget(self.calculate_btn, 0, 6)
        
        # 重置按钮
        self.reset_btn = QPushButton("🔄 重置数据")
        self.reset_btn.clicked.connect(self.reset_data)
        control_layout.addWidget(self.reset_btn, 0, 7)
        
        control_group.setLayout(control_layout)
        main_layout.addWidget(control_group)

        # 理想活度浓度信息
        info_group = QGroupBox("ℹ️ 参考信息")
        info_layout = QVBoxLayout()
        
        self.info_label = QLabel()
        self.info_label.setStyleSheet("color: #555; padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        info_layout.addWidget(self.info_label)
        
        info_group.setLayout(info_layout)
        main_layout.addWidget(info_group)

        # 活度数据表格
        table_group = QGroupBox("📈 活度时间序列")
        table_layout = QVBoxLayout()
        
        self.activity_table = QTableWidget()
        self.activity_table.setColumnCount(6)
        self.activity_table.setHorizontalHeaderLabels([
            '时间 (min)', '相对时刻', '计算活度', '单位', '备注', '状态'
        ])
        
        # 设置表格列宽
        header = self.activity_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        table_layout.addWidget(self.activity_table)
        
        # 表格操作按钮
        table_btn_layout = QHBoxLayout()
        
        self.export_btn = QPushButton("📤 导出数据")
        self.export_btn.clicked.connect(self.export_data)
        table_btn_layout.addWidget(self.export_btn)
        
        self.save_preset_btn = QPushButton("💾 保存为预设")
        self.save_preset_btn.clicked.connect(self.save_as_preset)
        table_btn_layout.addWidget(self.save_preset_btn)
        
        table_btn_layout.addStretch()
        
        self.status_label = QLabel("就绪 - 请选择模体类型并输入扫描时刻活度")
        self.status_label.setStyleSheet("color: #666;")
        table_btn_layout.addWidget(self.status_label)
        
        table_layout.addLayout(table_btn_layout)
        
        table_group.setLayout(table_layout)
        main_layout.addWidget(table_group, 1)  # stretch=1
        
        # 初始化显示
        self.on_phantom_type_changed()

    def get_current_unit(self):
        """获取当前活度单位"""
        if self.parent_window and hasattr(self.parent_window, 'activity_unit'):
            return self.parent_window.activity_unit
        return "mCi"

    def on_phantom_type_changed(self):
        """模体类型改变时的处理"""
        phantom_type = self.phantom_type_combo.currentText()
        preset = self.activity_presets.get(phantom_type, {})
        
        # 更新信息显示
        info_text = f"模体类型: {phantom_type}\n"
        if "ideal_concentration" in preset:
            info_text += f"理想活度浓度: {preset['ideal_concentration']}\n"
        if "range" in preset:
            info_text += f"范围: {preset['range']}\n"
        if "volume" in preset:
            info_text += f"体积: {preset['volume']} mL\n"
        if "hot_sphere_ratio" in preset:
            info_text += f"热球/背景比: {preset['hot_sphere_ratio']}\n"
        
        self.info_label.setText(info_text)
        
        # 更新单位显示
        self.unit_display.setText(self.get_current_unit())
        
        # 清空表格并重新计算
        self.clear_table()
        if self.scan_activity_input.text():
            self.calculate_activities()

    def on_unit_changed(self, new_unit):
        """全局单位改变时的处理"""
        # 更新单位显示
        self.unit_display.setText(new_unit)
        
        # 重新计算活度序列
        if self.scan_activity_input.text():
            self.calculate_activities()

    def calculate_activities(self):
        """计算活度序列"""
        try:
            scan_activity_text = self.scan_activity_input.text().strip()
            if not scan_activity_text:
                self.status_label.setText("请输入扫描时刻活度")
                return
                
            scan_activity = float(scan_activity_text)
            phantom_type = self.phantom_type_combo.currentText()
            unit = self.get_current_unit()  # 使用全局单位
            
            preset = self.activity_presets.get(phantom_type)
            if not preset:
                self.status_label.setText("未找到模体预设数据")
                return
            
            # 根据模体类型选择计算方法
            if phantom_type == "Uniform":
                self._calculate_uniform_activities(scan_activity, unit, preset)
            elif "NEMA-IQ" in phantom_type:
                self._calculate_nema_activities(scan_activity, unit, preset, phantom_type)
            
            self.status_label.setText(f"已计算 {self.activity_table.rowCount()} 个时间点的活度")
            
            # 保存数据
            self.save_to_experiment()
            
        except ValueError:
            self.status_label.setText("请输入有效的数值")
        except Exception as e:
            logging.error(f"计算活度失败: {e}")
            self.status_label.setText(f"计算失败: {str(e)}")

    def _calculate_uniform_activities(self, scan_activity, unit, preset):
        """计算Uniform模体的活度序列"""
        times = preset["times"]
        
        # 根据单位选择相应的因子
        if unit == "mCi":
            factors = preset["mci_factors"]
        elif unit == "MBq":
            factors = preset["mbq_factors"]
        else:
            # 对于其他单位，使用mCi因子并进行转换
            factors = preset["mci_factors"]
        
        self.activity_table.setRowCount(len(times))
        
        for i, (time_min, factor) in enumerate(zip(times, factors)):
            # 计算活度值
            if unit in ["mCi", "MBq"]:
                activity_value = scan_activity * factor
            else:
                # 其他单位需要转换
                mci_activity = scan_activity * self._convert_to_mci(1.0, unit)
                activity_value = mci_activity * factor
                activity_value = self._convert_from_mci(activity_value, unit)
            
            # 时间
            self.activity_table.setItem(i, 0, QTableWidgetItem(f"{time_min}"))
            
            # 相对时刻
            if time_min == 0:
                rel_time = "扫描时刻"
            else:
                rel_time = f"扫描前{time_min}分钟"
            self.activity_table.setItem(i, 1, QTableWidgetItem(rel_time))
            
            # 计算活度
            self.activity_table.setItem(i, 2, QTableWidgetItem(f"{activity_value:.3f}"))
            
            # 单位
            self.activity_table.setItem(i, 3, QTableWidgetItem(unit))
            
            # 备注
            if time_min == 0:
                remark = "基准时刻"
            else:
                remark = f"衰减系数: {factor:.3f}"
            self.activity_table.setItem(i, 4, QTableWidgetItem(remark))
            
            # 状态
            self.activity_table.setItem(i, 5, QTableWidgetItem("✓ 已计算"))

    def _calculate_nema_activities(self, scan_activity, unit, preset, phantom_type):
        """计算NEMA-IQ模体的活度序列"""
        times = preset["times"]
        activities = preset["activities"]  # 标准mCi值
        
        self.activity_table.setRowCount(len(times))
        
        for i, (time_min, std_activity) in enumerate(zip(times, activities)):
            # 根据扫描时刻活度计算比例因子
            if activities[0] > 0:  # 避免除零
                scale_factor = scan_activity / activities[0]
            else:
                scale_factor = 1.0
            
            # 计算活度值
            if unit == "mCi":
                activity_value = std_activity * scale_factor
            else:
                # 转换单位
                mci_value = std_activity * scale_factor
                activity_value = self._convert_from_mci(mci_value, unit)
            
            # 时间
            self.activity_table.setItem(i, 0, QTableWidgetItem(f"{time_min}"))
            
            # 相对时刻
            if time_min == 0:
                rel_time = "扫描时刻"
            else:
                rel_time = f"扫描前{time_min}分钟"
            self.activity_table.setItem(i, 1, QTableWidgetItem(rel_time))
            
            # 计算活度
            self.activity_table.setItem(i, 2, QTableWidgetItem(f"{activity_value:.4f}"))
            
            # 单位
            self.activity_table.setItem(i, 3, QTableWidgetItem(unit))
            
            # 备注
            volume = preset.get("volume", 0)
            if volume > 0:
                concentration = activity_value * 1000 / volume  # kBq/mL
                remark = f"浓度: {concentration:.2f} kBq/mL"
            else:
                remark = f"标准值: {std_activity:.4f} mCi"
            self.activity_table.setItem(i, 4, QTableWidgetItem(remark))
            
            # 状态
            self.activity_table.setItem(i, 5, QTableWidgetItem("✓ 已计算"))

    def _convert_activity(self, value, from_unit, to_unit):
        """活度单位转换"""
        if from_unit == to_unit:
            return value
        
        # 转换因子 (相对于mCi)
        factors = {
            "mCi": 1.0,
            "MBq": 37.0,
            "kBq": 37000.0,
            "Ci": 0.001,
            "GBq": 0.037
        }
        
        # 先转换到mCi
        mci_value = value / factors.get(from_unit, 1.0)
        # 再转换到目标单位
        return mci_value * factors.get(to_unit, 1.0)

    def _convert_to_mci(self, value, unit):
        """转换到mCi"""
        return self._convert_activity(value, unit, "mCi")

    def _convert_from_mci(self, value, unit):
        """从mCi转换"""
        return self._convert_activity(value, "mCi", unit)

    def clear_table(self):
        """清空表格"""
        self.activity_table.setRowCount(0)

    def reset_data(self):
        """重置数据"""
        reply = QMessageBox.question(
            self, "确认重置", "确定要重置所有数据吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.scan_activity_input.clear()
            self.clear_table()
            self.status_label.setText("数据已重置")

    def export_data(self):
        """导出数据"""
        if self.activity_table.rowCount() == 0:
            QMessageBox.information(self, "提示", "没有可导出的数据")
            return
        
        # 这里可以实现导出功能
        QMessageBox.information(self, "导出", "导出功能将在后续版本中实现")

    def save_as_preset(self):
        """保存为预设"""
        QMessageBox.information(self, "保存预设", "保存预设功能将在后续版本中实现")

    def save_to_experiment(self):
        """保存到实验数据"""
        try:
            activity_data = {
                "phantom_type": self.phantom_type_combo.currentText(),
                "scan_activity": self.scan_activity_input.text(),
                "unit": self.get_current_unit(),  # 使用全局单位
                "table_data": []
            }
            
            # 保存表格数据
            for row in range(self.activity_table.rowCount()):
                row_data = {}
                for col in range(self.activity_table.columnCount()):
                    item = self.activity_table.item(row, col)
                    row_data[f"col_{col}"] = item.text() if item else ""
                activity_data["table_data"].append(row_data)
            
            # 保存到实验参数
            self.experiment.parameters["activity_preset_data"] = activity_data
            
            # 发送更新信号
            self.activity_updated.emit(activity_data)
            
        except Exception as e:
            logging.error(f"保存活度预设数据失败: {e}")

    def load_saved_data(self):
        """加载保存的数据"""
        try:
            saved_data = self.experiment.parameters.get("activity_preset_data", {})
            if not saved_data:
                # 初始化单位显示
                self.unit_display.setText(self.get_current_unit())
                return
            
            # 恢复控件状态
            if "phantom_type" in saved_data:
                self.phantom_type_combo.setCurrentText(saved_data["phantom_type"])
            
            if "scan_activity" in saved_data:
                self.scan_activity_input.setText(saved_data["scan_activity"])
            
            # 更新单位显示（使用全局单位，不使用保存的单位）
            self.unit_display.setText(self.get_current_unit())
            
            # 恢复表格数据（需要重新计算以适应当前单位）
            if self.scan_activity_input.text():
                self.calculate_activities()
                
        except Exception as e:
            logging.error(f"加载活度预设数据失败: {e}")

    def update_activity_unit(self, new_unit):
        """更新活度单位"""
        self.on_unit_changed(new_unit) 
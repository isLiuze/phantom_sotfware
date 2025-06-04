1.梳理整个项目的逻辑，将程序的前端ui界面做的和专业级的软件一样，参考微软样式，要现代风格
2.梳理逻辑，找出明显不符合逻辑的地方
3.各种部件的布局要合理，都要尽可能的显示出来，整体界面的布局要舒服，
4，当在实验参数模块中切换活度按钮后，全局的包括标签和输入框都应该相应变化
5.当在实验参数中切换设备型号时，重建序列那里应该自动切换到当前设备的重建算法和重建参数，注意，不需要导入数据，该模块只是为了通过选择不同的参数，排列组合，来列出需要重建的序列，每当我在PET重建机上重建一个后，即可勾选，方便我记录，你可以加一个进度条等等：参考：from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QComboBox, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QHeaderView, QCheckBox, QSpinBox, QDoubleSpinBox,
    QProgressBar, QScrollArea, QSplitter, QTextEdit
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont
import itertools
import logging


class SequenceRebuildTab(QWidget):
    # 重建序列更新信号
    sequence_updated = pyqtSignal(dict)
    
    def __init__(self, experiment, parent=None):
        super().__init__(parent)
        self.experiment = experiment
        self.parent_window = parent
        
        # 设备类型的重建参数预设
        self.device_presets = {
            "Siemens Biograph mCT": {
                "algorithms": ["OSEM", "PSF", "TOF+PSF", "Q.Clear"],
                "iterations": [2, 3, 4, 5],
                "subsets": [10, 20],
                "matrix_size": ["256x256", "400x400", "512x512"],
                "filter": ["None", "Gaussian 2mm", "Gaussian 4mm", "Gaussian 6mm"],
                "zoom": [1.0, 2.0, 3.0],
                "slice_thickness": ["2.0mm", "3.0mm", "5.0mm"]
            },
            "GE Discovery MI": {
                "algorithms": ["OSEM", "Q.Clear", "Bayesian MAP", "OSEM+TOF"],
                "iterations": [2, 3, 4, 5],
                "subsets": [10, 20],
                "matrix_size": ["256x256", "384x384", "512x512"],
                "filter": ["None", "Butterworth", "Hann", "Gaussian"],
                "zoom": [1.0, 1.5, 2.0, 2.5],
                "slice_thickness": ["2.78mm", "3.27mm", "5.47mm"]
            },
            "Philips Vereos": {
                "algorithms": ["BLOB-OS-TF", "OSEM", "LOR-OSEM", "MAP"],
                "iterations": [2, 3, 4, 5],
                "subsets": [10, 20],
                "matrix_size": ["256x256", "384x384", "576x576"],
                "filter": ["None", "Gaussian", "Butterworth", "Shepp-Logan"],
                "zoom": [1.0, 1.5, 2.0],
                "slice_thickness": ["2.0mm", "4.0mm", "6.0mm"]
            },
            "United Imaging uEXPLORER": {
                "algorithms": ["OSEM", "TOF-OSEM", "MAP", "HYPER Iterative"],
                "iterations": [2, 3, 4, 5],
                "subsets": [10, 20, 30],
                "matrix_size": ["192x192", "256x256", "384x384"],
                "filter": ["None", "Gaussian", "Post-filter"],
                "zoom": [1.0, 2.0, 3.0],
                "slice_thickness": ["2.89mm", "4.33mm", "5.78mm"]
            },
            "Canon Celesteion": {
                "algorithms": ["OSEM", "DRAMA", "AiCE", "FBPEM"],
                "iterations": [2, 3, 4, 5],
                "subsets": [10, 20],
                "matrix_size": ["256x256", "384x384", "512x512"],
                "filter": ["None", "Gaussian", "Butterworth", "Ramp"],
                "zoom": [1.0, 1.5, 2.0],
                "slice_thickness": ["2.0mm", "3.0mm", "4.0mm"]
            }
        }
        
        self.reconstruction_sequences = []
        self.init_ui()
        self.load_saved_data()

    def init_ui(self):
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 顶部配置区域
        config_group = QGroupBox("⚙️ 重建参数配置")
        config_layout = QGridLayout()
        
        # 设备型号选择
        config_layout.addWidget(QLabel("设备型号:"), 0, 0)
        self.device_combo = QComboBox()
        self.device_combo.addItems(list(self.device_presets.keys()))
        self.device_combo.currentTextChanged.connect(self.on_device_changed)
        config_layout.addWidget(self.device_combo, 0, 1)
        
        # 重建算法选择
        config_layout.addWidget(QLabel("重建算法:"), 0, 2)
        self.algorithm_combo = QComboBox()
        self.algorithm_combo.setEditable(True)
        config_layout.addWidget(self.algorithm_combo, 0, 3)
        
        # 迭代次数范围
        config_layout.addWidget(QLabel("迭代次数:"), 1, 0)
        iter_layout = QHBoxLayout()
        self.iter_min_spin = QSpinBox()
        self.iter_min_spin.setRange(1, 20)
        self.iter_min_spin.setValue(2)
        iter_layout.addWidget(QLabel("从"))
        iter_layout.addWidget(self.iter_min_spin)
        iter_layout.addWidget(QLabel("到"))
        self.iter_max_spin = QSpinBox()
        self.iter_max_spin.setRange(1, 20)
        self.iter_max_spin.setValue(5)
        iter_layout.addWidget(self.iter_max_spin)
        config_layout.addLayout(iter_layout, 1, 1)
        
        # 子集数选择
        config_layout.addWidget(QLabel("子集数:"), 1, 2)
        subset_layout = QHBoxLayout()
        self.subset_10_cb = QCheckBox("10")
        self.subset_10_cb.setChecked(True)
        self.subset_20_cb = QCheckBox("20")
        self.subset_20_cb.setChecked(True)
        self.subset_30_cb = QCheckBox("30")
        subset_layout.addWidget(self.subset_10_cb)
        subset_layout.addWidget(self.subset_20_cb)
        subset_layout.addWidget(self.subset_30_cb)
        config_layout.addLayout(subset_layout, 1, 3)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        self.generate_btn = QPushButton("🔄 生成重建序列")
        self.generate_btn.setObjectName("primary")
        self.generate_btn.clicked.connect(self.generate_sequences)
        btn_layout.addWidget(self.generate_btn)
        
        self.clear_btn = QPushButton("🗑️ 清空序列")
        self.clear_btn.clicked.connect(self.clear_sequences)
        btn_layout.addWidget(self.clear_btn)
        
        self.export_btn = QPushButton("📤 导出配置")
        self.export_btn.clicked.connect(self.export_config)
        btn_layout.addWidget(self.export_btn)
        
        btn_layout.addStretch()
        config_layout.addLayout(btn_layout, 2, 0, 1, 4)
        
        config_group.setLayout(config_layout)
        main_layout.addWidget(config_group)

        # 高级参数区域
        advanced_group = QGroupBox("🔧 高级参数设置")
        advanced_layout = QGridLayout()
        
        # 矩阵大小
        advanced_layout.addWidget(QLabel("矩阵大小:"), 0, 0)
        self.matrix_combo = QComboBox()
        self.matrix_combo.setEditable(True)
        advanced_layout.addWidget(self.matrix_combo, 0, 1)
        
        # 滤波器
        advanced_layout.addWidget(QLabel("滤波器:"), 0, 2)
        self.filter_combo = QComboBox()
        self.filter_combo.setEditable(True)
        advanced_layout.addWidget(self.filter_combo, 0, 3)
        
        # 缩放因子
        advanced_layout.addWidget(QLabel("缩放因子:"), 1, 0)
        self.zoom_combo = QComboBox()
        self.zoom_combo.setEditable(True)
        advanced_layout.addWidget(self.zoom_combo, 1, 1)
        
        # 层厚
        advanced_layout.addWidget(QLabel("层厚:"), 1, 2)
        self.thickness_combo = QComboBox()
        self.thickness_combo.setEditable(True)
        advanced_layout.addWidget(self.thickness_combo, 1, 3)
        
        # 附加参数
        advanced_layout.addWidget(QLabel("附加参数:"), 2, 0)
        self.additional_params = QTextEdit()
        self.additional_params.setMaximumHeight(60)
        self.additional_params.setPlaceholderText("输入其他重建参数，每行一个参数...")
        advanced_layout.addWidget(self.additional_params, 2, 1, 1, 3)
        
        advanced_group.setLayout(advanced_layout)
        main_layout.addWidget(advanced_group)

        # 序列表格区域
        table_group = QGroupBox("📋 重建序列列表")
        table_layout = QVBoxLayout()
        
        # 统计信息
        self.stats_layout = QHBoxLayout()
        self.total_label = QLabel("总序列数: 0")
        self.completed_label = QLabel("已完成: 0")
        self.progress_label = QLabel("进度: 0%")
        self.stats_layout.addWidget(self.total_label)
        self.stats_layout.addWidget(self.completed_label)
        self.stats_layout.addWidget(self.progress_label)
        self.stats_layout.addStretch()
        
        # 全选操作
        self.select_all_btn = QPushButton("✓ 全选")
        self.select_all_btn.clicked.connect(self.select_all_sequences)
        self.stats_layout.addWidget(self.select_all_btn)
        
        self.deselect_all_btn = QPushButton("✗ 取消全选")
        self.deselect_all_btn.clicked.connect(self.deselect_all_sequences)
        self.stats_layout.addWidget(self.deselect_all_btn)
        
        table_layout.addLayout(self.stats_layout)
        
        # 重建序列表格
        self.sequence_table = QTableWidget()
        self.sequence_table.setColumnCount(9)
        self.sequence_table.setHorizontalHeaderLabels([
            '序号', '算法', '迭代', '子集', '矩阵', '滤波', '缩放', '完成状态', '备注'
        ])
        
        # 设置表格列宽
        header = self.sequence_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.Stretch)
        
        # 设置表格可以排序
        self.sequence_table.setSortingEnabled(True)
        
        table_layout.addWidget(self.sequence_table)
        
        table_group.setLayout(table_layout)
        main_layout.addWidget(table_group, 1)  # stretch=1
        
        # 状态栏
        self.status_label = QLabel("就绪 - 请选择设备型号并配置重建参数")
        self.status_label.setStyleSheet("color: #666; padding: 5px;")
        main_layout.addWidget(self.status_label)
        
        # 初始化设备预设
        self.on_device_changed()

    def on_device_changed(self):
        """设备型号改变时更新预设参数"""
        device = self.device_combo.currentText()
        if device in self.device_presets:
            preset = self.device_presets[device]
            
            # 更新算法列表
            self.algorithm_combo.clear()
            self.algorithm_combo.addItems(preset["algorithms"])
            
            # 更新矩阵大小
            self.matrix_combo.clear()
            self.matrix_combo.addItems(preset["matrix_size"])
            
            # 更新滤波器
            self.filter_combo.clear()
            self.filter_combo.addItems(preset["filter"])
            
            # 更新缩放因子
            self.zoom_combo.clear()
            self.zoom_combo.addItems([str(z) for z in preset["zoom"]])
            
            # 更新层厚
            self.thickness_combo.clear()
            self.thickness_combo.addItems(preset["slice_thickness"])
            
            # 更新迭代次数范围
            iterations = preset["iterations"]
            self.iter_min_spin.setValue(min(iterations))
            self.iter_max_spin.setValue(max(iterations))
            
            # 更新子集复选框
            subsets = preset["subsets"]
            self.subset_10_cb.setChecked(10 in subsets)
            self.subset_20_cb.setChecked(20 in subsets)
            self.subset_30_cb.setChecked(30 in subsets)
            
            self.status_label.setText(f"已加载 {device} 的预设参数")

    def generate_sequences(self):
        """生成重建序列"""
        try:
            # 获取配置参数
            device = self.device_combo.currentText()
            algorithms = [self.algorithm_combo.currentText()] if self.algorithm_combo.currentText() else []
            
            iterations = list(range(self.iter_min_spin.value(), self.iter_max_spin.value() + 1))
            
            subsets = []
            if self.subset_10_cb.isChecked():
                subsets.append(10)
            if self.subset_20_cb.isChecked():
                subsets.append(20)
            if self.subset_30_cb.isChecked():
                subsets.append(30)
                
            matrices = [self.matrix_combo.currentText()] if self.matrix_combo.currentText() else ["256x256"]
            filters = [self.filter_combo.currentText()] if self.filter_combo.currentText() else ["None"]
            zooms = [self.zoom_combo.currentText()] if self.zoom_combo.currentText() else ["1.0"]
            
            if not algorithms or not subsets:
                QMessageBox.warning(self, "参数错误", "请至少选择一个算法和一个子集数")
                return
            
            # 生成所有参数组合
            combinations = list(itertools.product(algorithms, iterations, subsets, matrices, filters, zooms))
            
            # 清空现有序列
            self.reconstruction_sequences.clear()
            self.sequence_table.setRowCount(len(combinations))
            
            # 填充表格
            for i, (algorithm, iteration, subset, matrix, filter_type, zoom) in enumerate(combinations):
                sequence_data = {
                    "sequence_id": i + 1,
                    "algorithm": algorithm,
                    "iterations": iteration,
                    "subsets": subset,
                    "matrix_size": matrix,
                    "filter": filter_type,
                    "zoom": zoom,
                    "completed": False,
                    "remark": f"{device} 标准配置"
                }
                
                self.reconstruction_sequences.append(sequence_data)
                
                # 添加到表格
                self.sequence_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
                self.sequence_table.setItem(i, 1, QTableWidgetItem(algorithm))
                self.sequence_table.setItem(i, 2, QTableWidgetItem(str(iteration)))
                self.sequence_table.setItem(i, 3, QTableWidgetItem(str(subset)))
                self.sequence_table.setItem(i, 4, QTableWidgetItem(matrix))
                self.sequence_table.setItem(i, 5, QTableWidgetItem(filter_type))
                self.sequence_table.setItem(i, 6, QTableWidgetItem(zoom))
                
                # 完成状态复选框
                completed_cb = QCheckBox()
                completed_cb.setChecked(False)
                completed_cb.stateChanged.connect(lambda state, row=i: self.on_completion_changed(row, state))
                self.sequence_table.setCellWidget(i, 7, completed_cb)
                
                self.sequence_table.setItem(i, 8, QTableWidgetItem(sequence_data["remark"]))
            
            # 更新统计信息
            self.update_statistics()
            
            self.status_label.setText(f"生成完成 - 共 {len(combinations)} 个重建序列")
            
            # 保存到实验参数
            self.save_to_experiment()
            
        except Exception as e:
            QMessageBox.critical(self, "生成错误", f"生成重建序列失败: {str(e)}")
            logging.error(f"生成重建序列失败: {e}")

    def on_completion_changed(self, row, state):
        """完成状态改变时的处理"""
        if row < len(self.reconstruction_sequences):
            self.reconstruction_sequences[row]["completed"] = (state == Qt.Checked)
            self.update_statistics()
            self.save_to_experiment()

    def update_statistics(self):
        """更新统计信息"""
        total = len(self.reconstruction_sequences)
        completed = sum(1 for seq in self.reconstruction_sequences if seq["completed"])
        progress = (completed / total * 100) if total > 0 else 0
        
        self.total_label.setText(f"总序列数: {total}")
        self.completed_label.setText(f"已完成: {completed}")
        self.progress_label.setText(f"进度: {progress:.1f}%")

    def select_all_sequences(self):
        """全选所有序列"""
        for row in range(self.sequence_table.rowCount()):
            cb = self.sequence_table.cellWidget(row, 7)
            if cb:
                cb.setChecked(True)

    def deselect_all_sequences(self):
        """取消全选"""
        for row in range(self.sequence_table.rowCount()):
            cb = self.sequence_table.cellWidget(row, 7)
            if cb:
                cb.setChecked(False)

    def clear_sequences(self):
        """清空所有序列"""
        reply = QMessageBox.question(
            self, "确认清空", "确定要清空所有重建序列吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.reconstruction_sequences.clear()
            self.sequence_table.setRowCount(0)
            self.update_statistics()
            self.status_label.setText("序列已清空 - 请重新生成重建序列")
            self.save_to_experiment()

    def export_config(self):
        """导出重建配置"""
        if not self.reconstruction_sequences:
            QMessageBox.warning(self, "警告", "没有可导出的重建序列")
            return
            
        from PyQt5.QtWidgets import QFileDialog
        import csv
        import json
        
        # 选择导出格式
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出重建配置", "", 
            "CSV Files (*.csv);;JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                if file_path.endswith('.json'):
                    # 导出为JSON格式
                    config_data = {
                        "device": self.device_combo.currentText(),
                        "sequences": self.reconstruction_sequences,
                        "generated_time": QTimer().currentDateTime().toString(),
                        "total_sequences": len(self.reconstruction_sequences),
                        "completed_sequences": sum(1 for seq in self.reconstruction_sequences if seq["completed"])
                    }
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(config_data, f, indent=2, ensure_ascii=False)
                else:
                    # 导出为CSV格式
                    with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                        writer = csv.writer(csvfile)
                        
                        # 写入表头
                        writer.writerow(['序号', '算法', '迭代次数', '子集数', '矩阵大小', '滤波器', '缩放因子', '完成状态', '备注'])
                        
                        # 写入数据
                        for seq in self.reconstruction_sequences:
                            writer.writerow([
                                seq["sequence_id"],
                                seq["algorithm"],
                                seq["iterations"],
                                seq["subsets"],
                                seq["matrix_size"],
                                seq["filter"],
                                seq["zoom"],
                                "是" if seq["completed"] else "否",
                                seq["remark"]
                            ])
                
                QMessageBox.information(self, "成功", f"重建配置已导出到:\n{file_path}")
                self.status_label.setText(f"配置已导出: {file_path.split('/')[-1]}")
                
            except Exception as e:
                QMessageBox.critical(self, "导出错误", f"导出失败:\n{str(e)}")

    def save_to_experiment(self):
        """保存重建序列到实验参数"""
        try:
            rebuild_data = {
                "device": self.device_combo.currentText(),
                "sequences": self.reconstruction_sequences,
                "config": {
                    "algorithm": self.algorithm_combo.currentText(),
                    "iter_min": self.iter_min_spin.value(),
                    "iter_max": self.iter_max_spin.value(),
                    "subset_10": self.subset_10_cb.isChecked(),
                    "subset_20": self.subset_20_cb.isChecked(),
                    "subset_30": self.subset_30_cb.isChecked(),
                    "matrix_size": self.matrix_combo.currentText(),
                    "filter": self.filter_combo.currentText(),
                    "zoom": self.zoom_combo.currentText(),
                    "thickness": self.thickness_combo.currentText(),
                    "additional_params": self.additional_params.toPlainText()
                }
            }
            
            # 保存到实验参数
            self.experiment.parameters["sequence_rebuild"] = rebuild_data
            
            # 触发保存
            if self.parent_window:
                self.parent_window._save_experiment()
                
            # 发送更新信号
            self.sequence_updated.emit(rebuild_data)
            
        except Exception as e:
            logging.error(f"保存重建序列失败: {e}")

    def load_saved_data(self):
        """加载已保存的数据"""
        try:
            rebuild_data = self.experiment.parameters.get("sequence_rebuild")
            if rebuild_data:
                # 恢复配置
                config = rebuild_data.get("config", {})
                self.device_combo.setCurrentText(rebuild_data.get("device", ""))
                self.algorithm_combo.setCurrentText(config.get("algorithm", ""))
                self.iter_min_spin.setValue(config.get("iter_min", 2))
                self.iter_max_spin.setValue(config.get("iter_max", 5))
                self.subset_10_cb.setChecked(config.get("subset_10", True))
                self.subset_20_cb.setChecked(config.get("subset_20", True))
                self.subset_30_cb.setChecked(config.get("subset_30", False))
                self.matrix_combo.setCurrentText(config.get("matrix_size", ""))
                self.filter_combo.setCurrentText(config.get("filter", ""))
                self.zoom_combo.setCurrentText(config.get("zoom", ""))
                self.thickness_combo.setCurrentText(config.get("thickness", ""))
                self.additional_params.setPlainText(config.get("additional_params", ""))
                
                # 恢复序列数据
                sequences = rebuild_data.get("sequences", [])
                self.reconstruction_sequences = sequences
                
                if sequences:
                    self.sequence_table.setRowCount(len(sequences))
                    
                    for i, seq in enumerate(sequences):
                        self.sequence_table.setItem(i, 0, QTableWidgetItem(str(seq.get("sequence_id", i+1))))
                        self.sequence_table.setItem(i, 1, QTableWidgetItem(seq.get("algorithm", "")))
                        self.sequence_table.setItem(i, 2, QTableWidgetItem(str(seq.get("iterations", ""))))
                        self.sequence_table.setItem(i, 3, QTableWidgetItem(str(seq.get("subsets", ""))))
                        self.sequence_table.setItem(i, 4, QTableWidgetItem(seq.get("matrix_size", "")))
                        self.sequence_table.setItem(i, 5, QTableWidgetItem(seq.get("filter", "")))
                        self.sequence_table.setItem(i, 6, QTableWidgetItem(seq.get("zoom", "")))
                        
                        # 完成状态复选框
                        completed_cb = QCheckBox()
                        completed_cb.setChecked(seq.get("completed", False))
                        completed_cb.stateChanged.connect(lambda state, row=i: self.on_completion_changed(row, state))
                        self.sequence_table.setCellWidget(i, 7, completed_cb)
                        
                        self.sequence_table.setItem(i, 8, QTableWidgetItem(seq.get("remark", "")))
                    
                    self.update_statistics()
                    self.status_label.setText("已加载保存的重建序列配置")
                
        except Exception as e:
            logging.error(f"加载重建序列失败: {e}") 

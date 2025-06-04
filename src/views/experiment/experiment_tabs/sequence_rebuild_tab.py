# src/views/experiment/experiment_tabs/sequence_rebuild_tab.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog, QMessageBox,
    QProgressBar, QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QTextCursor
import os
import sys
import subprocess
import logging

logger = logging.getLogger(__name__)


class SequenceRebuildTab(QWidget):
    def __init__(self, experiment, parent=None):
        super().__init__(parent)
        self.experiment = experiment
        self.parent_window = parent
        
        # 序列重建参数
        self.rebuild_params = self.experiment.parameters.get("sequence_rebuild", {
            "input_dir": "",
            "output_dir": "",
            "frame_duration": 10,  # 秒
            "total_frames": 36,
            "decay_correction": True,
            "attenuation_correction": False,
            "scatter_correction": False,
            "random_correction": True,
            "smoothing_filter": "Gaussian",
            "iterations": 4,
            "subsets": 16
        })
        
        self.init_ui()
        self.load_parameters()

    def init_ui(self):
        """初始化用户界面"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：参数设置区域
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # 输入输出路径设置
        path_group = QGroupBox("📁 路径设置")
        path_layout = QGridLayout()
        
        # 输入目录
        path_layout.addWidget(QLabel("输入目录:"), 0, 0)
        self.input_dir_edit = QLineEdit()
        self.input_dir_edit.setPlaceholderText("选择包含动态序列数据的目录")
        path_layout.addWidget(self.input_dir_edit, 0, 1)
        
        self.browse_input_btn = QPushButton("📂 浏览")
        self.browse_input_btn.clicked.connect(self.browse_input_directory)
        path_layout.addWidget(self.browse_input_btn, 0, 2)
        
        # 输出目录
        path_layout.addWidget(QLabel("输出目录:"), 1, 0)
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("选择重建结果保存目录")
        path_layout.addWidget(self.output_dir_edit, 1, 1)
        
        self.browse_output_btn = QPushButton("📂 浏览")
        self.browse_output_btn.clicked.connect(self.browse_output_directory)
        path_layout.addWidget(self.browse_output_btn, 1, 2)
        
        path_group.setLayout(path_layout)
        left_layout.addWidget(path_group)
        
        # 序列参数设置
        sequence_group = QGroupBox("⏱️ 序列参数")
        sequence_layout = QGridLayout()
        
        # 帧持续时间
        sequence_layout.addWidget(QLabel("帧持续时间 (秒):"), 0, 0)
        self.frame_duration_spin = QSpinBox()
        self.frame_duration_spin.setRange(1, 300)
        self.frame_duration_spin.setValue(10)
        self.frame_duration_spin.valueChanged.connect(self.save_parameters)
        sequence_layout.addWidget(self.frame_duration_spin, 0, 1)
        
        # 总帧数
        sequence_layout.addWidget(QLabel("总帧数:"), 0, 2)
        self.total_frames_spin = QSpinBox()
        self.total_frames_spin.setRange(1, 100)
        self.total_frames_spin.setValue(36)
        self.total_frames_spin.valueChanged.connect(self.save_parameters)
        sequence_layout.addWidget(self.total_frames_spin, 0, 3)
        
        # 扫描总时间显示
        self.total_time_label = QLabel("总时间: 6分钟")
        self.total_time_label.setStyleSheet("color: #1976d2; font-weight: bold;")
        sequence_layout.addWidget(self.total_time_label, 1, 0, 1, 4)
        
        # 连接信号更新总时间
        self.frame_duration_spin.valueChanged.connect(self.update_total_time)
        self.total_frames_spin.valueChanged.connect(self.update_total_time)
        
        sequence_group.setLayout(sequence_layout)
        left_layout.addWidget(sequence_group)
        
        # 校正选项
        correction_group = QGroupBox("🔧 校正选项")
        correction_layout = QGridLayout()
        
        self.decay_correction_cb = QCheckBox("衰减校正")
        self.decay_correction_cb.setChecked(True)
        self.decay_correction_cb.toggled.connect(self.save_parameters)
        correction_layout.addWidget(self.decay_correction_cb, 0, 0)
        
        self.attenuation_correction_cb = QCheckBox("衰减校正")
        self.attenuation_correction_cb.toggled.connect(self.save_parameters)
        correction_layout.addWidget(self.attenuation_correction_cb, 0, 1)
        
        self.scatter_correction_cb = QCheckBox("散射校正")
        self.scatter_correction_cb.toggled.connect(self.save_parameters)
        correction_layout.addWidget(self.scatter_correction_cb, 1, 0)
        
        self.random_correction_cb = QCheckBox("随机符合校正")
        self.random_correction_cb.setChecked(True)
        self.random_correction_cb.toggled.connect(self.save_parameters)
        correction_layout.addWidget(self.random_correction_cb, 1, 1)
        
        correction_group.setLayout(correction_layout)
        left_layout.addWidget(correction_group)
        
        # 重建参数
        recon_group = QGroupBox("⚙️ 重建参数")
        recon_layout = QGridLayout()
        
        # 平滑滤波器
        recon_layout.addWidget(QLabel("平滑滤波器:"), 0, 0)
        self.smoothing_combo = QComboBox()
        self.smoothing_combo.addItems(["Gaussian", "Butterworth", "Hamming", "Hann"])
        self.smoothing_combo.currentTextChanged.connect(self.save_parameters)
        recon_layout.addWidget(self.smoothing_combo, 0, 1)
        
        # 迭代次数
        recon_layout.addWidget(QLabel("迭代次数:"), 1, 0)
        self.iterations_spin = QSpinBox()
        self.iterations_spin.setRange(1, 20)
        self.iterations_spin.setValue(4)
        self.iterations_spin.valueChanged.connect(self.save_parameters)
        recon_layout.addWidget(self.iterations_spin, 1, 1)
        
        # 子集数
        recon_layout.addWidget(QLabel("子集数:"), 1, 2)
        self.subsets_spin = QSpinBox()
        self.subsets_spin.setRange(1, 32)
        self.subsets_spin.setValue(16)
        self.subsets_spin.valueChanged.connect(self.save_parameters)
        recon_layout.addWidget(self.subsets_spin, 1, 3)
        
        recon_group.setLayout(recon_layout)
        left_layout.addWidget(recon_group)
        
        # 控制按钮
        control_group = QGroupBox("🎮 控制")
        control_layout = QHBoxLayout()
        
        self.validate_btn = QPushButton("✅ 验证设置")
        self.validate_btn.setObjectName("primary")
        self.validate_btn.clicked.connect(self.validate_settings)
        control_layout.addWidget(self.validate_btn)
        
        self.start_rebuild_btn = QPushButton("🚀 开始重建")
        self.start_rebuild_btn.setObjectName("success")
        self.start_rebuild_btn.clicked.connect(self.start_rebuild)
        control_layout.addWidget(self.start_rebuild_btn)
        
        self.stop_rebuild_btn = QPushButton("⏹️ 停止重建")
        self.stop_rebuild_btn.setObjectName("danger")
        self.stop_rebuild_btn.setEnabled(False)
        self.stop_rebuild_btn.clicked.connect(self.stop_rebuild)
        control_layout.addWidget(self.stop_rebuild_btn)
        
        control_layout.addStretch()
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        control_layout.addWidget(self.progress_bar)
        
        control_group.setLayout(control_layout)
        left_layout.addWidget(control_group)
        
        left_layout.addStretch()
        splitter.addWidget(left_widget)
        
        # 右侧：日志和结果显示区域
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 重建日志
        log_group = QGroupBox("📋 重建日志")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        font = QFont("Consolas", 9)
        self.log_text.setFont(font)
        log_layout.addWidget(self.log_text)
        
        # 日志控制按钮
        log_control_layout = QHBoxLayout()
        
        self.clear_log_btn = QPushButton("🗑️ 清空日志")
        self.clear_log_btn.clicked.connect(self.clear_log)
        log_control_layout.addWidget(self.clear_log_btn)
        
        self.save_log_btn = QPushButton("💾 保存日志")
        self.save_log_btn.clicked.connect(self.save_log)
        log_control_layout.addWidget(self.save_log_btn)
        
        log_control_layout.addStretch()
        
        log_layout.addLayout(log_control_layout)
        log_group.setLayout(log_layout)
        right_layout.addWidget(log_group)
        
        # 文件列表
        files_group = QGroupBox("📁 文件列表")
        files_layout = QVBoxLayout()
        
        self.files_table = QTableWidget()
        self.files_table.setColumnCount(4)
        self.files_table.setHorizontalHeaderLabels(["文件名", "大小", "修改时间", "状态"])
        
        # 设置表格列宽
        header = self.files_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        files_layout.addWidget(self.files_table)
        
        # 文件操作按钮
        files_control_layout = QHBoxLayout()
        
        self.refresh_files_btn = QPushButton("🔄 刷新文件列表")
        self.refresh_files_btn.clicked.connect(self.refresh_file_list)
        files_control_layout.addWidget(self.refresh_files_btn)
        
        self.open_output_btn = QPushButton("📂 打开输出目录")
        self.open_output_btn.clicked.connect(self.open_output_directory)
        files_control_layout.addWidget(self.open_output_btn)
        
        files_control_layout.addStretch()
        
        files_layout.addLayout(files_control_layout)
        files_group.setLayout(files_layout)
        right_layout.addWidget(files_group)
        
        splitter.addWidget(right_widget)
        
        # 设置分割器比例 (左:右 = 1:1)
        splitter.setSizes([400, 400])
        
        main_layout.addWidget(splitter)
        
        # 初始化状态
        self.update_total_time()
        self.add_log("序列重建模块已初始化")

    def update_total_time(self):
        """更新总时间显示"""
        duration = self.frame_duration_spin.value()
        frames = self.total_frames_spin.value()
        total_seconds = duration * frames
        
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        
        if minutes > 0:
            time_str = f"{minutes}分{seconds}秒" if seconds > 0 else f"{minutes}分钟"
        else:
            time_str = f"{seconds}秒"
        
        self.total_time_label.setText(f"总时间: {time_str}")

    def browse_input_directory(self):
        """浏览输入目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择输入目录", 
            self.input_dir_edit.text() or os.path.expanduser("~")
        )
        
        if dir_path:
            self.input_dir_edit.setText(dir_path)
            self.save_parameters()
            self.refresh_file_list()
            self.add_log(f"设置输入目录: {dir_path}")

    def browse_output_directory(self):
        """浏览输出目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择输出目录",
            self.output_dir_edit.text() or os.path.expanduser("~")
        )
        
        if dir_path:
            self.output_dir_edit.setText(dir_path)
            self.save_parameters()
            self.add_log(f"设置输出目录: {dir_path}")

    def refresh_file_list(self):
        """刷新文件列表"""
        input_dir = self.input_dir_edit.text().strip()
        if not input_dir or not os.path.exists(input_dir):
            self.files_table.setRowCount(0)
            return
        
        try:
            files = []
            for filename in os.listdir(input_dir):
                file_path = os.path.join(input_dir, filename)
                if os.path.isfile(file_path):
                    stat = os.stat(file_path)
                    files.append({
                        'name': filename,
                        'size': f"{stat.st_size / (1024*1024):.1f} MB",
                        'mtime': os.path.getmtime(file_path),
                        'status': '待处理'
                    })
            
            # 按修改时间排序
            files.sort(key=lambda x: x['mtime'], reverse=True)
            
            self.files_table.setRowCount(len(files))
            for row, file_info in enumerate(files):
                self.files_table.setItem(row, 0, QTableWidgetItem(file_info['name']))
                self.files_table.setItem(row, 1, QTableWidgetItem(file_info['size']))
                
                # 格式化时间
                import datetime
                mtime_str = datetime.datetime.fromtimestamp(file_info['mtime']).strftime('%Y-%m-%d %H:%M:%S')
                self.files_table.setItem(row, 2, QTableWidgetItem(mtime_str))
                self.files_table.setItem(row, 3, QTableWidgetItem(file_info['status']))
            
            self.add_log(f"刷新文件列表完成，找到 {len(files)} 个文件")
            
        except Exception as e:
            self.add_log(f"刷新文件列表失败: {str(e)}", "ERROR")

    def validate_settings(self):
        """验证设置"""
        errors = []
        
        # 检查输入目录
        input_dir = self.input_dir_edit.text().strip()
        if not input_dir:
            errors.append("请选择输入目录")
        elif not os.path.exists(input_dir):
            errors.append("输入目录不存在")
        
        # 检查输出目录
        output_dir = self.output_dir_edit.text().strip()
        if not output_dir:
            errors.append("请选择输出目录")
        else:
            # 如果输出目录不存在，尝试创建
            try:
                os.makedirs(output_dir, exist_ok=True)
            except Exception as e:
                errors.append(f"无法创建输出目录: {str(e)}")
        
        # 检查参数范围
        if self.frame_duration_spin.value() <= 0:
            errors.append("帧持续时间必须大于0")
        
        if self.total_frames_spin.value() <= 0:
            errors.append("总帧数必须大于0")
        
        if errors:
            error_msg = "验证失败:\\n" + "\\n".join(errors)
            QMessageBox.warning(self, "验证失败", error_msg)
            self.add_log("设置验证失败", "ERROR")
            for error in errors:
                self.add_log(f"  - {error}", "ERROR")
            return False
        else:
            QMessageBox.information(self, "验证成功", "所有设置都有效，可以开始重建！")
            self.add_log("设置验证成功", "SUCCESS")
            return True

    def start_rebuild(self):
        """开始重建"""
        if not self.validate_settings():
            return
        
        # 模拟重建过程
        self.add_log("开始序列重建...", "INFO")
        self.add_log(f"输入目录: {self.input_dir_edit.text()}")
        self.add_log(f"输出目录: {self.output_dir_edit.text()}")
        self.add_log(f"帧持续时间: {self.frame_duration_spin.value()}秒")
        self.add_log(f"总帧数: {self.total_frames_spin.value()}")
        
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 禁用开始按钮，启用停止按钮
        self.start_rebuild_btn.setEnabled(False)
        self.stop_rebuild_btn.setEnabled(True)
        
        # 模拟重建过程（这里应该调用实际的重建算法）
        self.simulate_rebuild()

    def simulate_rebuild(self):
        """模拟重建过程"""
        self.rebuild_timer = QTimer()
        self.rebuild_progress = 0
        self.rebuild_timer.timeout.connect(self.update_rebuild_progress)
        self.rebuild_timer.start(200)  # 每200ms更新一次

    def update_rebuild_progress(self):
        """更新重建进度"""
        self.rebuild_progress += 2
        self.progress_bar.setValue(self.rebuild_progress)
        
        if self.rebuild_progress >= 100:
            self.rebuild_timer.stop()
            self.rebuild_finished()
        else:
            # 模拟重建日志
            if self.rebuild_progress % 10 == 0:
                frame_num = self.rebuild_progress // 10
                self.add_log(f"正在重建第 {frame_num} 帧...")

    def rebuild_finished(self):
        """重建完成"""
        self.add_log("序列重建完成！", "SUCCESS")
        self.progress_bar.setVisible(False)
        self.start_rebuild_btn.setEnabled(True)
        self.stop_rebuild_btn.setEnabled(False)
        
        # 更新文件列表状态
        for row in range(self.files_table.rowCount()):
            self.files_table.setItem(row, 3, QTableWidgetItem("已处理"))
        
        QMessageBox.information(self, "重建完成", "序列重建已成功完成！")

    def stop_rebuild(self):
        """停止重建"""
        reply = QMessageBox.question(
            self, "停止重建", "确定要停止当前的重建过程吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if hasattr(self, 'rebuild_timer'):
                self.rebuild_timer.stop()
            
            self.add_log("重建过程已停止", "WARNING")
            self.progress_bar.setVisible(False)
            self.start_rebuild_btn.setEnabled(True)
            self.stop_rebuild_btn.setEnabled(False)

    def open_output_directory(self):
        """打开输出目录"""
        output_dir = self.output_dir_edit.text().strip()
        if not output_dir:
            QMessageBox.warning(self, "警告", "请先设置输出目录")
            return
        
        if not os.path.exists(output_dir):
            QMessageBox.warning(self, "警告", "输出目录不存在")
            return
        
        try:
            if sys.platform == "win32":
                os.startfile(output_dir)
            elif sys.platform == "darwin":
                subprocess.run(["open", output_dir])
            else:
                subprocess.run(["xdg-open", output_dir])
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法打开目录: {str(e)}")

    def add_log(self, message, level="INFO"):
        """添加日志"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        if level == "ERROR":
            color = "red"
        elif level == "WARNING":
            color = "orange"
        elif level == "SUCCESS":
            color = "green"
        else:
            color = "black"
        
        formatted_msg = f'<span style="color: gray;">[{timestamp}]</span> <span style="color: {color};">[{level}]</span> {message}'
        
        self.log_text.append(formatted_msg)
        
        # 滚动到底部
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_text.setTextCursor(cursor)

    def clear_log(self):
        """清空日志"""
        self.log_text.clear()
        self.add_log("日志已清空")

    def save_log(self):
        """保存日志"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存日志", "rebuild_log.txt", "文本文件 (*.txt);;所有文件 (*)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    # 保存纯文本格式的日志
                    plain_text = self.log_text.toPlainText()
                    f.write(plain_text)
                
                QMessageBox.information(self, "保存成功", f"日志已保存到: {filename}")
            except Exception as e:
                QMessageBox.warning(self, "保存失败", f"保存日志失败: {str(e)}")

    def save_parameters(self):
        """保存参数到实验"""
        try:
            self.rebuild_params.update({
                "input_dir": self.input_dir_edit.text().strip(),
                "output_dir": self.output_dir_edit.text().strip(),
                "frame_duration": self.frame_duration_spin.value(),
                "total_frames": self.total_frames_spin.value(),
                "decay_correction": self.decay_correction_cb.isChecked(),
                "attenuation_correction": self.attenuation_correction_cb.isChecked(),
                "scatter_correction": self.scatter_correction_cb.isChecked(),
                "random_correction": self.random_correction_cb.isChecked(),
                "smoothing_filter": self.smoothing_combo.currentText(),
                "iterations": self.iterations_spin.value(),
                "subsets": self.subsets_spin.value()
            })
            
            self.experiment.parameters["sequence_rebuild"] = self.rebuild_params
            
            # 保存实验
            if hasattr(self.parent_window, '_save_experiment'):
                self.parent_window._save_experiment()
                
        except Exception as e:
            logger.error(f"保存序列重建参数失败: {e}")

    def load_parameters(self):
        """加载参数"""
        try:
            params = self.rebuild_params
            
            self.input_dir_edit.setText(params.get("input_dir", ""))
            self.output_dir_edit.setText(params.get("output_dir", ""))
            self.frame_duration_spin.setValue(params.get("frame_duration", 10))
            self.total_frames_spin.setValue(params.get("total_frames", 36))
            
            self.decay_correction_cb.setChecked(params.get("decay_correction", True))
            self.attenuation_correction_cb.setChecked(params.get("attenuation_correction", False))
            self.scatter_correction_cb.setChecked(params.get("scatter_correction", False))
            self.random_correction_cb.setChecked(params.get("random_correction", True))
            
            self.smoothing_combo.setCurrentText(params.get("smoothing_filter", "Gaussian"))
            self.iterations_spin.setValue(params.get("iterations", 4))
            self.subsets_spin.setValue(params.get("subsets", 16))
            
            # 如果有输入目录，刷新文件列表
            if params.get("input_dir"):
                self.refresh_file_list()
                
        except Exception as e:
            logger.error(f"加载序列重建参数失败: {e}") 
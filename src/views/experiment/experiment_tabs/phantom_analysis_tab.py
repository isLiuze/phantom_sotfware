# src/views/experiment/experiment_tabs/phantom_analysis_tab.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter, QComboBox,
    QCheckBox, QSpinBox, QDoubleSpinBox, QProgressBar, QTabWidget, QScrollArea,
    QListWidget, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QThread
from PyQt5.QtGui import QFont, QPixmap, QPainter, QPen, QBrush, QColor, QIcon
import os
import sys
import logging
import numpy as np
import json
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import csv
import pydicom
import matplotlib
matplotlib.use('Qt5Agg')
plt.style.use('default')

logger = logging.getLogger(__name__)


class DicomAnalysisWorker(QThread):
    """DICOM分析工作线程"""
    progress_updated = pyqtSignal(int)
    analysis_completed = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, dicom_files):
        super().__init__()
        self.dicom_files = dicom_files
        
    def run(self):
        try:
            analysis_results = {}
            total_files = len(self.dicom_files)
            
            for i, file_path in enumerate(self.dicom_files):
                try:
                    # 简化的DICOM分析（可扩展为真实的pydicom实现）
                    # 这里模拟分析结果
                    filename = os.path.basename(file_path)
                    
                    # 模拟图像数据
                    image_data = np.random.randint(0, 255, (512, 512), dtype=np.uint8)
                    
                    # 基本统计信息
                    stats = {
                        'mean': np.mean(image_data),
                        'std': np.std(image_data),
                        'min': np.min(image_data),
                        'max': np.max(image_data),
                        'median': np.median(image_data),
                        'shape': image_data.shape
                    }
                    
                    analysis_results[filename] = {
                        'stats': stats,
                        'pixel_array': image_data,
                        'metadata': {
                            'PatientName': 'PET_Phantom',
                            'StudyDate': '20240101',
                            'Modality': 'PT',
                            'SliceThickness': '3.0',
                            'PixelSpacing': '[2.0, 2.0]'
                        }
                    }
                    
                    progress = int((i + 1) / total_files * 100)
                    self.progress_updated.emit(progress)
                    
                except Exception as e:
                    logging.error(f"分析DICOM文件失败 {file_path}: {e}")
                    continue
                    
            self.analysis_completed.emit(analysis_results)
            
        except Exception as e:
            self.error_occurred.emit(str(e))


class MatplotlibWidget(QWidget):
    """matplotlib绘图组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        
    def clear(self):
        self.figure.clear()
        self.canvas.draw()
        
    def plot_image(self, image_data, title="DICOM图像"):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        im = ax.imshow(image_data, cmap='gray')
        ax.set_title(title)
        self.figure.colorbar(im, ax=ax)
        self.canvas.draw()
        
    def plot_histogram(self, image_data, title="像素值分布"):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.hist(image_data.flatten(), bins=100, alpha=0.7)
        ax.set_title(title)
        ax.set_xlabel('像素值')
        ax.set_ylabel('频次')
        self.canvas.draw()


class PhantomAnalysisTab(QWidget):
    def __init__(self, experiment, parent=None):
        super().__init__(parent)
        self.experiment = experiment
        self.parent_window = parent
        self.dicom_files = []
        self.analysis_results = {}
        self.current_image_data = None
        
        # 分析参数
        self.analysis_params = self.experiment.parameters.get("phantom_analysis", {
            "analysis_type": "Uniform",  # Uniform, NEMA-IQ
            "roi_settings": {
                "center_x": 128,
                "center_y": 128,
                "radius": 50,
                "background_radius": 80
            },
            "sphere_settings": {
                "sphere_positions": [],  # [(x, y, r), ...]
                "hot_sphere_ratio": 4.0
            },
            "uniformity_settings": {
                "threshold": 0.1,
                "include_edges": False
            },
            "export_settings": {
                "include_images": True,
                "include_statistics": True,
                "format": "Excel"
            }
        })
        
        self.init_ui()
        self.load_parameters()

    def init_ui(self):
        """初始化用户界面"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 创建标签页
        tab_widget = QTabWidget()
        
        # 第一个标签页：分析设置
        settings_tab = self.create_settings_tab()
        tab_widget.addTab(settings_tab, "⚙️ 分析设置")
        
        # 第二个标签页：结果显示
        results_tab = self.create_results_tab()
        tab_widget.addTab(results_tab, "📊 分析结果")
        
        # 第三个标签页：图像显示
        images_tab = self.create_images_tab()
        tab_widget.addTab(images_tab, "🖼️ 图像显示")
        
        main_layout.addWidget(tab_widget)

    def create_settings_tab(self):
        """创建设置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 分析类型选择
        type_group = QGroupBox("📋 分析类型")
        type_layout = QHBoxLayout()
        
        self.analysis_type_combo = QComboBox()
        self.analysis_type_combo.addItems(["Uniform", "NEMA-IQ"])
        self.analysis_type_combo.currentTextChanged.connect(self.on_analysis_type_changed)
        type_layout.addWidget(QLabel("分析类型:"))
        type_layout.addWidget(self.analysis_type_combo)
        type_layout.addStretch()
        
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)
        
        # ROI设置
        roi_group = QGroupBox("🎯 ROI设置")
        roi_layout = QGridLayout()
        
        # 中心位置
        roi_layout.addWidget(QLabel("中心X坐标:"), 0, 0)
        self.center_x_spin = QSpinBox()
        self.center_x_spin.setRange(0, 512)
        self.center_x_spin.setValue(128)
        self.center_x_spin.valueChanged.connect(self.save_parameters)
        roi_layout.addWidget(self.center_x_spin, 0, 1)
        
        roi_layout.addWidget(QLabel("中心Y坐标:"), 0, 2)
        self.center_y_spin = QSpinBox()
        self.center_y_spin.setRange(0, 512)
        self.center_y_spin.setValue(128)
        self.center_y_spin.valueChanged.connect(self.save_parameters)
        roi_layout.addWidget(self.center_y_spin, 0, 3)
        
        # 半径设置
        roi_layout.addWidget(QLabel("主ROI半径:"), 1, 0)
        self.roi_radius_spin = QSpinBox()
        self.roi_radius_spin.setRange(10, 200)
        self.roi_radius_spin.setValue(50)
        self.roi_radius_spin.valueChanged.connect(self.save_parameters)
        roi_layout.addWidget(self.roi_radius_spin, 1, 1)
        
        roi_layout.addWidget(QLabel("背景ROI半径:"), 1, 2)
        self.bg_radius_spin = QSpinBox()
        self.bg_radius_spin.setRange(20, 300)
        self.bg_radius_spin.setValue(80)
        self.bg_radius_spin.valueChanged.connect(self.save_parameters)
        roi_layout.addWidget(self.bg_radius_spin, 1, 3)
        
        roi_group.setLayout(roi_layout)
        layout.addWidget(roi_group)
        
        # 分析参数
        analysis_group = QGroupBox("📊 分析参数")
        analysis_layout = QGridLayout()
        
        # 均匀性阈值
        analysis_layout.addWidget(QLabel("均匀性阈值:"), 0, 0)
        self.uniformity_threshold_spin = QDoubleSpinBox()
        self.uniformity_threshold_spin.setRange(0.01, 1.0)
        self.uniformity_threshold_spin.setDecimals(3)
        self.uniformity_threshold_spin.setSingleStep(0.01)
        self.uniformity_threshold_spin.setValue(0.1)
        self.uniformity_threshold_spin.valueChanged.connect(self.save_parameters)
        analysis_layout.addWidget(self.uniformity_threshold_spin, 0, 1)
        
        # 热球/背景比
        analysis_layout.addWidget(QLabel("热球/背景比:"), 0, 2)
        self.hot_sphere_ratio_spin = QDoubleSpinBox()
        self.hot_sphere_ratio_spin.setRange(1.0, 10.0)
        self.hot_sphere_ratio_spin.setDecimals(1)
        self.hot_sphere_ratio_spin.setValue(4.0)
        self.hot_sphere_ratio_spin.valueChanged.connect(self.save_parameters)
        analysis_layout.addWidget(self.hot_sphere_ratio_spin, 0, 3)
        
        # 边缘包含选项
        self.include_edges_cb = QCheckBox("包含边缘像素")
        self.include_edges_cb.toggled.connect(self.save_parameters)
        analysis_layout.addWidget(self.include_edges_cb, 1, 0, 1, 2)
        
        analysis_group.setLayout(analysis_layout)
        layout.addWidget(analysis_group)
        
        # 文件选择
        files_group = QGroupBox("📁 文件选择")
        files_layout = QGridLayout()
        
        # 图像文件
        files_layout.addWidget(QLabel("图像文件:"), 0, 0)
        self.image_file_edit = QLineEdit()
        self.image_file_edit.setPlaceholderText("选择要分析的图像文件")
        files_layout.addWidget(self.image_file_edit, 0, 1)
        
        self.browse_image_btn = QPushButton("📂 浏览")
        self.browse_image_btn.clicked.connect(self.browse_image_file)
        files_layout.addWidget(self.browse_image_btn, 0, 2)
        
        # 输出目录
        files_layout.addWidget(QLabel("输出目录:"), 1, 0)
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("选择分析结果保存目录")
        files_layout.addWidget(self.output_dir_edit, 1, 1)
        
        self.browse_output_btn = QPushButton("📂 浏览")
        self.browse_output_btn.clicked.connect(self.browse_output_directory)
        files_layout.addWidget(self.browse_output_btn, 1, 2)
        
        files_group.setLayout(files_layout)
        layout.addWidget(files_group)
        
        # 控制按钮
        control_group = QGroupBox("🎮 控制")
        control_layout = QHBoxLayout()
        
        self.load_image_btn = QPushButton("📥 加载图像")
        self.load_image_btn.setObjectName("primary")
        self.load_image_btn.clicked.connect(self.load_image)
        control_layout.addWidget(self.load_image_btn)
        
        self.start_analysis_btn = QPushButton("🚀 开始分析")
        self.start_analysis_btn.setObjectName("success")
        self.start_analysis_btn.clicked.connect(self.start_analysis)
        control_layout.addWidget(self.start_analysis_btn)
        
        self.export_results_btn = QPushButton("📤 导出结果")
        self.export_results_btn.setObjectName("info")
        self.export_results_btn.clicked.connect(self.export_results)
        control_layout.addWidget(self.export_results_btn)
        
        control_layout.addStretch()
        
        # 进度条
        self.analysis_progress = QProgressBar()
        self.analysis_progress.setVisible(False)
        control_layout.addWidget(self.analysis_progress)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        layout.addStretch()
        return tab

    def create_results_tab(self):
        """创建结果标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 创建分割器
        splitter = QSplitter(Qt.Vertical)
        
        # 上部：统计结果表格
        stats_group = QGroupBox("📊 统计结果")
        stats_layout = QVBoxLayout()
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(["参数", "数值", "单位"])
        
        # 设置表格列宽
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        stats_layout.addWidget(self.results_table)
        stats_group.setLayout(stats_layout)
        splitter.addWidget(stats_group)
        
        # 下部：详细分析日志
        log_group = QGroupBox("📋 分析日志")
        log_layout = QVBoxLayout()
        
        self.analysis_log = QTextEdit()
        self.analysis_log.setReadOnly(True)
        self.analysis_log.setMaximumHeight(150)
        font = QFont("Consolas", 9)
        self.analysis_log.setFont(font)
        log_layout.addWidget(self.analysis_log)
        
        # 日志控制按钮
        log_control_layout = QHBoxLayout()
        
        self.clear_analysis_log_btn = QPushButton("🗑️ 清空日志")
        self.clear_analysis_log_btn.clicked.connect(self.clear_analysis_log)
        log_control_layout.addWidget(self.clear_analysis_log_btn)
        
        self.save_analysis_log_btn = QPushButton("💾 保存日志")
        self.save_analysis_log_btn.clicked.connect(self.save_analysis_log)
        log_control_layout.addWidget(self.save_analysis_log_btn)
        
        log_control_layout.addStretch()
        
        log_layout.addLayout(log_control_layout)
        log_group.setLayout(log_layout)
        splitter.addWidget(log_group)
        
        layout.addWidget(splitter)
        return tab

    def create_images_tab(self):
        """创建图像标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 图像显示控制
        image_control_group = QGroupBox("🖼️ 图像显示")
        image_control_layout = QHBoxLayout()
        
        self.show_roi_cb = QCheckBox("显示ROI")
        self.show_roi_cb.setChecked(True)
        self.show_roi_cb.toggled.connect(self.update_image_display)
        image_control_layout.addWidget(self.show_roi_cb)
        
        self.show_background_cb = QCheckBox("显示背景ROI")
        self.show_background_cb.setChecked(True)
        self.show_background_cb.toggled.connect(self.update_image_display)
        image_control_layout.addWidget(self.show_background_cb)
        
        self.show_spheres_cb = QCheckBox("显示热球")
        self.show_spheres_cb.setChecked(True)
        self.show_spheres_cb.toggled.connect(self.update_image_display)
        image_control_layout.addWidget(self.show_spheres_cb)
        
        image_control_layout.addStretch()
        
        self.refresh_image_btn = QPushButton("🔄 刷新显示")
        self.refresh_image_btn.clicked.connect(self.update_image_display)
        image_control_layout.addWidget(self.refresh_image_btn)
        
        image_control_group.setLayout(image_control_layout)
        layout.addWidget(image_control_group)
        
        # 图像显示区域
        image_group = QGroupBox("📸 图像")
        image_layout = QVBoxLayout()
        
        # 这里应该是图像显示控件，简化为标签
        self.image_display = QLabel("图像将在此处显示")
        self.image_display.setMinimumHeight(400)
        self.image_display.setStyleSheet("""
            QLabel {
                border: 2px dashed #ccc;
                background-color: #f9f9f9;
                color: #999;
                font-size: 16px;
                text-align: center;
            }
        """)
        self.image_display.setAlignment(Qt.AlignCenter)
        image_layout.addWidget(self.image_display)
        
        image_group.setLayout(image_layout)
        layout.addWidget(image_group)
        
        return tab

    def on_analysis_type_changed(self, analysis_type):
        """分析类型改变时的处理"""
        self.add_analysis_log(f"分析类型切换为: {analysis_type}")
        
        if analysis_type == "NEMA-IQ":
            # NEMA-IQ模式下启用热球相关设置
            self.hot_sphere_ratio_spin.setEnabled(True)
            self.show_spheres_cb.setEnabled(True)
        else:
            # Uniform模式下禁用热球相关设置
            self.hot_sphere_ratio_spin.setEnabled(False)
            self.show_spheres_cb.setEnabled(False)
        
        self.save_parameters()

    def browse_image_file(self):
        """浏览图像文件"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "选择图像文件",
            self.image_file_edit.text() or os.path.expanduser("~"),
            "图像文件 (*.dcm *.nii *.img *.hdr);;所有文件 (*)"
        )
        
        if filename:
            self.image_file_edit.setText(filename)
            self.save_parameters()
            self.add_analysis_log(f"选择图像文件: {os.path.basename(filename)}")

    def browse_output_directory(self):
        """浏览输出目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择输出目录",
            self.output_dir_edit.text() or os.path.expanduser("~")
        )
        
        if dir_path:
            self.output_dir_edit.setText(dir_path)
            self.save_parameters()
            self.add_analysis_log(f"设置输出目录: {dir_path}")

    def load_image(self):
        """加载图像"""
        image_file = self.image_file_edit.text().strip()
        if not image_file:
            QMessageBox.warning(self, "警告", "请先选择图像文件")
            return
        
        if not os.path.exists(image_file):
            QMessageBox.warning(self, "警告", "图像文件不存在")
            return
        
        try:
            self.add_analysis_log("开始加载图像...")
            
            # 这里应该实现真实的图像加载逻辑
            # 暂时模拟加载过程
            self.image_display.setText(f"已加载图像: {os.path.basename(image_file)}\\n\\n"
                                     f"图像尺寸: 256 x 256\\n"
                                     f"像素类型: float32\\n"
                                     f"数值范围: 0.0 - 1.0")
            
            self.add_analysis_log("图像加载完成", "SUCCESS")
            QMessageBox.information(self, "成功", "图像加载完成！")
            
        except Exception as e:
            self.add_analysis_log(f"图像加载失败: {str(e)}", "ERROR")
            QMessageBox.warning(self, "错误", f"加载图像失败: {str(e)}")

    def start_analysis(self):
        """开始分析"""
        image_file = self.image_file_edit.text().strip()
        if not image_file:
            QMessageBox.warning(self, "警告", "请先选择并加载图像文件")
            return
        
        try:
            self.add_analysis_log("开始模体分析...")
            
            # 显示进度条
            self.analysis_progress.setVisible(True)
            self.analysis_progress.setValue(0)
            
            # 模拟分析过程
            self.simulate_analysis()
            
        except Exception as e:
            self.add_analysis_log(f"分析失败: {str(e)}", "ERROR")
            QMessageBox.warning(self, "错误", f"分析失败: {str(e)}")

    def simulate_analysis(self):
        """模拟分析过程"""
        self.add_analysis_log("初始化分析参数...")
        
        # 模拟分析步骤
        self.analysis_timer = QTimer()
        self.analysis_step = 0
        self.analysis_steps = [
            "读取图像数据",
            "定义ROI区域", 
            "计算均匀性指标",
            "分析恢复系数",
            "计算对比度",
            "计算噪声水平",
            "生成分析报告"
        ]
        
        self.analysis_timer.timeout.connect(self.update_analysis_progress)
        self.analysis_timer.start(500)  # 每500ms一步

    def update_analysis_progress(self):
        """更新分析进度"""
        if self.analysis_step < len(self.analysis_steps):
            step_name = self.analysis_steps[self.analysis_step]
            self.add_analysis_log(f"正在{step_name}...")
            
            progress = int((self.analysis_step + 1) / len(self.analysis_steps) * 100)
            self.analysis_progress.setValue(progress)
            
            self.analysis_step += 1
        else:
            self.analysis_timer.stop()
            self.analysis_finished()

    def analysis_finished(self):
        """分析完成"""
        self.add_analysis_log("分析完成！", "SUCCESS")
        self.analysis_progress.setVisible(False)
        
        # 生成模拟结果
        self.generate_mock_results()
        
        # 更新结果显示
        self.update_results_display()
        
        QMessageBox.information(self, "分析完成", "模体分析已成功完成！")

    def generate_mock_results(self):
        """生成模拟分析结果"""
        analysis_type = self.analysis_type_combo.currentText()
        
        if analysis_type == "Uniform":
            self.analysis_results = {
                "uniformity": {
                    "integral_uniformity": 5.8,
                    "differential_uniformity": 3.2,
                    "mean_value": 125.6,
                    "std_deviation": 7.3
                },
                "noise": {
                    "noise_level": 2.1,
                    "snr": 42.3
                },
                "statistics": {
                    "roi_area": 7854,  # pixels
                    "background_area": 19635,
                    "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            }
        else:  # NEMA-IQ
            self.analysis_results = {
                "recovery_coefficients": {
                    "sphere_10mm": 0.85,
                    "sphere_13mm": 0.91,
                    "sphere_17mm": 0.94,
                    "sphere_22mm": 0.97,
                    "sphere_28mm": 0.98,
                    "sphere_37mm": 0.99
                },
                "contrast": {
                    "hot_sphere_contrast": 3.8,
                    "cold_sphere_contrast": -0.7
                },
                "noise": {
                    "background_noise": 4.2,
                    "uniformity": 6.1
                },
                "statistics": {
                    "total_spheres": 6,
                    "hot_sphere_ratio": self.hot_sphere_ratio_spin.value(),
                    "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            }

    def update_results_display(self):
        """更新结果显示"""
        self.results_table.setRowCount(0)
        
        row = 0
        for category, results in self.analysis_results.items():
            if isinstance(results, dict):
                for param, value in results.items():
                    self.results_table.insertRow(row)
                    
                    # 参数名称
                    param_name = f"{category}.{param}".replace("_", " ").title()
                    self.results_table.setItem(row, 0, QTableWidgetItem(param_name))
                    
                    # 数值
                    if isinstance(value, float):
                        value_str = f"{value:.3f}"
                    else:
                        value_str = str(value)
                    self.results_table.setItem(row, 1, QTableWidgetItem(value_str))
                    
                    # 单位
                    unit = self.get_unit_for_parameter(param)
                    self.results_table.setItem(row, 2, QTableWidgetItem(unit))
                    
                    row += 1

    def get_unit_for_parameter(self, param):
        """获取参数的单位"""
        unit_map = {
            "integral_uniformity": "%",
            "differential_uniformity": "%",
            "noise_level": "%",
            "snr": "dB",
            "hot_sphere_contrast": "ratio",
            "cold_sphere_contrast": "ratio",
            "background_noise": "%",
            "uniformity": "%",
            "roi_area": "pixels",
            "background_area": "pixels",
            "hot_sphere_ratio": "ratio"
        }
        return unit_map.get(param, "")

    def export_results(self):
        """导出结果"""
        if not self.analysis_results:
            QMessageBox.warning(self, "警告", "没有可导出的分析结果")
            return
        
        output_dir = self.output_dir_edit.text().strip()
        if not output_dir:
            output_dir = os.path.expanduser("~")
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        analysis_type = self.analysis_type_combo.currentText()
        filename = f"phantom_analysis_{analysis_type}_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)
        
        try:
            # 保存结果为JSON文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    "experiment": {
                        "name": self.experiment.name,
                        "center": self.experiment.center,
                        "date": self.experiment.date
                    },
                    "analysis_params": self.analysis_params,
                    "results": self.analysis_results
                }, f, indent=2, ensure_ascii=False)
            
            self.add_analysis_log(f"结果已导出到: {filename}", "SUCCESS")
            QMessageBox.information(self, "导出成功", f"分析结果已保存到:\\n{filepath}")
            
        except Exception as e:
            self.add_analysis_log(f"导出失败: {str(e)}", "ERROR")
            QMessageBox.warning(self, "导出失败", f"保存分析结果失败: {str(e)}")

    def update_image_display(self):
        """更新图像显示"""
        # 这里应该实现图像显示更新逻辑
        self.add_analysis_log("图像显示已更新")

    def add_analysis_log(self, message, level="INFO"):
        """添加分析日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if level == "ERROR":
            color = "red"
        elif level == "WARNING":
            color = "orange"
        elif level == "SUCCESS":
            color = "green"
        else:
            color = "black"
        
        formatted_msg = f'<span style="color: gray;">[{timestamp}]</span> <span style="color: {color};">[{level}]</span> {message}'
        
        self.analysis_log.append(formatted_msg)
        
        # 滚动到底部
        from PyQt5.QtGui import QTextCursor
        cursor = self.analysis_log.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.analysis_log.setTextCursor(cursor)

    def clear_analysis_log(self):
        """清空分析日志"""
        self.analysis_log.clear()
        self.add_analysis_log("日志已清空")

    def save_analysis_log(self):
        """保存分析日志"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存分析日志", "analysis_log.txt", "文本文件 (*.txt);;所有文件 (*)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    plain_text = self.analysis_log.toPlainText()
                    f.write(plain_text)
                
                QMessageBox.information(self, "保存成功", f"分析日志已保存到: {filename}")
            except Exception as e:
                QMessageBox.warning(self, "保存失败", f"保存日志失败: {str(e)}")

    def save_parameters(self):
        """保存参数到实验"""
        try:
            self.analysis_params.update({
                "analysis_type": self.analysis_type_combo.currentText(),
                "roi_settings": {
                    "center_x": self.center_x_spin.value(),
                    "center_y": self.center_y_spin.value(),
                    "radius": self.roi_radius_spin.value(),
                    "background_radius": self.bg_radius_spin.value()
                },
                "uniformity_settings": {
                    "threshold": self.uniformity_threshold_spin.value(),
                    "include_edges": self.include_edges_cb.isChecked()
                },
                "sphere_settings": {
                    "hot_sphere_ratio": self.hot_sphere_ratio_spin.value()
                }
            })
            
            self.experiment.parameters["phantom_analysis"] = self.analysis_params
            
            # 保存实验
            if hasattr(self.parent_window, '_save_experiment'):
                self.parent_window._save_experiment()
                
        except Exception as e:
            logger.error(f"保存分析参数失败: {e}")

    def load_parameters(self):
        """加载参数"""
        try:
            params = self.analysis_params
            
            self.analysis_type_combo.setCurrentText(params.get("analysis_type", "Uniform"))
            
            roi_settings = params.get("roi_settings", {})
            self.center_x_spin.setValue(roi_settings.get("center_x", 128))
            self.center_y_spin.setValue(roi_settings.get("center_y", 128))
            self.roi_radius_spin.setValue(roi_settings.get("radius", 50))
            self.bg_radius_spin.setValue(roi_settings.get("background_radius", 80))
            
            uniformity_settings = params.get("uniformity_settings", {})
            self.uniformity_threshold_spin.setValue(uniformity_settings.get("threshold", 0.1))
            self.include_edges_cb.setChecked(uniformity_settings.get("include_edges", False))
            
            sphere_settings = params.get("sphere_settings", {})
            self.hot_sphere_ratio_spin.setValue(sphere_settings.get("hot_sphere_ratio", 4.0))
            
            # 触发分析类型改变处理
            self.on_analysis_type_changed(self.analysis_type_combo.currentText())
            
        except Exception as e:
            logger.error(f"加载分析参数失败: {e}")
            
        # 初始化日志
        self.add_analysis_log("模体分析模块已初始化") 
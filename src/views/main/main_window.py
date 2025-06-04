import logging
import csv
import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QMessageBox,
    QAction, QTabWidget, QHeaderView, QTabBar, QFileDialog,
    QLineEdit, QLabel, QSplitter, QFrame, QStatusBar, QSizePolicy,
    QToolBar, QButtonGroup, QSpacerItem, QAbstractItemView
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSize, QThread, QObject
from PyQt5.QtGui import QIcon, QFont, QPixmap, QCloseEvent

from ...core.data_manager import DataManager
from ...models.entities.experiment import Experiment
from ...viewmodels.main_viewmodel import MainViewModel
from ..dialogs.add_experiment_dialog import AddExperimentDialog
from ..dialogs.activity_calculator_dialog import ActivityCalculatorDialog
from ...core.constants import PHANTOM_TYPES, DEVICE_MODELS, ISOTOPE_LIST

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PET 模体实验管理系统")
        
        # 尝试加载应用图标
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "assets", "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # 初始化 DataManager 并加载所有实验
        self.data_manager = DataManager()
        self.all_experiments = self.data_manager.load_experiments()
        self.filtered_experiments = self.all_experiments.copy()

        # 保存所有已打开的实验标签页
        self.experiment_tabs = {}

        # 应用现代化样式
        self.setStyleSheet(self.get_app_style("modern"))

        self.init_ui()
        self.start_timer()

        logging.debug(f"初始化主窗口，加载 {len(self.all_experiments)} 个实验")

    def get_app_style(self, theme="modern"):
        """获取应用样式"""
        return """
        /* 全局字体和背景 */
        QWidget {
            font-family: 'Microsoft YaHei', 'Segoe UI', Arial, sans-serif;
            font-size: 14px;
            color: #2c3e50;
            background-color: #f8f9fa;
        }

        /* 主窗口 */
        QMainWindow {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
        }

        /* 表格样式 - 与原版一致 */
        QTableWidget {
            background-color: #ffffff;
            border: none;
            border-radius: 8px;
            gridline-color: #e9ecef;
            selection-background-color: #e3f2fd;
            selection-color: #1976d2;
            font-size: 15px;
        }

        QTableWidget::item {
            padding: 8px 12px;
            border-bottom: 1px solid #e9ecef;
        }

        QTableWidget::item:hover {
            background-color: #f5f5f5;
        }

        QTableWidget::item:selected {
            background-color: #e3f2fd;
            color: #1976d2;
        }

        /* 表头样式 - 使用原版的蓝色主题 */
        QHeaderView::section {
            background-color: #5DADE2;
            color: white;
            font-weight: bold;
            font-size: 16px;
            padding: 12px;
            border: none;
            border-bottom: 2px solid #4A7C89;
        }

        /* 标签页样式 */
        QTabWidget::pane {
            background-color: #ffffff;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 12px;
        }

        QTabBar::tab {
            background-color: #f8f9fa;
            color: #6c757d;
            padding: 12px 24px;
            margin-right: 4px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            font-weight: 500;
            font-size: 16px;
        }

        QTabBar::tab:selected {
            background-color: #ffffff;
            color: #1976d2;
            border-bottom: 3px solid #1976d2;
        }

        QTabBar::tab:hover:!selected {
            background-color: #e9ecef;
        }

        /* 按钮样式 */
        QPushButton {
            background-color: #1976d2;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 10px 20px;
            font-weight: 500;
            font-size: 16px;
            min-width: 120px;
            min-height: 40px;
        }

        QPushButton:hover {
            background-color: #1565c0;
        }

        QPushButton:pressed {
            background-color: #0d47a1;
        }

        QPushButton:disabled {
            background-color: #e0e0e0;
            color: #9e9e9e;
        }

        /* 成功按钮 */
        QPushButton#success {
            background-color: #43a047;
        }

        QPushButton#success:hover {
            background-color: #388e3c;
        }

        /* 危险按钮 */
        QPushButton#danger {
            background-color: #e53935;
        }

        QPushButton#danger:hover {
            background-color: #d32f2f;
        }

        /* 信息按钮 */
        QPushButton#info {
            background-color: #17a2b8;
        }

        QPushButton#info:hover {
            background-color: #138496;
        }

        /* 主要按钮 */
        QPushButton#primary {
            background-color: #007bff;
        }

        QPushButton#primary:hover {
            background-color: #0056b3;
        }

        /* 输入框样式 */
        QLineEdit {
            background-color: #ffffff;
            border: 1px solid #ced4da;
            border-radius: 6px;
            padding: 10px 14px;
            font-size: 15px;
            min-height: 25px;
        }

        QLineEdit:focus {
            border-color: #1976d2;
            outline: none;
            border-width: 2px;
        }

        QLineEdit:disabled, QLineEdit[readOnly="true"] {
            background-color: #f5f5f5;
            color: #6c757d;
            border: 1px solid #e0e0e0;
        }

        /* 下拉框样式 */
        QComboBox {
            background-color: #ffffff;
            border: 1px solid #ced4da;
            border-radius: 6px;
            padding: 10px 14px;
            font-size: 15px;
            min-width: 150px;
            min-height: 25px;
        }

        QComboBox:focus {
            border-color: #1976d2;
            border-width: 2px;
        }

        QComboBox::drop-down {
            border: none;
            width: 20px;
        }

        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid #6c757d;
            margin-right: 5px;
        }

        QComboBox QAbstractItemView {
            border: 1px solid #ced4da;
            border-radius: 6px;
            background-color: white;
            selection-background-color: #e3f2fd;
            selection-color: #1976d2;
        }

        /* 分组框样式 */
        QGroupBox {
            font-weight: bold;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            padding-top: 12px;
            margin-top: 8px;
            background-color: #ffffff;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 15px;
            padding: 0 8px 0 8px;
            color: #495057;
            background-color: #ffffff;
        }

        /* 状态标签样式 */
        QLabel#header {
            color: #1976d2;
            font-weight: bold;
        }

        QLabel#result {
            background-color: #e8f5e8;
            border: 1px solid #c3e6c3;
            border-radius: 4px;
            padding: 6px 12px;
            font-weight: bold;
            color: #2e7d2e;
        }

        QLabel#countdown {
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 4px;
            padding: 6px 12px;
            font-weight: bold;
            color: #856404;
        }
        """

    def init_ui(self):
        # 窗口设置 - 更大的默认尺寸和更合理的最小尺寸
        screen_size = self.screen().availableSize()
        width = min(int(screen_size.width() * 0.9), 2000)  # 增大默认宽度
        height = min(int(screen_size.height() * 0.9), 1200)  # 增大默认高度
        
        self.resize(width, height)
        self.setMinimumSize(1600, 900)  # 增大最小尺寸

        # 创建工具栏
        self.create_toolbar()

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # ===== 主 QTabWidget =====
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        main_layout.addWidget(self.tab_widget)

        # ====== "主页" 布局 ======
        self.home_widget = QWidget()
        home_layout = QVBoxLayout(self.home_widget)
        home_layout.setSpacing(20)
        home_layout.setContentsMargins(25, 25, 25, 25)

        # 标题和搜索栏
        header_layout = QHBoxLayout()
        header_layout.setSpacing(20)
        
        # 标题标签
        title_label = QLabel("PET 模体实验管理")
        title_label.setObjectName("header")
        title_font = QFont()
        title_font.setPointSize(20)  # 增大标题字体
        title_font.setBold(True)
        title_label.setFont(title_font)
        
        # 搜索框布局
        search_layout = QHBoxLayout()
        search_layout.setSpacing(15)
        
        search_label = QLabel("🔍 搜索:")
        search_label.setFont(QFont("Microsoft YaHei", 14))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入实验名称、中心名称或核素进行搜索...")
        self.search_input.textChanged.connect(self.filter_experiments)
        self.search_input.setMinimumWidth(400)  # 增大搜索框宽度
        self.search_input.setMinimumHeight(35)  # 增大搜索框高度
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input, 1)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch(1)
        header_layout.addLayout(search_layout)
        
        home_layout.addLayout(header_layout)
        
        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        home_layout.addWidget(separator)

        # 实验列表表格
        self.experiment_table = QTableWidget()
        self.experiment_table.setColumnCount(7)
        self.experiment_table.setHorizontalHeaderLabels([
            "实验名称", "中心名称", "日期", "模体类型", "核素", "设备型号", "备注"
        ])
        self.experiment_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.experiment_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.experiment_table.setAlternatingRowColors(True)
        self.experiment_table.verticalHeader().setVisible(False)
        self.experiment_table.setSortingEnabled(True)
        
        # 连接双击信号到打开实验方法
        self.experiment_table.itemDoubleClicked.connect(self.open_experiment)
        
        # 设置表格字体大小
        table_font = self.experiment_table.font()
        table_font.setPointSize(13)  # 设置为13点字体
        self.experiment_table.setFont(table_font)

        # 设置表格行高
        self.experiment_table.verticalHeader().setDefaultSectionSize(40)  # 增加行高

        # 应用表格的列宽比例设置
        QTimer.singleShot(0, self._apply_column_widths)

        # 创建状态标签，用于显示实验数量
        self.status_label = QLabel(f"共 {len(self.all_experiments)} 个实验")
        self.status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.status_label.setFont(QFont("Microsoft YaHei", 12))

        # 填充数据
        self.update_experiment_table()
        home_layout.addWidget(self.experiment_table)

        # 按钮栏 - 重新设计按钮布局
        button_frame = QFrame()
        button_frame.setFrameStyle(QFrame.NoFrame)
        button_layout = QHBoxLayout(button_frame)
        button_layout.setSpacing(20)
        button_layout.setContentsMargins(0, 15, 0, 0)

        # 创建按钮组 - 统一的按钮样式
        button_style = """
        QPushButton {
            min-width: 120px;
            max-width: 140px;
            min-height: 40px;
            max-height: 45px;
            padding: 8px 16px;
            font-size: 14px;
            font-weight: 600;
            border-radius: 8px;
            border: none;
        }
        QPushButton:hover {
            transform: translateY(-1px);
        }
        QPushButton:pressed {
            transform: translateY(1px);
        }
        """
        
        new_btn = QPushButton("➕ 新建实验")
        new_btn.setObjectName("primary")
        new_btn.setToolTip("创建新的模体实验记录")
        new_btn.setStyleSheet(button_style)
        new_btn.clicked.connect(self.new_experiment)
        
        del_btn = QPushButton("🗑️ 删除选中")
        del_btn.setObjectName("danger")
        del_btn.setToolTip("删除选中的实验记录")
        del_btn.setStyleSheet(button_style)
        del_btn.clicked.connect(self.delete_experiment)
        
        export_btn = QPushButton("📥 导出数据")
        export_btn.setObjectName("success")
        export_btn.setToolTip("将选中的实验数据导出为CSV文件")
        export_btn.setStyleSheet(button_style)
        export_btn.clicked.connect(self.export_to_csv)
        
        calc_btn = QPushButton("🧮 活度计算器")
        calc_btn.setObjectName("info")
        calc_btn.setToolTip("打开核素活度计算工具")
        calc_btn.setStyleSheet(button_style)
        calc_btn.clicked.connect(self.open_activity_calculator)
        
        # 按钮布局
        button_layout.addWidget(new_btn)
        button_layout.addWidget(del_btn)
        button_layout.addWidget(export_btn)
        button_layout.addWidget(calc_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.status_label)
        
        home_layout.addWidget(button_frame)

        # 将主页添加到标签页
        self.tab_widget.addTab(self.home_widget, "🏠 主页")

        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪", 5000)

        # 设置菜单栏
        self.setup_menu()

    def create_toolbar(self):
        """创建工具栏"""
        toolbar = self.addToolBar("主工具栏")
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        toolbar.setIconSize(QSize(32, 32))

        # 新建实验
        new_action = QAction("新建实验", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_experiment)
        toolbar.addAction(new_action)

        toolbar.addSeparator()

        # 保存所有
        save_action = QAction("保存", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_all_data)
        toolbar.addAction(save_action)

        # 刷新
        refresh_action = QAction("刷新", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh_data)
        toolbar.addAction(refresh_action)

        toolbar.addSeparator()

        # 活度计算器
        calc_action = QAction("活度计算器", self)
        calc_action.triggered.connect(self.open_activity_calculator)
        toolbar.addAction(calc_action)

    def _apply_column_widths(self):
        """应用表格列宽比例设置"""
        table_width = self.experiment_table.width()
        if table_width > 0:
            # 列宽比例: 2:2:1:1:1:2:1 (与原版一致)
            ratios = [2, 2, 1, 1, 1, 2, 1]
            total_ratio = sum(ratios)
            
            for col, ratio in enumerate(ratios):
                width = int(table_width * ratio / total_ratio)
                self.experiment_table.setColumnWidth(col, width)

    def resizeEvent(self, event):
        """窗口大小改变时重新调整列宽"""
        super().resizeEvent(event)
        QTimer.singleShot(100, self._apply_column_widths)

    def filter_experiments(self, text):
        """过滤实验列表"""
        if not text.strip():
            self.filtered_experiments = self.all_experiments.copy()
        else:
            text_lower = text.lower()
            self.filtered_experiments = []
            for exp in self.all_experiments:
                if (text_lower in exp.name.lower() or
                    text_lower in exp.center.lower() or
                    text_lower in exp.parameters.get("isotope", "").lower() or
                    text_lower in exp.model_type.lower() or
                    text_lower in exp.parameters.get("device_model", "").lower() or
                    text_lower in exp.parameters.get("remark", "").lower()):
                    self.filtered_experiments.append(exp)
        
        self.update_experiment_table()

    def start_timer(self):
        """启动状态更新定时器"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(30000)  # 30秒更新一次

    def update_status(self):
        """更新状态栏信息"""
        exp_count = len(self.filtered_experiments)
        total_count = len(self.all_experiments)
        if exp_count == total_count:
            message = f"共 {total_count} 个实验"
        else:
            message = f"显示 {exp_count} / {total_count} 个实验"
        self.status_label.setText(message)

    def update_experiment_table(self):
        """更新实验列表表格"""
        self.experiment_table.setRowCount(len(self.filtered_experiments))
        
        for i, experiment in enumerate(self.filtered_experiments):
            name_item = QTableWidgetItem(experiment.name)
            name_item.setData(Qt.UserRole, experiment.id)
            self.experiment_table.setItem(i, 0, name_item)
            
            center_item = QTableWidgetItem(experiment.center)
            center_item.setData(Qt.UserRole, experiment.id)
            self.experiment_table.setItem(i, 1, center_item)
            
            date_item = QTableWidgetItem(experiment.date)
            date_item.setData(Qt.UserRole, experiment.id)
            self.experiment_table.setItem(i, 2, date_item)
            
            model_item = QTableWidgetItem(experiment.model_type)
            model_item.setData(Qt.UserRole, experiment.id)
            self.experiment_table.setItem(i, 3, model_item)
            
            isotope_item = QTableWidgetItem(experiment.parameters.get('isotope', ''))
            isotope_item.setData(Qt.UserRole, experiment.id)
            self.experiment_table.setItem(i, 4, isotope_item)
            
            device_item = QTableWidgetItem(experiment.parameters.get('device_model', ''))
            device_item.setData(Qt.UserRole, experiment.id)
            self.experiment_table.setItem(i, 5, device_item)
            
            remark_item = QTableWidgetItem(experiment.parameters.get('remark', ''))
            remark_item.setData(Qt.UserRole, experiment.id)
            self.experiment_table.setItem(i, 6, remark_item)
        
        # 更新状态
        self.update_status()

    def new_experiment(self):
        """创建新实验"""
        dialog = AddExperimentDialog(self)
        if dialog.exec_() == AddExperimentDialog.Accepted:
            exp_data = dialog.get_experiment_data()
            if exp_data:
                try:
                    # 创建新实验
                    experiment = self.data_manager.create_experiment(
                        name=exp_data['name'],
                        center=exp_data['center'],
                        model_type=exp_data['model_type']
                    )
                    
                    if experiment:
                        # 更新实验列表
                        self.all_experiments = self.data_manager.load_experiments()
                        self.filtered_experiments = self.all_experiments.copy()
                        self.update_experiment_table()
                        
                        # 自动打开新实验
                        self.open_experiment_tab(experiment)
                        
                        self.status_bar.showMessage(f"成功创建实验: {experiment.name}", 3000)
                    else:
                        QMessageBox.warning(self, "错误", "创建实验失败")
                except Exception as e:
                    logging.error(f"创建实验失败: {e}")
                    QMessageBox.critical(self, "错误", f"创建实验失败: {str(e)}")

    def open_experiment(self, item):
        """从表格中双击打开实验"""
        row = item.row()
        experiment_id_item = self.experiment_table.item(row, 0)
        
        if experiment_id_item is None:
            return
            
        experiment_id = experiment_id_item.data(Qt.UserRole)
        if experiment_id is None:
            return
            
        # 在 all_experiments 中查找实验
        experiment = None
        for exp in self.all_experiments:
            if hasattr(exp, 'id') and exp.id == experiment_id:
                experiment = exp
                break
            elif hasattr(exp, 'experiment_id') and exp.experiment_id == experiment_id:
                experiment = exp
                break
        
        if experiment:
            self.open_experiment_tab(experiment)
        else:
            QMessageBox.warning(self, "错误", "无法找到对应的实验数据")

    def open_experiment_tab(self, experiment):
        """打开实验标签页"""
        # 检查是否已经打开了这个实验的标签页
        experiment_id = getattr(experiment, 'id', None) or getattr(experiment, 'experiment_id', None)
        
        if experiment_id in self.experiment_tabs:
            # 如果已经打开，就切换到该标签页
            self.tab_widget.setCurrentWidget(self.experiment_tabs[experiment_id])
            return
        
        # 创建新的实验窗口
        from ..experiment.experiment_window import ExperimentWindow
        experiment_widget = ExperimentWindow(experiment, self)
        experiment_widget.experiment_updated.connect(self._on_experiment_updated)
        
        # 添加到标签页
        tab_index = self.tab_widget.addTab(experiment_widget, f"📋 {experiment.name}")
        self.tab_widget.setCurrentIndex(tab_index)
        
        # 保存标签页引用
        self.experiment_tabs[experiment_id] = experiment_widget

    def _on_experiment_updated(self, experiment):
        """实验更新时的回调"""
        self.update_experiment_table()

    def close_tab(self, index: int):
        """关闭标签页"""
        if index == 0:  # 不允许关闭主页
            return
            
        widget = self.tab_widget.widget(index)
        
        # 如果是实验窗口，从字典中移除
        for exp_id, exp_widget in list(self.experiment_tabs.items()):
            if exp_widget == widget:
                del self.experiment_tabs[exp_id]
                break
        
        # 移除标签页
        self.tab_widget.removeTab(index)
        
        # 删除widget
        if widget:
            widget.deleteLater()

    def delete_experiment(self):
        """删除选中的实验"""
        selected_items = self.experiment_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "提示", "请先选择要删除的实验")
            return
        
        # 获取选中的实验（避免重复）
        selected_experiments = set()
        for item in selected_items:
            if item.column() == 0:  # 只处理第一列的项目
                experiment = item.data(Qt.UserRole)
                if experiment:
                    selected_experiments.add(experiment)
        
        if not selected_experiments:
            return
        
        # 确认删除
        count = len(selected_experiments)
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除选中的 {count} 个实验吗？\n\n此操作不可恢复！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                deleted_count = 0
                for experiment in selected_experiments:
                    # 先关闭相关的标签页
                    if experiment.id in self.experiment_tabs:
                        tab_widget = self.experiment_tabs[experiment.id]
                        tab_index = self.tab_widget.indexOf(tab_widget)
                        if tab_index >= 0:
                            self.close_tab(tab_index)
                    
                    # 删除实验
                    if self.data_manager.delete_experiment(experiment.id):
                        deleted_count += 1
                
                # 重新加载数据
                self.all_experiments = self.data_manager.load_experiments()
                self.filtered_experiments = self.all_experiments.copy()
                self.update_experiment_table()
                
                self.status_bar.showMessage(f"成功删除 {deleted_count} 个实验", 3000)
                
            except Exception as e:
                logging.error(f"删除实验失败: {e}")
                QMessageBox.critical(self, "错误", f"删除实验失败: {str(e)}")

    def export_to_csv(self, export_all=False):
        """导出数据到CSV文件"""
        if not export_all:
            # 检查是否有选中的实验
            selected_items = self.experiment_table.selectedItems()
            if not selected_items:
                reply = QMessageBox.question(
                    self, "导出确认",
                    "没有选中任何实验，是否导出所有实验数据？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    export_all = True
                else:
                    return
        
        # 选择保存文件
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出实验数据",
            f"experiments_{len(self.filtered_experiments if export_all else 'selected')}.csv",
            "CSV文件 (*.csv)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                
                # 写入表头
                headers = [
                    '实验名称', '中心名称', '创建日期', '模体类型', '核素', 
                    '设备型号', '模体体积(L)', '目标活度(mCi)', '机器时间差(s)', '备注'
                ]
                writer.writerow(headers)
                
                # 确定要导出的实验
                if export_all:
                    experiments_to_export = self.filtered_experiments
                else:
                    # 获取选中的实验
                    selected_experiments = set()
                    for item in selected_items:
                        if item.column() == 0:  # 只处理第一列
                            experiment = item.data(Qt.UserRole)
                            if experiment:
                                selected_experiments.add(experiment)
                    experiments_to_export = list(selected_experiments)
                
                # 写入数据
                for experiment in experiments_to_export:
                    row = [
                        experiment.name,
                        experiment.center,
                        experiment.created_at.strftime("%Y-%m-%d %H:%M:%S") if experiment.created_at else "",
                        experiment.model_type,
                        experiment.parameters.get("isotope", ""),
                        experiment.parameters.get("device_model", ""),
                        experiment.parameters.get("volume", 0.0),
                        experiment.parameters.get("target_activity", 0.0),
                        experiment.parameters.get("machine_time_diff", 0.0),
                        experiment.parameters.get("remark", "")
                    ]
                    writer.writerow(row)
            
            count = len(experiments_to_export)
            QMessageBox.information(self, "导出成功", f"成功导出 {count} 个实验的数据到:\n{file_path}")
            self.status_bar.showMessage(f"成功导出 {count} 个实验数据", 3000)
            
        except Exception as e:
            logging.error(f"导出CSV失败: {e}")
            QMessageBox.critical(self, "导出失败", f"导出失败: {str(e)}")

    def open_activity_calculator(self):
        """打开活度计算器"""
        dialog = ActivityCalculatorDialog(self)
        dialog.exec_()

    def save_all_data(self):
        """保存所有数据"""
        try:
            # 保存所有实验数据
            self.data_manager.save_all_data(self.all_experiments)
            self.status_bar.showMessage("数据保存成功", 2000)
        except Exception as e:
            logging.error(f"保存数据失败: {e}")
            QMessageBox.critical(self, "保存失败", f"保存数据失败: {str(e)}")

    def refresh_data(self):
        """刷新数据"""
        try:
            self.all_experiments = self.data_manager.load_experiments()
            self.filtered_experiments = self.all_experiments.copy()
            self.update_experiment_table()
            self.status_bar.showMessage("数据刷新成功", 2000)
        except Exception as e:
            logging.error(f"刷新数据失败: {e}")
            QMessageBox.critical(self, "刷新失败", f"刷新数据失败: {str(e)}")

    def on_experiments_loaded(self, experiments):
        """实验加载完成回调"""
        self.all_experiments = experiments
        self.filtered_experiments = experiments.copy()
        self.update_experiment_table()

    def show_error(self, message):
        """显示错误消息"""
        QMessageBox.critical(self, "错误", message)

    def show_status(self, message, timeout=2000):
        """显示状态消息"""
        self.status_bar.showMessage(message, timeout)

    def closeEvent(self, event):
        """重写关闭事件"""
        try:
            # 保存所有数据
            self.data_manager.save_all_data()
            event.accept()
        except Exception as e:
            logging.error(f"关闭程序时保存数据失败: {e}")
            # 即使保存失败也允许关闭
            event.accept()

    def load_experiments(self):
        """加载实验数据"""
        experiments = self.data_manager.load_experiments()
        self.viewmodel.set_experiments(experiments)
        
    def setup_menu(self):
        """设置菜单栏 - 简化版本，只保留必要功能"""
        menubar = self.menuBar()
        
        # 工具菜单
        tools_menu = menubar.addMenu("工具(&T)")
        
        calc_action = QAction("活度计算器(&C)", self)
        calc_action.setShortcut("Ctrl+Shift+C")
        calc_action.triggered.connect(self.open_activity_calculator)
        tools_menu.addAction(calc_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        
        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self, "关于",
            "PET 模体实验管理系统 v2.0\n\n"
            "基于 PyQt5 开发的模体实验数据管理工具\n"
            "支持活度计算、序列重建和数据分析功能"
        )

    def setup_connections(self):
        # 连接信号
        self.viewmodel.experiments_loaded.connect(self.on_experiments_loaded)
        self.viewmodel.error_occurred.connect(self.show_error)
        self.viewmodel.status_changed.connect(self.show_status)

        logging.debug("设置信号连接完成") 
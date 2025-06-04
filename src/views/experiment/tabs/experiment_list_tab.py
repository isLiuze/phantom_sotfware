# src/views/experiment/tabs/experiment_list_tab.py

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QLineEdit, QComboBox, QPushButton, 
                             QLabel, QHeaderView, QAbstractItemView, QMenu,
                             QMessageBox, QSplitter, QTextEdit, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon
from typing import TYPE_CHECKING, List
from ...dialogs.add_experiment_dialog import AddExperimentDialog
from ....models.entities.experiment import Experiment

if TYPE_CHECKING:
    from ....viewmodels.tabs.experiment_list_viewmodel import ExperimentListViewModel

class ExperimentListTab(QWidget):
    """实验列表标签页"""
    
    experiment_selected = pyqtSignal(object)  # 实验选中信号
    experiment_opened = pyqtSignal(object)    # 实验打开信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.viewmodel = None
        self.current_experiment = None
        
        self._create_ui()
        self._setup_table()
        self._connect_signals()
    
    def set_viewmodel(self, viewmodel: 'ExperimentListViewModel'):
        """设置ViewModel"""
        self.viewmodel = viewmodel
        self._bind_viewmodel()
        self._load_experiments()
    
    def _create_ui(self):
        """创建用户界面"""
        layout = QVBoxLayout(self)
        
        # 工具栏
        toolbar_layout = self._create_toolbar()
        layout.addLayout(toolbar_layout)
        
        # 主要内容区域
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：实验列表
        left_widget = self._create_list_widget()
        splitter.addWidget(left_widget)
        
        # 右侧：实验详情
        right_widget = self._create_detail_widget()
        splitter.addWidget(right_widget)
        
        # 设置分割比例
        splitter.setSizes([700, 300])
        layout.addWidget(splitter)
        
        # 状态栏
        status_layout = self._create_status_bar()
        layout.addLayout(status_layout)
    
    def _create_toolbar(self) -> QHBoxLayout:
        """创建工具栏"""
        layout = QHBoxLayout()
        
        # 搜索框
        search_label = QLabel("搜索:")
        layout.addWidget(search_label)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索实验名称、中心、核素...")
        self.search_edit.setMaximumWidth(300)
        layout.addWidget(self.search_edit)
        
        # 核素过滤
        filter_label = QLabel("核素:")
        layout.addWidget(filter_label)
        
        self.filter_combo = QComboBox()
        self.filter_combo.setMinimumWidth(120)
        layout.addWidget(self.filter_combo)
        
        layout.addStretch()
        
        # 操作按钮
        self.add_button = QPushButton("添加实验")
        self.add_button.setMinimumWidth(100)
        layout.addWidget(self.add_button)
        
        self.edit_button = QPushButton("编辑")
        self.edit_button.setEnabled(False)
        layout.addWidget(self.edit_button)
        
        self.delete_button = QPushButton("删除")
        self.delete_button.setEnabled(False)
        layout.addWidget(self.delete_button)
        
        self.export_button = QPushButton("导出")
        layout.addWidget(self.export_button)
        
        self.refresh_button = QPushButton("刷新")
        layout.addWidget(self.refresh_button)
        
        return layout
    
    def _create_list_widget(self) -> QWidget:
        """创建列表区域"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 实验表格
        self.experiment_table = QTableWidget()
        layout.addWidget(self.experiment_table)
        
        return widget
    
    def _create_detail_widget(self) -> QWidget:
        """创建详情区域"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 标题
        title_label = QLabel("实验详情")
        title_font = QFont()
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # 详情文本
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setText("请选择一个实验查看详情")
        layout.addWidget(self.detail_text)
        
        return widget
    
    def _create_status_bar(self) -> QHBoxLayout:
        """创建状态栏"""
        layout = QHBoxLayout()
        
        self.status_label = QLabel("就绪")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        self.count_label = QLabel("实验: 0")
        layout.addWidget(self.count_label)
        
        return layout
    
    def _setup_table(self):
        """设置表格"""
        # 设置列
        headers = ["实验名称", "中心", "日期", "体模类型", "核素", "设备型号", "创建时间"]
        self.experiment_table.setColumnCount(len(headers))
        self.experiment_table.setHorizontalHeaderLabels(headers)
        
        # 表格属性
        self.experiment_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.experiment_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.experiment_table.setAlternatingRowColors(True)
        
        # 列宽自适应
        header = self.experiment_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # 实验名称列自适应
        for i in range(1, len(headers)):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        
        # 右键菜单
        self.experiment_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.experiment_table.customContextMenuRequested.connect(self._show_context_menu)
    
    def _connect_signals(self):
        """连接信号"""
        # 搜索和过滤
        self.search_edit.textChanged.connect(self._on_search_changed)
        self.filter_combo.currentTextChanged.connect(self._on_filter_changed)
        
        # 表格选择
        self.experiment_table.itemSelectionChanged.connect(self._on_selection_changed)
        self.experiment_table.itemDoubleClicked.connect(self._on_item_double_clicked)
        
        # 按钮操作
        self.add_button.clicked.connect(self._on_add_experiment)
        self.edit_button.clicked.connect(self._on_edit_experiment)
        self.delete_button.clicked.connect(self._on_delete_experiment)
        self.export_button.clicked.connect(self._on_export_experiments)
        self.refresh_button.clicked.connect(self._on_refresh)
        
        # 延迟搜索
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._apply_search)
    
    def _bind_viewmodel(self):
        """绑定ViewModel"""
        if not self.viewmodel:
            return
        
        # 绑定数据变化
        self.viewmodel.experiments.item_added.connect(self._on_experiment_added)
        self.viewmodel.experiments.item_removed.connect(self._on_experiment_removed)
        self.viewmodel.experiments.list_cleared.connect(self._on_experiments_cleared)
        
        # 绑定状态变化
        self.viewmodel.is_loading.bind_to(self._on_loading_changed)
        self.viewmodel.total_experiments.bind_to(self._update_count_display)
        self.viewmodel.filtered_count.bind_to(self._update_count_display)
        
        # 加载核素过滤选项
        self._load_filter_options()
    
    def _load_experiments(self):
        """加载实验列表"""
        if self.viewmodel:
            self.viewmodel.refresh_experiments()
    
    def _load_filter_options(self):
        """加载过滤选项"""
        if self.viewmodel:
            nuclides = self.viewmodel.get_available_nuclides()
            self.filter_combo.clear()
            self.filter_combo.addItems(nuclides)
    
    def _populate_table(self, experiments: List[Experiment]):
        """填充表格数据"""
        self.experiment_table.setRowCount(len(experiments))
        
        for row, exp in enumerate(experiments):
            # 实验名称
            self.experiment_table.setItem(row, 0, QTableWidgetItem(exp.name))
            
            # 中心
            self.experiment_table.setItem(row, 1, QTableWidgetItem(exp.center))
            
            # 日期
            self.experiment_table.setItem(row, 2, QTableWidgetItem(exp.date))
            
            # 体模类型
            self.experiment_table.setItem(row, 3, QTableWidgetItem(exp.model_type))
            
            # 核素
            isotope = exp.parameters.get("isotope", "")
            self.experiment_table.setItem(row, 4, QTableWidgetItem(isotope))
            
            # 设备型号
            device = exp.parameters.get("device_model", "")
            self.experiment_table.setItem(row, 5, QTableWidgetItem(device))
            
            # 创建时间
            self.experiment_table.setItem(row, 6, QTableWidgetItem(exp.created_at))
            
            # 存储实验对象
            self.experiment_table.item(row, 0).setData(Qt.UserRole, exp)
    
    def _on_search_changed(self):
        """搜索文本变化"""
        # 延迟搜索，避免频繁查询
        self.search_timer.start(300)
    
    def _apply_search(self):
        """应用搜索"""
        if self.viewmodel:
            search_text = self.search_edit.text()
            self.viewmodel.search_text.value = search_text
    
    def _on_filter_changed(self):
        """过滤条件变化"""
        if self.viewmodel:
            filter_nuclide = self.filter_combo.currentText()
            self.viewmodel.filter_nuclide.value = filter_nuclide
    
    def _on_selection_changed(self):
        """选择变化"""
        current_row = self.experiment_table.currentRow()
        if current_row >= 0:
            item = self.experiment_table.item(current_row, 0)
            if item:
                experiment = item.data(Qt.UserRole)
                self.current_experiment = experiment
                self._update_detail_view(experiment)
                self._update_button_states(True)
                
                if self.viewmodel:
                    self.viewmodel.selected_experiment.value = experiment
                
                self.experiment_selected.emit(experiment)
        else:
            self.current_experiment = None
            self._update_detail_view(None)
            self._update_button_states(False)
    
    def _on_item_double_clicked(self):
        """双击项目"""
        if self.current_experiment:
            self.experiment_opened.emit(self.current_experiment)
    
    def _update_detail_view(self, experiment: Experiment):
        """更新详情视图"""
        if experiment:
            detail_text = f"""<h3>{experiment.name}</h3>
            <p><b>中心:</b> {experiment.center}</p>
            <p><b>日期:</b> {experiment.date}</p>
            <p><b>体模类型:</b> {experiment.model_type}</p>
            <p><b>核素:</b> {experiment.parameters.get('isotope', 'N/A')}</p>
            <p><b>设备型号:</b> {experiment.parameters.get('device_model', 'N/A')}</p>
            <p><b>容器体积:</b> {experiment.parameters.get('volume', 0)} L</p>
            <p><b>目标活度:</b> {experiment.parameters.get('target_activity', 0)} {experiment.parameters.get('activity_unit', 'MBq')}</p>
            <p><b>创建时间:</b> {experiment.created_at}</p>
            <p><b>备注:</b> {experiment.parameters.get('remark', '无')}</p>
            """
            self.detail_text.setHtml(detail_text)
        else:
            self.detail_text.setText("请选择一个实验查看详情")
    
    def _update_button_states(self, has_selection: bool):
        """更新按钮状态"""
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
    
    def _update_count_display(self, *args):
        """更新计数显示"""
        if self.viewmodel:
            total = self.viewmodel.total_experiments.value
            filtered = self.viewmodel.filtered_count.value
            if total == filtered:
                self.count_label.setText(f"实验: {total}")
            else:
                self.count_label.setText(f"实验: {filtered}/{total}")
    
    def _show_context_menu(self, position):
        """显示右键菜单"""
        if self.current_experiment:
            menu = QMenu(self)
            
            menu.addAction("打开实验", self._on_item_double_clicked)
            menu.addAction("编辑实验", self._on_edit_experiment)
            menu.addSeparator()
            menu.addAction("复制实验", self._on_duplicate_experiment)
            menu.addAction("导出实验", self._on_export_current_experiment)
            menu.addSeparator()
            menu.addAction("删除实验", self._on_delete_experiment)
            
            menu.exec_(self.experiment_table.mapToGlobal(position))
    
    def _on_add_experiment(self):
        """添加实验"""
        dialog = AddExperimentDialog(self)
        dialog.experiment_created.connect(self._on_experiment_created)
        dialog.exec_()
    
    def _on_edit_experiment(self):
        """编辑实验"""
        if self.current_experiment and self.viewmodel:
            # TODO: 创建编辑实验对话框
            QMessageBox.information(self, "提示", "编辑功能开发中...")
    
    def _on_delete_experiment(self):
        """删除实验"""
        if self.current_experiment and self.viewmodel:
            reply = QMessageBox.question(
                self, "确认删除", 
                f"确定要删除实验 '{self.current_experiment.name}' 吗？\n此操作不可撤销。",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                try:
                    self.viewmodel._confirm_delete_experiment(self.current_experiment)
                    self.status_label.setText(f"已删除实验: {self.current_experiment.name}")
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"删除失败: {str(e)}")
    
    def _on_duplicate_experiment(self):
        """复制实验"""
        if self.current_experiment and self.viewmodel:
            self.viewmodel._duplicate_experiment()
    
    def _on_export_current_experiment(self):
        """导出当前实验"""
        if self.current_experiment and self.viewmodel:
            self.viewmodel._export_experiment()
    
    def _on_export_experiments(self):
        """导出所有实验"""
        if self.viewmodel:
            self.viewmodel._export_all_experiments()
    
    def _on_refresh(self):
        """刷新"""
        if self.viewmodel:
            self.viewmodel.refresh_experiments()
            self.status_label.setText("已刷新实验列表")
    
    def _on_experiment_created(self, experiment: Experiment):
        """处理实验创建"""
        if self.viewmodel:
            try:
                # 通过主ViewModel创建实验
                from ....viewmodels.main_viewmodel import MainViewModel
                main_viewmodel = MainViewModel()  # 这里应该是注入的实例
                main_viewmodel.create_experiment(experiment)
                self.status_label.setText(f"已创建实验: {experiment.name}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"创建实验失败: {str(e)}")
    
    def _on_experiment_added(self, experiment: Experiment, index: int):
        """实验添加事件"""
        self._populate_table(list(self.viewmodel.experiments))
        self._load_filter_options()
    
    def _on_experiment_removed(self, experiment: Experiment, index: int):
        """实验移除事件"""
        self._populate_table(list(self.viewmodel.experiments))
        self._load_filter_options()
    
    def _on_experiments_cleared(self):
        """实验列表清空事件"""
        self.experiment_table.setRowCount(0)
        self.current_experiment = None
        self._update_detail_view(None)
        self._update_button_states(False)
    
    def _on_loading_changed(self, is_loading: bool):
        """加载状态变化"""
        if is_loading:
            self.status_label.setText("正在加载...")
            self.refresh_button.setEnabled(False)
        else:
            self.status_label.setText("就绪")
            self.refresh_button.setEnabled(True)
            self._populate_table(list(self.viewmodel.experiments)) 
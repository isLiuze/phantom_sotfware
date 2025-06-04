from PyQt5.QtWidgets import (QToolBar, QAction, QWidget, QToolButton, 
                               QLabel, QHBoxLayout, QFrame, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QIcon
from typing import TYPE_CHECKING, Optional, Callable

if TYPE_CHECKING:
    from ...viewmodels.main_viewmodel import MainViewModel


class MainToolbar(QToolBar):
    """主窗口工具栏"""
    
    def __init__(self, parent, viewmodel: 'MainViewModel'):
        super().__init__(parent)
        self.viewmodel = viewmodel
        
        # 设置工具栏属性
        self.setMovable(False)
        self.setFloatable(False)
        self.setIconSize(QSize(24, 24))
        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        
        # 创建工具栏按钮
        self._create_toolbar_buttons()
        
        # 绑定ViewModel状态
        self._bind_viewmodel_state()
    
    def _create_toolbar_buttons(self):
        """创建工具栏按钮"""
        # 文件操作组
        self.addWidget(QLabel("文件: "))
        
        # 新建
        self.new_action = QAction("新建", self)
        self.new_action.setToolTip("新建项目 (Ctrl+N)")
        self.new_action.triggered.connect(lambda: self.viewmodel.new_project())
        self.addAction(self.new_action)
        
        # 打开
        self.open_action = QAction("打开", self)
        self.open_action.setToolTip("打开项目 (Ctrl+O)")
        self.open_action.triggered.connect(lambda: self.viewmodel.open_project())
        self.addAction(self.open_action)
        
        # 保存
        self.save_action = QAction("保存", self)
        self.save_action.setToolTip("保存项目 (Ctrl+S)")
        self.save_action.triggered.connect(lambda: self.viewmodel.save_project())
        self.addAction(self.save_action)
        
        # 分隔符
        self.addSeparator()
        
        # 编辑操作组
        self.addWidget(QLabel("编辑: "))
        
        # 撤销
        self.undo_action = QAction("撤销", self)
        self.undo_action.setToolTip("撤销 (Ctrl+Z)")
        self.undo_action.triggered.connect(lambda: self.viewmodel.undo())
        self.addAction(self.undo_action)
        
        # 重做
        self.redo_action = QAction("重做", self)
        self.redo_action.setToolTip("重做 (Ctrl+Y)")
        self.redo_action.triggered.connect(lambda: self.viewmodel.redo())
        self.addAction(self.redo_action)
        
        # 分隔符
        self.addSeparator()
        
        # 实验操作组
        self.addWidget(QLabel("实验: "))
        
        # 新建实验
        self.add_experiment_action = QAction("新建实验", self)
        self.add_experiment_action.setToolTip("新建实验 (Ctrl+Shift+N)")
        self.add_experiment_action.triggered.connect(lambda: self.viewmodel.add_experiment())
        self.addAction(self.add_experiment_action)
        
        # 编辑实验
        self.edit_experiment_action = QAction("编辑实验", self)
        self.edit_experiment_action.setToolTip("编辑选中的实验")
        self.edit_experiment_action.triggered.connect(lambda: self.viewmodel.edit_experiment())
        self.edit_experiment_action.setEnabled(False)  # 初始状态禁用
        self.addAction(self.edit_experiment_action)
        
        # 删除实验
        self.delete_experiment_action = QAction("删除实验", self)
        self.delete_experiment_action.setToolTip("删除选中的实验 (Delete)")
        self.delete_experiment_action.triggered.connect(lambda: self.viewmodel.delete_experiment())
        self.delete_experiment_action.setEnabled(False)  # 初始状态禁用
        self.addAction(self.delete_experiment_action)
        
        # 分隔符
        self.addSeparator()
        
        # 数据操作组
        self.addWidget(QLabel("数据: "))
        
        # 导出
        self.export_action = QAction("导出", self)
        self.export_action.setToolTip("导出数据")
        self.export_action.triggered.connect(lambda: self.viewmodel.export_experiment())
        self.export_action.setEnabled(False)  # 初始状态禁用
        self.addAction(self.export_action)
        
        # 刷新
        self.refresh_action = QAction("刷新", self)
        self.refresh_action.setToolTip("刷新数据 (F5)")
        self.refresh_action.triggered.connect(lambda: self.viewmodel.refresh())
        self.addAction(self.refresh_action)
        
        # 添加弹性空间
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.addWidget(spacer)
        
        # 状态指示器
        self.status_container = QWidget()
        layout = QHBoxLayout(self.status_container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 修改状态指示器
        self.unsaved_label = QLabel("●")
        self.unsaved_label.setStyleSheet("color: red; font-weight: bold;")
        self.unsaved_label.setToolTip("有未保存的更改")
        self.unsaved_label.setVisible(False)  # 初始状态隐藏
        layout.addWidget(self.unsaved_label)
        
        # 总实验数量显示
        self.experiment_count_label = QLabel("实验: 0")
        layout.addWidget(self.experiment_count_label)
        
        # 添加状态指示器到工具栏
        self.addWidget(self.status_container)
    
    def _bind_viewmodel_state(self):
        """绑定ViewModel状态"""
        # 绑定保存状态变化
        def update_save_state(has_changes):
            self.unsaved_label.setVisible(has_changes)
        
        if hasattr(self.viewmodel, 'has_unsaved_changes'):
            self.viewmodel.has_unsaved_changes.bind_to(update_save_state)
        
        # 绑定选中实验状态
        def update_experiment_buttons(experiment):
            has_selection = experiment is not None
            self.edit_experiment_action.setEnabled(has_selection)
            self.delete_experiment_action.setEnabled(has_selection)
            self.export_action.setEnabled(has_selection)
        
        if hasattr(self.viewmodel, 'selected_experiment'):
            self.viewmodel.selected_experiment.bind_to(update_experiment_buttons)
        
        # 绑定实验数量
        def update_experiment_count(count):
            self.experiment_count_label.setText(f"实验: {count}")
        
        if hasattr(self.viewmodel, 'experiment_count'):
            self.viewmodel.experiment_count.bind_to(update_experiment_count)
        
        # 绑定撤销/重做状态
        def update_undo_state(can_undo):
            self.undo_action.setEnabled(can_undo)
        
        def update_redo_state(can_redo):
            self.redo_action.setEnabled(can_redo)
        
        if hasattr(self.viewmodel, 'can_undo'):
            self.viewmodel.can_undo.bind_to(update_undo_state)
        
        if hasattr(self.viewmodel, 'can_redo'):
            self.viewmodel.can_redo.bind_to(update_redo_state)
        
        # 绑定加载状态
        def update_loading_state(is_loading):
            # 在加载时禁用所有按钮
            for action in self.actions():
                action.setEnabled(not is_loading)
            
            # 特殊处理需要选中状态的按钮
            if not is_loading and hasattr(self.viewmodel, 'selected_experiment'):
                update_experiment_buttons(self.viewmodel.selected_experiment.value)
            
            if not is_loading:
                if hasattr(self.viewmodel, 'can_undo'):
                    update_undo_state(self.viewmodel.can_undo.value)
                if hasattr(self.viewmodel, 'can_redo'):
                    update_redo_state(self.viewmodel.can_redo.value)
        
        if hasattr(self.viewmodel, 'is_loading'):
            self.viewmodel.is_loading.bind_to(update_loading_state)
    
    def add_custom_action(self, text: str, callback: Callable, tooltip: str = None, 
                          enabled: bool = True, icon: QIcon = None) -> QAction:
        """添加自定义操作按钮"""
        action = QAction(text, self)
        
        if tooltip:
            action.setToolTip(tooltip)
        
        if icon:
            action.setIcon(icon)
        
        action.setEnabled(enabled)
        action.triggered.connect(callback)
        self.addAction(action)
        
        return action 
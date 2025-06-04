from PyQt5.QtWidgets import (QStatusBar, QLabel, QProgressBar, 
                             QHBoxLayout, QWidget, QFrame)
from PyQt5.QtCore import Qt, QTimer
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...viewmodels.main_viewmodel import MainViewModel

class MainStatusBar(QStatusBar):
    """主窗口状态栏组件"""
    
    def __init__(self, parent, viewmodel: 'MainViewModel'):
        super().__init__(parent)
        self.viewmodel = viewmodel
        
        self._create_status_widgets()
        self._bind_viewmodel()
        self._setup_auto_clear()
    
    def _create_status_widgets(self):
        """创建状态栏控件"""
        # 主要状态信息
        self.status_label = QLabel("就绪")
        self.addWidget(self.status_label)
        
        # 分隔符
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.VLine)
        separator1.setFrameShadow(QFrame.Sunken)
        self.addPermanentWidget(separator1)
        
        # 实验数量信息
        self.experiment_count_label = QLabel("实验: 0")
        self.addPermanentWidget(self.experiment_count_label)
        
        # 分隔符
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.VLine)
        separator2.setFrameShadow(QFrame.Sunken)
        self.addPermanentWidget(separator2)
        
        # 进度条（用于显示加载状态）
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(150)
        self.addPermanentWidget(self.progress_bar)
        
        # 忙碌状态指示器
        self.busy_label = QLabel()
        self.busy_label.setVisible(False)
        self.addPermanentWidget(self.busy_label)
        
        # 时间显示
        self.time_label = QLabel()
        self.addPermanentWidget(self.time_label)
        self._update_time()
        
        # 定时更新时间
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self._update_time)
        self.time_timer.start(1000)  # 每秒更新
    
    def _bind_viewmodel(self):
        """绑定ViewModel"""
        # 状态消息变化
        self.viewmodel.status_changed.connect(self.show_message)
        
        # 错误消息
        self.viewmodel.error_occurred.connect(self.show_error)
        
        # 实验数量变化
        self.viewmodel.experiment_count.bind_to(self._update_experiment_count)
        
        # 忙碌状态变化
        self.viewmodel.bind_property("is_busy", self._update_busy_state)
        
        # 实验加载状态
        self.viewmodel.experiments_loaded.connect(lambda experiments: 
                                                 self.show_message(f"已加载 {len(experiments)} 个实验", 3000))
    
    def _setup_auto_clear(self):
        """设置状态消息自动清除"""
        self.auto_clear_timer = QTimer()
        self.auto_clear_timer.setSingleShot(True)
        self.auto_clear_timer.timeout.connect(lambda: self.show_message("就绪"))
    
    def _update_time(self):
        """更新时间显示"""
        from datetime import datetime
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_label.setText(current_time)
    
    def _update_experiment_count(self, count: int):
        """更新实验数量显示"""
        self.experiment_count_label.setText(f"实验: {count}")
    
    def _update_busy_state(self, is_busy: bool):
        """更新忙碌状态"""
        if is_busy:
            self.busy_label.setText("处理中...")
            self.busy_label.setVisible(True)
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # 不定进度
        else:
            self.busy_label.setVisible(False)
            self.progress_bar.setVisible(False)
    
    def show_message(self, message: str, timeout: int = 0):
        """显示状态消息"""
        self.status_label.setText(message)
        
        if timeout > 0:
            self.auto_clear_timer.start(timeout)
    
    def show_error(self, error_message: str):
        """显示错误消息"""
        self.status_label.setText(f"错误: {error_message}")
        self.status_label.setStyleSheet("color: red;")
        
        # 5秒后自动清除
        QTimer.singleShot(5000, lambda: (
            self.status_label.setText("就绪"),
            self.status_label.setStyleSheet("")
        ))
    
    def show_warning(self, warning_message: str):
        """显示警告消息"""
        self.status_label.setText(f"警告: {warning_message}")
        self.status_label.setStyleSheet("color: orange;")
        
        # 3秒后自动清除
        QTimer.singleShot(3000, lambda: (
            self.status_label.setText("就绪"),
            self.status_label.setStyleSheet("")
        ))
    
    def show_success(self, success_message: str):
        """显示成功消息"""
        self.status_label.setText(success_message)
        self.status_label.setStyleSheet("color: green;")
        
        # 2秒后自动清除
        QTimer.singleShot(2000, lambda: (
            self.status_label.setText("就绪"),
            self.status_label.setStyleSheet("")
        ))
    
    def set_progress(self, value: int, maximum: int = 100):
        """设置进度"""
        if maximum > 0:
            self.progress_bar.setRange(0, maximum)
            self.progress_bar.setValue(value)
            self.progress_bar.setVisible(True)
        else:
            self.progress_bar.setVisible(False)
    
    def clear_progress(self):
        """清除进度显示"""
        self.progress_bar.setVisible(False)
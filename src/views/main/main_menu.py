from PyQt5.QtWidgets import QMenuBar, QMenu, QAction, QActionGroup
from PyQt5.QtCore import Qt, QSettings
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from ...viewmodels.main_viewmodel import MainViewModel


class MainMenu(QMenuBar):
    """主窗口菜单栏"""
    
    def __init__(self, parent, viewmodel: 'MainViewModel'):
        super().__init__(parent)
        self.parent = parent
        self.viewmodel = viewmodel
        
        # 创建各个菜单
        self._create_file_menu()
        self._create_edit_menu()
        self._create_experiment_menu()
        self._create_view_menu()
        self._create_tools_menu()
        self._create_help_menu()
    
    def _create_file_menu(self):
        """创建文件菜单"""
        file_menu = self.addMenu("文件(&F)")
        
        # 新建项目
        new_action = QAction("新建项目(&N)...", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(lambda: self.viewmodel.new_project())
        file_menu.addAction(new_action)
        
        # 打开项目
        open_action = QAction("打开项目(&O)...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(lambda: self.viewmodel.open_project())
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        # 保存
        save_action = QAction("保存(&S)", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(lambda: self.viewmodel.save_project())
        file_menu.addAction(save_action)
        
        # 另存为
        save_as_action = QAction("另存为(&A)...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(lambda: self.viewmodel.save_as())
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        # 最近文件子菜单
        self.recent_menu = QMenu("最近的文件", self)
        file_menu.addMenu(self.recent_menu)
        self._update_recent_files_menu()
        
        file_menu.addSeparator()
        
        # 退出
        exit_action = QAction("退出(&Q)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(lambda: self.viewmodel.exit())
        file_menu.addAction(exit_action)
    
    def _create_edit_menu(self):
        """创建编辑菜单"""
        edit_menu = self.addMenu("编辑(&E)")
        
        # 撤销
        undo_action = QAction("撤销(&U)", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(lambda: self.viewmodel.undo())
        edit_menu.addAction(undo_action)
        
        # 重做
        redo_action = QAction("重做(&R)", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.triggered.connect(lambda: self.viewmodel.redo())
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        # 复制
        copy_action = QAction("复制(&C)", self)
        copy_action.setShortcut("Ctrl+C")
        copy_action.setEnabled(False)  # 暂时禁用
        edit_menu.addAction(copy_action)
        
        # 粘贴
        paste_action = QAction("粘贴(&V)", self)
        paste_action.setShortcut("Ctrl+V")
        paste_action.setEnabled(False)  # 暂时禁用
        edit_menu.addAction(paste_action)
        
        edit_menu.addSeparator()
        
        # 查找
        find_action = QAction("查找(&F)...", self)
        find_action.setShortcut("Ctrl+F")
        find_action.setEnabled(False)  # 暂时禁用
        edit_menu.addAction(find_action)
        
        # 替换
        replace_action = QAction("替换(&H)...", self)
        replace_action.setShortcut("Ctrl+H")
        replace_action.setEnabled(False)  # 暂时禁用
        edit_menu.addAction(replace_action)
    
    def _create_experiment_menu(self):
        """创建实验菜单"""
        experiment_menu = self.addMenu("实验(&X)")
        
        # 新建实验
        new_exp_action = QAction("新建实验(&N)...", self)
        new_exp_action.setShortcut("Ctrl+Shift+N")
        new_exp_action.triggered.connect(lambda: self.viewmodel.add_experiment())
        experiment_menu.addAction(new_exp_action)
        
        # 编辑实验
        edit_exp_action = QAction("编辑实验(&E)...", self)
        edit_exp_action.triggered.connect(lambda: self.viewmodel.edit_experiment())
        experiment_menu.addAction(edit_exp_action)
        
        # 删除实验
        delete_exp_action = QAction("删除实验(&D)", self)
        delete_exp_action.setShortcut("Delete")
        delete_exp_action.triggered.connect(lambda: self.viewmodel.delete_experiment())
        experiment_menu.addAction(delete_exp_action)
        
        experiment_menu.addSeparator()
        
        # 复制实验
        duplicate_action = QAction("复制实验(&C)", self)
        duplicate_action.triggered.connect(lambda: self.viewmodel.duplicate_experiment())
        experiment_menu.addAction(duplicate_action)
        
        experiment_menu.addSeparator()
        
        # 导出实验数据
        export_action = QAction("导出实验数据(&X)...", self)
        export_action.triggered.connect(lambda: self.viewmodel.export_experiment())
        experiment_menu.addAction(export_action)
        
        # 导出所有实验
        export_all_action = QAction("导出所有实验(&A)...", self)
        export_all_action.triggered.connect(lambda: self.viewmodel.export_all_experiments())
        experiment_menu.addAction(export_all_action)
    
    def _create_view_menu(self):
        """创建视图菜单"""
        view_menu = self.addMenu("视图(&V)")
        
        # 刷新
        refresh_action = QAction("刷新(&R)", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(lambda: self.viewmodel.refresh())
        view_menu.addAction(refresh_action)
        
        view_menu.addSeparator()
        
        # 主题子菜单
        theme_menu = QMenu("主题(&T)", self)
        view_menu.addMenu(theme_menu)
        
        # 添加主题选项
        themes = ["默认", "暗色", "浅色", "系统"]
        theme_group = QActionGroup(self)
        for theme in themes:
            theme_action = QAction(theme, self)
            theme_action.setCheckable(True)
            theme_action.triggered.connect(lambda checked, t=theme: self._change_theme(t))
            theme_group.addAction(theme_action)
            theme_menu.addAction(theme_action)
        
        # 默认选中第一个主题
        theme_group.actions()[0].setChecked(True)
        
        view_menu.addSeparator()
        
        # 全屏
        fullscreen_action = QAction("全屏(&F)", self)
        fullscreen_action.setShortcut("F11")
        fullscreen_action.setCheckable(True)
        fullscreen_action.triggered.connect(self._toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
    
    def _create_tools_menu(self):
        """创建工具菜单"""
        tools_menu = self.addMenu("工具(&T)")
        
        # 活度计算器
        calculator_action = QAction("活度计算器(&C)...", self)
        calculator_action.triggered.connect(self._show_activity_calculator)
        tools_menu.addAction(calculator_action)
        
        # 核素衰减查询
        nuclide_action = QAction("核素衰减查询(&N)...", self)
        nuclide_action.triggered.connect(self._show_nuclide_info)
        tools_menu.addAction(nuclide_action)
        
        tools_menu.addSeparator()
        
        # 数据导入向导
        import_action = QAction("数据导入向导(&I)...", self)
        import_action.triggered.connect(self._show_import_wizard)
        tools_menu.addAction(import_action)
        
        # 批量处理
        batch_action = QAction("批量处理(&B)...", self)
        batch_action.triggered.connect(self._show_batch_processor)
        tools_menu.addAction(batch_action)
        
        tools_menu.addSeparator()
        
        # 设置
        settings_action = QAction("设置(&S)...", self)
        settings_action.triggered.connect(self._show_settings)
        tools_menu.addAction(settings_action)
    
    def _create_help_menu(self):
        """创建帮助菜单"""
        help_menu = self.addMenu("帮助(&H)")
        
        # 用户手册
        help_action = QAction("用户手册(&M)", self)
        help_action.setShortcut("F1")
        help_action.triggered.connect(self._show_help)
        help_menu.addAction(help_action)
        
        # 快捷键
        shortcuts_action = QAction("快捷键(&K)...", self)
        shortcuts_action.triggered.connect(self._show_shortcuts)
        help_menu.addAction(shortcuts_action)
        
        help_menu.addSeparator()
        
        # 检查更新
        update_action = QAction("检查更新(&U)...", self)
        update_action.triggered.connect(self._check_updates)
        help_menu.addAction(update_action)
        
        # 关于
        about_action = QAction("关于(&A)...", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _update_recent_files_menu(self):
        """更新最近文件菜单"""
        self.recent_menu.clear()
        
        # 从设置中获取最近文件
        settings = QSettings("TiMo", "PET模体实验管理系统")
        recent_files = settings.value("recentFiles", [])
        
        if not recent_files:
            no_files_action = QAction("无最近文件", self)
            no_files_action.setEnabled(False)
            self.recent_menu.addAction(no_files_action)
            return
        
        # 添加最近文件到菜单
        for file_path in recent_files:
            action = QAction(file_path, self)
            action.triggered.connect(lambda checked, path=file_path: self.viewmodel.open_recent_file(path))
            self.recent_menu.addAction(action)
        
        self.recent_menu.addSeparator()
        clear_action = QAction("清除最近文件列表", self)
        clear_action.triggered.connect(self._clear_recent_files)
        self.recent_menu.addAction(clear_action)
    
    def _clear_recent_files(self):
        """清除最近文件列表"""
        settings = QSettings("TiMo", "PET模体实验管理系统")
        settings.setValue("recentFiles", [])
        self._update_recent_files_menu()
    
    def _change_theme(self, theme_name: str):
        """改变主题"""
        if hasattr(self.viewmodel, 'change_theme'):
            self.viewmodel.change_theme(theme_name)
    
    def _toggle_fullscreen(self, checked=False):
        """切换全屏模式"""
        if checked:
            self.parent.showFullScreen()
        else:
            self.parent.showNormal()
    
    def _show_activity_calculator(self):
        """显示活度计算器"""
        if hasattr(self.viewmodel, 'show_activity_calculator'):
            self.viewmodel.show_activity_calculator()
    
    def _show_nuclide_info(self):
        """显示核素衰减查询"""
        if hasattr(self.viewmodel, 'show_nuclide_info'):
            self.viewmodel.show_nuclide_info()
    
    def _show_import_wizard(self):
        """显示数据导入向导"""
        if hasattr(self.viewmodel, 'show_import_wizard'):
            self.viewmodel.show_import_wizard()
    
    def _show_batch_processor(self):
        """显示批量处理"""
        if hasattr(self.viewmodel, 'show_batch_processor'):
            self.viewmodel.show_batch_processor()
    
    def _show_settings(self):
        """显示设置"""
        if hasattr(self.viewmodel, 'show_settings'):
            self.viewmodel.show_settings()
    
    def _show_help(self):
        """显示帮助"""
        if hasattr(self.viewmodel, 'show_help'):
            self.viewmodel.show_help()
    
    def _show_shortcuts(self):
        """显示快捷键"""
        if hasattr(self.viewmodel, 'show_shortcuts'):
            self.viewmodel.show_shortcuts()
    
    def _check_updates(self):
        """检查更新"""
        if hasattr(self.viewmodel, 'check_updates'):
            self.viewmodel.check_updates()
    
    def _show_about(self):
        """显示关于对话框"""
        if hasattr(self.viewmodel, 'show_about'):
            self.viewmodel.show_about() 
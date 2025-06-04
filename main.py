#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from src.viewmodels.main_viewmodel import MainViewModel
from src.views.main.main_window import MainWindow

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 确保数据目录存在
experiment_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "experiments")
if not os.path.exists(experiment_dir):
    os.makedirs(experiment_dir)
    logging.info(f"创建实验数据目录: {experiment_dir}")

# 启动应用
if __name__ == "__main__":
    # 创建应用程序
    app = QApplication(sys.argv)
    
    # 创建ViewModel
    viewmodel = MainViewModel()
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec_()) 
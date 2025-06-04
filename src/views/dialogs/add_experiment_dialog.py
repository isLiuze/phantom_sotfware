from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QTextEdit,
    QFrame, QGridLayout, QMessageBox
)
from PyQt5.QtCore import Qt
from ...utils.time_utils import get_current_beijing_time
from ...core.constants import PHANTOM_TYPES

class AddExperimentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新建实验")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # 标题
        title = QLabel("新建实验")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #1976d2;
                padding-bottom: 10px;
            }
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        # 输入表单
        form_layout = QGridLayout()
        form_layout.setSpacing(15)
        form_layout.setColumnStretch(1, 1)

        # 创建输入控件
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("请输入实验名称...")
        
        self.center_input = QLineEdit()
        self.center_input.setPlaceholderText("请输入中心名称...")
        
        self.date_input = QLineEdit(get_current_beijing_time().strftime("%Y-%m-%d"))
        
        self.phantom_type = QComboBox()
        self.phantom_type.addItems(PHANTOM_TYPES)
        
        self.remark_input = QTextEdit()
        self.remark_input.setPlaceholderText("可选：输入备注信息...")
        self.remark_input.setMaximumHeight(80)

        # 添加到表单
        fields = [
            ("实验名称 *", self.name_input),
            ("中心名称 *", self.center_input),
            ("日期", self.date_input),
            ("模体类型", self.phantom_type),
            ("备注", self.remark_input)
        ]

        for row, (label_text, widget) in enumerate(fields):
            label = QLabel(label_text)
            label.setStyleSheet("font-weight: 600; color: #495057;")
            form_layout.addWidget(label, row, 0, Qt.AlignRight)
            form_layout.addWidget(widget, row, 1)

        layout.addLayout(form_layout)

        # 提示信息
        hint = QLabel("* 标记的字段为必填项")
        hint.setStyleSheet("color: #6c757d; font-size: 12px;")
        layout.addWidget(hint)

        # 添加弹性空间
        layout.addStretch()

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        cancel_button = QPushButton("取消")
        cancel_button.setFixedWidth(100)
        cancel_button.setObjectName("secondary")
        
        ok_button = QPushButton("创建")
        ok_button.setFixedWidth(100)
        ok_button.setDefault(True)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(ok_button)
        
        layout.addLayout(button_layout)

        # 连接信号
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

        self.setLayout(layout)

        # 设置焦点
        self.name_input.setFocus()

    def get_data(self):
        """返回用户输入的数据"""
        return {
            "name": self.name_input.text().strip(),
            "center": self.center_input.text().strip(),
            "date": self.date_input.text().strip(),
            "model_type": self.phantom_type.currentText().strip(),
            "remark": self.remark_input.toPlainText().strip()
        }
    
    def get_experiment_data(self):
        """返回用户输入的实验数据 - 与get_data方法保持一致"""
        return self.get_data()

    def accept(self):
        """验证必填字段后再关闭对话框"""
        if not self.name_input.text().strip() or not self.center_input.text().strip():
            QMessageBox.warning(self, "提示", "实验名称和中心名称为必填项")
            return
        super().accept()

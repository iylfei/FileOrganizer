from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import *
from organizer import organize

custom_list = []

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('文件整理')
        self.resize(400, 300)
        self.filepath = None

        # 储存自定义的关键词或拓展名列表
        self.custom_list = None

        # 储存自定义设置窗口
        self.custom_window = None

        # 整体布局
        whole_layout = QVBoxLayout()
        self.setLayout(whole_layout)

        # 整体样式
        self.setStyleSheet("""
            QLabel{
                font-size: 18pt;
                font-family: Microsoft YaHe;
            }
            QPushButton{
                background-color: rgb(211,211,211);
                font-family: Microsoft YaHe;
                font-size: 18pt;
                border: 1px solid black;
                border-radius: 5px;
            }
            QPushButton:hover{
                background-color: rgb(255, 255, 255);
                border: 1px solid black;
                border-radius: 5px;
            }
        """)

        # 提示标签
        select_dir_label = QLabel('选择要整理的文件夹：', self)
        # 选择按钮
        select_dir_button = QPushButton('选择', self)

        # 选择路径水平布局（提示+选择按钮）
        select_layout = QHBoxLayout()
        select_layout.addWidget(select_dir_label, alignment=Qt.AlignCenter)
        select_layout.addWidget(select_dir_button, alignment=Qt.AlignCenter)

        # 自定义标签
        custom_label = QLabel('自定义整理文件格式：', self)
        # 自定义设置按钮
        custom_button = QPushButton('设置', self)
        # 自定义设置水平布局 （提示+自定义按钮）
        custom_layout = QHBoxLayout()
        custom_layout.addWidget(custom_label, alignment=Qt.AlignCenter)
        custom_layout.addWidget(custom_button, alignment=Qt.AlignCenter)

        # 将布局添加到整体布局
        whole_layout.addLayout(select_layout)
        whole_layout.addLayout(custom_layout)

        # 连接槽函数
        select_dir_button.clicked.connect(self.getDir)
        custom_button.clicked.connect(self.open_customUI)

    def open_customUI(self):
        if self.custom_window == None:
            self.custom_window = CustomUI()
            self.custom_window.custom_confirmed.connect(self.update_custom_list)
        self.custom_window.show()
        self.custom_window.finished.connect(lambda : setattr(self, 'custom_window', None))

    def update_custom_list(self, received_list):
        self.custom_list = received_list
        msgBox = QMessageBox()
        msgBox.setWindowTitle('提示')
        msgBox.setText('自定义设置已保存')
        msgBox.setStyleSheet("font-size: 12pt;")
        msgBox.exec_()

    def getDir(self):
        self.filepath = QFileDialog.getExistingDirectory(self, '请选择要整理的文件夹')
        if self.filepath:
            print(f'已选择文件夹：{self.filepath}')
            organize(self.filepath, self.custom_list)
            # 完成后弹出完成提示
            QMessageBox.information(self, '提示', '文件整理完成')



class CustomUI(QDialog):
    custom_confirmed = Signal(list)
    def __init__(self):
        super().__init__()
        self.input_lineedit = None
        self.setWindowTitle("自定义")
        self.resize(300,150)
        w_layout = QVBoxLayout(self)
        self.setLayout(w_layout)

        # 输入框
        input_label = QLabel("输入文件名关键词或拓展名(用','隔开):", self)
        self.input_lineedit = QLineEdit(self)
        self.input_lineedit.setStyleSheet("font-size: 14pt;")  # 字体调小一点，不然显示不全
        input_label.setStyleSheet("font-size: 14pt;")
        w_layout.addWidget(input_label)

        input_layout = QHBoxLayout()
        input_layout.addStretch(1)
        input_layout.addWidget(self.input_lineedit)
        input_layout.addStretch(1)
        w_layout.addLayout(input_layout)

        # 提示信息
        info_label = QLabel("注意：拓展名请在开头加上 .", self)
        info_label.setStyleSheet("font-size: 15pt; color: red;")
        w_layout.addWidget(info_label, alignment=Qt.AlignCenter)

        # 加入确定和取消按钮
        confirm_button = QPushButton('确定', self)
        cancel_button = QPushButton('取消', self)
        c_layout = QHBoxLayout()
        c_layout.addStretch(1)
        c_layout.addWidget(confirm_button)
        c_layout.addStretch(1)
        c_layout.addWidget(cancel_button)
        c_layout.addStretch(1)
        w_layout.addLayout(c_layout)

        # 连接确定和取消按钮
        confirm_button.clicked.connect(self.confirm_and_close)
        cancel_button.clicked.connect(self.close)

    # 发送自定义列表并关闭窗口
    def confirm_and_close(self):
        line_text = self.input_lineedit.text()
        custom_list = []
        if line_text:
            line_text = line_text.replace('，', ',')
            custom_list = [item.strip() for item in line_text.split(',')]
        self.custom_confirmed.emit(custom_list)
        self.close()
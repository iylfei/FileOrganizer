# ui.py
import json
import os
from pydoc import describe

from PySide6.QtCore import Qt, Signal, QThread, QDate, QDateTime, QTime
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QHBoxLayout, QDialog, \
    QFileDialog, QWidget, QProgressBar, QTabWidget, QGroupBox, QCheckBox, QDateEdit, QComboBox, QTextEdit, QSizePolicy
from organizer import FileOrganizer


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('文件整理')
        self.resize(550, 350)
        self.filepath = None
        self.custom_list = []
        self.custom_window = None
        self.advanced_settings_window = None
        self.worker_thread = None
        self.organizer = None

        # 整体布局
        whole_layout = QVBoxLayout()
        self.setLayout(whole_layout)

        # 整体样式
        self.setStyleSheet("""
            QLabel{
                font-size: 16pt;
                font-family: Microsoft YaHe;
            }
            QPushButton{
                background-color: rgb(211,211,211);
                font-family: Microsoft YaHe;
                font-size: 16pt;
                border: 1px solid black;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover{
                background-color: rgb(255, 255, 255);
            }
            QPushButton:disabled{
                background-color: rgb(240, 240, 240);
                color: rgb(128, 128, 128);
            }
            QProgressBar {
                font-size: 12pt;
                text-align: center;
            }
        """)

        # 文件选择
        select_dir_label = QLabel(' 选择要整理的文件夹：', self)
        self.select_dir_button = QPushButton('选择文件夹', self)
        self.selected_path_label = QLabel("尚未选择文件夹", self)
        self.selected_path_label.setStyleSheet("font-size: 10pt; color: grey;")

        select_layout = QHBoxLayout()
        select_layout.addWidget(select_dir_label)
        select_layout.addWidget(self.select_dir_button)

        # 自定义设置
        custom_label = QLabel(' 高级整理设置(可选)：', self)
        self.custom_button = QPushButton('设置', self)
        custom_layout = QHBoxLayout()
        custom_layout.addWidget(custom_label)
        custom_layout.addWidget(self.custom_button)

        # 开始按钮
        self.start_button = QPushButton('开始整理', self)
        self.start_button.setEnabled(False)  # 初始时禁用，选择文件夹后启用

        # 进度显示
        self.status_label = QLabel("请先选择一个文件夹...", self)
        self.status_label.setStyleSheet("font-size: 12pt; color: blue;")
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)

        # 将所有控件添加到主布局
        whole_layout.addLayout(select_layout)
        whole_layout.addWidget(self.selected_path_label, alignment=Qt.AlignCenter)
        whole_layout.addStretch(1)
        whole_layout.addLayout(custom_layout)
        whole_layout.addStretch(1)
        whole_layout.addWidget(self.start_button)
        whole_layout.addStretch(1)
        whole_layout.addWidget(QLabel("整理状态:"))
        whole_layout.addWidget(self.status_label)
        whole_layout.addWidget(self.progress_bar)

        # 连接槽函数
        self.select_dir_button.clicked.connect(self.getDir)
        self.custom_button.clicked.connect(self.open_advanced_settings)
        self.start_button.clicked.connect(self.start_organization)

    def getDir(self):
        # 获取路径和更新UI
        dir_path = QFileDialog.getExistingDirectory(self, '请选择要整理的文件夹')
        if dir_path:
            self.filepath = dir_path
            self.selected_path_label.setText(f"已选择: {self.filepath}")
            self.start_button.setEnabled(True)  # 启用开始按钮
            self.status_label.setText("准备就绪，可以开始整理。")
            self.progress_bar.setValue(0)

    def start_organization(self):
        if not self.filepath:
            QMessageBox.warning(self, "警告", "请先选择一个要整理的文件夹！")
            return

        # 禁用按钮，防止重复点击
        self.start_button.setEnabled(False)
        self.select_dir_button.setEnabled(False)
        self.custom_button.setEnabled(False)

        # 创建 QThread 和 FileOrganizer 实例
        self.worker_thread = QThread()
        config_path = os.path.join(os.getcwd(), "config.json")
        self.organizer = FileOrganizer(self.filepath, config_path)

        # 将 organizer移动到新线程中
        self.organizer.moveToThread(self.worker_thread)

        # 连接信号和槽
        # 当线程启动时，执行 organizer.organize 方法
        self.worker_thread.started.connect(self.organizer.organize)

        # 连接 organizer 的信号到 MainWindow 的槽函数，以更新UI
        self.organizer.progress_updated.connect(self.update_progress)
        self.organizer.status_updated.connect(self.update_status)
        self.organizer.finished.connect(self.on_finished)

        # 当任务完成时，退出并清理线程
        self.organizer.finished.connect(self.worker_thread.quit)
        self.organizer.finished.connect(self.organizer.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)

        # 启动线程
        self.worker_thread.start()

    # 更新进度条
    def update_progress(self, value):
        self.progress_bar.setValue(value)

    # 更新状态文本
    def update_status(self, message):
        self.status_label.setText(message)

    # 任务完成后的处理
    def on_finished(self):
        # 重新启用按钮
        self.start_button.setEnabled(True)
        self.select_dir_button.setEnabled(True)
        self.custom_button.setEnabled(True)

        # 弹出提示
        if "错误" not in self.status_label.text():
            QMessageBox.information(self, '提示', '文件整理完成！')
        else:
            QMessageBox.critical(self, '错误', self.status_label.text())

    def open_advanced_settings(self):
        if self.advanced_settings_window is None:
            self.advanced_settings_window = AdvancedSettings()
        self.advanced_settings_window.show()


class CustomUI(QDialog):
    custom_confirmed = Signal(list)

    def __init__(self):
        super().__init__()
        self.input_lineedit = None
        self.setWindowTitle("自定义")
        self.resize(300, 150)
        w_layout = QVBoxLayout(self)
        self.setLayout(w_layout)

        # 输入框
        input_label = QLabel("输入文件名关键词或拓展名(用','隔开):", self)
        self.input_lineedit = QLineEdit(self)
        self.input_lineedit.setStyleSheet("font-size: 14pt;")
        input_label.setStyleSheet("font-size: 14pt;")
        w_layout.addWidget(input_label)

        input_layout = QHBoxLayout()
        input_layout.addStretch(1)
        input_layout.addWidget(self.input_lineedit)
        input_layout.addStretch(1)
        w_layout.addLayout(input_layout)

        # 提示信息
        info_label = QLabel("注意：拓展名请在开头加上 . ", self)
        info_label.setStyleSheet("font-size: 15pt; color: red;")
        w_layout.addWidget(info_label, alignment=Qt.AlignCenter)

        # 加入确定和取消按钮
        self.confirm_button = QPushButton('确定', self)
        cancel_button = QPushButton('取消', self)
        self.confirm_button.setEnabled(False)
        c_layout = QHBoxLayout()
        c_layout.addStretch(1)
        c_layout.addWidget(self.confirm_button)
        c_layout.addStretch(1)
        c_layout.addWidget(cancel_button)
        c_layout.addStretch(1)
        w_layout.addLayout(c_layout)

        # 连接确定和取消按钮
        self.confirm_button.clicked.connect(self.confirm_and_close)
        cancel_button.clicked.connect(self.close)
        # 连接input_edit更改信号
        self.input_lineedit.textChanged.connect(self.enable_confirmbutton)

    def enable_confirmbutton(self,text):
        self.confirm_button.setEnabled(bool(text.strip()))

    def confirm_and_close(self):
        line_text = self.input_lineedit.text()
        custom_list = []
        if line_text:
            line_text = line_text.replace('，', ',')
            custom_list = [item.strip() for item in line_text.split(',') if item.strip()]
        self.custom_confirmed.emit(custom_list)
        self.close()


class AdvancedSettings(QDialog):
    def __init__(self):
        super().__init__()
        self.custom_window = None
        self.setWindowTitle("高级整理设置")
        self.resize(250, 300)
        w_layout = QVBoxLayout(self)
        self.setLayout(w_layout)

        self.advanced_settings_tab = QTabWidget()

        self.setStyleSheet("""
                    QGroupBox {
                        font-size: 11pt; 
                    }
                    QGroupBox::title {
                        subcontrol-position: top center;
                    }
                    QLabel, QCheckBox {
                        font-size: 12pt; 
                        font-family: Microsoft YaHe;
                    }
                    QPushButton, QComboBox, QDateEdit, QLineEdit {
                        font-size: 11pt; 
                        font-family: Microsoft YaHe;
                    }
                """)

        # 分类规则界面
        classification_group = QGroupBox("分类规则")
        classification_layout = QVBoxLayout()

        # 预设规则选项
        self.default_checkbox = QCheckBox("预设规则：")
        self.default_checkbox.setChecked(True)
        default_layout = QHBoxLayout()
        self.image_checkbox = QCheckBox("图片")
        self.image_checkbox.setChecked(True)
        default_layout.addWidget(self.image_checkbox)
        self.video_checkbox = QCheckBox("视频")
        self.video_checkbox.setChecked(True)
        default_layout.addWidget(self.video_checkbox)
        self.doc_checkbox = QCheckBox("文档")
        self.doc_checkbox.setChecked(True)
        default_layout.addWidget(self.doc_checkbox)
        self.other_checkbox = QCheckBox("其他")
        self.other_checkbox.setChecked(True)
        default_layout.addWidget(self.other_checkbox)

        # 按时间分类
        self.time_checkbox = QCheckBox("按时间分类：")
        time_layout = QHBoxLayout()
        start_day_label = QLabel("开始日期：")
        end_day_label = QLabel("结束日期：")
        self.start_date = QDateEdit(calendarPopup=True)
        self.end_date = QDateEdit(calendarPopup=True)
        today = QDate.currentDate()
        self.start_date.setDate(today)
        self.end_date.setDate(today)
        # 添加到时间布局
        time_layout.addWidget(self.time_checkbox)
        time_layout.addWidget(start_day_label)
        time_layout.addWidget(self.start_date)
        time_layout.addStretch()
        time_layout.addWidget(end_day_label)
        time_layout.addWidget(self.end_date)
        time_layout.addStretch()
        # 初始设置为禁用
        self.start_date.setEnabled(False)
        self.end_date.setEnabled(False)

        # 按文件大小分类
        self.size_checkbox = QCheckBox("按大小分类：")
        size_layout = QHBoxLayout()
        self.size_combobox = QComboBox()
        self.size_combobox.addItem("大于")
        self.size_combobox.addItem("小于")
        self.size_combobox.addItem("介于")
        int_validator = QIntValidator()
        self.size_edit1 = QLineEdit()  # edit1总是作为大于的值
        self.size_edit1.setValidator(int_validator)
        self.size_edit1.setPlaceholderText("10")
        self.size_edit2 = QLineEdit()  # edit2总是作为小于的值
        self.size_edit2.setValidator(int_validator)
        self.size_edit2.setPlaceholderText("100")
        self.big_label = QLabel("大于")
        self.small_label = QLabel("小于")
        self.size_label = QLabel("MB")
        self.both_label = QLabel("和")
        # 添加到布局
        size_layout.addWidget(self.size_checkbox)
        size_layout.addWidget(self.size_combobox)
        size_layout.addWidget(self.big_label)
        size_layout.addWidget(self.size_edit1)
        size_layout.addWidget(self.small_label)
        size_layout.addWidget(self.both_label)
        size_layout.addWidget(self.size_edit2)
        size_layout.addWidget(self.size_label)
        size_layout.addStretch()
        # 初始设置为禁用
        self.size_combobox.setEnabled(False)
        self.size_edit1.setEnabled(False)
        self.size_edit2.setEnabled(False)

        # 连接更新标签状态更新函数
        self.size_combobox.currentIndexChanged.connect(self.update_sizelabel_show)

        # 添加自定义分类选项
        self.custom_checkbox = QCheckBox("自定义规则：")
        self.custom_button = QPushButton("添加")
        custom_layout = QHBoxLayout()
        custom_layout.addWidget(self.custom_checkbox)
        custom_layout.addWidget(self.custom_button)
        self.custom_button.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed))
        custom_layout.addStretch()
        # 初始设置为禁用
        self.custom_button.setEnabled(False)
        # 连接按钮到自定义规则界面
        self.custom_button.clicked.connect(self.open_customUI)

        # 连接checkbox更新槽函数
        self.default_checkbox.stateChanged.connect(self.update_default_checkbox_state)
        self.time_checkbox.stateChanged.connect(self.update_checkbox)
        self.size_checkbox.stateChanged.connect(self.update_checkbox)
        self.custom_checkbox.stateChanged.connect(self.update_checkbox)

        # 将所有分类规则组件按顺序添加到布局中
        classification_layout.addWidget(self.default_checkbox)
        classification_layout.addLayout(default_layout)
        classification_layout.addStretch(1)
        classification_layout.addLayout(time_layout)
        classification_layout.addStretch(1)
        classification_layout.addLayout(size_layout)
        classification_layout.addStretch(1)
        classification_layout.addLayout(custom_layout)
        classification_layout.addStretch(1)

        # 为Group设置最终布局
        classification_group.setLayout(classification_layout)

        # 筛选规则界面
        filter_group = QGroupBox("筛选规则")
        self.advanced_settings_tab.addTab(filter_group, "筛选规则")
        filter_layout = QVBoxLayout()

        # 按时间筛选
        self.time_filter_checkbox = QCheckBox("按时间筛选")
        time_filter_layout = QHBoxLayout()
        self.start_filter_label = QLabel("开始日期：")
        self.start_filter_date = QDateEdit(calendarPopup=True)
        self.start_filter_date.setDate(today)
        self.end_filter_label = QLabel("结束日期：")
        self.end_filter_date = QDateEdit(calendarPopup=True)
        self.end_filter_date.setDate(today)
        # 初始禁用
        self.start_filter_date.setEnabled(False)
        self.end_filter_date.setEnabled(False)
        # 添加到time_filter布局
        time_filter_layout.addWidget(self.start_filter_label)
        time_filter_layout.addWidget(self.start_filter_date)
        time_filter_layout.addStretch()
        time_filter_layout.addWidget(self.end_filter_label)
        time_filter_layout.addWidget(self.end_filter_date)
        time_filter_layout.addStretch()

        # 按大小筛选
        self.size_filter_checkbox = QCheckBox("按大小筛选")
        size_filter_layout = QHBoxLayout()
        self.size_filter_combobox = QComboBox()
        self.size_filter_combobox.addItem("大于")
        self.size_filter_combobox.addItem("小于")
        self.size_filter_combobox.addItem("介于")
        self.size_filter_edit1 = QLineEdit()
        self.size_filter_edit1.setValidator(int_validator)
        self.size_filter_edit1.setPlaceholderText("10")
        self.size_filter_edit2 = QLineEdit()
        self.size_filter_edit2.setValidator(int_validator)
        self.size_filter_edit2.setPlaceholderText("100")
        self.big_filter_label = QLabel("大于")
        self.small_filter_label = QLabel("小于")
        self.size_filter_label = QLabel("MB")
        self.both_filter_label = QLabel("和")
        # 初始禁用
        self.size_filter_combobox.setEnabled(False)
        self.size_filter_edit1.setEnabled(False)
        self.size_filter_edit2.setEnabled(False)
        # 添加控件到size_filter布局
        size_filter_layout.addWidget(self.size_filter_combobox)
        size_filter_layout.addWidget(self.big_filter_label)
        size_filter_layout.addWidget(self.size_filter_edit1)
        size_filter_layout.addWidget(self.both_filter_label)
        size_filter_layout.addWidget(self.small_filter_label)
        size_filter_layout.addWidget(self.size_filter_edit2)
        size_filter_layout.addWidget(self.size_filter_label)
        size_filter_layout.addStretch()

        # 连接信号与槽函数
        self.time_filter_checkbox.stateChanged.connect(self.update_filter_checkbox)
        self.size_filter_checkbox.stateChanged.connect(self.update_filter_checkbox)
        self.size_filter_combobox.currentIndexChanged.connect(self.update_filter_sizelabel_show)

        # 将筛选规则添加到整体布局中
        filter_layout.addStretch()
        filter_layout.addWidget(self.time_filter_checkbox)
        filter_layout.addLayout(time_filter_layout)
        filter_layout.addStretch()
        filter_layout.addWidget(self.size_filter_checkbox)
        filter_layout.addLayout(size_filter_layout)
        filter_layout.addStretch()

        filter_group.setLayout(filter_layout)

        # 说明界面
        instruction_tab = QWidget()
        instruction_edit = QTextEdit()
        instruction_edit.setStyleSheet("font-size: 14px;")
        instruction_edit.setReadOnly(True)
        instruction_edit.setText("""
        说明：请阅读以下规则以更好地使用本应用。

        一、分类规则 (Classification Rules)
        
        分类规则决定了文件如何被归入不同的文件夹。规则具有优先级，程序会从高到低依次应用：

        优先级顺序：
        1.  自定义规则 (最高)
        2.  按大小分类
        3.  按时间分类
        4.  预设分类 (最低)

        工作方式：
           程序首先会用最高优先级的规则（例如“自定义规则”）来整理所有文件。
           整理完毕后，剩下未被分类的文件会接着被下一个优先级的规则（例如“按大小分类”）处理。
           这个过程会一直持续下去，直到所有勾选的规则都应用完毕。

        示例：
        如果您同时勾选了“自定义规则”和“按时间分类”：
        1.  程序会先根据您的自定义关键词，将匹配的文件（如 "报告.docx", "文章.docx"）放入“自定义”文件夹。
        2.  然后，在剩余的文件中，程序会再找出那些符合您设定时间范围的文件，并将它们移入以时间命名的文件夹。
        ——————————————————
        二、筛选规则 (Filtering Rules)

        筛选规则像一个过滤器，它与“分类规则”同时工作，用于在分类时添加额外的限制条件。

        工作方式：
           当您启用一个分类规则时（如“预设分类”），如果您同时启用了筛选规则（如“按时间筛选”），那么只有同时满足这两个条件的文件才会被整理。

        示例：
        如果您勾选了分类规则中的“预设分类”（整理图片、视频等），并且在筛选规则中设置了时间范围为“2024年全年”：
           最终的整理结果将是：在您指定的文件夹中，所有创建于2024年的图片、视频、文档等文件才会被分类。其他时间的文件，即使是图片，也不会被处理。
        """)
        instruction_layout = QVBoxLayout()
        instruction_layout.addWidget(instruction_edit)
        instruction_tab.setLayout(instruction_layout)

        # 将页面添加到TabWidget
        self.advanced_settings_tab.addTab(classification_group, "分类规则")
        self.advanced_settings_tab.addTab(filter_group, "筛选规则")
        self.advanced_settings_tab.addTab(instruction_tab, "说明")

        w_layout.addWidget(self.advanced_settings_tab)

        # 添加确定和取消按钮
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("确定")
        self.cancel_button = QPushButton("取消")

        button_layout.addStretch()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)

        w_layout.addLayout(button_layout)

        # 连接按钮信号
        self.ok_button.clicked.connect(self.save_and_close)
        self.cancel_button.clicked.connect(self.reject)

        # 初始化UI状态
        self.update_sizelabel_show()

    def update_default_checkbox_state(self, state):
        is_checked = self.default_checkbox.isChecked()
        self.image_checkbox.setEnabled(is_checked)
        self.video_checkbox.setEnabled(is_checked)
        self.doc_checkbox.setEnabled(is_checked)
        self.other_checkbox.setEnabled(is_checked)

    def update_sizelabel_show(self):
        size_choice = self.size_combobox.currentText()
        if size_choice == "大于":
            self.big_label.show()
            self.size_label.setText("MB")
            self.size_label.show()
            self.small_label.hide()
            self.both_label.hide()
            self.size_edit1.show()
            self.size_edit2.hide()
        elif size_choice == "小于":
            self.big_label.hide()
            self.size_label.setText("MB")
            self.size_label.show()
            self.small_label.show()
            self.both_label.hide()
            self.size_edit1.hide()
            self.size_edit2.show()
        elif size_choice == "介于":
            self.big_label.hide()
            self.size_label.setText("MB 之间")
            self.size_label.show()
            self.small_label.hide()
            self.both_label.show()
            self.size_edit1.show()
            self.size_edit2.show()

    def open_customUI(self):
        if self.custom_window is None:
            self.custom_window = CustomUI()
            self.custom_window.custom_confirmed.connect(self.update_custom_list)
        self.custom_window.show()
        self.custom_window.finished.connect(lambda: setattr(self, 'custom_window', None))

    def update_custom_list(self, received_list):
        self.custom_list = received_list
        QMessageBox.information(self, "提示", "自定义设置已保存！")

    def update_checkbox(self):
        sender_checkbox = self.sender()
        is_checked = sender_checkbox.isChecked()
        print(f"Checkbox {sender_checkbox.text()} state: {'Checked' if is_checked else 'Unchecked'}")
        if sender_checkbox == self.time_checkbox:
            self.start_date.setEnabled(is_checked)
            self.end_date.setEnabled(is_checked)
        elif sender_checkbox == self.size_checkbox:
            self.size_combobox.setEnabled(is_checked)
            self.size_edit1.setEnabled(is_checked)
            self.size_edit2.setEnabled(is_checked)
        elif sender_checkbox == self.custom_checkbox:
            self.custom_button.setEnabled(is_checked)

    def update_filter_sizelabel_show(self):
        size_choice = self.size_filter_combobox.currentText()
        if size_choice == "大于":
            self.big_filter_label.show()
            self.small_filter_label.hide()
            self.both_filter_label.hide()
            self.size_filter_edit1.show()
            self.size_filter_edit2.hide()
            self.size_filter_label.setText("MB")
        elif size_choice == "小于":
            self.big_filter_label.hide()
            self.small_filter_label.show()
            self.both_filter_label.hide()
            self.size_filter_edit1.hide()
            self.size_filter_edit2.show()
            self.size_filter_label.setText("MB")
        elif size_choice == "介于":
            self.big_filter_label.hide()
            self.small_filter_label.hide()
            self.both_filter_label.show()
            self.size_filter_edit1.show()
            self.size_filter_edit2.show()
            self.size_filter_label.setText("MB之间")

    def update_filter_checkbox(self):
        sender_checkbox = self.sender()
        is_checked = sender_checkbox.isChecked()
        print(f"Checkbox {sender_checkbox.text()} state: {'Checked' if is_checked else 'Unchecked'}")
        if sender_checkbox == self.time_filter_checkbox:
            self.start_filter_date.setEnabled(is_checked)
            self.end_filter_date.setEnabled(is_checked)
        elif sender_checkbox == self.size_filter_checkbox:
            self.size_filter_combobox.setEnabled(is_checked)
            self.size_filter_edit1.setEnabled(is_checked)
            self.size_filter_edit2.setEnabled(is_checked)

    def save_and_close(self):
        # 保存配置并关闭
        self.save_config()
        self.accept()

    # 保存配置为json文件
    def save_config(self):
        config = {
            "classification_rule": {
                "priority": ["custom", "size", "time", "default"],
                "custom": {"enabled": False, "keyword": []},
                "size": {"enabled": False, "model": "", "value1": "", "value2": ""},
                "time": {"enabled": False, "start_time": "", "end_time": ""},
                "default": {"enabled": False,
                            "images": False, "videos": False, "documents": False, "others": False}
            },
            "filter_rule": {
                "size": {"enabled": False, "model": "", "value1": "", "value2": ""},
                "time": {"enabled": False, "start_time": "", "end_time": ""}
            }
        }

        # 填充分类规则
        if self.custom_checkbox.isChecked():
            config["classification_rule"]["custom"]["enabled"] = True
            config["classification_rule"]["custom"]["keyword"] = self.custom_list
        if self.size_checkbox.isChecked():
            config["classification_rule"]["size"]["enabled"] = True
            config["classification_rule"]["size"]["model"] = self.size_combobox.currentText()
            config["classification_rule"]["size"]["value1"] = float(
                self.size_edit1.text()) if self.size_edit1.text() else 0
            config["classification_rule"]["size"]["value2"] = float(
                self.size_edit2.text()) if self.size_edit2.text() else 0
        if self.time_checkbox.isChecked():
            config["classification_rule"]["time"]["enabled"] = True
            start_dt = QDateTime(self.start_date.date(), QTime(0, 0, 0))
            end_dt = QDateTime(self.end_date.date(), QTime(23, 59, 59))
            config["classification_rule"]["time"]["start_time"] = start_dt.toSecsSinceEpoch()
            config["classification_rule"]["time"]["end_time"] = end_dt.toSecsSinceEpoch()
        if self.default_checkbox.isChecked():
            config["classification_rule"]["default"]["enabled"] = True
            config["classification_rule"]["default"]["images"] = self.image_checkbox.isChecked()
            config["classification_rule"]["default"]["videos"] = self.video_checkbox.isChecked()
            config["classification_rule"]["default"]["documents"] = self.doc_checkbox.isChecked()
            config["classification_rule"]["default"]["others"] = self.other_checkbox.isChecked()

        # 填充筛选规则
        if self.size_filter_checkbox.isChecked():
            config["filter_rule"]["size"]["enabled"] = True
            config["filter_rule"]["size"]["model"] = self.size_filter_combobox.currentText()
            config["filter_rule"]["size"]["value1"] = float(
                self.size_filter_edit1.text()) if self.size_filter_edit1.text() else 0
            config["filter_rule"]["size"]["value2"] = float(
                self.size_filter_edit2.text()) if self.size_filter_edit2.text() else 0
        if self.time_filter_checkbox.isChecked():
            config["filter_rule"]["time"]["enabled"] = True
            start_dt = QDateTime(self.start_filter_date.date(), QTime(0, 0, 0))
            end_dt = QDateTime(self.end_filter_date.date(), QTime(23, 59, 59))
            config["filter_rule"]["time"]["start_time"] = start_dt.toSecsSinceEpoch()
            config["filter_rule"]["time"]["end_time"] = end_dt.toSecsSinceEpoch()

        try:
            path = os.getcwd()
            config_path = os.path.join(path, "config.json")
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存配置文件失败: {e}")


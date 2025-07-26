# ui.py
from PySide6.QtCore import Qt, Signal, QThread, QDate
from PySide6.QtWidgets import QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QHBoxLayout, QDialog, \
    QFileDialog, QWidget, QProgressBar, QTabWidget, QGroupBox, QCheckBox, QDateEdit, QComboBox
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
        self.organizer = FileOrganizer(self.filepath, self.custom_list)

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
            QMessageBox.critical(self, '错误', f'整理过程中发生错误：\n{self.status_label.text()}')

    def open_customUI(self):
        if self.custom_window is None:
            self.custom_window = CustomUI()
            self.custom_window.custom_confirmed.connect(self.update_custom_list)
        self.custom_window.show()
        self.custom_window.finished.connect(lambda: setattr(self, 'custom_window', None))

    def update_custom_list(self, received_list):
        self.custom_list = received_list
        QMessageBox.information(self, "提示", "自定义设置已保存！")

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
        self.setWindowTitle("高级整理设置")
        self.resize(450, 400)
        w_layout = QVBoxLayout(self)
        self.setLayout(w_layout)

        self.advanced_settings_tab = QTabWidget()

        # group样式
        group_style = ("""
                   QGroupBox::title {
                        subcontrol-position: top center;
                        }
               """)
        # 分类规则界面
        classification_tab = QWidget()
        classification_tab.setStyleSheet(group_style)
        classification_tab_layout = QVBoxLayout()

        classification_group = QGroupBox("分类规则")
        classification_layout = QVBoxLayout()

        # 预设规则选项
        default_layout = QHBoxLayout()
        image_checkbox = QCheckBox("图片")
        image_checkbox.setChecked(True)
        default_layout.addWidget(image_checkbox)
        video_checkbox = QCheckBox("视频")
        video_checkbox.setChecked(True)
        default_layout.addWidget(video_checkbox)
        doc_checkbox = QCheckBox("文档")
        doc_checkbox.setChecked(True)
        default_layout.addWidget(doc_checkbox)
        other_checkbox = QCheckBox("其他")
        other_checkbox.setChecked(True)
        default_layout.addWidget(other_checkbox)

        default_label = QLabel("预设规则：")
        classification_layout.addWidget(default_label)
        classification_layout.addLayout(default_layout)
        classification_tab_layout.addWidget(classification_group)

        # 按时间分类
        time_checkbox = QCheckBox("按时间分类：")
        time_layout = QHBoxLayout()
        start_day_label = QLabel("开始日期：")
        end_day_label = QLabel("结束日期：")
        # 创建并设置日期选择控件
        start_date = QDateEdit(calendarPopup=True)
        end_date = QDateEdit(calendarPopup=True)
        today = QDate.currentDate()
        start_date.setDate(today)
        end_date.setDate(today)
        # 添加到时间布局
        time_layout.addWidget(start_day_label)
        time_layout.addWidget(start_date)
        time_layout.addWidget(end_day_label)
        time_layout.addWidget(end_date)
        # 添加到分类规则布局
        classification_layout.addWidget(time_checkbox)
        classification_layout.addLayout(time_layout)

        # 按文件大小分类
        size_checkbox = QCheckBox("按文件大小分类")
        size_layout = QHBoxLayout()
        size_combobox = QComboBox()
        size_combobox.addItem("大于>")
        size_combobox.addItem("小于<")
        size_combobox.addItem("介于两者之间")
        self.size_edit1 = QLineEdit()
        self.size_edit1.setPlaceholderText("10")
        self.size_edit2 = QLineEdit()
        self.size_edit2.setPlaceholderText("100")
        big_label = QLabel("大于")
        small_label = QLabel("小于")
        size_label = QLabel("MB")
        both1_label = QLabel("和")
        both2_label = QLabel("MB之间")
        # 添加到布局
        size_layout.addWidget(size_checkbox)
        size_layout.addWidget(size_combobox)
        size_layout.addWidget(big_label)
        size_layout.addWidget(self.size_edit1)
        size_layout.addWidget(small_label)
        size_layout.addWidget(both1_label)
        size_layout.addWidget(self.size_edit2)
        size_layout.addWidget(size_label)
        size_layout.addWidget(both2_label)

        classification_layout.addLayout(size_layout)

        classification_group.setLayout(classification_layout)
        classification_tab.setLayout(classification_tab_layout)
        self.advanced_settings_tab.addTab(classification_tab, "分类规则")
        # 筛选规则界面
        filter_tab = QWidget()
        self.advanced_settings_tab.addTab(filter_tab, "筛选规则")

        w_layout.addWidget(self.advanced_settings_tab)






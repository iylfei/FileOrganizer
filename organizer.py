# organizer.py

import os
import re

from PySide6.QtCore import QObject, Signal


class FileOrganizer(QObject):
    # 状态更新信号
    status_updated = Signal(str)
    # 进度信号
    progress_updated = Signal(int)
    # 结束信号
    finished = Signal()

    def __init__(self, filepath, custom_list):
        super().__init__()
        self.filepath = filepath
        self.custom_list = custom_list if custom_list is not None else []
        self.isRunning = True

    def stop(self):
        self.isRunning = False

    def organize(self):
        if not os.path.isdir(self.filepath):
            self.status_updated.emit(f"错误：文件夹 '{self.filepath}' 不存在！")
            self.finished.emit()
            return

        self.status_updated.emit(f'准备整理位于 {self.filepath} 的文件...')

        # 定义默认分类
        default_dirs = {
            '图片': os.path.join(self.filepath, '图片'),
            '视频': os.path.join(self.filepath, '视频'),
            '文档': os.path.join(self.filepath, '文档'),
            '其他': os.path.join(self.filepath, '其他')
        }
        # 创建所有默认文件夹
        for dir_path in default_dirs.values():
            os.makedirs(dir_path, exist_ok=True)

        # 创建所有自定义文件夹
        custom_dirs = {}
        for item in self.custom_list:
            folder_name = ''
            if item.startswith('.'):
                folder_name = f'拓展名为{item}的文件'
            else:
                folder_name = f'文件名中存在{item}的文件'
            dir_path = os.path.join(self.filepath, folder_name)
            os.makedirs(dir_path, exist_ok=True)
            custom_dirs[item] = dir_path

        # --- 开始整理 ---
        try:
            filelist = [f for f in os.listdir(self.filepath) if os.path.isfile(os.path.join(self.filepath, f))]
            total_files = len(filelist)
            if total_files == 0:
                self.status_updated.emit("文件夹为空，无需整理。")
                self.finished.emit()
                return

            processed_files = 0
            for f in filelist:
                if not self.isRunning:
                    self.status_updated.emit("任务已被用户取消。")
                    self.finished.emit()
                    return
                old_path = os.path.join(self.filepath, f)

                filename, ext = os.path.splitext(f)
                ext_lower = ext.lower()

                moved = False

                # 处理自定义列表
                for item in self.custom_list:
                    if item.startswith('.') and ext_lower == item.lower():
                        dest_folder = custom_dirs[item]
                        new_path = os.path.join(dest_folder, f)
                        self.status_updated.emit(f"正在移动 [自定义-后缀] {f}")
                        os.rename(old_path, new_path)
                        moved = True
                        break
                    elif not item.startswith('.'):
                        if re.search(re.escape(item), filename, re.IGNORECASE):
                            dest_folder = custom_dirs[item]
                            new_path = os.path.join(dest_folder, f)
                            self.status_updated.emit(f"正在移动 [自定义-关键词] {f}")
                            os.rename(old_path, new_path)
                            moved = True
                            break

                if not moved:
                    if ext_lower in ['.jpg', '.png', '.gif', '.jpeg', '.bmp', '.svg']:
                        new_path = os.path.join(default_dirs['图片'], f)
                        self.status_updated.emit(f"正在移动 [图片] {f} ...")
                        os.rename(old_path, new_path)
                    elif ext_lower in ['.mp4', '.mov', '.avi', '.mkv', '.wmv']:
                        new_path = os.path.join(default_dirs['视频'], f)
                        self.status_updated.emit(f"正在移动 [视频] {f} ...")
                        os.rename(old_path, new_path)
                    elif ext_lower in ['.txt', '.doc', '.docx', '.rtf', '.xlsx', '.xls', '.ppt', '.pptx', '.pdf']:
                        new_path = os.path.join(default_dirs['文档'], f)
                        self.status_updated.emit(f"正在移动 [文档] {f}")
                        os.rename(old_path, new_path)
                    else:
                        new_path = os.path.join(default_dirs['其他'], f)
                        self.status_updated.emit(f"正在移动 [其他] {f}")
                        os.rename(old_path, new_path)

                processed_files += 1
                progress = int((processed_files / total_files) * 100)
                self.progress_updated.emit(progress)

            self.status_updated.emit('文件整理完毕！')
            self.finished.emit()

        except Exception as e:
            self.status_updated.emit(f"整理过程中发生错误: {e}")
            self.finished.emit()
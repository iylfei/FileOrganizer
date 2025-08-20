# organizer.py

import os
import json

from PySide6.QtCore import QObject, Signal


class FileOrganizer(QObject):
    # 状态更新信号
    status_updated = Signal(str)
    # 进度信号
    progress_updated = Signal(int)
    # 结束信号
    finished = Signal()

    def __init__(self, filepath, rules_json_filepath):
        super().__init__()
        self.filepath = filepath
        self.rules_json_filepath = rules_json_filepath
        self.rules = {}
        self.isRunning = True

    def stop(self):
        self.isRunning = False

    def loadRules(self):
        # 解析json文件
        if not os.path.isfile(self.rules_json_filepath):
            self.rules = {
                "classification_rule": {
                    "priority": ["default"],
                    "default": {"enabled": True, "model": {
                        "images": "图片", "videos": "视频", "decuments": "文档", "others": "其他"
                    }}
                },
                "filter_rule": {}
            }
            return True
        else:
            try:
                with open(self.rules_json_filepath, "r", encoding="utf-8") as f:
                    self.rules = json.load(f)
                    return True
            except (json.JSONDecodeError, KeyError) as e:
                self.status_updated.emit(f"错误：规则文件 '{os.path.basename(self.rules_path)}' 格式无效: {e}")
                return False
            except Exception as e:
                self.status_updated.emit(f"错误：无法读取规则文件: {e}")
                return False

    def orgnize(self):
        if not self.loadRules():
            self.finished.emit()
            return
        else:
        # 顺序：读取到文件->筛选规则：时间->大小->自定义规则->大小->时间->预设规则
            if not os.path.isdir(self.filepath):
                self.status_updated.emit(f"错误：文件夹 '{self.filepath}' 不存在！")
                self.finished.emit()
                return
            else:
                filenames = os.listdir(self.filepath)
                for filename in filenames:
                    self.status_updated.emit(f"正在整理 '{filename}")
                    # 按顺序依次调用整理函数

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

    def organize_by_custom(self, filename):
        classification_rule = self.rules["classification_rule"]
        custom = classification_rule.get("custom", {})
        if not custom.get("enabled", True):
            return False
        try:
            keywords = custom.get("keyword", [])
            name, ext = os.path.splitext(filename)
            for keyword in keywords:
                if keyword.startswith("."):
                    if keyword == ext:
                        return True
                elif keyword in name:
                    return True
            return False
        except Exception as e:
            self.status_updated.emit(f"按自定义规则分类 {filename} 时出错: {e}")
            return False
    """
    json格式
        {
            "classification_rule": {
                "priority": ["custom", "size", "time", "default"],
                "custom": {"enabled": True, "keyword": [xx,yy]}
                "size": {"enabled": True, "model": "大于", "value1" : 100, "value2" : 200},
                "time": {"enabled": True, "start_time": 1000000， "end_time": 2000000}, 
                "default": {"enabled": True,
                    "images": True, "videos": True, "decuments": True, "others": True
                }}
            },
            "filter_rule": {同上}
        }
    """
    def organize_by_size(self, filename):
        classification_rule = self.rules["classification_rule"]
        size = classification_rule.get("size", {})
        if not size.get("enabled", True):
            return False
        try:
            old_path = os.path.join(self.filepath, filename)
            file_size = os.getsize(old_path) / 1024
            model = size.get("model")
            value1 = size.get("value1")
            value2 = size.get("value2")
            if model == "大于":
                if file_size > value1:
                    return True
            elif model == "小于":
                if file_size < value2:
                    return True
            elif model == "介于":
                if value1 < file_size < value2:
                    return True
            return False
        except (TypeError, ValueError) as e:
            self.status_updated.emit(f"按大小分类时出错: 规则中的值无效 - {e}")
            return False

    def organize_by_time(self, filename):
        classification_rule = self.rules["classification_rule"]
        time = classification_rule.get("time", {})
        if not time.get("enabled", True):
            return False
        try:
            old_path = os.path.join(self.filepath, filename)
            file_time = os.path.getmtime(old_path)
            start_time = time.get("start_time")
            end_time = time.get("end_time")
            if start_time < file_time < end_time:
                return True
            return False
        except Exception as e:
            self.status_updated.emit(f"按时间分类 {filename} 时出错: {e}")
            return False

    def organize_by_default(self, filename):
        classification_rule = self.rules["classification_rule"]
        default = classification_rule.get("default", {})
        if not default.get("enabled", True):
            return False
        try:
            old_path = os.path.join(self.filepath, filename)
            name, ext = os.path.splitext(filename)
            if default.get("images", True):
                if ext in ['.jpg', '.png', '.gif', '.jpeg', '.bmp', '.svg']:
                    new_path = os.path.join(self.filepath, '图片')
                    self.status_updated.emit(f"正在移动 [图片] {filename} ...")
                    os.rename(old_path, new_path)
                elif ext in ['.mp4', '.mov', '.avi', '.mkv', '.wmv']:
                    new_path = os.path.join(self.filepath, '视频')
                    self.status_updated.emit(f"正在移动 [视频] {filename} ...")
                    os.rename(old_path, new_path)
                elif ext in ['.txt', '.doc', '.docx', '.rtf', '.xlsx', '.xls', '.ppt', '.pptx', '.pdf']:
                    new_path = os.path.join(self.filepath, '文档')
                    self.status_updated.emit(f"正在移动 [文档] {filename}")
                    os.rename(old_path, new_path)
                else:
                    new_path = os.path.join(self.filepath, '其他')
                    self.status_updated.emit(f"正在移动 [其他] {filename}")
                    os.rename(old_path, new_path)
            return False
        except Exception as e:
            self.status_updated.emit(f"按预设分类 {filename} 时出错: {e}")
            return False
    # 通用创建文件夹函数
    def makefile_dir(self, filename):
        pass

    # 通用移动函数
    def move_file(self, filename, dest_folder_name, category_prefix=""):
        if not self.isRunning: return False
        try:
            old_path = os.path.join(self.filepath, filename)
            if not os.path.exists(old_path): return False

            dest_dir = os.path.join(self.filepath, dest_folder_name)
            os.makedirs(dest_dir, exist_ok=True)
            new_path = os.path.join(dest_dir, filename)

            status_msg = f"正在移动 [{category_prefix}] {filename}" if category_prefix else f"正在移动 {filename}"
            self.status_updated.emit(status_msg)

            os.rename(old_path, new_path)
            return True
        except Exception as e:
            self.status_updated.emit(f"移动文件 {filename} 时出错: {e}")
            return False
    # 筛选时间
    def filter_by_time(self,filename):
        filter_rule = self.rules.get("filter_rule", {})
        time_filter = filter_rule.get("time", {})
        if not time_filter.get("enabled", True):
            return False
        try:
            old_path = os.path.join(self.filepath, filename)
            file_time = os.path.getmtime(old_path)
            start_time = filter_rule.get("start_time")
            end_time = filter_rule.get("end_time")
            if not start_time or not end_time:
                return False
            if start_time <= file_time <= end_time:
                return True
            else:
                return False
        except Exception as e:
            self.status_updated.emit(f"按时间筛选 {filename} 时出错: {e}")
        return False

    # 筛选大小
    def filter_by_size(self, filename):
        filter_rule = self.rules.get("filter_rule", {})
        size_filter = filter_rule.get("size", {})
        if not size_filter.get("enabled", True):
            return False
        else:
            try:
                old_path = os.path.join(self.filepath, filename)
                file_size = os.path.getsize(old_path) / 1024
                model = size_filter.get("model")
                value1 = float(size_filter.get("value1"))
                value2 = float(size_filter.get("value2"))
                if model == "大于":
                    if file_size > value1:
                        return True
                elif model == "小于":
                    if file_size < value2:
                        return True
                elif model == "介于":
                    if value1 < file_size < value2:
                        return True
                return False
            except (TypeError, ValueError) as e:
                self.status_updated.emit(f"按大小筛选时出错: 规则中的值无效 - {e}")
                return False



    # def organize(self):
    #     if not os.path.isdir(self.filepath):
    #         self.status_updated.emit(f"错误：文件夹 '{self.filepath}' 不存在！")
    #         self.finished.emit()
    #         return
    #
    #     self.status_updated.emit(f'准备整理位于 {self.filepath} 的文件...')
    #
    #     # 定义默认分类
    #     default_dirs = {
    #         '图片': os.path.join(self.filepath, '图片'),
    #         '视频': os.path.join(self.filepath, '视频'),
    #         '文档': os.path.join(self.filepath, '文档'),
    #         '其他': os.path.join(self.filepath, '其他')
    #     }
    #     # 创建所有默认文件夹
    #     for dir_path in default_dirs.values():
    #         os.makedirs(dir_path, exist_ok=True)
    #
    #     # 创建所有自定义文件夹
    #     custom_dirs = {}
    #     for item in self.custom_list:
    #         folder_name = ''
    #         if item.startswith('.'):
    #             folder_name = f'拓展名为{item}的文件'
    #         else:
    #             folder_name = f'文件名中存在{item}的文件'
    #         dir_path = os.path.join(self.filepath, folder_name)
    #         os.makedirs(dir_path, exist_ok=True)
    #         custom_dirs[item] = dir_path
    #
    #     # --- 开始整理 ---
    #     try:
    #         filelist = [f for f in os.listdir(self.filepath) if os.path.isfile(os.path.join(self.filepath, f))]
    #         total_files = len(filelist)
    #         if total_files == 0:
    #             self.status_updated.emit("文件夹为空，无需整理。")
    #             self.finished.emit()
    #             return
    #
    #         processed_files = 0
    #         for f in filelist:
    #             if not self.isRunning:
    #                 self.status_updated.emit("任务已被用户取消。")
    #                 self.finished.emit()
    #                 return
    #             old_path = os.path.join(self.filepath, f)
    #
    #             filename, ext = os.path.splitext(f)
    #             ext_lower = ext.lower()
    #
    #             moved = False
    #
    #             # 处理自定义列表
    #             for item in self.custom_list:
    #                 if item.startswith('.') and ext_lower == item.lower():
    #                     dest_folder = custom_dirs[item]
    #                     new_path = os.path.join(dest_folder, f)
    #                     self.status_updated.emit(f"正在移动 [自定义-后缀] {f}")
    #                     os.rename(old_path, new_path)
    #                     moved = True
    #                     break
    #                 elif not item.startswith('.'):
    #                     if re.search(re.escape(item), filename, re.IGNORECASE):
    #                         dest_folder = custom_dirs[item]
    #                         new_path = os.path.join(dest_folder, f)
    #                         self.status_updated.emit(f"正在移动 [自定义-关键词] {f}")
    #                         os.rename(old_path, new_path)
    #                         moved = True
    #                         break
    #
    #             if not moved:
    #                 if ext_lower in ['.jpg', '.png', '.gif', '.jpeg', '.bmp', '.svg']:
    #                     new_path = os.path.join(default_dirs['图片'], f)
    #                     self.status_updated.emit(f"正在移动 [图片] {f} ...")
    #                     os.rename(old_path, new_path)
    #                 elif ext_lower in ['.mp4', '.mov', '.avi', '.mkv', '.wmv']:
    #                     new_path = os.path.join(default_dirs['视频'], f)
    #                     self.status_updated.emit(f"正在移动 [视频] {f} ...")
    #                     os.rename(old_path, new_path)
    #                 elif ext_lower in ['.txt', '.doc', '.docx', '.rtf', '.xlsx', '.xls', '.ppt', '.pptx', '.pdf']:
    #                     new_path = os.path.join(default_dirs['文档'], f)
    #                     self.status_updated.emit(f"正在移动 [文档] {f}")
    #                     os.rename(old_path, new_path)
    #                 else:
    #                     new_path = os.path.join(default_dirs['其他'], f)
    #                     self.status_updated.emit(f"正在移动 [其他] {f}")
    #                     os.rename(old_path, new_path)
    #
    #             processed_files += 1
    #             progress = int((processed_files / total_files) * 100)
    #             self.progress_updated.emit(progress)
    #
    #         self.status_updated.emit('文件整理完毕！')
    #         self.finished.emit()
    #
    #     except Exception as e:
    #         self.status_updated.emit(f"整理过程中发生错误: {e}")
    #         self.finished.emit()
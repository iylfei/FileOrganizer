# organizer.py

import os
import json
from os import makedirs

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
    def loadRules(self):
        # 解析json文件
        if not os.path.isfile(self.rules_json_filepath):
            self.rules = {
                "classification_rule": {
                    "priority": ["default"],
                    "default": {"enabled": True, "model": {
                        "images": "图片", "videos": "视频", "documents": "文档", "others": "其他"
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

    def organize(self):
        if not self.loadRules():
            self.status_updated.emit("整理规则读取失败！")
            self.finished.emit()
            return

        if not os.path.isdir(self.filepath):
            self.status_updated.emit(f"错误：文件夹 '{self.filepath}' 不存在！")
            self.finished.emit()
            return

        self.status_updated.emit(f'准备整理位于 {self.filepath} 的文件...')

        if not self.makefile_dir():
            self.finished.emit()
            return

        try:
            # 获取文件夹中的全部文件
            all_items = os.listdir(self.filepath)
            filelist = [f for f in all_items if os.path.isfile(os.path.join(self.filepath, f))]

            total_files = len(filelist)
            if total_files == 0:
                self.status_updated.emit("文件夹为空")
                self.progress_updated.emit(100)
                self.finished.emit()
                return

            classification_rules = self.rules.get("classification_rule", {})
            filter_rules = self.rules.get("filter_rule", {})
            priority = classification_rules.get("priority", [])

            processed_files = 0
            # 开始整理
            for filename in filelist:
                if not self.isRunning:
                    self.status_updated.emit("整理停止")
                    self.finished.emit()
                    return

                self.status_updated.emit(f"正在整理 '{filename}' ")

                # 先对文件进行筛选
                passes_filters = True
                # 时间筛选
                if filter_rules.get("time", {}).get("enabled"):
                    if not self.filter_by_time(filename):
                        passes_filters = False
                # 大小筛选
                if passes_filters and filter_rules.get("size", {}).get("enabled"):
                    if not self.filter_by_size(filename):
                        passes_filters = False

                if not passes_filters:
                    # 判断下一个文件
                    processed_files += 1
                    continue

                # 对经过筛选的文件进行分类
                moved = False
                for rule_type in priority:
                    rule_details = classification_rules.get(rule_type, {})
                    if not rule_details.get("enabled"):
                        continue  # 跳过未启用的规则

                    # 检查文件是否符合当前规则
                    does_match = False
                    dest_folder_name = ""  # 目标文件夹名字

                    if rule_type == "custom" and self.organize_by_custom(filename):
                        does_match = True
                        keywords = rule_details.get("keyword", [])
                        name, ext = os.path.splitext(filename)
                        for item in keywords:
                            if (item.startswith('.') and item == ext) or (not item.startswith('.') and item in name):
                                dest_folder_name = f'拓展名为{item}的文件' if item.startswith(
                                    '.') else f'文件名中存在{item}的文件'
                                break

                    elif rule_type == "size" and self.organize_by_size(filename):
                        does_match = True
                        dest_folder_name = '按大小分类的文件'

                    elif rule_type == "time" and self.organize_by_time(filename):
                        does_match = True
                        dest_folder_name = '按时间分类的文件'

                    elif rule_type == "default" and self.organize_by_default(filename):
                        # default规则的文件移动在organize_by_default中已经完成
                        moved = True  # 标记一下，表示它已经被处理了

                    if does_match and dest_folder_name:
                        if self.move_file(filename, dest_folder_name, category_prefix=rule_type):
                            moved = True

                    if moved:
                        break

                processed_files += 1
                progress = int((processed_files / total_files) * 100)
                self.progress_updated.emit(progress)

            self.status_updated.emit('全部文件整理完成！')
            self.finished.emit()

        except Exception as e:
            self.status_updated.emit(f"整理过程发生错误: {e}")
            self.finished.emit()



    # 创建文件夹函数
    def makefile_dir(self):
        # 根据规则创建所需文件夹
        if not os.path.isdir(self.filepath):
            self.status_updated.emit(f"错误: 目标文件夹 {self.filepath} 不存在哦。")
            return False

        try:
            classification_rules = self.rules.get("classification_rule", {})
            if not classification_rules:
                return True

            # 获取优先级列表
            priority = classification_rules.get("priority", [])

            # 默认规则映射
            default_name_map = {
                "images": "图片",
                "videos": "视频",
                "documents": "文档",
                "others": "其他"
            }

            # 按照优先级创建文件夹
            for rule_type in priority:
                rule_details = classification_rules.get(rule_type, {})

                if rule_details.get("enabled"):
                    if rule_type == "default":
                        # 检查每一个分类（images, videos...）是不是True
                        for key, folder_name in default_name_map.items():
                            if rule_details.get(key):
                                dir_path = os.path.join(self.filepath, folder_name)
                                os.makedirs(dir_path, exist_ok=True)

                    elif rule_type == "custom":
                        keywords = rule_details.get("keyword", [])
                        for item in keywords:
                            folder_name = ''
                            if item.startswith('.'):
                                folder_name = f'拓展名为{item}的文件'
                            else:
                                folder_name = f'文件名中存在{item}的文件'

                            if folder_name:
                                dir_path = os.path.join(self.filepath, folder_name)
                                os.makedirs(dir_path, exist_ok=True)

                    elif rule_type == "size":
                        dir_path = os.path.join(self.filepath, '按大小分类的文件')
                        os.makedirs(dir_path, exist_ok=True)

                    elif rule_type == "time":
                        dir_path = os.path.join(self.filepath, '按时间分类的文件')
                        os.makedirs(dir_path, exist_ok=True)

            return True

        except Exception as e:
            self.status_updated.emit(f"创建文件夹时出错: {e}")
            return False

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


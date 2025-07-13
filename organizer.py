import os
import re

def organize(filepath: str, custom_list: list) -> None:
    if not os.path.isdir(filepath):
        print(f"错误：文件夹 '{filepath}' 不存在或不是一个文件夹！程序退出。")
        return

    print(f'即将整理位于 {filepath} 的文件...')

    # 定义默认分类
    default_dirs = {
        '图片': os.path.join(filepath, '图片'),
        '视频': os.path.join(filepath, '视频'),
        '文档': os.path.join(filepath, '文档'),
        '其他': os.path.join(filepath, '其他')
    }
    # 创建所有默认文件夹
    for dir_path in default_dirs.values():
        os.makedirs(dir_path, exist_ok=True)

    # 创建所有自定义文件夹
    custom_dirs = {}
    for item in custom_list:
        folder_name = ''
        if item.startswith('.'):
            folder_name = f'拓展名为{item}的文件'
        else:
            folder_name = f'文件名中存在{item}的文件'
        dir_path = os.path.join(filepath, folder_name)
        os.makedirs(dir_path, exist_ok=True)
        custom_dirs[item] = dir_path

    # --- 开始整理 ---
    try:
        filelist = os.listdir(filepath)
        for f in filelist:
            old_path = os.path.join(filepath, f)

            # 如果不是文件，或者就是要创建的那些目录，就直接跳过
            if not os.path.isfile(old_path) or old_path in default_dirs.values() or old_path in custom_dirs.values():
                continue

            filename, ext = os.path.splitext(f)
            ext_lower = ext.lower()

            moved = False # 设置标志判断文件是否已经被移动过

            # 处理自定义列表
            for item in custom_list:
                # 按拓展名匹配
                if item.startswith('.') and ext_lower == item.lower():
                    dest_folder = custom_dirs[item]
                    new_path = os.path.join(dest_folder, f)
                    print(f"正在移动 [自定义-后缀] {f}")
                    os.rename(old_path, new_path)
                    moved = True
                    break

                # 按文件名关键词匹配
                elif not item.startswith('.'):
                    if re.search(re.escape(item), filename, re.IGNORECASE): # re.escape避免特殊字符问题
                        dest_folder = custom_dirs[item]
                        new_path = os.path.join(dest_folder, f)
                        print(f"正在移动 [自定义-关键词] {f}")
                        os.rename(old_path, new_path)
                        moved = True
                        break

            if not moved:
                if ext_lower in ['.jpg', '.png', '.gif', '.jpeg', '.bmp', '.svg']:
                    new_path = os.path.join(default_dirs['图片'], f)
                    print(f"正在移动 [图片] {f} ...")
                    os.rename(old_path, new_path)
                elif ext_lower in ['.mp4', '.mov', '.avi', '.mkv', '.wmv']:
                    new_path = os.path.join(default_dirs['视频'], f)
                    print(f"正在移动 [视频] {f} ...")
                    os.rename(old_path, new_path)
                elif ext_lower in ['.txt', '.doc', '.docx', '.rtf', '.xlsx', '.xls', '.ppt', '.pptx', '.pdf']:
                    new_path = os.path.join(default_dirs['文档'], f)
                    print(f"正在移动 [文档] {f}")
                    os.rename(old_path, new_path)
                else:
                    new_path = os.path.join(default_dirs['其他'], f)
                    print(f"正在移动 [其他] {f}")
                    os.rename(old_path, new_path)

        print('文件整理完毕！')

    except Exception as e:
        print(f"整理过程中发生错误: {e}")
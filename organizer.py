import os

print('输入要整理的文件路径:')
filepath = input()

# 检查路径是否存在
if not os.path.isdir(filepath):
    print(f"错误：文件夹 '{filepath}' 不存在或不是一个文件夹，程序退出。")
else:
    print(f'即将整理位于 {filepath} 的文件...')
    # 在确认存在的路径里，创建目标文件夹
    dir_images = os.path.join(filepath, '图片')
    dir_videos = os.path.join(filepath, '视频')
    dir_texts = os.path.join(filepath, '文档')
    dir_others = os.path.join(filepath, '其他')

    os.makedirs(dir_images, exist_ok=True)
    os.makedirs(dir_videos, exist_ok=True)
    os.makedirs(dir_texts, exist_ok=True)
    os.makedirs(dir_others, exist_ok=True)

    # --- 开始整理 ---
    try:
        filelist = os.listdir(filepath)
        for f in filelist:
            old_path = os.path.join(filepath, f)

            if os.path.isfile(old_path):
                filename, ext = os.path.splitext(f)
                ext_lower = ext.lower()

                if ext_lower in ['.jpg', '.png', '.gif', '.jpeg']:
                    new_path = os.path.join(dir_images, f)
                    print(f"正在移动 [图片] {f}")
                    os.rename(old_path, new_path)

                elif ext_lower in ['.mp4', '.mov', '.avi', '.mkv']:
                    new_path = os.path.join(dir_videos, f)
                    print(f"正在移动 [视频] {f}")
                    os.rename(old_path, new_path)

                elif ext_lower in ['.txt', '.doc', '.docx', '.rtf', '.xlsx', '.xls', '.ppt', '.pptx', '.pdf']:
                    new_path = os.path.join(dir_texts, f)
                    print(f"正在移动 [文档] {f}")
                    os.rename(old_path, new_path)

                else:
                    new_path = os.path.join(dir_others, f)
                    print(f"正在移动 [其他] {f}")
                    os.rename(old_path, new_path)

        print('文件整理完毕')

    except Exception as e:
        print(f"整理过程中发生错误: {e}")
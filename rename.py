import os
import sys


def rename_ets_to_txt(folder_path):
    """
    将指定文件夹中所有 .ets 文件重命名为 .txt
    """
    if not os.path.exists(folder_path):
        print(f"错误：文件夹 '{folder_path}' 不存在")
        return

    if not os.path.isdir(folder_path):
        print(f"错误：'{folder_path}' 不是文件夹")
        return

    renamed_count = 0
    skipped_count = 0

    # 遍历文件夹中的所有文件
    for filename in os.listdir(folder_path):
        old_path = os.path.join(folder_path, filename)

        # 跳过子文件夹
        if os.path.isdir(old_path):
            continue

        # 检查是否是 .ets 文件（不区分大小写）
        if filename.lower().endswith('.ets'):
            # 生成新文件名
            new_filename = filename[:-4] + '.txt'  # 去掉 .ets 加上 .txt
            new_path = os.path.join(folder_path, new_filename)

            # 检查目标文件是否已存在
            if os.path.exists(new_path):
                print(f"跳过：'{filename}' -> 目标文件 '{new_filename}' 已存在")
                skipped_count += 1
                continue

            try:
                os.rename(old_path, new_path)
                print(f"重命名：'{filename}' -> '{new_filename}'")
                renamed_count += 1
            except Exception as e:
                print(f"错误：无法重命名 '{filename}' - {e}")
                skipped_count += 1

    print(f"\n完成！成功重命名 {renamed_count} 个文件，跳过 {skipped_count} 个文件")


if __name__ == "__main__":
    # 获取文件夹路径
    if len(sys.argv) > 1:
        folder_path = sys.argv[1]
    else:
        # 如果没有提供参数，使用当前目录
        folder_path = '/Users/langqin/Desktop'

    rename_ets_to_txt(folder_path)

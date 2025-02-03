import os
import shutil
import re

def create_folder_structure(source_folder, destination_folder):
    base_folder_name = os.path.basename(source_folder)

    for root, dirs, files in os.walk(source_folder):
        for dir in dirs:
            if "ResultsS" in dir:
                match = re.search(r'S(\d+)_?ResultsS', dir)
                s_level = f"S{match.group(1)}" if match else "S1"

                results_path = os.path.join(root, dir)
                for sub_dir in os.listdir(results_path):
                    if "_FunImg" in sub_dir:
                        name = sub_dir.split("_FunImg")[0]  # 修正索引使用

                        # 创建新的文件夹结构
                        new_folder = os.path.join(destination_folder, name, base_folder_name, s_level)
                        os.makedirs(new_folder, exist_ok=True)

                        # 复制以"sz"开头的文件
                        source_path = os.path.join(results_path, sub_dir)
                        for file in os.listdir(source_path):
                            if file.startswith("sz"):
                                try:
                                    shutil.copy2(os.path.join(source_path, file), new_folder)
                                except IOError as e:
                                    print(f"Unable to copy file {file}. Reason: {e}")

# 使用示例
source_folder = "/Users/sunny/Desktop/sham"
destination_folder = "/Users/sunny/Desktop/test"
create_folder_structure(source_folder, destination_folder)
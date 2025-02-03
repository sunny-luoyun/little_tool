import os
import shutil
import re

# 工作目录
source_folder = "/Users/sunny/Desktop/sham"
# 输出目录
destination_folder = "/Users/sunny/Desktop/test"

def create_folder_structure(source_folder, destination_folder):
    base_folder_name = os.path.basename(source_folder)
    print(f"开始处理文件夹: {base_folder_name}")

    total_dirs = sum([len(dirs) for _, dirs, _ in os.walk(source_folder)])
    processed_dirs = 0

    for root, dirs, files in os.walk(source_folder):
        for dir in dirs:
            if "ResultsS" in dir:
                processed_dirs += 1
                print(f"正在处理: {dir} ({processed_dirs}/{total_dirs})")

                match = re.search(r'S(\d+)_?ResultsS', dir)
                s_level = f"S{match.group(1)}" if match else "S1"

                results_path = os.path.join(root, dir)
                for sub_dir in os.listdir(results_path):
                    if "_FunImg" in sub_dir:
                        name = sub_dir.split("_FunImg")[0]
                        print(f"  处理子文件夹: {sub_dir}")

                        source_path = os.path.join(results_path, sub_dir)

                        if "FC_FunImg" in sub_dir:
                            # 处理FC_FunImg文件夹
                            fc_files = [f for f in os.listdir(source_path) if f.startswith("sz")]
                            for i, file in enumerate(fc_files, 1):
                                print(f"    复制FC文件: {file} ({i}/{len(fc_files)})")
                                match = re.search(r'szROI(\d+)FC', file)
                                if match:
                                    fc_num = match.group(1)
                                    fc_folder = f"FC{fc_num}"
                                    new_folder = os.path.join(destination_folder, fc_folder, base_folder_name, s_level)
                                    os.makedirs(new_folder, exist_ok=True)
                                    try:
                                        shutil.copy2(os.path.join(source_path, file), new_folder)
                                    except IOError as e:
                                        print(f"    无法复制文件 {file}. 原因: {e}")
                        else:

                            new_folder = os.path.join(destination_folder, name, base_folder_name, s_level)
                            os.makedirs(new_folder, exist_ok=True)
                            other_files = [f for f in os.listdir(source_path) if f.startswith("sz")]
                            for i, file in enumerate(other_files, 1):
                                print(f"    复制文件: {file} ({i}/{len(other_files)})")
                                try:
                                    shutil.copy2(os.path.join(source_path, file), new_folder)
                                except IOError as e:
                                    print(f"    无法复制文件 {file}. 原因: {e}")

    print(f"处理完成: 共处理了 {processed_dirs} 个目录")

create_folder_structure(source_folder, destination_folder)

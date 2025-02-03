import os
import shutil


def move_specific_named_folders(src_folder, dst_folder, folder_name_pattern):
    if not os.path.exists(dst_folder):
        os.makedirs(dst_folder)

    for item in os.listdir(src_folder):
        item_path = os.path.join(src_folder, item)

        if os.path.isdir(item_path) and folder_name_pattern in item:
            dst_path = os.path.join(dst_folder, item)

            shutil.move(item_path, dst_path)
            print(f"已移动: {item_path} 到 {dst_path}")


src_folder = 'H:\\1TANGDONGSHENG\\TI\\pretreatment\\TIJ\\Sub001'

dst_folder = 'H:\\1TANGDONGSHENG\\TI\\new_pretreatment'

folder_name_pattern = 'FunImg'

move_specific_named_folders(src_folder, dst_folder, folder_name_pattern)

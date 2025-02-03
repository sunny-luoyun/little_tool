import os
import shutil


def copy_specific_named_files(src_folder, dst_folder, file_name_pattern):
    if not os.path.exists(dst_folder):
        os.makedirs(dst_folder)

    for filename in os.listdir(src_folder):

        if file_name_pattern in filename:

            src_file = os.path.join(src_folder, filename)
            dst_file = os.path.join(dst_folder, filename)

            shutil.copy(src_file, dst_file)
            print(f"已复制: {src_file} 到 {dst_file}")
# 移出文件夹
src_folder = 'H:\\1TANGDONGSHENG\\TI\\pretreatment\\TIJ\\Sub001'
# 移入文件夹
dst_folder = 'H:\\1TANGDONGSHENG\\TI\\new_pretreatment'
# 移动文件所属名
file_name_pattern = 'FunImg'
copy_specific_named_files(src_folder, dst_folder, file_name_pattern)

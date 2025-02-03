import os
import shutil


def copy(src_folder, dst_folder, folder_name):
    if not os.path.exists(dst_folder):
        os.makedirs(dst_folder)

    for item in os.listdir(src_folder):
        item_path = os.path.join(src_folder, item)

        if os.path.isdir(item_path) and item == folder_name:
            dst_path = os.path.join(dst_folder, item)

            if os.path.exists(dst_path):
                shutil.rmtree(dst_path)

            shutil.copytree(item_path, dst_path)
            print(f"已复制: {item_path} 到 {dst_path}")

folder_name = ['FunImg','S2_FunImg','T1Img']
sub_name = ['01', '02','03','04','06','07','08','09','12','13','14','15','17','18','20','21','22','24','25','26','27','28','29','30','31']
for a in sub_name:
    # 移出文件夹
    src_folder = f'H:\\1TANGDONGSHENG\\TI\\pretreatment\\TIJ\\Sub0{a}'
    # 移入文件夹
    dst_folder = f'H:\\1TANGDONGSHENG\\TI\\new_pretreatment\\Sub0{a}'
    for b in folder_name:
        # 移动文件所属名
        file_name_pattern = b
        copy(src_folder, dst_folder, file_name_pattern)
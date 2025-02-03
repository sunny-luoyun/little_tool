import os
import shutil


def copy_and_rename_file(src_folder, src_filename, dst_folder, dst_filename):
    src_path = os.path.join(src_folder, src_filename)
    dst_path = os.path.join(dst_folder, dst_filename)

    if not os.path.isfile(src_path):
        print(f"文件 {src_path} 不存在")
        return

    os.makedirs(dst_folder, exist_ok=True)

    shutil.copy2(src_path, dst_path)
    print(f"文件已从 {src_path} 复制到 {dst_path}")

name = ['01', '02','03','04','06','07','08','09','12','13','14','15','17','18','20','21','22','24','25','27']
for i in name:
    # 移出文件夹名字
    src_folder = "H:\\1TANGDONGSHENG\\data\\TIJ\\Result\\FC2\\post"
    # 移出文件名字
    src_filename = f"zROI2FCMap_Sub0{i}.nii"
    # 移入文件夹名字
    dst_folder = f"H:\\1TANGDONGSHENG\\data\\TIJ\\Result\\FC2_R\\Sub0{i}"
    # 修改名字
    dst_filename = "3.nii"

    copy_and_rename_file(src_folder, src_filename, dst_folder, dst_filename)

import os


def delete_file(folder_path, file_name):

    file_path = os.path.join(folder_path, file_name)

    if os.path.exists(file_path):

        os.remove(file_path)
        print(f"文件 {file_name} 已被删除。")
    else:
        print(f"文件 {file_name} 不存在。")

file = ['01','02','03','04','06','07','08','09','12','13','14','15','17','18','20','21','22','24','25','26','27','28','29','30']
for i in file:
    folder_path = f'H:\\1TANGDONGSHENG\\data\\TIJ\\Result\\31and\\{i}\\mid'
    file_name = f'zROI2FCMap_Sub0{i}.nii'
    delete_file(folder_path, file_name)
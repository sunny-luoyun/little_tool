import os
import shutil

def copy_files(source_folder, destination_folder):

    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    files = [f for f in os.listdir(source_folder) if os.path.isfile(os.path.join(source_folder, f))]

    if not files:
        print("空文件夹")
        return


    for file in files:
        source_path = os.path.join(source_folder, file)
        destination_path = os.path.join(destination_folder, file)
        shutil.copy2(source_path, destination_path)
        print(f"文件 '{file}' 已被复制到 {destination_folder}")

# out_path_template = input('输入移出文件夹路径（{name}代替变更文件夹）')
# in_path_template = input('输入移入文件夹路径（{name}代替变更文件夹）')

# 移出文件夹
out_path_template = 'H:\1TANGDONGSHENG\TI\pretreatment\TIJ\Sub001'
# 移入文件夹
in_path_template = 'H:\\1TANGDONGSHENG\\data\\TIJ\\pre\\FunImgARCW\\{name}'
# 文件编号
folders = ['Sub001', 'Sub002', 'Sub003', 'Sub004', 'Sub006', 'Sub007', 'Sub008', 'Sub009', 'Sub012', 'Sub013', 'Sub014', 'Sub015', 'Sub017', 'Sub018', 'Sub020', 'Sub021', 'Sub022', 'Sub024', 'Sub025', 'Sub026', 'Sub027', 'Sub028', 'Sub029', 'Sub030', 'Sub031']
while True:
    h = input('添加name，输入0停止添加')
    if h == '0':
        break
    folders.append(h)

for name in folders:
    source_folder = out_path_template.replace('{name}', name)
    destination_folder = in_path_template.replace('{name}', name)

    copy_files(source_folder, destination_folder)


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

out_path_template = input('输入移出文件夹路径（{name}代替变更文件夹）')
in_path_template = input('输入移入文件夹路径（{name}代替变更文件夹）')

folders = []
while True:
    h = input('添加name，输入0停止添加')
    if h == '0':
        break
    folders.append(h)

for name in folders:
    source_folder = out_path_template.replace('{name}', name)
    destination_folder = in_path_template.replace('{name}', name)

    copy_files(source_folder, destination_folder)


"""
处理行为运动学习的数据，按钮1234象限，8个list，结果输出为整理后的数据（正确值，反应时，list）以及归纳每个list的反应时和正确率
使用方法：在终端运行脚本文件 python sort_behavior.py 将结果文件txt拖入后回车即可得到结果文件。
"""

import os
import csv
from collections import defaultdict

def process_file(file_path):
    # 获取输入文件所在的目录
    input_dir = os.path.dirname(file_path)
    # 使用 os.path.splitext 分离文件名和扩展名
    file_name_with_extension = os.path.basename(file_path)  # 得到 'ex-38-01.txt'
    file_name, _ = os.path.splitext(file_name_with_extension)

    with open(file_path, 'r', encoding='utf-16') as file:
        lines = file.readlines()

    # 解析Header部分
    header = {}
    log_frames = []

    is_header = True
    for line in lines:
        line = line.strip()
        if line.startswith('*** Header End ***'):
            is_header = False
            continue
        if is_header:
            if ':' in line:
                key, value = line.split(':', 1)
                header[key.strip()] = value.strip()
        else:
            log_frames.append(line)

    # 解析LogFrame部分
    log_data = []

    current_frame = {}
    for line in log_frames:
        if line.startswith('*** LogFrame Start ***'):
            current_frame = {}
        elif line.startswith('*** LogFrame End ***'):
            log_data.append(current_frame)
        else:
            key, value = line.split(':', 1)
            current_frame[key.strip()] = value.strip()

    # 提取特定列
    extracted_data = []

    for frame in log_data:
        acc = frame.get('probe.ACC', 'N/A')
        rt = frame.get('probe.RT', 'N/A')
        run = frame.get('Running', 'N/A')

        extracted_data.append({
            'ACC': acc,
            'RT': rt,
            'Running': run
        })

    # 保存为CSV文件
    output_file = os.path.join(input_dir, f'{file_name}_data.csv')

    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['ACC', 'RT', 'Running']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for data in extracted_data:
            writer.writerow(data)

    print(f"数据已保存到 {output_file}")

    # 读取CSV文件
    input_file = output_file

    # 初始化数据结构
    data_by_list = defaultdict(lambda: {'total': 0, 'correct': 0, 'correct_rt_sum': 0})

    # 读取数据并进行分组统计
    with open(input_file, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            running = row['Running']
            acc = row['ACC']
            rt = row['RT']

            # 检查ACC是否为'N/A'，如果是则跳过
            if acc == 'N/A':
                continue

            # 将ACC和RT转换为适当的数据类型
            acc = int(acc)
            rt = float(rt) if rt != 'N/A' else None

            data_by_list[running]['total'] += 1
            if acc == 1:
                data_by_list[running]['correct'] += 1
                if rt is not None:
                    data_by_list[running]['correct_rt_sum'] += rt

    # 计算每个大组的正确率和反应时
    results = []
    for running, data in data_by_list.items():
        accuracy = data['correct'] / data['total'] if data['total'] > 0 else 0
        correct_rt_avg = data['correct_rt_sum'] / data['correct'] if data['correct'] > 0 else 0
        results.append({
            'List': running,
            'Accuracy': accuracy,
            'Correct RT': correct_rt_avg
        })

    # 保存结果到新的CSV文件
    output_file = os.path.join(input_dir, f'{file_name}_result.csv')

    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['List', 'Accuracy', 'Correct RT']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result)

    print(f"结果已保存到 {output_file}")

def main():
    print("请将文件拖入终端或输入文件路径：")
    file_path = input().strip()
    if os.path.isfile(file_path):
        process_file(file_path)
    else:
        print("输入的路径无效，请确保文件存在。")

if __name__ == "__main__":
    while True:
        main()
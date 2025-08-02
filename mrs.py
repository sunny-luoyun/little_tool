import re
import os
import pandas as pd
from datetime import datetime

def clean_path(path: str) -> str:
    """去除单引号、双引号和多余空格"""
    return re.sub(r'^["\']|["\']$', '', path).strip()

def extract_lcmodel_ps(ps_file_path, output_excel_path):
    with open(ps_file_path, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()

    # 初始化结果字典
    data = {}

    # 提取受检者信息
    subject_match = re.search(r'([A-Z0-9_]+_Sub\d+)', text)
    if subject_match:
        data['Subject'] = subject_match.group(1)

    date_match = re.search(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2})', text)
    if date_match:
        data['ScanDate'] = date_match.group(1)

    tr_te_match = re.search(r'TR/TE/NS=(\d+)/(\d+)/(\d+)', text)
    if tr_te_match:
        data['TR'] = int(tr_te_match.group(1))
        data['TE'] = int(tr_te_match.group(2))
        data['NS'] = int(tr_te_match.group(3))

    vol_match = re.search(r'([\d.E+-]+mL)', text)
    if vol_match:
        data['Volume'] = vol_match.group(1)

    age_sex_weight_match = re.search(r'([\d.]+Y),\s*(\d+)kg', text)
    if age_sex_weight_match:
        data['Age'] = age_sex_weight_match.group(1)
        data['Weight'] = f"{age_sex_weight_match.group(2)}kg"

    # 提取代谢物信息
    pattern = re.compile(r'\(\s*([0-9.E+-]+)\s+([0-9]+%)\s+([0-9.E+-]+)\s+([A-Za-z0-9+-]+)\)')
    matches = pattern.findall(text)

    for conc, sd, rel, name in matches:
        base_name = name.strip()
        data[f"{base_name}_Conc"] = float(conc)
        data[f"{base_name}_SD"] = sd
        data[f"{base_name}_Rel"] = float(rel)

    # 转换为 DataFrame（2 行 N 列）
    df = pd.DataFrame([data.values()], columns=data.keys())

    # 保存为 Excel 文件
    df.to_excel(output_excel_path, index=False, header=True)

    print(f"提取完成，已保存为：{output_excel_path}")

# 示例用法
if __name__ == "__main__":
    ps_file = input('输入你的ps文件路径')
    ps_file = clean_path(ps_file)
    excel_file = os.path.join(os.path.dirname(os.path.abspath(ps_file)), "lcmodel_output.xlsx")
    extract_lcmodel_ps(ps_file, excel_file)
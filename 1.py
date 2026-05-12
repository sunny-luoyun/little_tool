import pandas as pd

def convert_chat_excel_to_txt(excel_path, output_path='output.txt'):
    # 读取 Excel，如果第一行是数据，设置 header=None
    df = pd.read_excel(excel_path, header=None, dtype=str)

    # 确保有四列
    if df.shape[1] < 4:
        raise ValueError("Excel 文件至少需要四列：时间、QQ号、发送人、内容")

    # 给列取个名字方便处理
    df.columns = ['time', 'qq', 'sender', 'content'] + list(df.columns[4:])

    # 替换发送人
    df['sender'] = df['sender'].str.strip()  # 去掉可能存在的空格
    df['sender'] = df['sender'].replace({
        '越宝': '（邓越）',
        '洛韵唯汐': '（我）'
    })

    # 生成文本行 {时间} {发送人}: {内容}
    lines = []
    for _, row in df.iterrows():
        t = row['time']
        s = row['sender']
        c = row['content']
        # 如果内容为空，也保留格式
        if pd.isna(c):
            c = ''
        lines.append(f"{t} {s}: {c}")

    # 写入 txt
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"已生成文件：{output_path}")

if __name__ == '__main__':
    # 请修改为你的 Excel 文件路径
    convert_chat_excel_to_txt('/Users/langqin/Desktop/mes.xlsx')
import pandas as pd



def read_excel(file_path):
    try:
        return pd.read_excel(file_path, header=None)
    except Exception as e:
        print(f"读取文件 {file_path} 时发生错误: {e}")
        return None



def mask_id_card(id_card):
    id_card = str(id_card)
    return id_card[:4] + '********' + id_card[-4:]



def mask_phone(phone):
    phone = str(phone)
    return phone[:3] + '*****' + phone[-3:]



def match_names_and_scores(names_file, scores_file, output_file):
    # 读取名单和成绩
    names_df = read_excel(names_file)
    scores_df = read_excel(scores_file)

    if names_df is None or scores_df is None:
        print("无法读取文件，请检查文件路径和文件格式。")
        return


    names_df.columns = ['姓名', '身份证号', '电话']
    scores_df.columns = ['身份证号', '电话', '成绩']


    names_df['脱敏身份证号'] = names_df['身份证号'].apply(mask_id_card)
    names_df['脱敏电话'] = names_df['电话'].apply(mask_phone)


    matched_data = []
    for index, row in names_df.iterrows():
        masked_id_card = row['脱敏身份证号']
        masked_phone = row['脱敏电话']


        match_by_id_card = scores_df[scores_df['身份证号'] == masked_id_card]
        if not match_by_id_card.empty:
            matched_data.append({
                '姓名': row['姓名'],
                '身份证号': row['身份证号'],
                '电话': row['电话'],
                '成绩': match_by_id_card['成绩'].values[0]
            })
        else:

            match_by_phone = scores_df[scores_df['电话'] == masked_phone]
            if not match_by_phone.empty:
                matched_data.append({
                    '姓名': row['姓名'],
                    '身份证号': row['身份证号'],
                    '电话': row['电话'],
                    '成绩': match_by_phone['成绩'].values[0]
                })


    matched_df = pd.DataFrame(matched_data)


    try:
        matched_df.to_excel(output_file, index=False)
        print(f"匹配结果已保存到 {output_file}")
    except Exception as e:
        print(f"保存文件 {output_file} 时发生错误: {e}")


# 调用主程序
names_file = '/Users/langqin/Desktop/名单.xlsx'  # 名单文件路径
scores_file = '/Users/langqin/Desktop/成绩.xls'  # 成绩文件路径
output_file = '/Users/langqin/Desktop/匹配结果.xlsx'  # 输出文件路径
match_names_and_scores(names_file, scores_file, output_file)
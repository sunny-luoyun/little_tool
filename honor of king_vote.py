import requests
import base64
import os
import re
import pandas as pd

API_KEY = "v1NRsf6FzC0LdaNi0BFYF4bF"
SECRET_KEY = "NSrqBoy8BW4F7DpWue512w3v0UGhjl2E"

def main():
    # 获取access_token
    access_token = get_access_token()
    if not access_token:
        print("Failed to get access token")
        return

    # 构造OCR接口的URL
    url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic?access_token={access_token}"

    # 指定图片文件夹路径
    image_folder = "/Users/langqin/Desktop/picture"  # 替换为你的图片文件夹路径

    # 初始化一个列表，用于存储所有图片的解析结果
    all_parsed_results = []

    # 遍历文件夹中的所有图片文件
    for filename in os.listdir(image_folder):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
            image_path = os.path.join(image_folder, filename)
            print(f"Processing image: {image_path}")

            # 读取图片文件
            with open(image_path, "rb") as image_file:
                image_data = image_file.read()

            # 设置请求参数
            payload = {
                'image': base64.b64encode(image_data).decode('utf-8'),  # 图片转为base64编码
                'detect_direction': 'false',
                'detect_language': 'false',
                'paragraph': 'false',
                'probability': 'false'
            }

            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }

            # 发送POST请求
            response = requests.post(url, headers=headers, data=payload)

            # 打印响应
            print(f"OCR result for {filename}:")
            print(response.json())
            print("-" * 40)

            # 解析OCR结果
            parsed_result = parse_ocr_result(response.json())
            print(f"Parsed result for {filename}:")
            for role, votes in parsed_result.items():
                print(f"{role}: {votes}")
            print("-" * 40)

            # 将当前图片的解析结果添加到总列表中
            all_parsed_results.append(parsed_result)

    # 将所有解析结果保存到Excel文件中
    save_to_excel(all_parsed_results, "/Users/langqin/Desktop/picture/results.xlsx")

def get_access_token():
    """
    使用 AK，SK 生成鉴权签名（Access Token）
    :return: access_token，或是None(如果错误)
    """
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {"grant_type": "client_credentials", "client_id": API_KEY, "client_secret": SECRET_KEY}
    response = requests.post(url, params=params)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print("Error getting access token:", response.text)
        return None

def parse_ocr_result(ocr_result):
    """
    解析OCR结果，提取角色和对应的票数
    :param ocr_result: OCR接口返回的JSON结果
    :return: 一个字典，键是角色名称，值是对应的票数
    """
    words_result = ocr_result.get('words_result', [])
    parsed_result = {}
    votes = []
    roles = []

    # 遍历结果，提取票数和角色名称
    for item in words_result:
        word = item['words']
        if re.match(r'\d+(,\d+)*票', word):  # 匹配票数
            votes.append(word)
        elif re.match(r'\D', word):  # 匹配非数字开头的字符串，假设这些是角色名称
            roles.append(word)

    # 清洗数据，去除一些不必要的字符串
    roles = [role for role in roles if '票' not in role and '投票' not in role and '返场' not in role and '获取' not in role
             and '今日' not in role and '周年庆' not in role and '默认' not in role and '送限' not in role
             and '英雄拾忆' not in role and '拾年声藏' not in role and '传说' not in role and '⊙' not in role
             and '送周年' not in role and '史诗' not in role and '精彩' not in role and '中' not in role and '天命' not in role
             and '@' not in role and '砖' not in role]

    # 确保票数和角色数量匹配
    min_len = min(len(votes), len(roles))
    parsed_result = dict(zip(roles[:min_len], votes[:min_len]))

    return parsed_result

def save_to_excel(parsed_results, filename):
    """
    将解析结果保存到Excel文件中
    :param parsed_results: 所有图片的解析结果列表
    :param filename: 输出的Excel文件名
    """
    # 创建一个空的DataFrame
    df = pd.DataFrame(columns=['角色', '票数'])

    # 遍历所有解析结果，将数据添加到DataFrame中
    for result in parsed_results:
        for role, votes in result.items():
            # 去掉“票”字，并将票数转换为以千为单位的整数
            votes = votes.replace('票', '').replace(',', '')
            votes = int(votes) // 1000
            df = pd.concat([df, pd.DataFrame({'角色': [role], '票数': [votes]})], ignore_index=True)

    # 保存到Excel文件
    df.to_excel(filename, index=False)
    print(f"Results saved to {filename}")

if __name__ == '__main__':
    main()
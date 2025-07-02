import os
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# 获取当前时间
today = datetime.now()

# 计算昨天和前天的日期
yesterday = today - timedelta(days=1)
day_before_yesterday = today - timedelta(days=2)

url = 'http://192.168.84.3:9090/cgcSims/selectList.do'
header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                        'Chrome/99.0.4844.84 Safari/537.36 HBPC/12.1.3.310'}
data = {'hiddenType': None,
        'isHost': None,
        'beginTime': day_before_yesterday.strftime('%Y-%m-%d'),
        'endTime': today.strftime('%Y-%m-%d'),
        'type': '2',
        'client': '192.168.84.1',
        'roomId': '7219',
        'roomName': '1704',
        'building': None}

print(f"发送POST请求到: {url}")
print(f"请求头: {header}")
print(f"请求数据: {data}")

try:
    resp = requests.post(url=url, headers=header, data=data, timeout=2)
    resp.raise_for_status()  # 检查请求是否成功
    print(f"请求成功，状态码: {resp.status_code}")
except requests.RequestException as e:
    print(f"请求失败: {e}")
    exit(1)

soup = BeautifulSoup(resp.text, "lxml")

# 找到表格
table = soup.find("table", {"id": "oTable"})
if not table:
    print("未找到表格")
    exit(1)
print("找到表格")

# 找到包含数据的行
data_rows = table.find_all("tr")[1:-2]  # 排除标题行和最后两行（统计行和按钮行）
print(f"找到数据行数: {len(data_rows)}")

# 提取“剩余电量(度)”列的值（假设它是每行的第3个单元格）
remaining_power_today = None
remaining_power_yesterday = None
for row in data_rows:
    cells = row.find_all("td")
    if len(cells) > 2:  # 确保单元格足够多
        remaining_power = cells[2].get_text().strip()  # 使用strip()去除前后空格
        date_str = cells[5].get_text().strip()  # 获取日期字符串
        date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S.%f')  # 转换为datetime对象
        print(f"日期: {date_obj.date()}, 剩余电量: {remaining_power}")
        if date_obj.date() == yesterday.date():
            remaining_power_today = float(remaining_power)
            print(f"今日剩余电量: {remaining_power_today}")
        elif date_obj.date() == day_before_yesterday.date():
            remaining_power_yesterday = float(remaining_power)
            print(f"昨日剩余电量: {remaining_power_yesterday}")

# 计算昨日用电
if remaining_power_today is not None and remaining_power_yesterday is not None:
    yesterday_power_usage = remaining_power_yesterday - remaining_power_today
    yesterday_power_usage_rounded = round(yesterday_power_usage, 2)  # 四舍五入到小数点后两位
    print(f"昨日用电: {yesterday_power_usage_rounded}度")
    os.system(f"""
              osascript -e 'display notification "{remaining_power_today}度，前日用电{yesterday_power_usage_rounded}度" with title "{yesterday.strftime('%Y-%m-%d')}剩余电量"'
              """)
else:
    print("无法获取足够的数据来计算昨日用电。")
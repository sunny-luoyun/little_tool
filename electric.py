import os
import time, re, requests, socket
from datetime import datetime, timedelta
from bs4 import BeautifulSoup



today = datetime.now()

yesterday = today - timedelta(days=1)

url = ' http://192.168.84.3:9090/cgcSims/selectList.do'
header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                        'Chrome/99.0.4844.84 Safari/537.36 HBPC/12.1.3.310'}
data = {'hiddenType': None,
        'isHost': None,
        'beginTime': yesterday.strftime('%Y-%m-%d'),
        'endTime': today.strftime('%Y-%m-%d'),
        'type': '2',
        'client': '192.168.84.1',
        'roomId': '7219',
        'roomName': '1704',
        'building': None}
resp = requests.post(url=url, headers=header, data=data, timeout=2)
soup = BeautifulSoup(resp.text, "lxml")

# 找到表格
table = soup.find("table", {"id": "oTable"})

# 找到包含数据的第二行
data_rows = table.find_all("tr")[1:]  # 排除标题行

# 提取“剩余电量(度)”列的值（假设它是每行的第3个单元格）
for row in data_rows:
    cells = row.find_all("td")
    if len(cells) > 2:  # 确保单元格足够多
        remaining_power = cells[2].get_text().strip()  # 使用strip()去除前后空格
        # print("剩余电量(度):", remaining_power)


os.system(f"""
          osascript -e 'display notification "{remaining_power}度" with title "宿舍今日剩余电量"'
          """)
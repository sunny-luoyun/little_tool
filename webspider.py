import requests

# 目标地址
URL = "https://www.pixiv.net/search/users?s_mode=s_usr&nick=听雨&i=1&comment=&p=1"


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}


def fetch_source():
    print(f"正在请求: {URL} ...")
    try:
        response = requests.get(URL, headers=HEADERS, timeout=10)
        response.encoding = 'utf-8'

        if response.status_code == 200:
            html_content = response.result if hasattr(response, 'result') else response.text


            with open("../little_tool/source.txt", "w", encoding="utf-8") as f:
                f.write(html_content)

            print("✅ 成功！源码已保存至: source.txt")

            print(html_content[:100000])
        else:
            print(f"❌ 失败，状态码: {response.status_code}")

    except Exception as e:
        print(f"💥 发生错误: {e}")


if __name__ == "__main__":
    fetch_source()
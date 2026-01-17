import json
import os
import re
import requests
from bs4 import BeautifulSoup
import time
import random

BASE = "https://mirror.chromaso.net"
FORUM_OFFSET_URL = BASE + "/forum/18/+{}"
HEADERS = {"User-Agent": "Mozilla/5.0"}

STATE_FILE = "thread_state.json"
PAGE_SIZE = 30
MAX_PAGES = 20
SLEEP_MIN = 5
SLEEP_MAX = 6

STOP_AFTER_OLD_PAGES = 2  # 连续2页都“明显旧”才停

THREAD_ID_RE = re.compile(r"^/thread/(\d+)$")
LAST_LINK_RE = re.compile(r"^/thread/\d+/last#p\d+$")
POST_ID_RE = re.compile(r"#p(\d+)")


def parse_threads(html: str):
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table", id="thread-table-main")
    if not table or not table.tbody:
        return []

    out = []
    for row in table.tbody.find_all("tr"):
        title_a = row.find("a", class_="ui-link")
        if not title_a or not title_a.get("href"):
            continue

        href = title_a["href"].strip()
        m = THREAD_ID_RE.match(href)
        if not m:
            continue
        thread_id = m.group(1)

        title = title_a.get_text(strip=True)
        link = BASE + href

        reply_td = row.find("td", class_="text-end")
        reply_cnt = int(reply_td.get_text(strip=True)) if reply_td else 0

        last_a = row.find("a", href=LAST_LINK_RE)
        if not last_a or not last_a.get("href"):
            continue

        last_href = last_a["href"].strip()
        pm = POST_ID_RE.search(last_href)
        if not pm:
            continue
        last_pid = int(pm.group(1))

        last_time = ""
        last_user = ""

        last_td = row.find("td", class_="d-none d-sm-table-cell")
        if last_td:
            time_tag = last_td.find("time")
            if time_tag and time_tag.get("datetime"):
                last_time = time_tag["datetime"]
            a = last_td.find("a")
            if a:
                last_user = a.get_text(strip=True).split("\n")[0].strip()
        else:
            mobile_span = row.find("span", class_="d-sm-none")
            if mobile_span:
                time_tag = mobile_span.find("time")
                if time_tag and time_tag.get("datetime"):
                    last_time = time_tag["datetime"]
                a = mobile_span.find("a")
                if a:
                    last_user = a.get_text(strip=True).split("@")[0].strip()

        out.append({
            "thread_id": thread_id,
            "title": title,
            "link": link,
            "reply": reply_cnt,
            "last_pid": last_pid,
            "last_time": last_time,
            "last_user": last_user,
            "last_href": BASE + last_href,
        })

    return out


def load_state():
    if not os.path.exists(STATE_FILE):
        return {"max_seen_pid": 0, "threads": {}}

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "threads" not in data or not isinstance(data["threads"], dict):
            data["threads"] = {}
        if "max_seen_pid" not in data:
            data["max_seen_pid"] = max((v.get("last_pid", 0) for v in data["threads"].values()), default=0)
        return data
    except Exception:
        return {"max_seen_pid": 0, "threads": {}}


def save_state(state: dict):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def fetch_page(offset: int) -> str:
    url = FORUM_OFFSET_URL.format(offset)
    r = requests.get(url, headers=HEADERS, timeout=10)
    r.raise_for_status()
    return r.text


def main():
    state = load_state()
    known = state["threads"]
    max_seen_pid = int(state.get("max_seen_pid", 0))

    new_threads = []
    updated_threads = []

    newest_pid_this_run = max_seen_pid
    old_page_streak = 0  # 连续“旧页”计数

    for page_idx in range(MAX_PAGES):
        offset = page_idx * PAGE_SIZE
        html = fetch_page(offset)
        threads = parse_threads(html)
        if not threads:
            break

        page_max_pid = max(t["last_pid"] for t in threads)
        newest_pid_this_run = max(newest_pid_this_run, page_max_pid)

        # 对比更新/新帖
        for t in threads:
            tid = t["thread_id"]
            prev = known.get(tid)
            if prev is None:
                new_threads.append(t)
            else:
                prev_pid = int(prev.get("last_pid", 0))
                if t["last_pid"] > prev_pid:
                    updated_threads.append(t)

        # 写入 state（渐进补全）
        for t in threads:
            known[t["thread_id"]] = {
                "last_pid": t["last_pid"],
                "last_time": t["last_time"],
                "title": t["title"],
                "link": t["link"],
            }

        # ---------- 智能停爬（连续2页旧才停） ----------
        if page_max_pid <= max_seen_pid:
            old_page_streak += 1
        else:
            old_page_streak = 0

        if old_page_streak >= STOP_AFTER_OLD_PAGES:
            break

        # ✅ 合理休息：避免频繁请求
        time.sleep(random.uniform(SLEEP_MIN, SLEEP_MAX))

    # 输出
    if not new_threads and not updated_threads:
        print("没有检测到新帖或更新（在你扫描到的范围内）")
    else:
        if new_threads:
            new_threads.sort(key=lambda x: x["last_pid"], reverse=True)
            print(f"🆕 新帖子：{len(new_threads)}")
            for t in new_threads:
                print(f"- pid={t['last_pid']} | {t['last_time']} | {t['title']} | {t['last_user']} | 回复 {t['reply']}")
                print(f"  {t['link']}")
                print(f"  last: {t['last_href']}")
            print()

        if updated_threads:
            updated_threads.sort(key=lambda x: x["last_pid"], reverse=True)
            print(f"🔥 更新的帖子：{len(updated_threads)}")
            for t in updated_threads:
                prev = state["threads"].get(t["thread_id"], {})
                print(f"- pid {prev.get('last_pid','?')} -> {t['last_pid']} | {prev.get('last_time','')} -> {t['last_time']} | {t['title']}")
                print(f"  {t['link']}")
                print(f"  last: {t['last_href']}")

    state["max_seen_pid"] = newest_pid_this_run
    save_state(state)
    print(f"\nstate 已更新：{STATE_FILE}（已记录 {len(known)} 个帖子，max_seen_pid={state['max_seen_pid']}）")


if __name__ == "__main__":
    main()

import pyautogui
import time
import random
import sys
import subprocess

screen_width, screen_height = pyautogui.size()
pyautogui.FAILSAFE = False
def random_offset(original, max_offset=10):

    new_x = original[0] + random.randint(-max_offset, max_offset)
    new_y = original[1] + random.randint(-max_offset, max_offset)

    new_x = max(0, min(screen_width, new_x))
    new_y = max(0, min(screen_height, new_y))
    return new_x, new_y

def activate_my_android_window():
    """激活 MuMuEmulator 进程中的“我的安卓”窗口"""
    script = '''
    tell application "System Events"
        tell process "BlueStacks"
            set frontmost to true
            -- 找到标题为“我的安卓”的窗口并提升
            repeat with aWindow in windows
                if name of aWindow is "我的安卓" then
                    perform action "AXRaise" of aWindow
                    exit repeat
                end if
            end repeat
        end tell
    end tell
    '''
    try:
        subprocess.run(['osascript', '-e', script], check=True, capture_output=True, text=True)
        print("✅ 已激活窗口：我的安卓")
        time.sleep(0.5)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 激活失败: {e.stderr}")
        return False

def random_sleep(base_seconds, variation=0.2):

    actual = base_seconds * random.uniform(1 - variation, 1 + variation)
    time.sleep(actual)

def random_key_hold(key, base_seconds, variation=0.0):

    pyautogui.keyDown(key)
    actual = base_seconds * random.uniform(1 - variation, 1 + variation)
    time.sleep(actual)
    pyautogui.keyUp(key)

def safe_click(x, y, offset=10, move_duration=0.2):

    target_x, target_y = random_offset((x, y), offset)

    pyautogui.click(target_x, target_y)

def countdown_sleep(base_seconds, variation=0.05, update_interval=1):

    actual = base_seconds * random.uniform(1 - variation, 1 + variation)
    total = int(actual)
    print(f"开始休息，预计 {total} 秒后继续... (按 Ctrl+C 可中断)")
    for remaining in range(total, 0, -update_interval):
        sys.stdout.write(f"\r剩余时间: {remaining:4d} 秒")
        sys.stdout.flush()

        sleep_time = min(update_interval, remaining)
        time.sleep(sleep_time)
    print("\n休息结束，继续执行脚本。")

random_sleep(2)

t = 1
while True:
    print(f'循环第{t}遍')

    activate_my_android_window()

    safe_click(856, 838)
    random_sleep(10)

    for i in range(6):
        safe_click(60, 290)
        random_sleep(1)

    safe_click(546, 702)
    random_sleep(10)

    random_key_hold('a', 0.8)
    random_sleep(1)

    random_key_hold('w', 1.0)
    random_sleep(3)

    safe_click(1142, 619)
    random_sleep(2)

    # 连续3次点击
    for i in range(3):
        safe_click(78, 342)
        random_sleep(1)

    random_sleep(5)

    safe_click(115, 125)
    random_sleep(1)

    safe_click(1070, 731)
    random_sleep(1)

    safe_click(1574, 120)
    random_sleep(1)

    safe_click(1474, 888)
    random_sleep(1)

    safe_click(1029, 755)

    time.sleep(1)
    pyautogui.click(1793,401)

    t += 1

    countdown_sleep(850, variation=0)

    activate_my_android_window()

    time.sleep(1)


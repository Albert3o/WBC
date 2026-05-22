# test_glyder.py
from sshkeyboard import listen_keyboard, stop_listening

press_count = {}

def on_press(key):
    press_count[key] = press_count.get(key, 0) + 1
    print(f"[PRESS]   key='{key}'  total_fires={press_count[key]}")

def on_release(key):
    print(f"[RELEASE] key='{key}'  (reset edge trigger)")
    press_count[key] = 0  # 松键后计数归零

print("开始监听键盘事件，按 ESC 退出")
print("测试方法：")
print("  1. 踩一下脚踏板 -> 应该看到1次 PRESS + 1次 RELEASE")
print("  2. 踩住不松     -> 应该看到1次 PRESS + 若干次 PRESS(key-repeat) + 1次 RELEASE")
print("-" * 50)

try:
    listen_keyboard(
        on_press=on_press,
        on_release=on_release,
        delay_second_char=0.1,
        delay_other_chars=0.05,
        sleep=0.01,
    )
except KeyboardInterrupt:
    stop_listening()

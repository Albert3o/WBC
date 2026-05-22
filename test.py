import time
from sshkeyboard import listen_keyboard, stop_listening

last_key_time = {}
DEBOUNCE_SEC = 0.25  # 和 policy 里一样的值

def on_press(key):
    now = time.monotonic()
    if (now - last_key_time.get(key, 0)) < DEBOUNCE_SEC:
        # print(f"[IGNORED]   key='{key}' (debounce 窗口内，不触发速度变化)")
        return
    last_key_time[key] = now
    print(f"[PROCESSED] key='{key}' → 速度会变化！")

def on_release(key):
    pass  # 忽略假 release，不需要

print("开始监听（带 debounce），按 ESC 退出")
print("长按：应该只看到 1 次 PROCESSED，其余都是 IGNORED")
print("松开后重新踩：应该看到新的 PROCESSED")
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

# test_keyboard_edge_trigger.py（临时测试脚本）
import sys
sys.path.insert(0, "gr00t_wbc")

# 手动 mock 掉依赖，避免需要 ROS 和 ONNX
import unittest.mock as mock
sys.modules['rclpy'] = mock.MagicMock()
sys.modules['ort'] = mock.MagicMock()
sys.modules['torch'] = mock.MagicMock()

from gr00t_wbc.control.policy.g1_gear_wbc_policy import G1GearWbcPolicy

# 创建一个最简的 mock policy 实例（只测试键盘逻辑）
policy = mock.MagicMock(spec=G1GearWbcPolicy)
policy._last_key = None
policy.cmd = [0.0, 0.0, 0.0]

# 直接调用真实方法
real_handle = G1GearWbcPolicy.handle_keyboard_button.__get__(policy)

print("=== 测试边沿触发逻辑 ===")

# 测试1：第一次按 w，速度应该增加
real_handle("w")
assert policy.cmd[0] == 0.2, f"FAIL: 期望 0.2，得到 {policy.cmd[0]}"
print(f"[PASS] 第一次按 w: cmd[0] = {policy.cmd[0]}")

# 测试2：key-repeat（同一个键再来），速度不应增加
real_handle("w")
assert policy.cmd[0] == 0.2, f"FAIL: key-repeat 不应累加，得到 {policy.cmd[0]}"
print(f"[PASS] 按住 w 时 key-repeat: cmd[0] = {policy.cmd[0]} (未变)")

# 测试3：松键（None），_last_key 应该重置
real_handle(None)
assert policy._last_key is None, f"FAIL: 松键后 _last_key 应为 None"
print(f"[PASS] 松键后 _last_key = {policy._last_key}")

# 测试4：重新按 w，速度应该再增加
real_handle("w")
assert policy.cmd[0] == 0.4, f"FAIL: 重新按 w 期望 0.4，得到 {policy.cmd[0]}"
print(f"[PASS] 松开后重新按 w: cmd[0] = {policy.cmd[0]}")

print("\n所有测试通过！")
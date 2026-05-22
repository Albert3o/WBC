(gr00t) (base) deepak@deepak-System-Product-Name:~/G1_teleoperation/Isaac-GR00T$ python test.py
开始监听键盘事件，按 ESC 退出
测试方法：
  1. 踩一下脚踏板 -> 应该看到1次 PRESS + 1次 RELEASE
  2. 踩住不松     -> 应该看到1次 PRESS + 若干次 PRESS(key-repeat) + 1次 RELEASE
--------------------------------------------------
[PRESS]   key='w'  total_fires=1
[RELEASE] key='w'  (reset edge trigger)
[PRESS]   key='w'  total_fires=1

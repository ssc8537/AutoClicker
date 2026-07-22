"""由"12eqr左键-今汐.json"只读等价转换。"""

NAME = '12eqr左键-今汐'  # 宏库中显示的脚本名称
HOTKEY = 'mouse_back'    # 物理触发键：鼠标侧键 1
MODE = 'down'            # 按住侧键运行，松开后请求停止
COUNT = 0                # 0 表示持续重复 run，直到松开或手动停止
SPEED = 1.0              # 等待速度倍率；只影响 player.sleep()
ENABLED = False           # True 表示程序启动后允许该宏响应触发键


def run(player):
    # 第一段：调用共享角色槽位，依次切换到 1 号位和 2 号位。
    player.切换(1)
    player.sleep(10)
    player.切换(2)
    player.sleep(10)
    # 第二段：依次轻按物理 1、Q、R、F；hold_ms=10 表示每键按住 10ms。
    # 这些是原始物理键，不代表程序会判断对应技能是否成功。
    player.tap("1", hold_ms=10)
    player.sleep(10)
    player.tap("q", hold_ms=10)
    player.sleep(10)
    player.tap("r", hold_ms=10)
    player.sleep(10)
    player.tap("f", hold_ms=10)
    player.sleep(10)
    # 收尾：点击一次鼠标左键。因为 COUNT=0，整轮结束后会再次从头运行。
    player.mouse_click("left", hold_ms=10)
    player.sleep(10)

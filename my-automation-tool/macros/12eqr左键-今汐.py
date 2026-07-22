"""由"12eqr左键-今汐.json"只读等价转换。"""

NAME = '12eqr左键-今汐'
HOTKEY = 'mouse_back'
MODE = 'down'
COUNT = 0
SPEED = 1.0
ENABLED = True


def run(player):
    # 角色切换：1、2 互相切换
    player.切换(1)
    player.sleep(10)
    player.切换(2)
    player.sleep(10)
    # 按键释放：1、Q、R、F
    player.tap("1", hold_ms=10)
    player.sleep(10)
    player.tap("q", hold_ms=10)
    player.sleep(10)
    player.tap("r", hold_ms=10)
    player.sleep(10)
    player.tap("f", hold_ms=10)
    player.sleep(10)
    # 鼠标左键一直点击
    player.mouse_click("left", hold_ms=10)
    player.sleep(10)
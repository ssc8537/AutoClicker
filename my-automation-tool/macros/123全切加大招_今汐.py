"""由“123全切+大招-今汐.json”只读等价转换。"""

NAME = "123全切+大招-今汐"  # 宏库中显示的脚本名称
HOTKEY = "mouse_back"       # 物理触发键：鼠标侧键 1
MODE = "down"               # 按住侧键运行，松开后请求停止
COUNT = 0                   # 0 表示持续重复 run，直到松开或手动停止
SPEED = 1.0                 # 等待速度倍率；只影响 player.sleep()
ENABLED = False             # False 表示当前默认不启用此宏


def _点击(player, key):
    """点击一个物理键 15ms，并在点击完成后额外等待 15ms。"""
    if key == "mouse_left":
        player.mouse_click("left", hold_ms=15)
    else:
        player.tap(key, hold_ms=15)
    player.sleep(15)


def run(player):
    # 起手：先点击物理 F 键。具体游戏含义由当前键位设置决定。
    _点击(player, "f")

    # 1 号位：数字 1 → 左键 → E → Q → R，每个动作后再等 10ms。
    _点击(player, "1")
    player.sleep(10)
    _点击(player, "mouse_left")
    player.sleep(10)
    _点击(player, "e")
    player.sleep(10)
    _点击(player, "q")
    player.sleep(10)
    _点击(player, "r")
    player.sleep(10)

    # 2 号位：复用与 1 号位相同的物理按键顺序。
    _点击(player, "2")
    player.sleep(10)
    _点击(player, "mouse_left")
    player.sleep(10)
    _点击(player, "e")
    player.sleep(10)
    _点击(player, "q")
    player.sleep(10)
    _点击(player, "r")
    player.sleep(10)

    # 3 号位：完成最后一组后，本轮 run 结束。
    _点击(player, "3")
    player.sleep(10)
    _点击(player, "mouse_left")
    player.sleep(10)
    _点击(player, "e")
    player.sleep(10)
    _点击(player, "q")
    player.sleep(10)
    _点击(player, "r")
    player.sleep(10)

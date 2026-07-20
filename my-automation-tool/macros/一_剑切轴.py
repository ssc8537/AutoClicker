"""由“（一）剑切轴.json”只读等价转换；不包含识别或窗口绑定。"""

NAME = "（一）剑切轴"
HOTKEY = "numpad0"
MODE = "down"
COUNT = 0
SPEED = 1.0
ENABLED = False


def _点击(player, key):
    """QuickInput 点击的 10–20ms 随机间隔固定取中值 15ms。"""
    if key == "mouse_left":
        player.mouse_click("left", hold_ms=15)
    else:
        player.tap(key, hold_ms=15)
    player.sleep(15)


def run(player):
    # 切千咲-E-A，5 次。
    for _ in range(5):
        _点击(player, "3")
        player.sleep(50)
        _点击(player, "e")
        player.sleep(50)
        _点击(player, "mouse_left")
        player.sleep(50)

    # 切卡提-A，8 次。
    for _ in range(8):
        _点击(player, "1")
        player.sleep(50)
        _点击(player, "mouse_left")
        player.sleep(50)

    # 切千咲-A打出剪刀，3 次。
    for _ in range(3):
        _点击(player, "3")
        player.sleep(50)
        _点击(player, "mouse_left")
        player.sleep(50)

    player.sleep(400)

    # 切卡提-A，7 次；原 JSON 的左键后没有额外显式等待。
    for _ in range(7):
        _点击(player, "1")
        player.sleep(30)
        _点击(player, "mouse_left")

    player.sleep(100)
    _点击(player, "r")

    # 小卡提-A，1000 次。
    for _ in range(1000):
        _点击(player, "mouse_left")
        player.sleep(10)

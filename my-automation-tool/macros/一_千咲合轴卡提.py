"""由“（一）千咲合轴卡提.json”只读等价转换。"""

NAME = "（一）千咲合轴卡提"
HOTKEY = 'mouse_back'
MODE = 'down'
COUNT = 0
SPEED = 1.0
ENABLED = True


def _点击(player, key):
    if key == "mouse_left":
        player.mouse_click("left", hold_ms=15)
    else:
        player.tap(key, hold_ms=15)
    player.sleep(15)


def run(player):
    _点击(player, "e")
    player.sleep(50)

    # 切卡提-Q-a2-a3，5 次。
    for _ in range(5):
        _点击(player, "1")
        player.sleep(35)
        _点击(player, "q")
        player.sleep(35)
        _点击(player, "mouse_left")
        player.sleep(10)
        _点击(player, "mouse_left")
        player.sleep(10)
        _点击(player, "mouse_left")
        player.sleep(10)

    # 切千咲-电锯a2-a3，8 次。
    for _ in range(8):
        _点击(player, "3")
        player.sleep(50)
        _点击(player, "mouse_left")
        player.sleep(50)

    # 切卡提-a4，5 次。
    for _ in range(5):
        _点击(player, "1")
        player.sleep(35)
        _点击(player, "mouse_left")
        player.sleep(35)

    # 切千咲-电锯下砸，8 次。
    for _ in range(8):
        _点击(player, "3")
        player.sleep(30)
        _点击(player, "mouse_left")
        player.sleep(30)
        _点击(player, "mouse_left")
        player.sleep(30)

    player.sleep(100)

    # 变奏卡提，100 次。
    for _ in range(100):
        _点击(player, "1")
        player.sleep(35)

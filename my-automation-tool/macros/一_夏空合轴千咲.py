"""由“（一）夏空合轴千咲.json”只读等价转换。"""

NAME = "（一）夏空合轴千咲"
HOTKEY = 'mouse_forward'
MODE = 'down'
COUNT = 0
SPEED = 1.0
ENABLED = False


def _点击(player, key):
    if key == "mouse_left":
        player.mouse_click("left", hold_ms=15)
    else:
        player.tap(key, hold_ms=15)
    player.sleep(15)


def run(player):
    player.sleep(100)

    for _ in range(1):
        _点击(player, "space")
        player.sleep(100)

    for _ in range(2):
        _点击(player, "mouse_left")
        player.sleep(100)

    # 切千咲-E-E-E-A-A-R，4 次。
    for _ in range(4):
        _点击(player, "3")
        player.sleep(100)
        _点击(player, "e")
        player.sleep(20)
        _点击(player, "e")
        player.sleep(20)
        _点击(player, "e")
        player.sleep(20)
        _点击(player, "mouse_left")
        player.sleep(10)
        _点击(player, "mouse_left")
        player.sleep(10)
        _点击(player, "r")
        player.sleep(50)

    player.sleep(2100)

    # A-切夏空，6 次。
    for _ in range(6):
        _点击(player, "mouse_left")
        player.sleep(100)
        _点击(player, "2")
        player.sleep(100)

    # 原 JSON 此处 mark 写“等待100000秒”，实际 ms/ex 都是 0，严格保留 0ms。
    player.sleep(0)

    for _ in range(1):
        _点击(player, "space")
        player.sleep(100)

    for _ in range(2):
        _点击(player, "mouse_left")
        player.sleep(100)

    for _ in range(2):
        _点击(player, "3")
        player.sleep(30)
        _点击(player, "mouse_left")
        player.sleep(30)

    for _ in range(100):
        _点击(player, "2")
        player.sleep(20)
        _点击(player, "mouse_left")
        player.sleep(20)

"""由“123全切+大招-今汐.json”只读等价转换。"""

NAME = "123全切+大招-今汐"
HOTKEY = "mouse_back"
MODE = "down"
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
    _点击(player, "f")

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

"""由“1234eqfR左键.json”只读等价转换。"""

NAME = "1234eqfR左键"
HOTKEY = 'mouse_back'
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


def _角色段(player, slot):
    _点击(player, slot)
    player.sleep(10)
    _点击(player, "mouse_left")
    player.sleep(10)
    _点击(player, "e")
    player.sleep(10)
    _点击(player, "q")
    player.sleep(10)
    _点击(player, "f")
    player.sleep(10)


def run(player):
    _点击(player, "r")
    _角色段(player, "1")
    _角色段(player, "2")
    _角色段(player, "3")
    _角色段(player, "4")

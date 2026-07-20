"""可信本地 Python 测试宏。"""

NAME = "hello world"
HOTKEY = 'mouse_back'
MODE = 'down'
COUNT = 0
SPEED = 1.0
ENABLED = False


def run(player):
    """输出小句 hello world。"""
    for key in ("h", "e", "l", "l", "o", "space", "w", "o", "r", "l", "d"):
        player.tap(key)
        player.sleep(50)

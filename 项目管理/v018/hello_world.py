"""阶段 3 的可信本地 Python 测试宏。"""

NAME = "hello world"
HOTKEY = "f9"
MODE = "down"
COUNT = 1
SPEED = 1.0


def run(player):
    """用真实键盘按键输出小写 hello world。"""
    for key in ("h", "e", "l", "l", "o", "space", "w", "o", "r", "l", "d"):
        player.tap(key)
        player.sleep(50)

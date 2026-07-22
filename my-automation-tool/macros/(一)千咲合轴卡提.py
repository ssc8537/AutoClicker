"""由“（一）千咲合轴卡提.json”只读等价转换。"""

NAME = "（一）千咲合轴卡提"  # 宏库中显示的脚本名称
HOTKEY = 'mouse_back'             # 物理触发键：鼠标侧键 1
MODE = 'down'                     # 按住侧键运行，松开后请求停止
COUNT = 0                         # 0 表示持续重复 run，直到松开或手动停止
SPEED = 1.0                       # 等待速度倍率；只影响 player.sleep()
ENABLED = False                   # False 表示当前默认不启用此宏


def _点击(player, key):
    """点击一个物理键 15ms，并在点击完成后额外等待 15ms。"""
    if key == "mouse_left":
        player.mouse_click("left", hold_ms=15)
    else:
        player.tap(key, hold_ms=15)
    player.sleep(15)


def run(player):
    # 起手：点击物理 E 键，再等待 50ms。程序不判断这个键是否成功释放技能。
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

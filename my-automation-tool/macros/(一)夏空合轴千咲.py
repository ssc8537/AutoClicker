"""由“（一）夏空合轴千咲.json”只读等价转换。"""

NAME = "（一）夏空合轴千咲"  # 宏库中显示的脚本名称
HOTKEY = 'mouse_forward'          # 物理触发键：鼠标侧键 2
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
    # 起手缓冲：先等待 100ms，避免触发键刚按下就立刻发送动作。
    player.sleep(100)

    # 跳跃一次。range(1) 保留自原 JSON，也可以直接理解为“执行一次”。
    for _ in range(1):
        _点击(player, "space")
        player.sleep(100)

    # 接两次鼠标左键，每次点击后再等待 100ms。
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

    # 千咲短段：切到 3 号位并点击左键，共两轮。
    for _ in range(2):
        _点击(player, "mouse_left")
        player.sleep(100)

    for _ in range(2):
        _点击(player, "3")
        player.sleep(30)
        _点击(player, "mouse_left")
        player.sleep(30)

    # 收尾重复段：2 号位与左键交替 100 次；松开触发键仍可中断。
    for _ in range(100):
        _点击(player, "2")
        player.sleep(20)
        _点击(player, "mouse_left")
        player.sleep(20)

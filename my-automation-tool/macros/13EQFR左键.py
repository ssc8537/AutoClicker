"""由“13EQFR左键.json”只读等价转换。"""

NAME = "13EQFR左键"      # 宏库中显示的脚本名称
HOTKEY = 'mouse_forward'  # 物理触发键：鼠标侧键 2
MODE = 'down'             # 按住侧键运行，松开后请求停止
COUNT = 0                 # 0 表示持续重复 run，直到松开或手动停止
SPEED = 1.0               # 等待速度倍率；只影响 player.sleep()
ENABLED = False           # False 表示当前默认不启用此宏


def _点击(player, key):
    """点击一个物理键 15ms，并在点击完成后额外等待 15ms。"""
    if key == "mouse_left":
        player.mouse_click("left", hold_ms=15)
    else:
        player.tap(key, hold_ms=15)
    player.sleep(15)


def run(player):
    # 一轮固定顺序：1 → 3 → E → Q → F → R → 鼠标左键。
    # 修改顺序时直接调整下面各行；增加间隔可插入 player.sleep(毫秒数)。
    _点击(player, "1")
    _点击(player, "3")
    _点击(player, "e")
    _点击(player, "q")
    _点击(player, "f")
    _点击(player, "r")
    _点击(player, "mouse_left")

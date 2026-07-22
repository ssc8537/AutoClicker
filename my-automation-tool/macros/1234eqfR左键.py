"""由“1234eqfR左键.json”只读等价转换。"""

NAME = "1234eqfR左键"  # 宏库中显示的脚本名称
HOTKEY = 'mouse_back'   # 物理触发键：鼠标侧键 1
MODE = 'down'           # 按住侧键运行，松开后请求停止
COUNT = 0               # 0 表示持续重复 run，直到松开或手动停止
SPEED = 1.0             # 等待速度倍率；只影响 player.sleep()
ENABLED = False         # False 表示当前默认不启用此宏


def _点击(player, key):
    """点击一个物理键 15ms，并在点击完成后额外等待 15ms。"""
    if key == "mouse_left":
        player.mouse_click("left", hold_ms=15)
    else:
        player.tap(key, hold_ms=15)
    player.sleep(15)


def _角色段(player, slot):
    """执行一个通用角色段：角色编号 → 左键 → E → Q → F。"""
    # slot 是字符串形式的物理数字键，例如 "1"；不是游戏角色识别结果。
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
    # 起手先按物理 R 键，然后依次执行 1、2、3、4 号位的相同动作模板。
    _点击(player, "r")
    _角色段(player, "1")
    _角色段(player, "2")
    _角色段(player, "3")
    _角色段(player, "4")

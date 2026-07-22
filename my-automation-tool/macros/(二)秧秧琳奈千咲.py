"""由用户提供的 QuickInput JSON 等价转换；不包含角色识别或条件判断。"""

# 角色编号（以用户最后一次更正为准）
# 1 号角色：秧秧
# 2 号角色：琳奈
# 3 号角色：千咲

NAME = "秧秧、琳奈、千咲合轴"  # 宏库中显示的脚本名称
HOTKEY = 'mouse_back'             # 物理触发键：鼠标侧键 1
MODE = 'down'                     # 按住侧键运行，松开后请求停止
COUNT = 0                         # 0 表示持续重复 run，直到松开或手动停止
SPEED = 1.0                       # 等待速度倍率；只影响 player.sleep()
ENABLED = False                   # False 表示当前默认不启用此宏


def _平A(player, wait_ms, times=1):
    """执行指定次数的左键点击；每次点击后等待 wait_ms 毫秒。"""
    for _ in range(times):
        # hold_ms 是鼠标左键保持按下的时间，不是两次点击之间的间隔。
        player.mouse_click("left", hold_ms=15)
        player.sleep(wait_ms)


def run(player):
    # 每次进入 run 都执行一整轮连招；COUNT=0 会在本轮结束后继续下一轮。
    # JSON 顶层：E，等待 50ms。
    player.战技()
    player.sleep(50)

    # “切秧秧，切琳奈合轴”：1 号秧秧 4 次平A，再切 2 号琳奈 6 次平A。
    player.切换(1)
    player.sleep(60)
    _平A(player, 49, times=4)
    player.切换(2)
    _平A(player, 49, times=6)

    # 原标记“切千咲-电锯a2-a3”：严格保留 JSON 的 8 次循环。
    for _ in range(8):
        player.切换(3)
        player.sleep(50)
        _平A(player, 50)

    # JSON 的 1 号位 a4 段：1 号位按用户要求为秧秧。
    for _ in range(5):
        player.切换(1)
        player.sleep(35)
        _平A(player, 35)

    # “切千咲-电锯下砸”：每轮切 3 号位后两次平A，共 8 轮。
    for _ in range(8):
        player.切换(3)
        player.sleep(30)
        _平A(player, 30, times=2)

    player.sleep(100)

    # JSON 的变奏 1 号位段：严格保留 100 次切 1 号位。
    for _ in range(100):
        player.切换(1)
        player.sleep(35)

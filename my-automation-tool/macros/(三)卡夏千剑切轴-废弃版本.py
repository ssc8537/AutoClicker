"""卡夏千双下落主轴。

来源：卡夏千剑切会话 events.jsonl 第 143–332 条事件（首尾包含）。
角色槽位：1=千咲、2=卡提、3=夏空。

已排除浏览器前台和错误键：N、Ctrl、A、Backspace。
所有保留的按住与等待均已从 0.3 倍速还原。非大招的讲解长停顿压缩为 100ms；
大招后的长停顿复用启动轴参数，为 880ms（500ms + 380ms）。
"""

NAME = "(三)卡夏千剑切轴"     # 宏库中显示的名称
HOTKEY = 'mouse_back'          # 物理触发键：鼠标侧键 1
MODE = 'down'                  # 按住触发键运行，松开后立即停止
COUNT = 1                       # 每次触发只执行一轮
SPEED = 1.0                     # 等待速度倍率
ENABLED = False                 # 初始不启用，确认后再在宏库中启用


def _动作(player, 动作名称, 按住毫秒, 等待毫秒=0):
    """发送共享动作。"""
    player.按键(动作名称, hold_ms=按住毫秒)
    if 等待毫秒:
        player.sleep(等待毫秒)


def _平A(player, 按住毫秒, 等待毫秒=0):
    """点击一次鼠标左键平A。"""
    player.mouse_click("left", hold_ms=按住毫秒)
    if 等待毫秒:
        player.sleep(等待毫秒)


def _重击(player, 按住毫秒, 等待毫秒=0):
    """长按鼠标左键执行重击或下落攻击。"""
    player.mouse_click("left", hold_ms=按住毫秒)
    if 等待毫秒:
        player.sleep(等待毫秒)


def _闪避(player, 按住毫秒, 等待毫秒=0):
    """点击鼠标右键执行文字轴中的“闪”。"""
    player.mouse_click("right", hold_ms=按住毫秒)
    if 等待毫秒:
        player.sleep(等待毫秒)


def run(player):
    # 双下落主轴：
    # 大卡EE 千咲A下落 夏空A4跳A 小卡RA23 夏空A4E 卡提A4E闪Z下落R
    #
    # 千咲A12EA 大卡A到砸下 R变小卡打一套 变大卡再打一套
    # 至此，双下落一轮完成，进入循环。

    # 大卡 EE（手动）
    # 按键：战技 → 战技。
    # _动作(player, "战技", 34, 100)
    # _动作(player, "战技", 39, 367)

    # 千咲 A 下落
    # 按键：切角色 1 → 平A。
    _动作(player, "角色 1", 36, 20)
    for _ in range(2):
        _平A(player, 37, 10)

    # 夏空 A4 跳 A
    # 按键：切角色 3 → 平A → 跳跃 → 平A。
    _动作(player, "角色 3", 33, 60)
    for _ in range(4):
        _平A(player, 37, 140)
    _动作(player, "跳跃", 41, 93)
    for _ in range(2):
        _平A(player, 37, 80)

    # 小卡 RA23
    # 按键：切角色 2 →R大招 → 平A → 平A。
    _动作(player, "角色 2", 33, 20)
    for _ in range(2):
        _动作(player, "大招", 33, 10)
    for _ in range(4):
        _平A(player, 37, 160)

    # 夏空 A4E
    _动作(player, "角色 3", 33, 100)
    for _ in range(4):
        _平A(player, 37, 150)
    _动作(player, "战技", 35, 100)

    # 卡提 A4 E 闪 Z 下落 R
    # 按键：切角色 2 → 平A → 战技 → 鼠标右键闪避 → 重击 → 平A → 大招。
    for _ in range(2):
        _动作(player, "角色 2", 34, 30)
    for _ in range(2):
        _平A(player, 37, 70)
    _动作(player, "战技", 34, 30)
    _闪避(player, 36, 50)
    for _ in range(2):
        _重击(player, 400, 50)
    for _ in range(4):
        _平A(player, 34, 220)
    _动作(player, "大招", 34, 50)

    # 千咲 A12 EA
    # 按键：切角色 1 → 平A → 平A → 战技 → 平A。
    _动作(player, "角色 1", 37, 30)
    for _ in range(4):
        _平A(player, 37, 80)
    _动作(player, "战技", 26, 30)
    for _ in range(2):
        _平A(player, 31, 60)

    # 大卡 A 到砸下
    # 按键：切角色 2 → 平A。
    for _ in range(4):
        _动作(player, "角色 2", 35, 30)
    for _ in range(4):
        _平A(player, 37, 150)

    # R变小卡打一套
    # 按键：R大招 → 平A。
    for _ in range(4):
        _动作(player, "大招", 34, 50)
    for _ in range(8):
        _平A(player, 37, 150)

    # 后续变大卡打一套开大招-手动操作




    # _动作(player, "战技", 33, 187)
    # _闪避(player, 26, 113)
    # _重击(player, 181, 100)
    # _平A(player, 31, 428)
    # _动作(player, "大招", 17, 880)
    # _平A(player, 43, 207)
    # _平A(player, 48, 100)
    # _平A(player, 41, 100)
    # _平A(player, 30, 100)

    # # 变大卡再打一套：开场 EE
    # # 按键：战技 → 战技。
    # _动作(player, "战技", 31, 100)
    # _动作(player, "战技", 38, 379)

    # # 千咲 A 下落
    # # 按键：切角色 1 → 平A。
    # _动作(player, "角色 1", 37, 195)
    # _平A(player, 43, 100)

    # # 夏空 A4 跳 A
    # # 按键：切角色 3 → 平A → 跳跃 → 平A。
    # _动作(player, "角色 3", 38, 256)
    # _平A(player, 38, 144)
    # _动作(player, "跳跃", 32, 60)
    # _平A(player, 39, 100)

    # # 小卡 A23
    # # 按键：切角色 2 → 平A → 平A。
    # _动作(player, "角色 2", 36, 173)
    # _平A(player, 33, 137)
    # _平A(player, 40, 100)

    # # 夏空 A4E
    # # 按键：切角色 3 → 平A → 战技。
    # _动作(player, "角色 3", 42, 100)
    # _平A(player, 36, 233)
    # _动作(player, "战技", 34, 100)

    # # 卡提 A4E 闪 Z 下落 R
    # # 按键：切角色 2 → 平A → 战技 → 鼠标右键闪避 → 重击 → 平A → 大招。
    # _动作(player, "角色 2", 42, 161)
    # _平A(player, 40, 100)
    # _动作(player, "战技", 40, 202)
    # _闪避(player, 23, 100)
    # _重击(player, 166, 100)
    # _平A(player, 50, 376)
    # _动作(player, "大招", 32, 880)

    # # 千咲 A12EA
    # # 按键：切角色 1 → 平A → 平A → 战技 → 平A。
    # _动作(player, "角色 1", 38, 108)
    # _平A(player, 41, 97)
    # _平A(player, 37, 284)
    # _动作(player, "战技", 34, 85)
    # _平A(player, 36, 100)

    # # 卡提收尾
    # # 按键：切角色 2 → 平A连段 → 大招 → 平A连段 → 大招收尾。
    # _动作(player, "角色 2", 49, 396)
    # _平A(player, 35, 130)
    # _平A(player, 32, 119)
    # _平A(player, 44, 100)
    # _平A(player, 36, 100)
    # _动作(player, "大招", 33, 225)
    # _平A(player, 31, 61)
    # _平A(player, 34, 152)
    # _平A(player, 38, 276)
    # _平A(player, 41, 296)
    # _平A(player, 44, 285)
    # _平A(player, 45, 471)
    # _平A(player, 46, 100)
    # _动作(player, "大招", 36, 408)
    # _平A(player, 27, 94)
    # _平A(player, 41, 130)
    # _平A(player, 47, 100)
    # _平A(player, 42, 290)
    # _平A(player, 31, 100)
    # _动作(player, "大招", 35)

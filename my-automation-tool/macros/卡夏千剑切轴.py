"""卡夏千剑切轴。

来源：卡夏千剑切会话的 events.csv 第 13–234 条事件（首尾均包含）。
当前角色槽位：1=千咲、2=卡提、3=夏空。
清洗规则：所有按住和等待已按 0.3 倍速还原；非大招操作后超过 500ms 的讲解停顿压缩为 100ms；
大招后的等待保留记录值。文字轴仅用于阅读对齐，所有记录到的按键均保留在代码中。
"""

NAME = "卡夏千剑切轴"          # 宏库中显示的名称
HOTKEY = "mouse_forward"       # 物理触发键：鼠标侧键 2
MODE = "down"                  # 按住触发键运行，松开后立即停止
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
    """长按鼠标左键执行重击。"""
    player.mouse_click("left", hold_ms=按住毫秒)
    if 等待毫秒:
        player.sleep(等待毫秒)


def run(player):
    # 剑切轴：卡ee千a夏a跳a卡a3a4千跳a夏a跳a卡a5ra2a3千跳a夏a跳z卡a4e变奏夏e变奏卡跳ara2千跳a夏a跳a卡a3a4千跳a夏a跳z卡a5ee千a夏a跳a卡a3a4千跳a夏a跳a卡a5R

    _动作(player, "战技", 27, 78)
    _动作(player, "战技", 30, 100)
    _动作(player, "角色 1", 40, 194)
    _平A(player, 29, 31)
    _平A(player, 26, 100)
    _动作(player, "角色 3", 33, 263)
    _平A(player, 28, 26)
    _平A(player, 35, 75)
    _动作(player, "跳跃", 27, 44)
    _平A(player, 34, 154)
    _平A(player, 37, 100)
    _动作(player, "角色 2", 30, 65)
    _平A(player, 23, 32)
    _平A(player, 33, 100)
    _动作(player, "角色 1", 30, 59)
    _动作(player, "跳跃", 34, 263)
    _平A(player, 29, 20)
    _平A(player, 37, 100)
    _动作(player, "角色 3", 26, 102)
    _平A(player, 30, 28)
    _平A(player, 31, 56)
    _动作(player, "跳跃", 32, 48)
    _平A(player, 26, 23)
    _平A(player, 29, 100)
    _动作(player, "角色 2", 36, 63)
    _平A(player, 27, 24)
    _平A(player, 30, 23)
    _平A(player, 30, 88)
    _平A(player, 26, 100)
    _动作(player, "大招", 35, 142)
    _平A(player, 23, 26)
    _平A(player, 25, 34)
    _平A(player, 24, 184)
    _平A(player, 26, 100)
    _动作(player, "角色 1", 30, 72)
    _动作(player, "跳跃", 31, 59)
    _平A(player, 25, 25)
    _平A(player, 29, 100)
    _动作(player, "角色 3", 35, 92)
    _平A(player, 21, 39)
    _平A(player, 26, 445)
    _动作(player, "跳跃", 30, 43)
    _重击(player, 159, 100)
    _动作(player, "角色 2", 37, 283)
    _平A(player, 33, 34)
    _平A(player, 37, 298)
    _动作(player, "战技", 36, 100)
    _动作(player, "角色 3", 34, 100)
    _动作(player, "战技", 37, 100)
    _动作(player, "角色 2", 43, 100)
    _重击(player, 175, 262)
    _动作(player, "跳跃", 28, 34)
    _平A(player, 37, 100)
    _动作(player, "大招", 37, 789)
    _动作(player, "角色 1", 36, 103)
    _动作(player, "跳跃", 37, 88)
    _平A(player, 27, 27)
    _平A(player, 30, 100)
    _动作(player, "角色 3", 37, 334)
    _平A(player, 24, 28)
    _平A(player, 33, 218)
    _动作(player, "跳跃", 33, 123)
    _平A(player, 33, 27)
    _平A(player, 32, 100)
    _动作(player, "角色 2", 34, 74)
    _平A(player, 25, 32)
    _平A(player, 33, 100)
    _动作(player, "角色 1", 35, 133)
    _动作(player, "跳跃", 34, 109)
    _平A(player, 23, 32)
    _平A(player, 26, 100)
    _动作(player, "角色 3", 33, 142)
    _平A(player, 29, 26)
    _平A(player, 34, 202)
    _动作(player, "跳跃", 37, 68)
    _重击(player, 160, 100)
    _动作(player, "角色 2", 35, 69)
    _平A(player, 24, 32)
    _平A(player, 26, 36)
    _平A(player, 33, 100)
    _动作(player, "战技", 37, 419)
    _动作(player, "战技", 27, 100)
    _动作(player, "角色 1", 42, 230)
    _平A(player, 29, 27)
    _平A(player, 25, 100)
    _动作(player, "角色 3", 35, 180)
    _平A(player, 28, 31)
    _平A(player, 35, 107)
    _动作(player, "跳跃", 31, 83)
    _平A(player, 35, 38)
    _平A(player, 39, 100)
    _动作(player, "角色 2", 42, 92)
    _平A(player, 28, 34)
    _平A(player, 40, 334)
    _平A(player, 22, 32)
    _平A(player, 29, 100)
    _动作(player, "角色 1", 40, 116)
    _动作(player, "跳跃", 34, 62)
    _平A(player, 24, 34)
    _平A(player, 34, 434)
    _动作(player, "角色 3", 32, 94)
    _平A(player, 31, 26)
    _平A(player, 36, 76)
    _动作(player, "跳跃", 31, 69)
    _平A(player, 27, 32)
    _平A(player, 35, 100)
    _动作(player, "角色 2", 43, 138)
    _平A(player, 32, 35)
    _平A(player, 32, 100)
    _动作(player, "大招", 35, 291)
    _动作(player, "大招", 37)

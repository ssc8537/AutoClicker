"""卡提、夏空、千咲启动轴。

参数速查（单位：毫秒）：

- 卡提：切人后等待 20–30；跳后等待 150；战技后等待 30；平A按住 37，段内间隔为 60、180 或 20。
- 夏空：切人后常用等待 100；声骸后直接接平A；平A按住 37、间隔 150；跳后等待 93；
  重击长按 240、重击后等待 10；大招按住 20，每次后等待 500，再额外等待 380。
- 千咲：切人后等待 20；平A按住 37，段内间隔为 220、200 或 180；跳后等待 33；
  强化战技后等待 50。

后续新增连招时，优先参考对应角色的现有参数；新实测值优先。
"""

NAME = "卡夏千9秒启动"       # 宏库中显示的名称
HOTKEY = 'mouse_forward'        # 物理触发键：鼠标侧键 1
MODE = 'down'                # 按住侧键运行，松开后立即请求停止
COUNT = 1                     # 每次触发只执行一轮 run(player)
SPEED = 1.0                   # 等待速度倍率
ENABLED = True               # 当前未启用

def _动作(player, 动作名称, 按住毫秒, 等待毫秒=0):
    """发送共享动作。"""
    player.按键(动作名称, hold_ms=按住毫秒)
    if 等待毫秒:
        player.sleep(等待毫秒)


def _平A(player, 按住毫秒, 等待毫秒=0):
    """按一次平A（鼠标左键）。"""
    player.mouse_click("left", hold_ms=按住毫秒)
    if 等待毫秒:
        player.sleep(等待毫秒)


def _重击(player, 按住毫秒, 等待毫秒=0):
    """以长按鼠标左键执行一次重击；参数均为正常速度毫秒。"""
    player.mouse_click("left", hold_ms=按住毫秒)
    if 等待毫秒:
        player.sleep(等待毫秒)


def run(player):
    # 本文件只对应启动轴：千咲EA3 → 卡提跳E声骸 → 夏空声骸A4跳A → 千咲A4跳A → 夏空A4跳A → 千咲大招。
    # 千咲瞬间--强E 夏空A4跳Z 千咲锯A23 卡提A23 千咲终结 卡提A4 夏空R延千 延卡
    # 卡提跳A开大-手动操作
    # 角色映射：1=千咲、2=卡提、3=夏空。

    # 启动：千咲 E + A3。
    player.sleep(20)
    _动作(player, "战技", 26, 30)
    for _ in range(3):
        _平A(player, 31, 60)

    # 卡提 跳 + E 声骸
    _动作(player, "角色 2", 33, 30)
    _动作(player, "跳跃", 32, 150)
    _动作(player, "战技", 34, 30)
    _动作(player, "声骸", 20, 0)

    # 夏空 A4 声骸 跳 A。
    _动作(player, "角色 3", 33, 100)
    for _ in range(4):
        _平A(player, 37, 150)
    _动作(player, "声骸", 20, 0)
    _动作(player, "跳跃", 41, 93)
    for _ in range(2):
        _平A(player, 37, 100)

    # 千咲 A4 跳 A。
    _动作(player, "角色 1", 37, 20)
    for _ in range(4):
        _平A(player, 37, 220)
    _动作(player, "跳跃", 41, 33)
    for _ in range(2):
        _平A(player, 37, 100)

    # 夏空 A4 跳 A。
    _动作(player, "角色 3", 33, 100)
    for _ in range(4):
        _平A(player, 37, 150)
    _动作(player, "跳跃", 41, 93)
    for _ in range(2):
        _平A(player, 37, 100)

    # 千咲 大招 强化E。
    _动作(player, "角色 1", 37, 20)
    for _ in range(4):
        _动作(player, "大招", 20, 500)
        player.sleep(300)
    #########################################################################################################
    # 上面可作为阶段一
    # 千咲强化E
    for _ in range(3):
        _动作(player, "战技", 20, 50)

    # 夏空A4 跳 Z重击
    _动作(player, "角色 3", 33, 100)
    for _ in range(4):
        _平A(player, 37, 150)
    _动作(player, "跳跃", 41, 93)
    _重击(player, 240, 10)

    # 千咲锯A23
    _动作(player, "角色 1", 37, 20)
    for _ in range(4):
        _平A(player, 37, 210)

    # 卡提A23
    _动作(player, "角色 2", 33, 20)
    for _ in range(4):
        _平A(player, 37, 180)

    # 千咲终结
    _动作(player, "角色 1", 37, 20)
    for _ in range(4):
        _平A(player, 37, 180)

    # 卡提A4
    _动作(player, "角色 2", 33, 20)
    for _ in range(2):
        _平A(player, 37, 20)

    # 夏空 R 延千 延卡
    _动作(player, "角色 3", 33, 20)
    for _ in range(4):
        _动作(player, "大招", 20, 500)
        player.sleep(380)
    _动作(player, "角色 1", 37, 20)
    for _ in range(8):
        _动作(player, "角色 2", 37, 105)

    # 卡提跳A开大-手动操作

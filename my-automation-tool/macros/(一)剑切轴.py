NAME = "（一）剑切轴"  # 宏库中显示的脚本名称
HOTKEY = 'backslash'             # 物理触发键：鼠标侧键 1
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

def _闪避(player, 按住毫秒, 等待毫秒=0):
    """点击鼠标右键执行文字轴中的“闪”。"""
    player.mouse_click("right", hold_ms=按住毫秒)
    if 等待毫秒:
        player.sleep(等待毫秒)

def run(player):
    # 千咲EA 大卡A34举剑 千咲A出剪刀 大卡A5劈下 R变小卡一直平A
    # 手动操作-小卡A一套 Z重 下落 R切大卡A到开大
    # 角色映射：1=卡提、2=夏空、3=千咲

    # 千咲EA
    _动作(player, "角色 3", 37, 20)
    _动作(player, "战技", 34, 30)
    for _ in range(4):
        _平A(player, 37, 180)

    # 大卡A34举剑
    _动作(player, "角色 1", 33, 20)
    for _ in range(4):
        _平A(player, 37, 220)

    # 千咲A出剪刀
    _动作(player, "角色 3", 37, 20)
    for _ in range(4):
        _平A(player, 37, 200)

    # 大卡A5劈下
    _动作(player, "角色 1", 33, 20)
    for _ in range(4):
        _平A(player, 37, 40)

    # R变小卡一直平A
    _动作(player, "大招", 33, 20)
    for _ in range(10):
        _平A(player, 37, 200)

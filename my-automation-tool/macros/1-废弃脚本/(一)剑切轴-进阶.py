NAME = "（一）剑切轴-进阶"  # 宏库中显示的脚本名称
HOTKEY = 'backslash'             # 物理触发键：鼠标侧键 1
MODE = 'down'                # 按住侧键运行，松开后立即请求停止
COUNT = 1                     # 每次触发只执行一轮 run(player)
SPEED = 1.0                   # 等待速度倍率
ENABLED = False               # 当前未启用

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
    # 大卡EE 夏空A4跳A 千咲E 大卡A34举剑 夏空A4E 千咲A3
    # 大卡A5劈下 R变小卡A23 千咲A4剪刀 夏空R大招 小卡A4
    # 手动操作-E闪Z重下落 R切大卡A到开大
    # 角色映射：1=卡提、2=夏空、3=千咲

    # # 大卡EE
    # for _ in range(4):
    #     _动作(player, "战技", 33, 220)

    # 夏空A4跳A
    _动作(player, "角色 2", 33, 100)
    for _ in range(5):
        _平A(player, 37, 140)
    _动作(player, "跳跃", 41, 93)
    for _ in range(2):
        _平A(player, 37, 90)

    # 千咲E
    _动作(player, "角色 3", 37, 20)
    _动作(player, "战技", 34, 30)
    
    # 大卡A34举剑
    for _ in range(4):
        _动作(player, "角色 1", 33, 20) 
        _平A(player, 37, 140)

    # 夏空A4E
    _动作(player, "角色 2", 33, 60)
    for _ in range(4):
        _平A(player, 37, 140)
    _动作(player, "战技", 41, 30)

    # 千咲A3
    _动作(player, "角色 3", 37, 30)
    for _ in range(4):
        _平A(player, 37, 15)   

    # 大卡A5劈下
    _动作(player, "角色 1", 33, 30)
    for _ in range(4):
        _平A(player, 37, 30)

    # R变小卡A23
    _动作(player, "大招", 33, 60)
    for _ in range(4):
        _平A(player, 37, 190)

    # 千咲A4剪刀
    _动作(player, "角色 3", 37, 20)
    for _ in range(4):
        _平A(player, 37, 20)

    # 夏空R大招
    _动作(player, "角色 2", 33, 20)
    for _ in range(20):
        _动作(player, "大招", 33, 140)

    # 小卡A4 E闪
    _动作(player, "角色 1", 37, 20)
    for _ in range(4):
        _平A(player, 37, 40)
    for _ in range(4):
        _动作(player, "战技", 34, 0)
    for _ in range(4):
        _闪避(player, 33, 10)   

    # 手动操作-Z重下落 R切大卡A到开大










































































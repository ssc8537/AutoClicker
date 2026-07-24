NAME = "(一)夏空合轴千咲"   # 宏库中显示的脚本名称
HOTKEY = 'mouse_forward'          # 物理触发键：鼠标侧键 2
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
    # 夏空跳A 千咲EA大A 夏空A4跳A 千咲A出剪刀 夏空A4
    # 手动操作---战技Z重开大
    # 角色映射：1=卡提、2=夏空、3=千咲

    # 夏空跳 声骸 A
    _动作(player, "跳跃", 33, 30)
    for _ in range(2):
        _动作(player, "声骸", 36, 0)
    for _ in range(2):
        _平A(player, 37, 40)

    # 千咲EA大招A。
    _动作(player, "角色 3", 37, 20)
    _动作(player, "战技", 34, 30)
    for _ in range(2):
        _平A(player, 37, 100)
    for _ in range(4):
        _动作(player, "大招", 20, 500)
        player.sleep(300)
    for _ in range(2):
        _平A(player, 37, 120)

    # 夏空 A4 跳 A。
    _动作(player, "角色 2", 33, 60)
    for _ in range(4):
        _平A(player, 37, 140)
    _动作(player, "跳跃", 41, 93)
    for _ in range(2):
        _平A(player, 37, 100)

    # 千咲A出剪刀。
    _动作(player, "角色 3", 37, 20)
    for _ in range(4):
        _平A(player, 37, 220)

    # 夏空 A4
    _动作(player, "角色 2", 33, 100)
    for _ in range(4):
        _平A(player, 37, 150)

NAME = "(一)千咲合轴卡提"   # 宏库中显示的脚本名称
HOTKEY = 'mouse_back'             # 物理触发键：鼠标侧键 1
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
    # 千咲强E 卡提声骸A23 千咲锯A23 卡提A4 千咲锯终结 变奏卡提
    # 角色映射：1=卡提、2=夏空、3=千咲

    # 千咲强E
    for _ in range(4):
        _动作(player, "战技", 26, 60)

    # 卡提声骸A23
    _动作(player, "角色 1", 33, 20)
    _动作(player, "声骸", 20, 0)
    for _ in range(4):
        _平A(player, 37, 180)

    # 千咲锯A23
    _动作(player, "角色 3", 37, 20)
    for _ in range(4):
        _平A(player, 37, 210)

    # 卡提A4
    _动作(player, "角色 1", 33, 20)
    for _ in range(4):
        _平A(player, 37, 60)

    # 千咲终结
    for _ in range(6):
        _动作(player, "角色 3", 37, 70)
    for _ in range(4):
        _平A(player, 37, 80)

    # 延卡
    for _ in range(16):
        _动作(player, "角色 1", 33, 120)

NAME = "z-自动压枪宏"         # 宏库中显示的脚本名称
HOTKEY = 'backslash'          # 物理触发键：反斜杠键
MODE = 'down'                 # 按住触发键运行，松开立即停止
COUNT = 1                      # 每次按住最多执行一轮压枪
SPEED = 1.0                    # 等待速度倍率（本脚本的移动时长不受它影响）
ENABLED = True                 # 已启用，可直接进行本轮验收

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

def _压枪(player, 每次下移单位=1, 每步毫秒=15, 单轮最长毫秒=5_000):
    """按住鼠标左键持续开火，同时让鼠标按固定速度向下移动。"""
    player.mouse_down("left")
    try:
        # 单轮最多运行 5000ms，也就是 5 秒。
        # 5000 // 15 = 333，因此一轮实际约运行 4995ms。
        # COUNT=0 会在按住反斜杠时自动开始下一轮；松开后仍会立即停止。
        最多移动次数 = max(1, 单轮最长毫秒 // 每步毫秒)

        for _ in range(最多移动次数):
            # X=0 表示不左右移动；Y 为正数表示向下移动。
            player.mouse_move(0, 每次下移单位, duration_ms=每步毫秒)
    finally:
        # 无论正常停止还是发生错误，都必须松开左键，避免鼠标一直按住。
        player.mouse_up("left")


def run(player):
    """程序规定的统一入口：触发宏后，从这里调用上面的压枪动作。"""
    # 每 15ms 向下移动 1 个单位；想调整压枪力度，只需修改这一行。
    _压枪(player, 每次下移单位=1, 每步毫秒=15, 单轮最长毫秒=5_000)

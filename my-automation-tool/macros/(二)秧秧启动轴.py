NAME = "(一)秧秧启动轴"   # 宏库中显示的脚本名称
HOTKEY = 'mouse_forward'          # 物理触发键：鼠标侧键 2
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
    # 秧秧启动轴：1=秧秧、2=千咲、3=穗穗。
    # 左键=平A，E=战技，Q=声骸，R=大招，空格=跳跃。
    # “释放”行只保留等待，不重复发送按键。

    # 执行块 1
    _平A(player, 50, 250)
    _平A(player, 50, 600)
    _平A(player, 50, 200)
    _平A(player, 50, 150)
    _动作(player, "角色 1", 50, 100)
    _平A(player, 50, 50)
    _动作(player, "角色 2", 50, 50)

    # 执行块 2
    _动作(player, "战技", 50, 250)
    _平A(player, 50, 250)
    _动作(player, "角色 1", 50, 50)
    _动作(player, "战技", 50, 200)
    _动作(player, "角色 3", 50, 50)
    _平A(player, 50, 400)
    _平A(player, 50)

    # 执行块 3
    _平A(player, 100, 200)
    _动作(player, "角色 2", 50, 50)
    _平A(player, 50, 200)
    _平A(player, 50, 250)
    _平A(player, 50, 50)
    _平A(player, 100, 450)

    # 执行块 4
    _动作(player, "角色 1", 50, 600)
    _平A(player, 50, 800)
    _平A(player, 50, 250)
    _动作(player, "角色 3", 50, 50)
    _动作(player, "战技", 50, 250)
    _动作(player, "角色 2", 50, 200)

    # 执行块 5
    _平A(player, 50, 550)
    _动作(player, "跳跃", 50, 100)
    _平A(player, 50, 10)
    _动作(player, "角色 1", 50, 50)
    _平A(player, 50, 850)
    _动作(player, "声骸", 25)

    # 执行块 6
    _动作(player, "声骸", 50, 4354)
    _动作(player, "声骸", 50)
    _平A(player, 50)
    player.sleep(800)  # 文本“3 释放”只表示等待
    player.sleep(50)   # 文本“左键 释放”只表示等待
    _平A(player, 250, 50)
    _平A(player, 200, 50)
    _动作(player, "角色 2", 1)  # 文本 0ms，API 要求 >0，按 1ms 发送
    _动作(player, "声骸", 1)    # 文本 0ms，API 要求 >0，按 1ms 发送

    # 执行块 7
    _动作(player, "大招", 50, 3700)
    _动作(player, "战技", 50)
    _动作(player, "角色 3", 50, 50)
    _平A(player, 50, 400)
    _平A(player, 50, 450)
    _动作(player, "角色 2", 50, 50)

    # 执行块 8
    _平A(player, 1150)
    _平A(player, 1)  # 文本 0ms，API 要求 >0，按 1ms 发送
    _动作(player, "声骸", 50, 50)
    _平A(player, 600, 650)
    _动作(player, "角色 2", 50, 50)
    _平A(player, 300)

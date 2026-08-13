NAME = '快速-1234E左键'          # 宏库中显示的脚本名称
HOTKEY = 'mouse_back'         # 物理触发键：鼠标侧键 1（可自行修改）
MODE = 'down'                 # 按住侧键运行，松开后立即请求停止
COUNT = 0                     # 每次触发只执行一轮 run(player)
SPEED = 1.0                   # 等待速度倍率
ENABLED = False                # 当前启用

def _点击(player, key, hold_ms=20, wait_ms=0):
    """
    点击一个物理键或鼠标键，并在点击后等待指定毫秒。

    参数：
        player: 宏播放器对象
        key: 物理键内部值（如 '1', 'e', 'mouse_left' 等）
        hold_ms: 按键按下的持续时间（毫秒）
        wait_ms: 按键抬起后的等待时间（毫秒）
    """
    if key == "mouse_left":
        player.mouse_click("left", hold_ms=hold_ms)
    else:
        player.tap(key, hold_ms=hold_ms)
    if wait_ms:
        player.sleep(wait_ms)

def run(player):
    # 按顺序依次点击：1、2、3、4、E、Q、F、左键
    # 每次按键后等待 60 毫秒（由 _点击 的默认 wait_ms=60 实现）

    # 第 1 步：点击数字键 1
    _点击(player, "1")
    # 第 2 步：点击数字键 2
    _点击(player, "2")
    # 第 3 步：点击数字键 3
    _点击(player, "3")
    # 第 4 步：点击数字键 4
    _点击(player, "4")
    # 第 5 步：点击字母键 E
    _点击(player, "e")
    # # 第 6 步：点击字母键 Q
    # _点击(player, "q")
    # # 第 7 步：点击字母键 F
    # _点击(player, "f")
    
    # 第 8 步：点击鼠标左键
    for _ in range(4):
        _点击(player, "mouse_left")

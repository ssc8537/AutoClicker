"""由“（一）剑切轴.json”只读等价转换；不包含识别或窗口绑定。"""

NAME = "（一）剑切轴"  # 宏库中显示的脚本名称
HOTKEY = 'numpad0'     # 物理触发键：小键盘 0
MODE = 'down'          # 按住小键盘 0 运行，松开后请求停止
COUNT = 0              # 0 表示持续重复 run，直到松开或手动停止
SPEED = 1.0            # 等待速度倍率；只影响 player.sleep()
ENABLED = False        # False 表示当前默认不启用此宏


def _点击(player, key):
    """点击一个物理键，并把原随机点击时间固定为中值 15ms。"""
    # 鼠标左键必须调用鼠标 API；其他键统一使用键盘 tap API。
    if key == "mouse_left":
        player.mouse_click("left", hold_ms=15)
    else:
        player.tap(key, hold_ms=15)
    # 每次辅助点击自带 15ms 基础等待；调用处的 sleep 是额外间隔。
    player.sleep(15)


def run(player):
    # 每次进入 run 都执行一整轮；可修改 range(...) 中的数字调整该段次数。
    # 切千咲-E-A，5 次。
    for _ in range(5):
        _点击(player, "3")
        player.sleep(50)
        _点击(player, "e")
        player.sleep(50)
        _点击(player, "mouse_left")
        player.sleep(50)

    # 切卡提-A，8 次。
    for _ in range(8):
        _点击(player, "1")
        player.sleep(50)
        _点击(player, "mouse_left")
        player.sleep(50)

    # 切千咲-A打出剪刀，3 次。
    for _ in range(3):
        _点击(player, "3")
        player.sleep(50)
        _点击(player, "mouse_left")
        player.sleep(50)

    player.sleep(400)

    # 切卡提-A，7 次；原 JSON 的左键后没有额外显式等待。
    for _ in range(7):
        _点击(player, "1")
        player.sleep(30)
        _点击(player, "mouse_left")

    player.sleep(100)
    _点击(player, "r")

    # 小卡提-A，1000 次。按下模式松开触发键时仍可中断，不必等满 1000 次。
    for _ in range(1000):
        _点击(player, "mouse_left")
        player.sleep(10)

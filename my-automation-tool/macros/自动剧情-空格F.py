NAME = '自动剧情-空格F'                 # 宏库中显示的脚本名称
HOTKEY = 'mouse_back'            # 物理触发键：鼠标侧键 1（可自行修改为其他内部值）
MODE = 'down'                    # 按住触发键运行，松开立即停止
COUNT = 1                        # 每次触发只执行一轮
SPEED = 1.0                      # 等待速度倍率（仅影响 player.sleep）
ENABLED = True
WHEEL = True                   # 启用此宏

def run(player):
    # 步骤1：按下空格键（跳跃）
    player.tap("space", hold_ms=20)

    # 步骤2：等待 30 毫秒
    player.sleep(30)

    # 步骤3：按下 F 键
    player.tap("f", hold_ms=20)
NAME = '新宏6'
HOTKEY = "f9"
MODE = "switch"
COUNT = 1
SPEED = 1.0

def run(player):
    player.切换(1)
    player.sleep(10000)
    player.切换(2)
    player.切换(3)
    player.战技()
    player.声骸()
    player.大招()
    player.跳跃()
    player.处决()
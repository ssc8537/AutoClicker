NAME = '新宏6'
HOTKEY = "f9"
MODE = "switch"
COUNT = 1
SPEED = 1.0

def run(player):
    player.mouse_down("left")
    player.sleep(5000)
    player.mouse_up("left")
    player.mouse_click("right")
    player.mouse_repeat(3, "left", interval_ms=100)
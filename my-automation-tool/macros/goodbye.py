NAME = "goodbye"
HOTKEY = "f9"
MODE = "down"
COUNT = 0
SPEED = 1.0


def run(player):
    for key in ("g", "o", "o", "d", "b", "y", "e", "n", "b"):
        player.tap(key)
        player.sleep(50)

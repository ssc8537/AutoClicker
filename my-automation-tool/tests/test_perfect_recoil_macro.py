import unittest
from pathlib import Path

from src.core.script_engine import load_python_macro


class _PhysicalLeftPlayer:
    def __init__(self):
        self.pressed = False
        self.sleeps = []
        self.moves = []
        self.mouse_edges = []

    def is_physical_pressed(self, key):
        if key != "mouse_left":
            raise AssertionError(key)
        return self.pressed

    def sleep(self, milliseconds):
        self.sleeps.append(milliseconds)
        self.pressed = True

    def mouse_move(self, x, y, duration_ms=0):
        self.moves.append((x, y, duration_ms))
        if len(self.moves) == 9:
            self.pressed = False

    def mouse_down(self, button):
        self.mouse_edges.append(("down", button))

    def mouse_up(self, button):
        self.mouse_edges.append(("up", button))


class PerfectRecoilMacroTests(unittest.TestCase):
    def test_backslash_toggles_listener_and_physical_left_controls_movement(self):
        path = Path(__file__).parents[1] / "macros" / "z-完美压枪宏.py"
        macro = load_python_macro(path)
        self.assertEqual((macro.hotkey, macro.mode, macro.count), ("backslash", "switch", 0))

        player = _PhysicalLeftPlayer()
        macro.run(player)

        self.assertEqual(player.sleeps[0], 10)
        self.assertTrue(90 <= player.sleeps[1] <= 110)
        self.assertEqual(len(player.moves), 9)
        self.assertTrue(all(y > 0 and duration > 0 for _x, y, duration in player.moves))
        self.assertEqual(player.mouse_edges, [
            ("down", "left"),
            ("up", "left"),
            ("down", "left"),
            ("up", "left"),
        ])


if __name__ == "__main__":
    unittest.main()

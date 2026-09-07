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

    def mouse_click(self, button, hold_ms=10):
        self.mouse_edges.append(("down", button))
        self.mouse_edges.append(("up", button))


class PerfectRecoilMacroTests(unittest.TestCase):
    def test_backslash_toggles_listener_and_physical_left_controls_movement(self):
        path = Path(__file__).parents[1] / "macros" / "z-完美压枪宏.py"
        macro = load_python_macro(path)
        self.assertEqual((macro.hotkey, macro.mode, macro.count), ("backslash", "switch", 0))

        player = _PhysicalLeftPlayer()
        macro.run(player)

        # 当前宏先补一次平A点击（等待 10ms + 点击后等 30ms），再进入压枪；
        # 第 8 步点射重置等待 100±10ms。
        self.assertEqual(player.sleeps[0], 10)
        self.assertEqual(player.sleeps[1], 30)
        self.assertTrue(90 <= player.sleeps[2] <= 110)
        self.assertEqual(len(player.moves), 9)
        self.assertTrue(all(y > 0 and duration > 0 for _x, y, duration in player.moves))
        self.assertEqual(player.mouse_edges, [
            ("down", "left"),   # 平A 点击
            ("up", "left"),
            ("down", "left"),   # 压枪开始
            ("up", "left"),     # 第 8 步点射重置
            ("down", "left"),
            ("up", "left"),     # 物理松开后 finally 释放
        ])


if __name__ == "__main__":
    unittest.main()

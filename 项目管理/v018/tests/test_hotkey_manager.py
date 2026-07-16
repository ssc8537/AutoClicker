import unittest
from types import SimpleNamespace

from src.core.hotkey_manager import HotkeyManager, TriggerMode


class HotkeyManagerTests(unittest.TestCase):
    def make_handler(self, mode, stop_on_release=True):
        started = []
        stopped = []
        manager = HotkeyManager()
        manager.global_disabled = False
        manager.is_mouse_over_window = lambda: False
        manager.register(
            "f9", lambda: started.append("start"), mode, lambda: stopped.append("stop"),
            stop_on_release=stop_on_release,
        )
        return manager, manager._make_handler("f9"), started, stopped

    def event(self, event_type):
        return SimpleNamespace(event_type=event_type)

    def test_down_starts_on_press_and_stops_on_release(self):
        _, handler, started, stopped = self.make_handler(TriggerMode.DOWN)
        handler(self.event("down"))
        handler(self.event("up"))
        self.assertEqual(started, ["start"])
        self.assertEqual(stopped, ["stop"])

    def test_down_finite_count_does_not_stop_on_release(self):
        _, handler, started, stopped = self.make_handler(
            TriggerMode.DOWN, stop_on_release=False
        )
        handler(self.event("down"))
        handler(self.event("up"))
        self.assertEqual(started, ["start"])
        self.assertEqual(stopped, [])

    def test_switch_toggles_on_each_physical_press(self):
        _, handler, started, stopped = self.make_handler(TriggerMode.SWITCH)
        handler(self.event("down"))
        handler(self.event("up"))
        handler(self.event("down"))
        self.assertEqual(started, ["start"])
        self.assertEqual(stopped, ["stop"])

if __name__ == "__main__":
    unittest.main()

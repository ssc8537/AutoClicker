import unittest
from types import SimpleNamespace

from src.core.hotkey_manager import HotkeyManager, TriggerMode


class HotkeyManagerTests(unittest.TestCase):
    def make_handler(self, mode):
        started = []
        stopped = []
        manager = HotkeyManager()
        manager.global_disabled = False
        manager.is_mouse_over_window = lambda: False
        manager.register("f9", lambda: started.append("start"), mode, lambda: stopped.append("stop"))
        return manager, manager._make_handler("f9"), started, stopped

    def event(self, event_type):
        return SimpleNamespace(event_type=event_type)

    def test_down_starts_on_press_and_stops_on_release(self):
        _, handler, started, stopped = self.make_handler(TriggerMode.DOWN)
        handler(self.event("down"))
        handler(self.event("up"))
        self.assertEqual(started, ["start"])
        self.assertEqual(stopped, ["stop"])

    def test_switch_toggles_on_each_physical_press(self):
        _, handler, started, stopped = self.make_handler(TriggerMode.SWITCH)
        handler(self.event("down"))
        handler(self.event("up"))
        handler(self.event("down"))
        self.assertEqual(started, ["start"])
        self.assertEqual(stopped, ["stop"])

    def test_up_starts_on_release(self):
        _, handler, started, stopped = self.make_handler(TriggerMode.UP)
        handler(self.event("down"))
        handler(self.event("up"))
        self.assertEqual(started, ["start"])
        self.assertEqual(stopped, [])


if __name__ == "__main__":
    unittest.main()

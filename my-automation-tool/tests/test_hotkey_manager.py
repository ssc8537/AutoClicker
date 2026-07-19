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

    def test_second_hotkey_can_start_while_first_execution_is_active(self):
        started = []
        manager = HotkeyManager()
        manager.global_disabled = False
        manager.is_mouse_over_window = lambda: False
        manager.register("f1", lambda: started.append("f1"), TriggerMode.DOWN)
        manager.register("f3", lambda: started.append("f3"), TriggerMode.DOWN)
        first = manager._make_handler("f1")
        second = manager._make_handler("f3")
        first(self.event("down"))
        second(self.event("down"))
        second(self.event("up"))
        self.assertEqual(started, ["f1", "f3"])
        manager.mark_finished("f1")
        second(self.event("down"))
        self.assertEqual(started, ["f1", "f3", "f3"])

if __name__ == "__main__":
    unittest.main()

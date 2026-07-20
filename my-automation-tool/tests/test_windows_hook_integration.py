import os
import threading
import time
import unittest

from src.core.hotkey_manager import HotkeyManager
from src.core.input_simulator import (
    KEYEVENTF_KEYDOWN,
    KEYEVENTF_KEYUP,
    _make_kb_input,
    _send_input,
)


@unittest.skipUnless(
    os.name == "nt" and os.environ.get("MYAUTOPLAYER_RUN_LIVE_HOOK_TEST") == "1",
    "仅在明确启用时发送一次隔离的 F24 Windows 输入",
)
class WindowsHookIntegrationTests(unittest.TestCase):
    def test_unmarked_f24_toggles_the_real_global_hook_within_one_second(self):
        manager = HotkeyManager()
        manager.set_global_disable_key("f24")
        toggled = threading.Event()
        edges = []
        queue_event = manager._queue_physical_event
        manager._queue_physical_event = lambda key, pressed: (
            edges.append((key, pressed)), queue_event(key, pressed)
        )[-1]
        manager.on_toggle(lambda _disabled: toggled.set())
        manager.start()
        try:
            time.sleep(0.1)
            down = _make_kb_input(0x87, KEYEVENTF_KEYDOWN)
            up = _make_kb_input(0x87, KEYEVENTF_KEYUP)
            down.union.ki.dwExtraInfo = 0
            up.union.ki.dwExtraInfo = 0
            self.assertEqual(_send_input(down, up), 2)
            self.assertTrue(toggled.wait(1.0), f"真实 hook 边沿={edges!r}")
            self.assertFalse(manager.global_disabled)
        finally:
            manager.stop()


if __name__ == "__main__":
    unittest.main()

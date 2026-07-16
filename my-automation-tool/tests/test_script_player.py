import threading
import time
import unittest

from src.core.script_player import ScriptInterrupted, ScriptPlayer


class ScriptPlayerTests(unittest.TestCase):
    def test_tap_sends_physical_down_and_up(self):
        events = []
        player = ScriptPlayer(
            threading.Event(), 1.0,
            press=lambda key: events.append(("down", key)),
            release=lambda key: events.append(("up", key)),
        )
        player.tap("h", hold_ms=1)
        self.assertEqual(events, [("down", "h"), ("up", "h")])

    def test_stop_during_tap_releases_key(self):
        events = []
        stop_event = threading.Event()
        player = ScriptPlayer(
            stop_event, 1.0,
            press=lambda key: events.append(("down", key)),
            release=lambda key: events.append(("up", key)),
        )
        worker = threading.Thread(target=lambda: self._tap_and_capture(player, events))
        worker.start()
        deadline = time.monotonic() + 1.0
        while ("down", "h") not in events and time.monotonic() < deadline:
            time.sleep(0.005)
        stop_event.set()
        worker.join(1.0)
        self.assertEqual(events[:2], [("down", "h"), ("up", "h")])
        self.assertIn("interrupted", events)

    def test_sleep_scales_with_speed_and_is_interruptible(self):
        player = ScriptPlayer(threading.Event(), 2.0)
        start = time.monotonic()
        player.sleep(40)
        self.assertLess(time.monotonic() - start, 0.06)

    @staticmethod
    def _tap_and_capture(player, events):
        try:
            player.tap("h", hold_ms=5000)
        except ScriptInterrupted:
            events.append("interrupted")


if __name__ == "__main__":
    unittest.main()

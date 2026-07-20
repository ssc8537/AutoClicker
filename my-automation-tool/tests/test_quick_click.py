import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from src.core.quick_click import (
    QuickClickController,
    QuickClickSettings,
    QuickClickSettingsStore,
)


class QuickClickTests(unittest.TestCase):
    def test_missing_config_uses_reference_aligned_one_row_defaults(self):
        with tempfile.TemporaryDirectory() as directory:
            store = QuickClickSettingsStore(Path(directory) / "quick_click.json")
            self.assertEqual(store.load(), QuickClickSettings())

    def test_settings_round_trip_atomically(self):
        with tempfile.TemporaryDirectory() as directory:
            store = QuickClickSettingsStore(Path(directory) / "quick_click.json")
            expected = QuickClickSettings(True, "mouse_back", "switch", 130)
            store.save(expected)
            self.assertEqual(store.load(), expected)

    def test_worker_uses_interruptible_wait_and_always_releases(self):
        pressed = threading.Event()
        calls = []
        controller = QuickClickController()
        controller.configure(QuickClickSettings(True, "mouse_left", "down", 10000))
        with patch.object(
            controller,
            "_input_functions",
            return_value=(lambda: (calls.append("down"), pressed.set()), lambda: calls.append("up")),
        ):
            controller.start(1)
            self.assertTrue(pressed.wait(1.0))
            start = time.monotonic()
            controller.stop(2)
            controller.shutdown()
            self.assertLess(time.monotonic() - start, 0.5)
        self.assertEqual(calls, ["down", "up"])
        self.assertFalse(controller.is_running())


if __name__ == "__main__":
    unittest.main()

import json
import tempfile
import unittest
from pathlib import Path

from src.core.replay_settings import ReplaySettings, ReplaySettingsStore


class ReplaySettingsTests(unittest.TestCase):
    def test_defaults_are_portable_performance_first_values(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            store = ReplaySettingsStore(root / "settings.json", root / "captures")
            self.assertEqual(
                store.load(),
                ReplaySettings((root / "captures").resolve(), 10, "1080p", "gpu"),
            )

    def test_round_trip_keeps_absolute_directory_duration_and_quality(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            store = ReplaySettingsStore(root / "settings.json", root / "captures")
            core = (root / "myautoplayer-native-replay.exe").resolve()
            expected = ReplaySettings(
                (root / "视频").resolve(),
                30,
                "720p",
                "cpu",
                60,
                2,
                core,
                True,
                "device-123",
                "USB 麦克风",
                150,
            )
            self.assertEqual(store.save(expected), expected)
            self.assertEqual(store.load(), expected)
            raw = json.loads(store.path.read_text(encoding="utf-8"))
            self.assertEqual(raw["save_directory"], str(expected.save_directory))
            self.assertEqual(raw["encoder_mode"], "cpu")
            self.assertEqual(raw["fps"], 60)
            self.assertEqual(raw["monitor_index"], 2)
            self.assertEqual(raw["core_path"], str(core))
            self.assertTrue(raw["record_microphone"])
            self.assertEqual(raw["microphone_device_id"], "device-123")
            self.assertEqual(raw["microphone_device_name"], "USB 麦克风")
            self.assertEqual(raw["microphone_gain_percent"], 150)

    def test_invalid_values_fail_closed_to_defaults(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "settings.json"
            path.write_text(
                json.dumps(
                    {
                        "save_directory": "relative",
                        "duration_minutes": 99,
                        "quality": "4K",
                        "encoder_mode": "automatic",
                        "fps": 120,
                        "monitor_index": 0,
                        "record_microphone": "yes",
                        "microphone_device_id": 123,
                        "microphone_device_name": [],
                    }
                ),
                encoding="utf-8",
            )
            store = ReplaySettingsStore(path, root / "captures")
            self.assertEqual(
                store.load(),
                ReplaySettings((root / "captures").resolve(), 10, "1080p", "gpu"),
            )


if __name__ == "__main__":
    unittest.main()

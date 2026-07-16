import json
import tempfile
import unittest
from pathlib import Path

from src.core.macro_loader import MacroValidationError, load_test_macro


def valid_macro():
    return {
        "name": "hello world",
        "mode": "down",
        "count": 1,
        "speed": 1.0,
        "steps": [{"type": "key_tap", "key": "h", "hold_ms": 20, "delay_ms": 50}],
    }


class MacroLoaderTests(unittest.TestCase):
    def load(self, data):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "macro.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            return load_test_macro(path)

    def test_loads_valid_physical_keyboard_macro(self):
        macro = self.load(valid_macro())
        self.assertEqual(macro.mode, "down")
        self.assertEqual(macro.steps[0].key, "h")

    def test_rejects_unknown_field_and_action(self):
        data = valid_macro()
        data["hotkey"] = "f9"
        with self.assertRaises(MacroValidationError):
            self.load(data)
        data = valid_macro()
        data["steps"][0]["type"] = "text"
        with self.assertRaises(MacroValidationError):
            self.load(data)

    def test_rejects_invalid_count_speed_and_key(self):
        for field, value in (("count", 100), ("speed", 8.1)):
            data = valid_macro()
            data[field] = value
            with self.assertRaises(MacroValidationError):
                self.load(data)
        data = valid_macro()
        data["steps"][0]["key"] = "unsupported"
        with self.assertRaises(MacroValidationError):
            self.load(data)

    def test_rejects_malformed_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "macro.json"
            path.write_text("{", encoding="utf-8")
            with self.assertRaises(MacroValidationError):
                load_test_macro(path)


if __name__ == "__main__":
    unittest.main()

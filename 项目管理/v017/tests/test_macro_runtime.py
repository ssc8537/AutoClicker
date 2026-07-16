import json
import tempfile
import unittest
from pathlib import Path

from src.core.macro_loader import MacroValidationError
from src.core.macro_runtime import MacroRuntime


def macro_with_count(count):
    return {
        "name": "hello world",
        "mode": "down",
        "count": count,
        "speed": 1.0,
        "steps": [{"type": "key_tap", "key": "h", "hold_ms": 20, "delay_ms": 50}],
    }


class MacroRuntimeTests(unittest.TestCase):
    def test_reload_uses_saved_count_without_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "macro.json"
            path.write_text(json.dumps(macro_with_count(1)), encoding="utf-8")
            runtime = MacroRuntime(path)
            path.write_text(json.dumps(macro_with_count(0)), encoding="utf-8")
            self.assertEqual(runtime.reload().count, 0)
            self.assertEqual(runtime.current().count, 0)

    def test_invalid_save_keeps_last_valid_macro(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "macro.json"
            path.write_text(json.dumps(macro_with_count(1)), encoding="utf-8")
            runtime = MacroRuntime(path)
            path.write_text("{", encoding="utf-8")
            with self.assertRaises(MacroValidationError):
                runtime.reload()
            self.assertEqual(runtime.current().count, 1)


if __name__ == "__main__":
    unittest.main()

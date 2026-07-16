import tempfile
import textwrap
import threading
import unittest
from pathlib import Path

from src.core.script_engine import (
    PythonMacroRuntime,
    PythonMacroValidationError,
    load_python_macro,
    run_python_macro_once,
)


def script(count=1, mode="down", body="player.sleep(0)"):
    return textwrap.dedent(f'''\
        NAME = "test"
        HOTKEY = "f9"
        MODE = "{mode}"
        COUNT = {count}
        SPEED = 1.0

        def run(player):
            {body}
    ''')


class ScriptEngineTests(unittest.TestCase):
    def write(self, directory, content):
        path = Path(directory) / "macro.py"
        path.write_text(content, encoding="utf-8")
        return path

    def test_loads_valid_script_and_executes_one_round(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write(directory, script())
            macro = load_python_macro(path)
            self.assertEqual(macro.count, 1)
            self.assertTrue(run_python_macro_once(macro, threading.Event()))

    def test_reload_uses_saved_count_without_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write(directory, script(count=1))
            runtime = PythonMacroRuntime(path)
            self.write(directory, script(count=0))
            self.assertEqual(runtime.reload().count, 0)

    def test_invalid_script_keeps_last_valid_macro(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write(directory, script(count=1))
            runtime = PythonMacroRuntime(path)
            self.write(directory, "def run(:\n")
            with self.assertRaises(PythonMacroValidationError):
                runtime.reload()
            self.assertEqual(runtime.current().count, 1)

    def test_rejects_missing_run_and_invalid_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write(directory, "NAME = 'x'\n")
            with self.assertRaises(PythonMacroValidationError):
                load_python_macro(path)
            path = self.write(directory, script(mode="up"))
            with self.assertRaises(PythonMacroValidationError):
                load_python_macro(path)
            path = self.write(directory, script().replace('HOTKEY = "f9"', 'HOTKEY = "f10"'))
            with self.assertRaises(PythonMacroValidationError):
                load_python_macro(path)


if __name__ == "__main__":
    unittest.main()

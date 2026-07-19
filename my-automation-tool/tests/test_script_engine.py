import tempfile
import textwrap
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from src.core.script_engine import (
    PythonMacro,
    PythonMacroRuntime,
    PythonMacroValidationError,
    load_python_macro,
    run_python_macro_once,
)
from src.core.script_player import ScriptPlayer


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
            runtime.reload()
            self.write(directory, "def run(:\n")
            with self.assertRaises(PythonMacroValidationError):
                runtime.reload()
            self.assertEqual(runtime.current().count, 1)

    def test_rejects_missing_run_and_invalid_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write(directory, "NAME = 'x'\n")
            with self.assertRaises(PythonMacroValidationError):
                load_python_macro(path)

    def test_rejects_non_player_run_signature(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write(directory, script().replace("def run(player):", "def run(other):"))
            with self.assertRaises(PythonMacroValidationError):
                load_python_macro(path)

    def test_runtime_allows_safe_empty_selection(self):
        runtime = PythonMacroRuntime()
        self.assertIsNone(runtime.current())
        with self.assertRaises(PythonMacroValidationError):
            runtime.reload()

    def test_setting_selected_path_does_not_load_macro(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write(directory, script())
            runtime = PythonMacroRuntime()
            runtime.set_selected_path(path)
            self.assertEqual(runtime.selected_path(), path)
            self.assertIsNone(runtime.current())
            path = self.write(directory, script(mode="up"))
            with self.assertRaises(PythonMacroValidationError):
                load_python_macro(path)
            path = self.write(directory, script().replace('HOTKEY = "f9"', 'HOTKEY = "f12"'))
            with self.assertRaises(PythonMacroValidationError):
                load_python_macro(path)

    def test_macro_completion_releases_held_mouse_button(self):
        events = []
        player = self._tracking_player(events)
        macro = self._macro(lambda active_player: active_player.mouse_down("left"))
        with patch("src.core.script_engine.ScriptPlayer", return_value=player):
            self.assertTrue(run_python_macro_once(macro, threading.Event()))
        self.assertEqual(events, [("down", "left"), ("up", "left")])

    def test_macro_exception_releases_held_mouse_button(self):
        events = []
        player = self._tracking_player(events)

        def failing_run(active_player):
            active_player.mouse_down("right")
            raise RuntimeError("expected test error")

        with patch("src.core.script_engine.ScriptPlayer", return_value=player):
            with self.assertRaisesRegex(RuntimeError, "expected test error"):
                run_python_macro_once(self._macro(failing_run), threading.Event())
        self.assertEqual(events, [("down", "right"), ("up", "right")])

    @staticmethod
    def _macro(run):
        return PythonMacro("test", "f9", "switch", 1, 1.0, True, run)

    @staticmethod
    def _tracking_player(events):
        return ScriptPlayer(
            threading.Event(), 1.0,
            mouse_press=lambda button: events.append(("down", button)),
            mouse_release=lambda button: events.append(("up", button)),
        )


if __name__ == "__main__":
    unittest.main()

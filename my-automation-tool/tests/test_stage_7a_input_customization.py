import os
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from src.core import input_simulator
from src.core.global_hotkey import (
    DEFAULT_GLOBAL_HOTKEY,
    load_global_hotkey,
    save_global_hotkey,
)
from src.core.hotkey_manager import HotkeyManager
from src.core.input_keys import display_input_key, normalise_input_key
from src.core.input_simulator import _INPUT_MARKER, _make_kb_input, _make_mouse_input
from src.ui.trigger_key_edit import TriggerKeyEdit


class Stage7AInputCustomizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_default_global_key_is_the_chinese_backquote_key(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(load_global_hotkey(Path(directory) / "global_hotkey.ini"), DEFAULT_GLOBAL_HOTKEY)
        self.assertEqual(display_input_key(DEFAULT_GLOBAL_HOTKEY), "· / `")

    def test_global_key_round_trips_keyboard_and_mouse(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "global_hotkey.ini"
            self.assertEqual(save_global_hotkey("f12", path), "f12")
            self.assertEqual(load_global_hotkey(path), "f12")
            self.assertEqual(save_global_hotkey("mouse_forward", path), "mouse_forward")
            self.assertEqual(load_global_hotkey(path), "mouse_forward")

    def test_standard_keyboard_and_all_mouse_buttons_have_stable_names(self):
        self.assertEqual(normalise_input_key("`"), "backquote")
        self.assertEqual(normalise_input_key("F24"), "f24")
        self.assertEqual(normalise_input_key("numpad7"), "numpad7")
        for key in ("mouse_left", "mouse_right", "mouse_middle", "mouse_back", "mouse_forward"):
            self.assertEqual(normalise_input_key(key), key)

    def test_capture_box_accepts_f12_and_all_mouse_buttons(self):
        field = TriggerKeyEdit()
        selected = []
        field.hotkey_selected.connect(selected.append)
        field.show()
        QTest.mouseClick(field, Qt.MouseButton.LeftButton)
        QTest.keyClick(field, Qt.Key.Key_F12)
        self.assertEqual(selected[-1], "f12")
        for button, expected in (
            (Qt.MouseButton.LeftButton, "mouse_left"),
            (Qt.MouseButton.RightButton, "mouse_right"),
            (Qt.MouseButton.MiddleButton, "mouse_middle"),
            (Qt.MouseButton.BackButton, "mouse_back"),
            (Qt.MouseButton.ForwardButton, "mouse_forward"),
        ):
            QTest.mouseClick(field, Qt.MouseButton.LeftButton)
            QTest.mouseClick(field, button)
            self.assertEqual(selected[-1], expected)

    def test_mouse_global_key_toggles_without_any_macro_binding(self):
        manager = HotkeyManager()
        manager.set_global_disable_key("mouse_back")
        self.assertTrue(manager.global_disabled)
        manager._on_global_disable_pressed(True)
        manager._on_global_disable_pressed(False)
        self.assertFalse(manager.global_disabled)

    def test_all_sendinput_events_carry_the_project_marker(self):
        keyboard_input = _make_kb_input(0x41)
        self.assertEqual(keyboard_input.union.ki.dwExtraInfo, _INPUT_MARKER)
        self.assertNotEqual(keyboard_input.union.ki.wScan, 0)
        self.assertEqual(_make_mouse_input(0x0002).union.mi.dwExtraInfo, _INPUT_MARKER)

    def test_sendinput_failure_is_logged_for_game_compatibility_diagnosis(self):
        with patch.object(input_simulator, "_last_send_input_warning", 0.0), patch.object(
            input_simulator.ctypes.windll.user32,
            "SendInput",
            return_value=0,
        ), self.assertLogs("src.core.input_simulator", level="WARNING") as logs:
            sent = input_simulator._send_input(_make_mouse_input(0x0002))
            input_simulator._send_input(_make_mouse_input(0x0002))
        self.assertEqual(sent, 0)
        self.assertIn("SendInput 未完整发送", "\n".join(logs.output))
        self.assertEqual(len(logs.output), 1)

import unittest
from types import SimpleNamespace

from main import (
    _HotkeyDispatcher,
    _INSTRUCTION_TEXT,
    global_status_notification,
    show_startup_window,
)


class _FakeLabel:
    def __init__(self):
        self.text = None
        self.style = None

    def setText(self, value):
        self.text = value

    def setStyleSheet(self, value):
        self.style = value


class _FakeOsd:
    def __init__(self):
        self.calls = []

    def show_notification(self, text, success):
        self.calls.append((text, success))


class _FakePlayer:
    def __init__(self):
        self.stop_calls = 0

    def stop(self):
        self.stop_calls += 1


class _FakeSoundEffects:
    def __init__(self):
        self.calls = []

    def play_started(self):
        self.calls.append("started")

    def play_stopped(self):
        self.calls.append("stopped")


class _FakeWindow:
    def __init__(self):
        self.calls = []

    def show(self):
        self.calls.append("show")

    def raise_(self):
        self.calls.append("raise")

    def activateWindow(self):
        self.calls.append("activate")


class MainStatusTests(unittest.TestCase):
    def test_startup_window_is_shown_raised_and_activated(self):
        window = _FakeWindow()
        show_startup_window(window)
        self.assertEqual(window.calls, ["show", "raise", "activate"])

    def test_instruction_text_has_real_newlines(self):
        self.assertIn("\n", _INSTRUCTION_TEXT)
        self.assertNotIn("\\\\n", _INSTRUCTION_TEXT)

    def test_global_status_messages(self):
        self.assertEqual(global_status_notification(False), ("全局脚本已就绪", True))
        self.assertEqual(global_status_notification(True), ("全局脚本已禁用", False))

    def test_global_toggle_updates_label_and_osd(self):
        sounds = _FakeSoundEffects()
        target = SimpleNamespace(
            _status_label=_FakeLabel(), _osd_popup=_FakeOsd(), _sound_effects=sounds
        )
        _HotkeyDispatcher._apply_global_status(target, False)
        self.assertEqual(target._status_label.text, "● 热键已启用")
        self.assertEqual(target._osd_popup.calls, [("全局脚本已就绪", True)])
        _HotkeyDispatcher._apply_global_status(target, True)
        self.assertEqual(target._status_label.text, "● 热键已禁用")
        self.assertEqual(target._osd_popup.calls[-1], ("全局脚本已禁用", False))
        self.assertEqual(sounds.calls, ["started", "stopped"])

    def test_stop_osd_uses_the_macro_name_cached_at_start(self):
        player = _FakePlayer()
        target = SimpleNamespace(
            _players={"a": player},
            _running_names={"a": "新宏6"},
            _osd_popup=_FakeOsd(),
        )
        _HotkeyDispatcher._stop_f9(target, "a")
        self.assertEqual(player.stop_calls, 1)

    def test_natural_finish_keeps_the_started_macro_name_after_selection_changes(self):
        target = SimpleNamespace(
            _on_natural_finish=None,
            _players={"a": object()},
            _running_names={"a": "goodbye"},
            _osd_popup=_FakeOsd(),
        )
        _HotkeyDispatcher._on_player_finished(target, "a")
        self.assertEqual(target._osd_popup.calls, [("goodbye 宏已停止", False)])
        self.assertEqual(target._running_names, {})


if __name__ == "__main__":
    unittest.main()

import unittest
from types import SimpleNamespace

from main import _HotkeyDispatcher, _INSTRUCTION_TEXT, global_status_notification


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


class MainStatusTests(unittest.TestCase):
    def test_instruction_text_has_real_newlines(self):
        self.assertIn("\n", _INSTRUCTION_TEXT)
        self.assertNotIn("\\\\n", _INSTRUCTION_TEXT)

    def test_global_status_messages(self):
        self.assertEqual(global_status_notification(False), ("全局脚本已就绪", True))
        self.assertEqual(global_status_notification(True), ("全局脚本已禁用", False))

    def test_global_toggle_updates_label_and_osd(self):
        target = SimpleNamespace(_status_label=_FakeLabel(), _osd_popup=_FakeOsd())
        _HotkeyDispatcher._apply_global_status(target, False)
        self.assertEqual(target._status_label.text, "🟢 热键已启用")
        self.assertEqual(target._osd_popup.calls, [("全局脚本已就绪", True)])
        _HotkeyDispatcher._apply_global_status(target, True)
        self.assertEqual(target._status_label.text, "🔴 热键已禁用")
        self.assertEqual(target._osd_popup.calls[-1], ("全局脚本已禁用", False))

    def test_stop_osd_uses_the_macro_name_cached_at_start(self):
        target = SimpleNamespace(
            _player=_FakePlayer(),
            _execution_active=True,
            _running_macro_name="新宏6",
            _osd_popup=_FakeOsd(),
        )
        _HotkeyDispatcher._stop_f9(target)
        self.assertEqual(target._player.stop_calls, 1)
        self.assertEqual(target._osd_popup.calls, [("新宏6 宏已停止", False)])
        self.assertIsNone(target._running_macro_name)

    def test_natural_finish_keeps_the_started_macro_name_after_selection_changes(self):
        target = SimpleNamespace(
            _on_natural_finish=None,
            _execution_active=True,
            _running_macro_name="goodbye",
            _osd_popup=_FakeOsd(),
        )
        _HotkeyDispatcher._on_player_finished(target)
        self.assertEqual(target._osd_popup.calls, [("goodbye 宏已停止", False)])
        self.assertIsNone(target._running_macro_name)


if __name__ == "__main__":
    unittest.main()

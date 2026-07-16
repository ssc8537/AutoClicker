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


if __name__ == "__main__":
    unittest.main()

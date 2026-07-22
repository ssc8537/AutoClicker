import json
import os
import tempfile
import time
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from src.core.hotkey_manager import PhysicalInputEvent
from src.ui.key_monitor_window import (
    DEFAULT_MONITOR_KEYS,
    DETAIL_BACKGROUND_PRESETS,
    KeyMonitorWindow,
)


class KeyMonitorWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    @staticmethod
    def event(key: str, pressed: bool, timestamp: int) -> PhysicalInputEvent:
        return PhysicalInputEvent(key, pressed, 69, timestamp, 1, 2)

    def test_default_keys_highlight_and_show_hold_duration(self):
        self.assertEqual(
            [label for label, _rgb in DETAIL_BACKGROUND_PRESETS.values()],
            ["淡黑色", "淡白色", "淡樱粉", "天空蓝", "薄荷绿"],
        )
        with tempfile.TemporaryDirectory() as directory:
            window = KeyMonitorWindow(settings_path=Path(directory) / "keys.json")
            now = time.perf_counter_ns()
            window.observe_input(self.event("e", True, now))
            self.app.processEvents()
            self.assertIn("按下 大写 E", window._last_event.text())
            self.assertIn("#F3A8BE", window._buttons["e"].styleSheet())
            window.observe_input(self.event("e", False, now + 25_000_000))
            self.app.processEvents()
            self.assertIn("25.0 ms", window._hold_detail.text())
            self.assertIn("松开 大写 E", window._last_event.text())
            self.assertIn("按下时长 25.0 ms", window._last_event.text())
            self.assertIn("rgba(0,0,0,28)", window._buttons["e"].styleSheet())
            window.close()

    def test_old_explicit_key_list_keeps_the_users_exact_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "keys.json"
            path.write_text(json.dumps({"keys": ["3", "5", "7"]}), encoding="utf-8")
            window = KeyMonitorWindow(settings_path=path)
            self.assertEqual(window.keys, ("3", "5", "7"))
            self.assertEqual(window.extra_keys, ("5", "7"))
            window.close()

    def test_schema_two_migrates_defaults_plus_extras(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "keys.json"
            path.write_text(
                json.dumps({"schema": 2, "extra_keys": ["5", "7"]}),
                encoding="utf-8",
            )
            window = KeyMonitorWindow(settings_path=path)
            self.assertEqual(window.keys, (*DEFAULT_MONITOR_KEYS, "5", "7"))
            window.close()

    def test_selected_keys_and_recent_count_persist_and_defaults_can_be_removed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "keys.json"
            window = KeyMonitorWindow(settings_path=path)
            window.set_keys(["1", "e", "a", "mouse_middle"])
            window.set_recent_count(5)
            window.set_appearance("soft_white", 35, 12)
            self.assertEqual(window.keys, ("1", "e", "a", "mouse_middle"))
            self.assertNotIn("mouse_back", window._buttons)
            window.close()

            restored = KeyMonitorWindow(settings_path=path)
            self.assertEqual(restored.extra_keys, ("a", "mouse_middle"))
            self.assertEqual(restored.recent_count, 5)
            self.assertEqual(restored.keys, ("1", "e", "a", "mouse_middle"))
            self.assertEqual(restored.detail_background, "soft_white")
            self.assertEqual(restored.detail_opacity, 35)
            self.assertEqual(restored.window_opacity, 12)
            restored.close()

    def test_recent_events_are_detailed_and_limited_to_selected_count(self):
        with tempfile.TemporaryDirectory() as directory:
            window = KeyMonitorWindow(settings_path=Path(directory) / "keys.json")
            window.set_recent_count(3)
            now = time.perf_counter_ns()
            for index, key in enumerate(("1", "2", "3", "q")):
                timestamp = now + index * 20_000_000
                window.observe_input(self.event(key, True, timestamp))
                window.observe_input(self.event(key, False, timestamp + 10_000_000))
            self.app.processEvents()
            self.assertEqual(len(window._recent_events), 8)
            self.assertIn("松开 大写 3", window._recent_labels[0].text())
            self.assertIn("按下 大写 Q", window._recent_labels[1].text())
            self.assertIn("松开 大写 Q", window._recent_labels[2].text())
            self.assertIn("按下时长 10.0 ms", window._recent_labels[2].text())
            self.assertIn("background-color: rgba(24,30,43", window._recent_labels[0].styleSheet())
            self.assertRegex(window._recent_labels[0].text(), r"\d{2}:\d{2}:\d{2}:\d{3}")
            self.assertFalse(window._recent_labels[3].isVisible())
            window.close()

    def test_repeat_keydown_does_not_reset_hold_or_advance_sequence_color(self):
        with tempfile.TemporaryDirectory() as directory:
            window = KeyMonitorWindow(settings_path=Path(directory) / "keys.json")
            now = time.perf_counter_ns()
            window.observe_input(self.event("e", True, now))
            window.observe_input(self.event("e", True, now + 40_000_000))
            window.observe_input(self.event("e", False, now + 100_000_000))
            self.app.processEvents()
            self.assertEqual(window._press_sequence, 1)
            self.assertEqual(len(window._recent_events), 2)
            self.assertIn("100.0 ms", window._hold_detail.text())

            window.observe_input(self.event("q", True, now + 120_000_000))
            self.app.processEvents()
            self.assertIn("#F6C28B", window._buttons["q"].styleSheet())
            window.close()

    def test_overlapping_keys_show_order_and_remaining_pressed_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            window = KeyMonitorWindow(settings_path=Path(directory) / "keys.json")
            now = time.perf_counter_ns()
            window.observe_input(self.event("1", True, now))
            window.observe_input(self.event("q", True, now + 34_000_000))
            window.observe_input(self.event("1", False, now + 50_000_000))
            self.app.processEvents()
            self.assertIn("按下时长 50.0 ms", window._recent_labels[2].text())
            self.assertIn("距上一事件 +16.0 ms", window._recent_labels[2].text())
            self.assertIn("仍在按住：大写 Q", window._recent_labels[2].text())
            self.assertIn("同时按住：大写 1", window._recent_labels[1].text())
            window.close()

    def test_recent_events_read_oldest_at_top_and_newest_at_bottom(self):
        with tempfile.TemporaryDirectory() as directory:
            window = KeyMonitorWindow(settings_path=Path(directory) / "keys.json")
            window.set_recent_count(3)
            now = time.perf_counter_ns()
            for index, key in enumerate(("1", "2", "3", "q")):
                window.observe_input(self.event(key, True, now + index * 10_000_000))
            self.app.processEvents()

            self.assertIn("按下 大写 2", window._recent_labels[0].text())
            self.assertIn("按下 大写 3", window._recent_labels[1].text())
            self.assertIn("按下 大写 Q", window._recent_labels[2].text())
            self.assertIs(window._last_event, window._recent_labels[2])
            window.close()

    def test_event_history_wraps_and_arrow_keys_scroll_one_unit_for_all_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            window = KeyMonitorWindow(settings_path=Path(directory) / "keys.json")
            window.set_recent_count(10)
            now = time.perf_counter_ns()
            for index in range(5):
                pressed = now + index * 80_000_000
                window.observe_input(self.event("1", True, pressed))
                window.observe_input(self.event("q", True, pressed + 15_000_000))
                window.observe_input(self.event("1", False, pressed + 35_000_000))
                window.observe_input(self.event("q", False, pressed + 55_000_000))
            window.show()
            self.app.processEvents()
            window.resize(window.minimumSize())
            self.app.processEvents()

            self.assertTrue(all(label.wordWrap() for label in window._recent_labels))
            self.assertEqual(
                window._history_scroll.horizontalScrollBarPolicy(),
                Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
            )
            bar = window._history_scroll.verticalScrollBar()
            self.assertGreater(bar.maximum(), 0)
            self.assertGreaterEqual(
                window._recent_labels[0].height(),
                window._recent_labels[0].fontMetrics().height() * 2,
            )
            window._history_scroll.setFocus()
            QTest.keyClick(window._history_scroll, Qt.Key.Key_Down)
            self.assertEqual(bar.value(), min(bar.singleStep(), bar.maximum()))
            QTest.keyClick(window._history_scroll, Qt.Key.Key_Up)
            self.assertEqual(bar.value(), 0)

            for count in (3, 5, 10):
                window.set_recent_count(count)
                self.app.processEvents()
                self.assertEqual(
                    sum(not label.isHidden() for label in window._recent_labels), count
                )
            window.close()

    def test_transparent_surface_and_half_size_keep_all_default_tiles(self):
        with tempfile.TemporaryDirectory() as directory:
            window = KeyMonitorWindow(settings_path=Path(directory) / "keys.json")
            base = window._base_size
            window.show()
            self.app.processEvents()
            window.resize(window.minimumSize())
            self.app.processEvents()
            self.assertEqual(window.minimumWidth(), max(210, base.width() // 2))
            self.assertEqual(set(window._buttons), set(DEFAULT_MONITOR_KEYS))
            self.assertGreaterEqual(window._buttons["e"].width(), 32)
            self.assertLess(window._buttons["e"].width(), 66)
            self.assertIn("rgba(5,8,13,71)", window._surface.styleSheet())
            self.assertIn("rgba(255,255,255,225)", window._buttons["e"].styleSheet())
            self.assertIn("rgba(24,30,43", window._details_panel.styleSheet())
            self.assertRegex(window._clock_label.text(), r"^\d{2}:\d{2}:\d{2}:\d{3}$")
            self.assertEqual(set(window._resize_handles), {"top_left", "top_right", "bottom_left", "bottom_right"})
            bottom_right = window._resize_handles["bottom_right"]
            self.assertLessEqual(bottom_right.width(), 10)
            self.assertEqual(bottom_right.x(), window.width() - bottom_right.width() - 2)
            self.assertEqual(bottom_right.y(), window.height() - bottom_right.height() - 2)
            window.close()

    def test_window_position_is_remembered_and_restored_inside_the_screen(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "keys.json"
            area = self.app.primaryScreen().availableGeometry()
            target = QPoint(area.left() + 72, area.top() + 54)
            window = KeyMonitorWindow(settings_path=path)
            window.show()
            self.app.processEvents()
            window.move(target)
            window.close()
            self.app.processEvents()

            saved = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(saved["schema"], 5)
            self.assertEqual((saved["window_x"], saved["window_y"]), (target.x(), target.y()))

            restored = KeyMonitorWindow(settings_path=path)
            restored.show()
            self.app.processEvents()
            self.assertEqual(restored.pos(), target)
            restored.close()

    def test_offscreen_saved_position_is_clamped_to_current_display(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "keys.json"
            path.write_text(
                json.dumps({"schema": 5, "window_x": 999999, "window_y": 999999}),
                encoding="utf-8",
            )
            window = KeyMonitorWindow(settings_path=path)
            window.show()
            self.app.processEvents()
            area = self.app.primaryScreen().availableGeometry()
            self.assertGreaterEqual(window.x(), area.left())
            self.assertGreaterEqual(window.y(), area.top())
            self.assertLessEqual(window.frameGeometry().right(), area.right())
            self.assertLessEqual(window.frameGeometry().bottom(), area.bottom())
            window.close()


if __name__ == "__main__":
    unittest.main()

import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTabWidget,
)

from main import MainWindow


class UiShellTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = MainWindow.__new__(MainWindow)
        QMainWindow.__init__(self.window)
        self.window._setup_ui()

    def tearDown(self):
        self.window.deleteLater()

    def test_window_is_fixed_width_and_vertically_resizable(self):
        self.assertEqual(self.window.width(), 642)
        self.assertEqual(self.window.minimumWidth(), 642)
        self.assertEqual(self.window.maximumWidth(), 642)
        self.assertEqual(self.window.minimumHeight(), 510)
        self.assertGreaterEqual(self.window.maximumHeight(), 510)
        screen = QApplication.primaryScreen()
        self.assertIsNotNone(screen)
        self.assertEqual(
            self.window.frameGeometry().center(), screen.availableGeometry().center()
        )

    def test_four_tabs_default_to_macro_library(self):
        tabs = self.window.findChild(QTabWidget, "main_tabs")
        self.assertIsNotNone(tabs)
        self.assertEqual(tabs.currentIndex(), 0)
        self.assertEqual([tabs.tabText(index) for index in range(tabs.count())], ["宏库", "触发", "功能", "设置"])
        tabs.setCurrentIndex(2)
        self.assertEqual(tabs.currentIndex(), 2)

    def test_macro_and_trigger_pages_are_read_only(self):
        disabled_buttons = {
            button.text()
            for button in self.window.findChildren(QPushButton)
            if button.text() in {"新建", "编辑", "保存", "刷新", "导入", "导出", "删除", "保存触发设置"}
        }
        self.assertEqual(disabled_buttons, {"新建", "编辑", "保存", "刷新", "导入", "导出", "删除", "保存触发设置"})
        for button in self.window.findChildren(QPushButton):
            if button.text() in disabled_buttons:
                self.assertFalse(button.isEnabled())
        self.assertTrue(all(field.isReadOnly() for field in self.window.findChildren(QLineEdit)))

    def test_features_are_disabled_and_f2_is_only_a_label(self):
        feature_button = next(
            button
            for button in self.window.findChildren(QPushButton)
            if button.text() == "应用功能设置"
        )
        self.assertFalse(feature_button.isEnabled())
        combo_values = {
            combo.currentText() for combo in self.window.findChildren(QComboBox)
        }
        field_values = {field.text() for field in self.window.findChildren(QLineEdit)}
        self.assertIn("F2（仅占位）", combo_values)
        self.assertIn("仅 UI 占位，不注册", field_values)

    def test_candy_theme_is_applied(self):
        stylesheet = self.window.styleSheet()
        for color in ("#FDF", "#FFF5FF", "#FCE", "#FBE", "#FFF0FF"):
            self.assertIn(color, stylesheet)

    def test_complete_window_registers_only_f9_and_f12(self):
        runtime = Mock()
        runtime.current.return_value = SimpleNamespace(mode="switch", count=1)
        manager = Mock()

        with patch("main.HotkeyManager", return_value=manager), patch("main.OsdPopup"):
            window = MainWindow(runtime)

        self.assertEqual([call.args[0] for call in manager.register.call_args_list], ["f9"])
        manager.set_global_disable_key.assert_called_once_with("f12")
        manager.start.assert_called_once()
        window.deleteLater()

    def test_close_stops_and_cleans_up_dependencies(self):
        window = MainWindow.__new__(MainWindow)
        QMainWindow.__init__(window)
        window._dispatcher = Mock()
        window._hotkey_mgr = Mock()
        window._osd_popup = Mock()

        with patch("main.keyboard.unhook_all") as unhook_all:
            window.close()

        window._dispatcher.stop_active_execution.assert_called_once()
        unhook_all.assert_called_once()
        window._hotkey_mgr.stop.assert_called_once()
        window._osd_popup.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()

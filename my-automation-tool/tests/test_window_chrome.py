import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel, QMainWindow

from src.ui.window_chrome import application_icon, WindowChromeController, WindowTitleBar


class _TrackingWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.close_count = 0

    def closeEvent(self, event):
        self.close_count += 1
        event.accept()


class WindowChromeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = _TrackingWindow()
        self.window.setWindowTitle("MyAutoPlayer")

    def tearDown(self):
        self.window.hide()
        self.window.deleteLater()

    def test_title_bar_exposes_only_close_minimize_and_hide_actions(self):
        title_bar = WindowTitleBar(self.window)
        title = title_bar.findChild(QLabel, "window_title_label")
        self.assertEqual(title.text(), "我的自动播放器")
        calls = []
        title_bar.close_requested.connect(lambda: calls.append("close"))
        title_bar.minimize_requested.connect(lambda: calls.append("minimize"))
        title_bar.hide_requested.connect(lambda: calls.append("hide"))
        title_bar._close_button.click()
        title_bar._minimize_button.click()
        title_bar._hide_button.click()
        self.assertEqual(calls, ["close", "minimize", "hide"])

    def test_unavailable_tray_disables_hide_without_hiding_window(self):
        title_bar = WindowTitleBar(self.window)
        chrome = WindowChromeController(self.window, tray_available=lambda: False)
        chrome.install(title_bar)
        self.window.show()
        chrome.hide_window()
        self.assertIsNone(chrome.tray)
        self.assertFalse(title_bar._hide_button.isEnabled())
        self.assertTrue(self.window.isVisible())

    def test_tray_menu_hide_restore_minimize_and_exit(self):
        title_bar = WindowTitleBar(self.window)
        self.window.setWindowIcon(application_icon())
        chrome = WindowChromeController(self.window, tray_available=lambda: True)
        chrome.install(title_bar)
        self.window.show()
        self.assertIsNotNone(chrome.tray)
        self.assertFalse(self.window.windowIcon().isNull())
        self.assertEqual(chrome.tray.icon().cacheKey(), self.window.windowIcon().cacheKey())
        self.assertEqual(
            [action.text() for action in chrome.menu.actions()],
            ["显示主窗口", "隐藏主窗口", "退出程序"],
        )
        chrome.hide_window()
        self.assertFalse(self.window.isVisible())
        chrome.show_window()
        self.assertTrue(self.window.isVisible())
        chrome.minimize_window()
        self.assertTrue(self.window.isMinimized())
        chrome.exit_program()
        self.assertEqual(self.window.close_count, 1)


if __name__ == "__main__":
    unittest.main()

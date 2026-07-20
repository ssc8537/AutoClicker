import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QFontMetrics
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from src.ui.osd_window import OsdPopup


class OsdWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _popup(self, directory: str) -> OsdPopup:
        return OsdPopup(settings_path=Path(directory) / "settings.json")

    def test_long_macro_name_expands_or_wraps_beyond_the_old_fixed_width(self):
        with tempfile.TemporaryDirectory() as directory:
            popup = self._popup(directory)
            text = "秧秧、琳奈、千咲联合轴超长脚本名称 宏运行中"
            popup.show_notification(text, success=True)
            self.app.processEvents()

            self.assertEqual(popup._label.text(), text)
            self.assertTrue(popup.width() > 400 or popup._label.wordWrap())
            if popup._label.wordWrap():
                self.assertGreater(popup.height(), popup._MIN_HEIGHT)
            else:
                self.assertGreaterEqual(
                    popup._label.width(),
                    QFontMetrics(popup._label.font()).horizontalAdvance(text),
                )
            self.assertTrue(
                popup.windowFlags() & Qt.WindowType.WindowDoesNotAcceptFocus
            )
            self.assertTrue(popup.testAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents))
            popup.close()

    def test_extreme_name_wraps_and_grows_instead_of_clipping(self):
        with tempfile.TemporaryDirectory() as directory:
            popup = self._popup(directory)
            text = "特别长的完整脚本名称" * 30 + " 宏已停止"
            popup.show_notification(text, success=False)
            self.app.processEvents()

            screen = QApplication.primaryScreen()
            self.assertTrue(popup._label.wordWrap())
            self.assertGreater(popup.height(), popup._MIN_HEIGHT)
            if screen is not None:
                self.assertLessEqual(
                    popup.width(),
                    screen.availableGeometry().width() - (popup._SCREEN_MARGIN * 2),
                )
            popup.close()

    def test_formal_build_requests_case_aligned_administrator_privileges(self):
        build_script = (
            Path(__file__).resolve().parents[1] / "scripts" / "build_windows.ps1"
        ).read_text(encoding="utf-8")
        self.assertIn('"--uac-admin"', build_script)


if __name__ == "__main__":
    unittest.main()

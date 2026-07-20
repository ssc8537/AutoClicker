import os
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("MYAUTOPLAYER_DISABLE_AUDIO", "1")

from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QLabel,
    QComboBox,
    QGroupBox,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QStyle,
    QStyleOptionViewItem,
    QStyleOptionSpinBox,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor
from PySide6.QtTest import QTest
from src.ui.ai_prompt_dialog import AiPromptDialog, build_ai_prompt_content, load_prompt_template
from src.ui.macro_library_panel import MacroEditorDialog, MacroLibraryPanel
from src.ui.game_keybinds_panel import GameKeybindsPanel
from src.ui.appearance import (
    AppearanceSettings,
    AppearanceSettingsStore,
    CLASSIC_LAYOUT,
    CLASSIC_THEME,
    GALLERY_LAYOUT,
    SAKURA_THEME,
)
from src.ui.table_selection import PreserveForegroundSelectionDelegate
from src.ui.window_chrome import VerticalResizeHandle, WindowTitleBar
from src.core.macro_file_manager import MacroFileError
from src.core.hotkey_manager import TriggerMode

from main import MainWindow
from src.core.script_engine import PythonMacroRuntime


VALID_MACRO = 'NAME="x"\nHOTKEY="f9"\nMODE="switch"\nCOUNT=1\nSPEED=1\ndef run(player): pass\n'


class UiShellTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.appearance_directory = tempfile.TemporaryDirectory()
        self.window = MainWindow.__new__(MainWindow)
        QMainWindow.__init__(self.window)
        self.window._appearance_store = AppearanceSettingsStore(
            Path(self.appearance_directory.name) / "settings.json"
        )
        self.window._appearance = AppearanceSettings()
        self.window._setup_ui()

    def tearDown(self):
        self.window.deleteLater()
        self.appearance_directory.cleanup()

    def test_window_is_fixed_width_and_vertically_resizable(self):
        self.assertFalse(self.window.windowIcon().isNull())
        self.assertEqual(self.window.width(), 642)
        self.assertEqual(self.window.minimumWidth(), 642)
        self.assertGreater(self.window.maximumWidth(), 642)
        self.assertEqual(self.window.minimumHeight(), 510)
        self.assertGreaterEqual(self.window.maximumHeight(), 510)
        screen = QApplication.primaryScreen()
        self.assertIsNotNone(screen)
        self.assertEqual(
            self.window.frameGeometry().center(), screen.availableGeometry().center()
        )
        self.assertIsNotNone(self.window.findChild(WindowTitleBar, "window_title_bar"))
        self.assertIsNotNone(self.window.findChild(VerticalResizeHandle, "vertical_resize_handle"))

    def test_vertical_resize_handle_changes_only_height(self):
        self.window.show()
        resize_handle = self.window.findChild(VerticalResizeHandle, "vertical_resize_handle")
        original_height = self.window.height()
        original_width = self.window.width()
        QTest.mousePress(resize_handle, Qt.MouseButton.LeftButton, pos=resize_handle.rect().center())
        QTest.mouseMove(resize_handle, resize_handle.rect().center() + QPoint(0, 40))
        QTest.mouseRelease(resize_handle, Qt.MouseButton.LeftButton, pos=resize_handle.rect().center() + QPoint(0, 40))
        self.assertGreater(self.window.height(), original_height)
        self.assertEqual(self.window.width(), original_width)

    def test_right_edge_resize_handle_changes_window_width(self):
        self.window.show()
        resize_handle = self.window.findChild(QWidget, "window_resize_right")
        self.assertIsNotNone(resize_handle)
        original_width = self.window.width()
        original_height = self.window.height()
        QTest.mousePress(
            resize_handle,
            Qt.MouseButton.LeftButton,
            pos=resize_handle.rect().center(),
        )
        QTest.mouseMove(resize_handle, resize_handle.rect().center() + QPoint(48, 0))
        QTest.mouseRelease(
            resize_handle,
            Qt.MouseButton.LeftButton,
            pos=resize_handle.rect().center() + QPoint(48, 0),
        )
        self.assertGreater(self.window.width(), original_width)
        self.assertEqual(self.window.height(), original_height)

    def test_four_tabs_default_to_macro_library(self):
        tabs = self.window.findChild(QTabWidget, "main_tabs")
        self.assertIsNotNone(tabs)
        self.assertEqual(tabs.currentIndex(), 0)
        self.assertEqual([tabs.tabText(index) for index in range(tabs.count())], ["宏库", "触发", "功能", "设置"])
        tabs.setCurrentIndex(2)
        self.assertEqual(tabs.currentIndex(), 2)

    def test_trigger_table_prioritizes_name_width_and_short_status(self):
        table = self.window.findChild(QTableWidget, "trigger_table")
        self.assertGreater(table.columnWidth(1), table.columnWidth(2))
        self.assertGreater(table.columnWidth(1), table.columnWidth(4))
        self.assertEqual(table.columnWidth(4), 44)
        self.assertEqual(
            table.horizontalHeader().sectionResizeMode(1),
            table.horizontalHeader().ResizeMode.Stretch,
        )
        titles = {group.title() for group in self.window.findChildren(QGroupBox)}
        self.assertIn("触发详情（自动保存）", titles)

    def test_trigger_spin_box_arrows_are_visible_and_clickable(self):
        self.window.findChild(QTabWidget, "main_tabs").setCurrentIndex(1)
        self.window.show()
        self.app.processEvents()
        field = self.window._trigger_speed_field
        field.setEnabled(True)
        field.setValue(1.0)
        option = QStyleOptionSpinBox()
        field.initStyleOption(option)
        up_rect = field.style().subControlRect(
            QStyle.ComplexControl.CC_SpinBox,
            option,
            QStyle.SubControl.SC_SpinBoxUp,
            field,
        )
        down_rect = field.style().subControlRect(
            QStyle.ComplexControl.CC_SpinBox,
            option,
            QStyle.SubControl.SC_SpinBoxDown,
            field,
        )
        self.assertFalse(up_rect.isEmpty())
        self.assertFalse(down_rect.isEmpty())
        self.assertEqual(type(field).__name__, "RoseDoubleSpinBox")
        self.assertEqual(field.grab().toImage().pixelColor(up_rect.center()).name(), "#6e4055")
        self.assertEqual(field.grab().toImage().pixelColor(down_rect.center()).name(), "#6e4055")
        QTest.mouseClick(field, Qt.MouseButton.LeftButton, pos=up_rect.center())
        self.assertGreater(field.value(), 1.0)

    def test_clicking_an_unselected_status_cell_toggles_that_row_immediately(self):
        """案例行为：状态列单击以点击行保存，不要求先选中宏。"""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "first.py").write_text(VALID_MACRO, encoding="utf-8")
            target = root / "second.py"
            target.write_text(
                VALID_MACRO.replace('NAME="x"', 'NAME="second"'), encoding="utf-8"
            )
            manager = Mock()
            with patch("main._MACRO_ROOT", root), patch(
                "main.HotkeyManager", return_value=manager
            ), patch("main.OsdPopup"):
                window = MainWindow(PythonMacroRuntime())
            tabs = window.findChild(QTabWidget, "main_tabs")
            tabs.setCurrentIndex(1)
            window.show()
            self.app.processEvents()
            table = window._trigger_table
            target_row = next(
                row for row, entry in enumerate(window._macro_entries) if entry.path == target
            )
            table.clearSelection()
            self.app.processEvents()

            QTest.mouseClick(
                table.viewport(),
                Qt.MouseButton.LeftButton,
                pos=table.visualItemRect(table.item(target_row, 4)).center(),
            )
            self.app.processEvents()

            self.assertEqual(table.item(target_row, 4).text(), "禁用")
            self.assertIn("ENABLED = False", target.read_text(encoding="utf-8"))
            self.assertEqual(table.selectionModel().selectedRows()[0].row(), target_row)
            window.close()

    def test_macro_cannot_save_the_current_global_key(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "first.py"
            target.write_text(VALID_MACRO, encoding="utf-8")
            manager = Mock()
            with patch("main._MACRO_ROOT", root), patch(
                "main.HotkeyManager", return_value=manager
            ), patch("main.OsdPopup"), patch("main.load_global_hotkey", return_value="backquote"), patch(
                "main.QMessageBox.warning"
            ) as warning:
                window = MainWindow(PythonMacroRuntime())
                table = window._trigger_table
                table.selectRow(0)
                window._show_selected_trigger_detail()
                window._trigger_hotkey_field.set_hotkey("backquote")
                window._save_trigger_settings()
            self.assertIn("HOTKEY=\"f9\"", target.read_text(encoding="utf-8"))
            warning.assert_called_once()
            window.close()

    @unittest.skip("Stage 6B 触发页从只读控件升级为即时可编辑控件")
    def test_macro_and_trigger_pages_have_only_stage_2b_controls(self):
        buttons = {button.text(): button for button in self.window.findChildren(QPushButton)}
        self.assertTrue(buttons["新建"].isEnabled())
        self.assertTrue(buttons["重新加载"].isEnabled())
        self.assertFalse(buttons["编辑"].isEnabled())
        self.assertFalse(buttons["保存"].isEnabled())
        self.assertFalse(buttons["删除"].isEnabled())
        self.assertFalse(buttons["保存触发设置"].isEnabled())
        button_texts = {button.text() for button in self.window.findChildren(QPushButton)}
        self.assertNotIn("启用", button_texts)
        self.assertNotIn("校验", button_texts)
        macro_table = self.window.findChild(QTableWidget, "macro_library_table")
        self.assertEqual(
            [macro_table.horizontalHeaderItem(index).text() for index in range(macro_table.columnCount())],
            ["序号", "Python 宏"],
        )
        self.assertIsInstance(macro_table.parentWidget().layout(), QHBoxLayout)
        action_panel = self.window.findChild(QWidget, "macro_action_panel")
        self.assertIsInstance(action_panel.layout(), QVBoxLayout)
        self.assertTrue(
            all(
                field.isReadOnly()
                for field in self.window.findChildren(QLineEdit)
                if field.objectName() != "macro_name_field"
                and not field.objectName().startswith("game_keybind_")
            )
        )

    @unittest.skip("Stage 6B 触发详情不再只读")
    def test_trigger_page_uses_chinese_read_only_labels(self):
        label_values = {
            label.text() for label in self.window.findChildren(QLabel)
        }
        field_values = {
            field.text() for field in self.window.findChildren(QLineEdit)
        }
        self.assertTrue({"模式", "次数", "速度", "状态"}.issubset(label_values))
        self.assertIn("未选择有效宏", field_values)
        self.assertIn("F9", field_values)
        trigger_table = self.window.findChild(QTableWidget, "trigger_table")
        self.assertEqual(
            [trigger_table.horizontalHeaderItem(index).text() for index in range(trigger_table.columnCount())],
            ["序号", "名称", "按键", "模式", "状态"],
        )
        self.assertEqual(trigger_table.horizontalHeader().defaultAlignment(), Qt.AlignmentFlag.AlignCenter)
        self.assertEqual(
            trigger_table.horizontalScrollBarPolicy(), Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.window.findChild(QTabWidget, "main_tabs").setCurrentIndex(1)
        self.window.show()
        self.app.processEvents()
        self.assertEqual(trigger_table.horizontalScrollBar().maximum(), 0)
        self.assertEqual(trigger_table.horizontalScrollBar().value(), 0)

    def test_quick_click_controls_share_one_compact_row(self):
        group = self.window.findChild(QGroupBox, "quick_click_group")
        enabled = self.window.findChild(QCheckBox, "quick_click_enabled")
        hotkey = self.window.findChild(QLineEdit, "quick_click_hotkey")
        mode = self.window.findChild(QComboBox, "quick_click_mode")
        interval = self.window.findChild(QWidget, "quick_click_interval")
        self.assertIsNotNone(group)
        self.assertEqual(enabled.text(), "启用")
        self.assertEqual([mode.itemText(i) for i in range(mode.count())], ["按下", "切换"])
        controls = (enabled, hotkey, mode, interval)
        self.assertLessEqual(max(control.pos().y() for control in controls) - min(control.pos().y() for control in controls), 8)

    def test_features_page_exposes_editable_game_keybinds_and_save_button(self):
        panel = self.window.findChild(GameKeybindsPanel)
        scroll = self.window.findChild(QScrollArea, "features_scroll_area")
        self.assertIsNotNone(panel)
        self.assertTrue(scroll.widget().isAncestorOf(panel))
        self.assertEqual(
            panel.findChild(QLineEdit, "game_keybind_character_1").text(), "1"
        )
        self.assertTrue(panel.findChild(QPushButton, "save_game_keybinds_button").isEnabled())
        self.assertIsNotNone(panel.findChild(QLineEdit, "game_keybind_label_ultimate"))
        self.assertIsNotNone(panel.findChild(QLineEdit, "game_keybind_label_extension_1"))

    def test_features_page_scrolls_without_compressing_game_keybind_rows(self):
        scroll = self.window.findChild(QScrollArea, "features_scroll_area")
        panel = self.window.findChild(GameKeybindsPanel)
        self.assertIsNotNone(scroll)
        self.assertEqual(scroll.horizontalScrollBarPolicy(), Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.assertGreaterEqual(panel.minimumHeight(), panel.sizeHint().height())
        fields = [
            panel.findChild(QLineEdit, f"game_keybind_{name}")
            for name in ("character_1", "character_2", "character_3", "skill", "echo", "ultimate", "jump", "execute")
        ]
        self.window.findChild(QTabWidget, "main_tabs").setCurrentIndex(2)
        self.window.show()
        self.app.processEvents()
        for field in fields:
            scroll.ensureWidgetVisible(field)
            self.assertGreaterEqual(field.height(), 22)
        self.assertGreater(
            panel.findChild(QPushButton, "save_game_keybinds_button").pos().y(),
            fields[-1].pos().y(),
        )

    def test_settings_page_has_osd_switch_and_unclipped_status_dot(self):
        osd = self.window.findChild(QCheckBox, "osd_enabled_field")
        status = self.window.findChild(QLabel, "global_status_label")
        self.assertIsNotNone(osd)
        self.assertEqual(osd.text(), "显示 OSD 屏幕提示")
        self.assertTrue(status.text().startswith("● "))

    def test_mature_rose_theme_is_applied(self):
        stylesheet = self.window.styleSheet()
        for color in ("#FCF7FA", "#C984A1", "#6E4055", "#D8D0D6"):
            self.assertIn(color, stylesheet)

    def test_macro_sequence_numbers_are_centered(self):
        table = self.window.findChild(QTableWidget, "macro_library_table")
        self.assertEqual(
            table.horizontalHeader().defaultAlignment(), Qt.AlignmentFlag.AlignCenter
        )
        self.assertGreater(table.rowCount(), 0)
        self.assertEqual(
            table.item(0, 0).textAlignment(), int(Qt.AlignmentFlag.AlignCenter)
        )

    def test_theme_and_layout_switch_independently_and_restore_classic(self):
        theme = self.window.findChild(QComboBox, "theme_selector")
        layout = self.window.findChild(QComboBox, "layout_selector")
        side_panel = self.window.findChild(QWidget, "side_panel")
        side_navigation = self.window.findChild(QListWidget, "side_navigation")
        self.assertEqual(theme.currentData(), CLASSIC_THEME)
        self.assertEqual(layout.currentData(), CLASSIC_LAYOUT)

        theme.setCurrentIndex(theme.findData(SAKURA_THEME))
        self.app.processEvents()
        self.assertIn("#F3A8BE", self.window.styleSheet())
        self.assertEqual(self.window.width(), 642)

        layout.setCurrentIndex(layout.findData(GALLERY_LAYOUT))
        self.app.processEvents()
        self.assertEqual(
            self.window.width(),
            min(840, self.app.primaryScreen().availableGeometry().width()),
        )
        self.assertLessEqual(side_panel.width(), 108)
        self.assertFalse(side_panel.isHidden())
        self.assertTrue(self.window._tabs.tabBar().isHidden())
        self.assertTrue(
            all(
                side_navigation.item(index).textAlignment()
                == Qt.AlignmentFlag.AlignCenter
                for index in range(side_navigation.count())
            )
        )
        avatar = self.window.findChild(QLabel, "gallery_avatar")
        self.assertIsNotNone(avatar.pixmap())
        self.assertFalse(avatar.pixmap().isNull())

        self.window.findChild(QPushButton, "restore_classic_appearance").click()
        self.app.processEvents()
        self.assertEqual(theme.currentData(), CLASSIC_THEME)
        self.assertEqual(layout.currentData(), CLASSIC_LAYOUT)
        self.assertEqual(self.window.width(), 642)
        self.assertTrue(side_panel.isHidden())
        self.assertFalse(self.window._tabs.tabBar().isHidden())

    def test_selected_table_item_keeps_its_own_foreground_color(self):
        table = QTableWidget(1, 1)
        delegate = PreserveForegroundSelectionDelegate(table)
        item = QTableWidgetItem("禁用")
        item.setForeground(QColor("#d43131"))
        table.setItem(0, 0, item)
        option = QStyleOptionViewItem()
        option.state = QStyle.StateFlag.State_Selected
        prepared = delegate.option_for_index(option, table.model().index(0, 0))
        self.assertEqual(
            prepared.palette.highlightedText().color().name(), "#d43131"
        )
        plain_item = QTableWidgetItem("普通文字")
        table.setItem(0, 0, plain_item)
        plain = delegate.option_for_index(option, table.model().index(0, 0))
        self.assertEqual(
            plain.palette.highlightedText().color(), plain.palette.text().color()
        )

    @unittest.skip("Stage 6B 每个已启用宏均注册自己的触发键")
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

    def test_trigger_parameter_change_rebinds_immediately(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "instant.py").write_text(VALID_MACRO, encoding="utf-8")
            manager = Mock()
            manager.clear_pending_events.return_value = 0
            with patch("main._MACRO_ROOT", root), patch(
                "main.HotkeyManager", return_value=manager
            ), patch("main.OsdPopup"), patch("main.SoundEffects"):
                window = MainWindow(PythonMacroRuntime())
            manager.reset_mock()
            manager.clear_pending_events.return_value = 0
            window._trigger_table.selectRow(0)
            window._show_selected_trigger_detail()
            start = time.monotonic()
            window._trigger_mode_field.setCurrentIndex(1)
            self.app.processEvents()
            self.assertLess(time.monotonic() - start, 1.0)
            self.assertTrue(
                any(call.kwargs.get("mode") == TriggerMode.DOWN for call in manager.register.call_args_list)
            )
            manager.clear_pending_events.assert_called()
            window.deleteLater()

    @unittest.skip("Stage 6B 状态改为每个宏独立启用，不再唯一活动宏")
    def test_activity_status_is_unique_and_invalidated_macro_stops(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first.py"
            second = root / "second.py"
            invalid = root / "invalid.py"
            first.write_text(VALID_MACRO.replace('NAME="x"', 'NAME="first"'), encoding="utf-8")
            second.write_text(VALID_MACRO.replace('NAME="x"', 'NAME="second"'), encoding="utf-8")
            invalid.write_text("NAME = 'invalid'\n", encoding="utf-8")
            runtime = PythonMacroRuntime()
            manager = Mock()

            with patch("main._MACRO_ROOT", root):
                with patch("main.HotkeyManager", return_value=manager), patch("main.OsdPopup"):
                    window = MainWindow(runtime)

                panel = window._macro_panel
                rows = {entry.path.name: index for index, entry in enumerate(panel.entries)}
                first_row = rows["first.py"]
                second_row = rows["second.py"]
                invalid_row = rows["invalid.py"]
                self.assertEqual(
                    [panel.table.item(first_row, column).text() for column in range(2)],
                    [str(first_row + 1), "first"],
                )
                self.assertEqual(panel.table.item(invalid_row, 1).text(), "invalid")
                self.assertEqual(panel.table.item(invalid_row, 1).foreground().color().name(), "#ff0000")
                panel.table.selectRow(first_row)
                self.assertIsNone(runtime.selected_path())
                self.assertEqual(panel._name_field.text(), "first")
                self.assertTrue(panel._edit_button.isEnabled())
                self.assertTrue(panel._save_button.isEnabled())
                trigger_rows = {
                    window._trigger_table.item(row, 1).text(): row
                    for row in range(window._trigger_table.rowCount())
                }
                self.assertEqual(set(trigger_rows), {"first", "second", "invalid"})
                self.assertEqual(
                    [window._trigger_table.item(row, 0).text() for row in range(window._trigger_table.rowCount())],
                    ["1", "2", "3"],
                )
                self.assertEqual(window._trigger_table.item(trigger_rows["first"], 2).text(), "F9")
                self.assertEqual(window._trigger_table.item(trigger_rows["first"], 3).text(), "切换")
                self.assertEqual(window._trigger_table.item(trigger_rows["invalid"], 4).text(), "不可启用")
                self.assertEqual(
                    window._trigger_table.item(trigger_rows["invalid"], 1).foreground().color().name(),
                    "#ff0000",
                )
                for row in range(window._trigger_table.rowCount()):
                    for column in range(window._trigger_table.columnCount()):
                        self.assertEqual(
                            window._trigger_table.item(row, column).textAlignment(),
                            int(Qt.AlignmentFlag.AlignCenter),
                        )
                window._trigger_table.selectRow(trigger_rows["first"])
                self.assertEqual(window._trigger_mode_field.text(), "切换")
                self.assertEqual(window._trigger_count_field.text(), "1")
                self.assertEqual(window._trigger_speed_field.text(), "1.0")
                self.assertEqual(window._trigger_status_field.text(), "禁用")

                window._on_trigger_cell_clicked(trigger_rows["first"], 4)
                self.assertEqual(runtime.selected_path(), first)
                self.assertEqual(window._trigger_table.item(trigger_rows["first"], 4).text(), "启用")
                self.assertTrue(panel._edit_button.isEnabled())
                self.assertTrue(panel._save_button.isEnabled())
                self.assertTrue(panel._delete_button.isEnabled())
                window._on_trigger_cell_clicked(trigger_rows["second"], 4)
                self.assertEqual(runtime.selected_path(), second)
                self.assertEqual(window._trigger_table.item(trigger_rows["first"], 4).text(), "禁用")
                self.assertEqual(window._trigger_table.item(trigger_rows["second"], 4).text(), "启用")
                window._on_trigger_cell_clicked(trigger_rows["second"], 4)
                self.assertIsNone(runtime.selected_path())
                window._on_trigger_cell_clicked(trigger_rows["invalid"], 4)
                self.assertIsNone(runtime.selected_path())

                window._on_trigger_cell_clicked(trigger_rows["first"], 4)
                window._dispatcher.stop_active_execution = Mock()
                first.write_text("NAME = 'broken'\n", encoding="utf-8")
                panel.refresh()
                self.assertIsNone(runtime.selected_path())
                window._dispatcher.stop_active_execution.assert_called_once()
                manager.mark_finished.assert_called_once_with("f9")
                self.assertEqual(panel.table.item(first_row, 1).text(), "first")
                self.assertEqual(panel.table.item(first_row, 1).foreground().color().name(), "#ff0000")

                panel._schedule_refresh(str(second))
                self.assertTrue(panel.refresh_timer.isActive())
                window.close()

    @unittest.skip("Stage 6B 删除通过每宏绑定停止，不再依赖 F9 当前选择")
    def test_active_macro_rename_preserves_activity_for_next_f9_and_delete_stops_first(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = root / "first.py"
            original.write_text(VALID_MACRO.replace('NAME="x"', 'NAME="first"'), encoding="utf-8")
            runtime = PythonMacroRuntime()
            manager = Mock()
            with patch("main._MACRO_ROOT", root), patch("main.HotkeyManager", return_value=manager), patch("main.OsdPopup"):
                window = MainWindow(runtime)
            panel = window._macro_panel
            window._on_trigger_cell_clicked(0, 4)
            panel.table.selectRow(0)
            panel._name_field.setText("renamed")
            panel._rename_selected_macro()
            renamed = root / "renamed.py"
            self.assertEqual(runtime.selected_path(), renamed)
            self.assertFalse(original.exists())
            self.assertTrue(renamed.exists())
            self.assertEqual(window._active_macro_path, renamed)

            window._dispatcher.stop_active_execution = Mock()
            with patch("src.core.macro_file_manager._move_to_windows_recycle_bin", side_effect=lambda path: path.unlink()), patch.object(
                panel, "_confirm_delete", return_value=True
            ):
                panel._delete_button.click()
            self.assertFalse(renamed.exists())
            self.assertIsNone(runtime.selected_path())
            self.assertIsNone(window._active_macro_path)
            window._dispatcher.stop_active_execution.assert_called_once()
            manager.mark_finished.assert_called_once_with("f9")
            window.close()

    def test_delete_confirmation_cancel_keeps_selected_macro(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            macro = root / "first.py"
            macro.write_text(VALID_MACRO, encoding="utf-8")
            panel = MacroLibraryPanel(root)
            panel.table.selectRow(0)
            callback = Mock()
            panel._on_delete_requested = callback
            with patch.object(panel, "_confirm_delete", return_value=False):
                panel._delete_button.click()
            callback.assert_not_called()
            self.assertTrue(macro.exists())
            panel.deleteLater()

    def test_name_enter_uses_the_same_safe_rename_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = root / "first.py"
            original.write_text(
                VALID_MACRO.replace('NAME="x"', 'NAME="first"'), encoding="utf-8"
            )
            panel = MacroLibraryPanel(root)
            panel.table.selectRow(0)
            panel._name_field.setText("renamed")

            QTest.keyClick(panel._name_field, Qt.Key.Key_Return)
            self.app.processEvents()

            renamed = root / "renamed.py"
            self.assertTrue(renamed.is_file())
            self.assertFalse(original.exists())
            self.assertIn("NAME='renamed'", renamed.read_text(encoding="utf-8"))
            self.assertEqual(panel.table.item(0, 1).text(), "renamed")
            panel.deleteLater()

    def test_python_editor_uses_chinese_buttons_highlighting_and_python_indentation(self):
        source = 'def run(player):\n    # 注释\n    value = "彩色"\n'
        parent = QWidget()
        dialog = MacroEditorDialog(parent, "新建 Python 宏", "测试", source, lambda *_: None)
        buttons = {button.text() for button in dialog.findChildren(QPushButton)}
        self.assertTrue({"保存", "取消"}.issubset(buttons))
        editor = dialog.source_editor
        editor.setPlainText("pass")
        cursor = editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        editor.setTextCursor(cursor)
        editor.setFocus()
        QTest.keyClick(editor, Qt.Key.Key_Tab)
        self.assertEqual(editor.toPlainText(), "pass    ")

        editor.setPlainText("def run(player):")
        cursor = editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        editor.setTextCursor(cursor)
        QTest.keyClick(editor, Qt.Key.Key_Return)
        self.assertEqual(editor.toPlainText(), "def run(player):\n    ")

        editor.setPlainText("    player.sleep(50)")
        cursor = editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        editor.setTextCursor(cursor)
        QTest.keyClick(editor, Qt.Key.Key_Return)
        self.assertEqual(editor.toPlainText(), "    player.sleep(50)\n    ")

        editor.setPlainText("first\nsecond")
        cursor = editor.textCursor()
        cursor.select(cursor.SelectionType.Document)
        editor.setTextCursor(cursor)
        QTest.keyClick(editor, Qt.Key.Key_Tab)
        self.assertEqual(editor.toPlainText(), "    first\n    second")

        editor.setPlainText(source)
        editor.highlighter.rehighlight()
        self.app.processEvents()
        formats = editor.document().firstBlock().layout().formats()
        self.assertTrue(formats)
        self.assertTrue(any(item.format.foreground().color().isValid() for item in formats))
        dialog.deleteLater()
        parent.deleteLater()

    def test_ai_prompt_is_always_available_read_only_and_copies_the_current_api_template(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prompt_config = root / "prompt_config"
            prompt_config.mkdir()
            shipped_default = Path(__file__).resolve().parents[1] / "config" / "ai_prompt.default.md"
            (prompt_config / "ai_prompt.default.md").write_text(
                shipped_default.read_text(encoding="utf-8"), encoding="utf-8"
            )
            macro = root / "first.py"
            source = VALID_MACRO.replace('NAME="x"', 'NAME="first"') + "# 保留的源码注释\n"
            macro.write_text(source, encoding="utf-8")
            panel = MacroLibraryPanel(root, prompt_config_dir=prompt_config)
            actions = panel.findChild(QWidget, "macro_action_panel").layout()
            self.assertLess(actions.indexOf(panel._edit_button), actions.indexOf(panel._ai_prompt_button))
            self.assertTrue(panel._ai_prompt_button.isEnabled())

            general_prompt = panel._build_ai_prompt()
            self.assertEqual(
                (prompt_config / "ai_prompt.md").read_text(encoding="utf-8"),
                (prompt_config / "ai_prompt.default.md").read_text(encoding="utf-8"),
            )
            self.assertIn("## 3. 唯一允许使用的 `player` API", general_prompt)
            self.assertIn("player.tap(key, hold_ms=20)", general_prompt)
            self.assertIn("player.sleep(ms)", general_prompt)
            for method in ("切换(1)", "切换(2)", "切换(3)", "战技()", "声骸()", "大招()", "跳跃()", "处决()"):
                self.assertIn(f"player.{method}", general_prompt)
            self.assertIn("| `HOTKEY` |", general_prompt)
            self.assertIn('player.按键("当前动作名称"', general_prompt)
            for method in ("mouse_click", "mouse_down", "mouse_up", "mouse_repeat"):
                self.assertIn(f"player.{method}", general_prompt)
            for name in ("mouse_left", "mouse_right", "mouse_middle", "mouse_back", "mouse_forward"):
                self.assertIn(name, general_prompt)
            self.assertIn("角色 1、角色 2、角色 3", general_prompt)
            self.assertIn("特殊资源", general_prompt)
            self.assertIn("增益窗口", general_prompt)
            for direction in ("1→2", "1→3", "2→1", "2→3", "3→1", "3→2"):
                self.assertIn(direction.replace("→", " 到 "), general_prompt)
            self.assertIn("至少等待 50ms", general_prompt)
            self.assertIn("至少等待 1080ms", general_prompt)
            self.assertIn("1000ms 和 80ms 余量", general_prompt)
            self.assertIn("项目现有保守等待为 1500ms", general_prompt)
            self.assertIn("### 示例 A：按下模式与鼠标动作", general_prompt)
            self.assertIn("### 示例 B：切换模式", general_prompt)
            self.assertIn("### 示例 C：三角色确定性轮转", general_prompt)
            self.assertIn("当前共享动作映射", general_prompt)
            self.assertIn("完整按键字典", general_prompt)
            self.assertNotIn("小技能", general_prompt)
            self.assertIn("##", general_prompt)
            self.assertIn("```python", general_prompt)
            self.assertIn("\n- ", general_prompt)
            self.assertNotIn("BaseChar.py", general_prompt)

            panel.table.selectRow(0)
            selected_prompt = panel._build_ai_prompt()
            self.assertIn(source, selected_prompt)
            self.assertIn("# 保留的源码注释", selected_prompt)
            self.assertIn("```python", selected_prompt)
            dialog = AiPromptDialog(panel, selected_prompt)
            self.assertTrue(dialog.prompt_editor.isReadOnly())
            self.assertFalse(dialog.isModal())
            self.assertEqual(dialog.prompt_editor.textCursor().position(), 0)
            self.assertEqual(dialog.copy_button.text(), "复制提示词")
            dialog.copy_button.click()
            self.assertEqual(QApplication.clipboard().text(), selected_prompt)
            self.assertEqual(dialog.copy_status.text(), "提示词已复制，请粘贴给 AI")
            dialog.deleteLater()

            panel._open_ai_prompt_dialog()
            self.assertIsNotNone(panel._ai_prompt_dialog)
            self.assertFalse(panel._ai_prompt_dialog.isModal())
            self.assertTrue(panel.isEnabled())
            panel._ai_prompt_dialog.close()

            macro.write_text("NAME = 'invalid'\n", encoding="utf-8")
            panel.refresh()
            panel.table.selectRow(0)
            self.assertTrue(panel._ai_prompt_button.isEnabled())
            self.assertNotIn(source, panel._build_ai_prompt())
            with patch.object(panel._manager, "read_source", side_effect=MacroFileError("read failed")):
                self.assertNotIn(source, panel._build_ai_prompt())
            panel.deleteLater()

    def test_ai_prompt_files_are_editable_reloaded_and_fail_safe(self):
        with tempfile.TemporaryDirectory() as directory:
            config_dir = Path(directory) / "config"
            config_dir.mkdir()
            default_path = config_dir / "ai_prompt.default.md"
            current_path = config_dir / "ai_prompt.md"
            default_text = "默认模板\nplayer.tap(\"R\")\nplayer.sleep(1800)"
            default_path.write_text(default_text, encoding="utf-8")

            first = build_ai_prompt_content(config_dir=config_dir)
            self.assertEqual(current_path.read_text(encoding="utf-8"), default_text)
            self.assertIn("已从默认备份恢复", first.load.notice)
            self.assertEqual(first.load.current_path, current_path.resolve())
            self.assertEqual(first.load.default_path, default_path.resolve())

            current_path.write_text("外部修改后的提示词", encoding="utf-8")
            reopened = build_ai_prompt_content(config_dir=config_dir)
            self.assertIn("外部修改后的提示词", reopened.text)
            dialog = AiPromptDialog(self.window, reopened.text, reopened.load)
            self.assertIn(str(current_path.resolve()), dialog.path_info.text())
            self.assertIn(str(default_path.resolve()), dialog.path_info.text())
            dialog.copy_button.click()
            self.assertEqual(QApplication.clipboard().text(), reopened.text)
            dialog.deleteLater()

            original_default = default_path.read_bytes()
            current_path.unlink()
            restored = load_prompt_template(config_dir)
            self.assertEqual(current_path.read_text(encoding="utf-8"), default_text)
            self.assertEqual(default_path.read_bytes(), original_default)
            self.assertIn("已从默认备份恢复", restored.notice)

            invalid_current = b"\xff\xfe\x00"
            current_path.write_bytes(invalid_current)
            fallback = load_prompt_template(config_dir)
            self.assertEqual(fallback.template, default_text)
            self.assertIn("未覆盖当前文件", fallback.notice)
            self.assertEqual(current_path.read_bytes(), invalid_current)
            self.assertEqual(default_path.read_bytes(), original_default)

            default_path.write_bytes(b"\xff")
            unavailable = build_ai_prompt_content(config_dir=config_dir)
            self.assertIn("无法读取", unavailable.text)
            self.assertIn("没有写入任何文件", unavailable.load.notice)
            self.assertEqual(current_path.read_bytes(), invalid_current)

    @unittest.skip("Stage 6B 重载会按所有已启用宏重新注册触发键")
    def test_manual_reload_adds_external_macro_without_changing_active_runtime(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first.py"
            first.write_text(
                VALID_MACRO.replace('NAME="x"', 'NAME="first"'), encoding="utf-8"
            )
            runtime = PythonMacroRuntime()
            manager = Mock()

            with patch("main._MACRO_ROOT", root):
                with patch("main.HotkeyManager", return_value=manager), patch("main.OsdPopup"):
                    window = MainWindow(runtime)

                panel = window._macro_panel
                first_row = next(
                    row for row, entry in enumerate(panel.entries) if entry.path == first
                )
                window._on_trigger_cell_clicked(first_row, 4)
                self.assertEqual(runtime.selected_path(), first)
                register_count = manager.register.call_count

                external = root / "external.py"
                external.write_text(
                    VALID_MACRO.replace('NAME="x"', 'NAME="external"'), encoding="utf-8"
                )
                panel._reload_button.click()

                self.assertEqual(runtime.selected_path(), first)
                self.assertEqual(manager.register.call_count, register_count)
                self.assertEqual(
                    {entry.path.name for entry in panel.entries}, {"first.py", "external.py"}
                )
                self.assertEqual(
                    {
                        window._trigger_table.item(row, 1).text()
                        for row in range(window._trigger_table.rowCount())
                    },
                    {"first", "external"},
                )
                self.assertEqual(
                    window._trigger_table.item(
                        next(
                            row
                            for row in range(window._trigger_table.rowCount())
                            if window._trigger_table.item(row, 1).text() == "first"
                        ),
                        4,
                    ).text(),
                    "启用",
                )
                window.close()

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
